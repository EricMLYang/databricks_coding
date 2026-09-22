# Databricks notebook source
# DBTITLE 1,Install dependencies
# MAGIC %pip install pypdf --quiet

# COMMAND ----------

# DBTITLE 1,Restart Python
dbutils.library.restartPython()

# COMMAND ----------

# DBTITLE 1,Config - 路徑與設定
# === 設定區 ===
VOLUME_BASE_PATH = "/Volumes/micenter/mi3_datahub_prod/micenterfile_ext/unstructured_data_file"
META_TABLE = "micenter.mi3_datahub_prod.b_meta_unstructured_info"

# 路由設定（各文件類型對應的 parsed_content table）
ROUTING_MAP = {
    "financial_report": "micenter.mi3_datahub_prod.b_financial_report_parsed_content",
    "earnings_transcript": "micenter.mi3_datahub_prod.b_earnings_transcript_parsed_content",
    "presentation": "micenter.mi3_datahub_prod.b_presentation_parsed_content",
}

# presentation 類型啟用圖表描述
DESCRIPTION_ELEMENT_TYPES = {
    "presentation": "figure",
    "financial_report": "",
    "earnings_transcript": "",
}

# COMMAND ----------

# DBTITLE 1,Step 1 - 取得未解析的檔案
# ============================================================
# 前置清理：將 parsed_content 中 status='failed' 的檔案
# 重設 meta 表的 is_parsed = FALSE，讓下次執行時自動重試
# ============================================================
for source_folder, parsed_table in ROUTING_MAP.items():
    reset_result = spark.sql(f"""
        UPDATE {META_TABLE}
        SET is_parsed = FALSE
        WHERE file_id IN (
            SELECT DISTINCT file_id FROM {parsed_table} WHERE status = 'failed'
        )
    """)
    failed_count = spark.sql(f"""
        SELECT COUNT(DISTINCT file_id) AS cnt FROM {parsed_table} WHERE status = 'failed'
    """).collect()[0].cnt
    if failed_count > 0:
        print(f'🔄 [{source_folder}] 重設 {failed_count} 個解析失敗檔案的 is_parsed 為 FALSE，將重新擷取')

# 遍歷所有 source_folder，收集待解析檔案
all_unparsed = {}  # {source_folder: [Row(file_id, batch_id, file_path, file_name), ...]}

for source_folder in ROUTING_MAP.keys():
    files = spark.sql(f"""
        SELECT file_id, batch_id, file_path, file_name
        FROM {META_TABLE}
        WHERE source_folder = '{source_folder}' AND is_parsed = FALSE
    """).collect()
    
    if files:
        all_unparsed[source_folder] = files
        print(f'📄 [{source_folder}] 找到 {len(files)} 個待解析檔案')
        for row in files:
            print(f'      - {row.file_name}')
    else:
        print(f'ℹ️  [{source_folder}] 無待解析檔案')

if not all_unparsed:
    print('\nℹ️ 所有類型皆無待解析檔案')
else:
    total = sum(len(v) for v in all_unparsed.values())
    print(f'\n📊 總計 {total} 個檔案待解析')

# COMMAND ----------

# DBTITLE 1,Step 2 - 整檔解析（一次處理整個檔案）
import io
import time
from datetime import datetime
from pypdf import PdfReader
from pyspark.sql.types import StructType, StructField, BinaryType, StringType, IntegerType, TimestampType, BooleanType
from pyspark.sql import Row

# 解析設定
MAX_RETRIES = 3   # 每檔最多重試次數
SLEEP_BETWEEN_FILES = 15  # 每個檔案處理完後的等待秒數，避免連續呼叫觸發 API rate limit

# parsed_content 表的 schema
PARSED_SCHEMA = StructType([
    StructField('file_id', StringType()),
    StructField('batch_id', StringType()),
    StructField('file_name', StringType()),
    StructField('content', StringType()),
    StructField('parse_time', TimestampType()),
    StructField('total_pages', IntegerType()),
    StructField('status', StringType()),
    StructField('is_extracted', BooleanType()),
])

if not all_unparsed:
    dbutils.notebook.exit('無待解析檔案，結束執行')

# 遍歷所有文件類型
for source_folder, unparsed_files in all_unparsed.items():
    PARSED_TABLE = ROUTING_MAP[source_folder]
    desc_element_types = DESCRIPTION_ELEMENT_TYPES.get(source_folder, "")
    
    print(f"\n{'#'*60}")
    print(f'# 處理類型: {source_folder} ({len(unparsed_files)} 個檔案)')
    if desc_element_types:
        print(f'# 圖表描述: 啟用 (descriptionElementTypes={desc_element_types})')
    print(f"{'#'*60}")
    
    for file_row in unparsed_files:
        file_id = file_row.file_id
        batch_id = file_row.batch_id
        file_path = file_row.file_path.replace('dbfs:/Volumes/', '/Volumes/')
        file_name = file_row.file_name
        
        print(f"\n{'='*60}")
        print(f'開始處理: {file_name}')
        print(f'路徑: {file_path}')
        print(f"{'='*60}")
        
        # 取得 PDF 總頁數
        try:
            with open(file_path, 'rb') as f:
                pdf_binary = f.read()
            reader = PdfReader(io.BytesIO(pdf_binary))
            total_pages = len(reader.pages)
            print(f'📄 PDF 總頁數: {total_pages}')
            
            # 建立暫存表放入 binary
            pdf_schema = StructType([StructField('content', BinaryType(), True)])
            pdf_df = spark.createDataFrame([(bytearray(pdf_binary),)], schema=pdf_schema)
            pdf_df.createOrReplaceTempView('current_pdf_binary')
        except Exception as e:
            print(f'✗ 無法讀取 PDF: {str(e)[:200]}')
            # 寫入失敗紀錄（用 DataFrame write 避免字串轉義問題）
            fail_row = [(file_id, batch_id, file_name, None, datetime.now(), 0, 'failed', False)]
            spark.createDataFrame(fail_row, schema=PARSED_SCHEMA) \
                .write.mode('append').saveAsTable(PARSED_TABLE)
            continue
        
        # 寫入前先刪除同一 file_id 的舊記錄（冒冪性）
        # 防止中斷重試時產生重複記錄
        spark.sql(f"DELETE FROM {PARSED_TABLE} WHERE file_id = '{file_id}'")

        # === 整檔解析（一次呼叫 ai_parse_document 處理整個檔案） ===
        print(f'\n開始整檔解析...')
        file_start = time.time()
        parse_success = False
        
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                # 不指定 pageRange，讓 ai_parse_document 一次處理整個檔案
                result_df = spark.sql(f"""
                    SELECT CAST(ai_parse_document(
                        content,
                        MAP('version', '2.0', 'descriptionElementTypes', '{desc_element_types}')
                    ) AS STRING) AS parsed_content
                    FROM current_pdf_binary
                """)
                parsed_content = result_df.collect()[0].parsed_content
                
                # 用 DataFrame write 寫入（避免大型 JSON 字串轉義問題）
                success_row = [(file_id, batch_id, file_name, parsed_content, 
                               datetime.now(), total_pages, 'success', False)]
                spark.createDataFrame(success_row, schema=PARSED_SCHEMA) \
                    .write.mode('append').saveAsTable(PARSED_TABLE)
                
                elapsed = time.time() - file_start
                parse_success = True
                print(f'  ✓ 整檔解析完成（耗時 {elapsed:.1f}s，內容長度: {len(parsed_content):,} 字元）')
                break
            except Exception as e:
                if attempt < MAX_RETRIES:
                    err_str = str(e).lower()
                    is_rate_limit = any(kw in err_str for kw in ['429', 'rate limit', 'resource_exhausted', 'quota', 'too many requests'])
                    wait_time = (120 * attempt) if is_rate_limit else (30 * attempt)
                    hint = '（偵測到 rate limit，延長等待）' if is_rate_limit else ''
                    print(f'  ⚠ 第 {attempt} 次嘗試失敗，{wait_time}s 後重試{hint}... ({str(e)[:150]})')
                    time.sleep(wait_time)
                else:
                    print(f'  ✗ 重試 {MAX_RETRIES} 次後仍失敗: {str(e)[:200]}')
        
        if not parse_success:
            # 寫入失敗紀錄
            fail_row = [(file_id, batch_id, file_name, None, datetime.now(), total_pages, 'failed', False)]
            spark.createDataFrame(fail_row, schema=PARSED_SCHEMA) \
                .write.mode('append').saveAsTable(PARSED_TABLE)
        
        # 更新 meta 表
        spark.sql(f"""
            UPDATE {META_TABLE} SET is_parsed = TRUE
            WHERE file_id = '{file_id}'
        """)
        print(f'  ✓ 已更新 meta 表 is_parsed = TRUE')
        # 每個檔案處理完後稍作等待，避免連續呼叫觸發 API rate limit
        print(f'  ⏸ 等待 {SLEEP_BETWEEN_FILES}s 後繼續...')
        time.sleep(SLEEP_BETWEEN_FILES)

print(f'\n✅ 所有檔案解析完成')

# COMMAND ----------

# DBTITLE 1,Step 3 - 驗證解析結果
# 顯示本次解析的結果摘要
for source_folder, parsed_table in ROUTING_MAP.items():
    folder_ids = [f"'{r.file_id}'" for r in all_unparsed.get(source_folder, [])]
    if not folder_ids:
        continue
    print(f'\n=== {source_folder} ===')
    display(spark.sql(f"""
        SELECT file_name, total_pages, status,
               LENGTH(content) AS content_length,
               parse_time
        FROM {parsed_table}
        WHERE file_id IN ({','.join(folder_ids)})
        ORDER BY file_name
    """))

# COMMAND ----------

# DBTITLE 1,Step 4 - 回填 company_name（AI 辨識）
# ============================================================
# Step 4: 回填 company_name（混合策略 D — AI 辨識）
# 對於檔名無法取得公司名的記錄，
# 從剛解析完的 parsed_content 內容用 AI 辨識公司名並回填 meta 表。
# ============================================================

AI_MODEL = "databricks-claude-sonnet-4-6"

COMPANY_EXTRACT_PROMPT = """Based on the following text from a financial report/earnings document, identify the company that PUBLISHED this report.
Return ONLY the company's common short name (e.g. "Dell", "HP Inc", "Lenovo").
Do NOT include suffixes like "Inc.", "Corp.", "Technologies" unless it's part of the commonly used name.
If you cannot determine the company, return exactly "UNKNOWN".
{existing_hint}
Text:
{text}
"""


def get_existing_company_names():
    """取得 meta 表中已有的公司名稱（排除 UNKNOWN）"""
    rows = spark.sql(f"""
        SELECT DISTINCT company_name FROM {META_TABLE}
        WHERE company_name != 'UNKNOWN'
    """).collect()
    return [r.company_name for r in rows]


def normalize_company_name(ai_result: str, existing_names: list) -> str:
    """
    正規化公司名：若 AI 回傳的名稱與已存在的名稱屬於同一公司，統一使用既有名稱。
    比對邏輯：
      - 完全匹配（不分大小寫）
      - 包含關係（"Dell Technologies" 包含已有的 "Dell"）
    """
    ai_lower = ai_result.lower().strip()
    for name in existing_names:
        name_lower = name.lower().strip()
        # 完全匹配
        if ai_lower == name_lower:
            return name
        # AI 結果包含既有名稱（e.g. "Dell Technologies" contains "Dell"）
        if name_lower in ai_lower:
            return name
        # 既有名稱包含 AI 結果（e.g. 既有 "Dell Technologies"，AI 回 "Dell"）
        if ai_lower in name_lower:
            return name
    # 無匹配，使用 AI 原始結果
    return ai_result


def identify_company_with_ai(text: str, existing_names: list) -> str:
    """用 AI 從文字內容辨識公司名稱，並正規化為既有名稱"""
    truncated = text[:2000]
    # 將已有公司名加入 prompt，引導 AI 回傳一致的名稱
    existing_hint = ""
    if existing_names:
        existing_hint = f"\nExisting company names in our system: {', '.join(existing_names)}. If the company matches one of these, use that exact name.\n"
    prompt = COMPANY_EXTRACT_PROMPT.format(text=truncated, existing_hint=existing_hint)
    result = spark.sql(
        "SELECT ai_query(:model, :prompt) AS company_name",
        args={"model": AI_MODEL, "prompt": prompt}
    ).collect()[0].company_name
    ai_result = result.strip().strip('"').strip("'")
    # 二次正規化確保一致性
    return normalize_company_name(ai_result, existing_names)


def backfill_company_from_parsed_content():
    """
    對 company_name = 'UNKNOWN' 且已完成 parse 的記錄，
    用 AI 從 parsed_content 辨識公司名並回填 meta 表。
    """
    unknown_files = spark.sql(f"""
        SELECT file_id, file_name, fiscal_period, source_folder, batch_id
        FROM {META_TABLE}
        WHERE company_name = 'UNKNOWN' AND is_parsed = TRUE
    """).collect()

    if not unknown_files:
        print("ℹ️  無需回填（沒有 UNKNOWN 且已 parsed 的記錄）")
        return 0

    print(f"🔍 找到 {len(unknown_files)} 筆待回填記錄...\n")
    updated_count = 0

    for row in unknown_files:
        parsed_table = ROUTING_MAP.get(row.source_folder)
        if not parsed_table:
            print(f"  ⚠️  {row.file_name} - 無對應 routing，跳過")
            continue

        # 從 parsed_content 表取內容（截取前段）
        try:
            content_rows = spark.sql(f"""
                SELECT LEFT(content, 3000) AS text_content
                FROM {parsed_table}
                WHERE file_id = '{row.file_id}'
                LIMIT 1
            """).collect()
        except Exception:
            print(f"  ⚠️  {row.file_name} - 無法讀取解析內容，跳過")
            continue

        if not content_rows or not content_rows[0].text_content:
            print(f"  ⚠️  {row.file_name} - 尚無解析內容，跳過")
            continue

        search_text = content_rows[0].text_content

        # AI 辨識公司名
        existing_names = get_existing_company_names()
        try:
            company_name = identify_company_with_ai(search_text, existing_names)
        except Exception as e:
            print(f"  ⚠️  {row.file_name} - AI 辨識失敗: {e}")
            continue

        if not company_name or company_name == "UNKNOWN":
            print(f"  ❓ {row.file_name} - AI 無法辨識公司，保持 UNKNOWN")
            continue

        # 查找是否已有該 company+period 的 batch_id（合併到現有 batch）
        existing_batch = spark.sql(f"""
            SELECT DISTINCT batch_id FROM {META_TABLE}
            WHERE company_name = '{company_name}' AND fiscal_period = '{row.fiscal_period}'
            AND company_name != 'UNKNOWN'
            LIMIT 1
        """).collect()

        new_batch_id = existing_batch[0].batch_id if existing_batch else row.batch_id

        # 更新 meta 表
        spark.sql(f"""
            UPDATE {META_TABLE}
            SET company_name = '{company_name}', batch_id = '{new_batch_id}'
            WHERE file_id = '{row.file_id}'
        """)
        # 同步更新 parsed_content 表的 batch_id（確保後續 notebook 18 一致）
        spark.sql(f"""
            UPDATE {parsed_table}
            SET batch_id = '{new_batch_id}'
            WHERE file_id = '{row.file_id}'
        """)
        updated_count += 1
        print(f"  ✅ {row.file_name} → {company_name} (batch: {new_batch_id[:8]}...)")

    print(f"\n📊 共回填 {updated_count}/{len(unknown_files)} 筆公司名稱")
    return updated_count


# === 執行回填 ===
backfill_company_from_parsed_content()

# COMMAND ----------

# DBTITLE 1,Step 5 - 補填 calendar_period（AI 轉換）
import re

# ============================================================
# Step 5: 補填 calendar_period
# 對所有 calendar_period IS NULL 且 company_name 已確認的記錄，
# 透過 AI 將 fiscal_period 轉換為日曆季度并寫回 meta 表。
# 此步在 Step 4 company_name 回填完成後執行，確保轉換時公司名稱已可靠。
# ============================================================

AI_MODEL_CALENDAR = "databricks-claude-sonnet-4-6"

# session 內快取，避免相同 (company, fiscal_period) 重複呼叫 AI
_cal_period_cache: dict = {}


def fiscal_to_calendar_period(company_name: str, fiscal_period: str) -> str:
    """
    使用 AI 將會計季度（QXFYXX）轉換為日曆季度（QXCYXX）。
    無需維護公司 FY 起始月份名單，AI 依公司知識自動判斷。
    Fallback：直接將 FY 替換為 CY（不做季度偏移）。
    """
    if not fiscal_period or fiscal_period == 'UNKNOWN':
        return fiscal_period
    if not re.match(r'Q\d+FY\d{2,4}', fiscal_period, re.IGNORECASE):
        return fiscal_period  # 已是日曆格式或非標準格式，原樣回傳

    cache_key = f"{company_name}|{fiscal_period}"
    if cache_key in _cal_period_cache:
        return _cal_period_cache[cache_key]

    prompt = (
        f"Convert fiscal period to calendar quarter. "
        f"Company: {company_name}. Fiscal period: {fiscal_period}. "
        f"Reply ONLY with the calendar quarter in format Q#CY## using 2-digit year "
        f"(examples: Q1CY26, Q4CY25). No explanation."
    )
    prompt_safe = prompt.replace("'", "''")

    try:
        result = spark.sql(f"""
            SELECT TRIM(ai_query('{AI_MODEL_CALENDAR}', '{prompt_safe}')) AS cal_period
        """).collect()[0][0]

        match = re.search(r'Q\dCY\d{2,4}', result.upper())
        if match:
            cal_period = match.group(0)
            _cal_period_cache[cache_key] = cal_period
            return cal_period
    except Exception as e:
        print(f'      ⚠️  AI 轉換失敗（{company_name} {fiscal_period}）: {e}')

    # Fallback：直接 FY → CY，不做季度偏移
    fallback = re.sub(r'FY', 'CY', fiscal_period, flags=re.IGNORECASE).upper()
    _cal_period_cache[cache_key] = fallback
    return fallback


# 查詢需補填的記錄：calendar_period IS NULL 且 company_name / fiscal_period 已知
pending_rows = spark.sql(f"""
    SELECT DISTINCT company_name, fiscal_period
    FROM {META_TABLE}
    WHERE calendar_period IS NULL
      AND company_name  != 'UNKNOWN'
      AND fiscal_period != 'UNKNOWN'
""").collect()

if not pending_rows:
    print('⛹️  所有記錄 calendar_period 已補填，無需處理')
else:
    print(f'🗓️  複填 calendar_period：共 {len(pending_rows)} 個（company, fiscal_period）組合\n')
    updated = 0
    for row in pending_rows:
        cal = fiscal_to_calendar_period(row.company_name, row.fiscal_period)
        company_safe = row.company_name.replace("'", "''")
        fiscal_safe  = row.fiscal_period.replace("'", "''")
        spark.sql(f"""
            UPDATE {META_TABLE}
            SET    calendar_period = '{cal}'
            WHERE  company_name  = '{company_safe}'
              AND  fiscal_period = '{fiscal_safe}'
              AND  calendar_period IS NULL
        """)
        print(f'   ✅ {row.company_name:20s} {row.fiscal_period} → {cal}')
        updated += 1
    print(f'\n✅ calendar_period 補填完成，共更新 {updated} 個組合')


