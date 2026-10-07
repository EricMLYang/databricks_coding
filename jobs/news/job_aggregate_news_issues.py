# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# ///
# DBTITLE 1,Install Dependencies
# MAGIC %pip install pydantic jinja2 tiktoken psycopg2-binary httpx -q

# COMMAND ----------

# DBTITLE 1,Diagnostic: Check Latest PostgreSQL Record
# === Diagnostic: Check latest record in PostgreSQL ===
import psycopg2
from datetime import datetime
import pytz

tz = pytz.timezone("Asia/Taipei")
today = datetime.now(tz).date()

PG_HOST = dbutils.secrets.get(scope="mi3-postgres", key="pg-host")
PG_USER = dbutils.secrets.get(scope="mi3-postgres", key="pg-user")
PG_PASS = dbutils.secrets.get(scope="mi3-postgres", key="pg-password")
PG_DB   = dbutils.secrets.get(scope="mi3-postgres", key="pg-database")

try:
    conn = psycopg2.connect(host=PG_HOST, port=5432, dbname=PG_DB, user=PG_USER, password=PG_PASS, sslmode="require")
    cur = conn.cursor()

    cur.execute("""
        SELECT brief_date, title, status, created_by, created_at
        FROM public.app_custom_reports
        ORDER BY brief_date DESC
        LIMIT 5
    """)
    rows = cur.fetchall()

    print(f"✅ Connected to PostgreSQL: {PG_HOST}")
    print(f"📅 Today (Taipei): {today}")
    print(f"\n📋 app_custom_reports (latest 5 records):")
    print(f"{'brief_date':<14} {'status':<12} {'created_by':<16} {'created_at':<22} {'title'}")
    print("-" * 110)
    for row in rows:
        print(f"{str(row[0]):<14} {str(row[2]):<12} {str(row[3]):<16} {str(row[4]):<22} {str(row[1])[:50]}")

    # Check if today's data exists
    cur.execute("SELECT COUNT(*) FROM public.app_custom_reports WHERE brief_date = %s", (today,))
    today_count = cur.fetchone()[0]
    yesterday = today - __import__('datetime').timedelta(days=1)
    cur.execute("SELECT COUNT(*) FROM public.app_custom_reports WHERE brief_date = %s", (yesterday,))
    yesterday_count = cur.fetchone()[0]

    print(f"\n📊 Today ({today}) records: {today_count}")
    print(f"📊 Yesterday ({yesterday}) records: {yesterday_count}")

    cur.close()
    conn.close()
except Exception as e:
    print(f"❌ PostgreSQL connection failed: {type(e).__name__}: {e}")

# COMMAND ----------

# DBTITLE 1,Diagnostic: Check PostgreSQL Data
# MAGIC %md
# MAGIC # === Diagnostic: Verify PostgreSQL has data ===
# MAGIC import psycopg2
# MAGIC
# MAGIC PG_HOST = dbutils.secrets.get(scope="mi3-postgres", key="pg-host")
# MAGIC PG_USER = dbutils.secrets.get(scope="mi3-postgres", key="pg-user")
# MAGIC PG_PASS = dbutils.secrets.get(scope="mi3-postgres", key="pg-password")
# MAGIC PG_DB   = dbutils.secrets.get(scope="mi3-postgres", key="pg-database")
# MAGIC
# MAGIC try:
# MAGIC     conn = psycopg2.connect(host=PG_HOST, port=5432, dbname=PG_DB, user=PG_USER, password=PG_PASS, sslmode="require")
# MAGIC     cur = conn.cursor()
# MAGIC     
# MAGIC     cur.execute("""
# MAGIC         SELECT brief_date, title, status, created_at
# MAGIC         FROM public.app_custom_reports
# MAGIC         ORDER BY brief_date DESC
# MAGIC         LIMIT 10
# MAGIC     """)
# MAGIC     rows = cur.fetchall()
# MAGIC     
# MAGIC     print(f"✅ Connected to PostgreSQL: {PG_HOST}")
# MAGIC     print(f"\n📋 app_custom_reports (latest records):")
# MAGIC     print(f"{'brief_date':<14} {'status':<12} {'created_at':<22} {'title'}")
# MAGIC     print("-" * 90)
# MAGIC     for row in rows:
# MAGIC         print(f"{str(row[0]):<14} {str(row[2]):<12} {str(row[3]):<22} {str(row[1])[:50]}")
# MAGIC     
# MAGIC     cur.execute("SELECT COUNT(*) FROM public.app_custom_reports")
# MAGIC     total = cur.fetchone()[0]
# MAGIC     print(f"\nTotal records: {total}")
# MAGIC     
# MAGIC     cur.close()
# MAGIC     conn.close()
# MAGIC except Exception as e:
# MAGIC     print(f"❌ PostgreSQL connection failed: {e}")

# COMMAND ----------

# DBTITLE 1,Patch: Update existing records to published + ericmlyang
# MAGIC %md
# MAGIC # === Patch: 將所有 draft 改為 published，created_by 改為 ericmlyang ===
# MAGIC import psycopg2
# MAGIC
# MAGIC # --- 1. Update Delta Table ---
# MAGIC spark.sql("""
# MAGIC     UPDATE micenter.mi3_datahub_prod.s_news_issue_reports
# MAGIC     SET status = 'published',
# MAGIC         created_by = 'ericmlyang',
# MAGIC         updated_by = 'ericmlyang',
# MAGIC         updated_at = current_timestamp()
# MAGIC     WHERE status = 'draft'
# MAGIC """)
# MAGIC print("✅ Delta table updated: all draft → published, created_by → ericmlyang")
# MAGIC
# MAGIC # --- 2. Update PostgreSQL ---
# MAGIC PG_HOST = dbutils.secrets.get(scope="mi3-postgres", key="pg-host")
# MAGIC PG_USER = dbutils.secrets.get(scope="mi3-postgres", key="pg-user")
# MAGIC PG_PASS = dbutils.secrets.get(scope="mi3-postgres", key="pg-password")
# MAGIC PG_DB   = dbutils.secrets.get(scope="mi3-postgres", key="pg-database")
# MAGIC
# MAGIC try:
# MAGIC     conn = psycopg2.connect(host=PG_HOST, port=5432, dbname=PG_DB, user=PG_USER, password=PG_PASS, sslmode="require")
# MAGIC     cur = conn.cursor()
# MAGIC     
# MAGIC     cur.execute("""
# MAGIC         UPDATE public.app_custom_reports
# MAGIC         SET status = 'published',
# MAGIC             created_by = 'ericmlyang',
# MAGIC             updated_by = 'ericmlyang',
# MAGIC             updated_at = NOW()
# MAGIC         WHERE status = 'draft'
# MAGIC     """)
# MAGIC     updated_count = cur.rowcount
# MAGIC     conn.commit()
# MAGIC     cur.close()
# MAGIC     conn.close()
# MAGIC     print(f"✅ PostgreSQL updated: {updated_count} rows → published, created_by → ericmlyang")
# MAGIC except Exception as e:
# MAGIC     print(f"❌ PostgreSQL update failed: {e}")

# COMMAND ----------

# DBTITLE 1,Backfill: Sync All Data to PostgreSQL
# MAGIC %md
# MAGIC # === Backfill: Sync ALL s_news_issue_reports → PostgreSQL ===
# MAGIC import sys
# MAGIC sys.path.insert(0, "/Workspace/Users/eric.ml.yang@auo.com/mi3-data-center")
# MAGIC from modules.postgres.postgres_jdbc import sync_to_postgres, prepare_df_for_postgres
# MAGIC from pyspark.sql import functions as F
# MAGIC
# MAGIC SCHEMA = "micenter.mi3_datahub_prod"
# MAGIC
# MAGIC # Read all data from Delta
# MAGIC df_all = spark.table(f"{SCHEMA}.s_news_issue_reports")
# MAGIC print(f"Total records in Delta: {df_all.count()}")
# MAGIC
# MAGIC # Get all distinct dates
# MAGIC dates = [row.brief_date for row in df_all.select("brief_date").distinct().orderBy("brief_date").collect()]
# MAGIC print(f"Dates to sync: {dates}")
# MAGIC
# MAGIC # PostgreSQL connection
# MAGIC PG_HOST = dbutils.secrets.get(scope="mi3-postgres", key="pg-host")
# MAGIC PG_USER = dbutils.secrets.get(scope="mi3-postgres", key="pg-user")
# MAGIC PG_PASS = dbutils.secrets.get(scope="mi3-postgres", key="pg-password")
# MAGIC PG_DB   = dbutils.secrets.get(scope="mi3-postgres", key="pg-database")
# MAGIC
# MAGIC # Sync each date
# MAGIC for d in dates:
# MAGIC     df_day = df_all.filter(F.col("brief_date") == F.lit(d))
# MAGIC     df_pg = prepare_df_for_postgres(
# MAGIC         df_day,
# MAGIC         array_columns=["visible_pillars"],
# MAGIC         exclude_columns=["id", "md_content", "highlights_json", "model_ids", "agent_analysis"],
# MAGIC     )
# MAGIC     sync_to_postgres(
# MAGIC         df_pg, spark=spark,
# MAGIC         host=PG_HOST, port=5432, database=PG_DB, user=PG_USER, password=PG_PASS,
# MAGIC         table="app_custom_reports", schema="public",
# MAGIC         key_column="brief_date",
# MAGIC         key_value=str(d),
# MAGIC     )
# MAGIC     print(f"  ✅ {d} synced")
# MAGIC
# MAGIC print(f"\n🎉 Backfill complete: {len(dates)} dates synced to PostgreSQL")

# COMMAND ----------

# DBTITLE 1,Config & Dependencies
# === Configuration ===
from datetime import date, timedelta, datetime
import json, hashlib, re, textwrap
import pytz
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

# --- Pipeline Parameters ---
# 執行時抓完整新聞（確保當日新聞已全數入庫）
_tz_taipei = pytz.timezone("Asia/Taipei")
BRIEF_DATE = datetime.now(_tz_taipei).date()  # 07:00 執行 → 抓當天新聞
SCHEMA = "micenter.mi3_datahub_prod"
# --- LLM Model Selection ---
# Sonnet 5: 大量處理（Stage 1 批次過濾、Stage 2 選題、Stage 3 撰稿）
# Opus 4: 關鍵決策（Stage 2.5 頭條否決權）
MODEL_SONNET = "claude-sonnet-5"
MODEL_OPUS = "claude-opus-4-8"

# --- Target Table Constants ---
CATEGORY_ID = 1
CATEGORY_KEY = "weekly-news"
VISIBLE_PILLARS = ["ADP", "AMSC", "AUO"]

# --- Stage 1 Batching ---
MAX_BATCH_CHARS = 12000   # Max chars per batch (~10 articles × 1200 lead)
MAX_ARTICLES_PER_BATCH = 12
LEAD_MAX_CHARS = 1200     # ~400 tokens approx (3 chars/token for CJK)

print(f"Pipeline date: {BRIEF_DATE}")
print(f"Schema: {SCHEMA}")
print(f"Models: Sonnet={MODEL_SONNET}, Opus={MODEL_OPUS}")

# COMMAND ----------

# DBTITLE 1,P0: LLM Client Setup & Connection Test
# === LLM Client Setup (Azure Foundry via httpx — no SDK dependency) ===
import httpx

FOUNDRY_API_KEY = dbutils.secrets.get(scope="llm-api-keys", key="ms-foundry")
FOUNDRY_BASE_URL = "https://micenter.services.ai.azure.com/anthropic/v1/messages"

import time as _time

def call_claude(model: str, messages: list, max_tokens: int = 4096, retries: int = 2, thinking: bool = True) -> str:
    """Call Claude via Azure Foundry (raw HTTP) with retry on timeout.
    
    Args:
        thinking: If False, explicitly disable extended thinking to save tokens.
                  Use False for simple classification (Stage 1) and writing (Stage 3).
    """
    for attempt in range(retries + 1):
        try:
            body = {"model": model, "max_tokens": max_tokens, "messages": messages}
            if not thinking:
                body["thinking"] = {"type": "disabled"}
            resp = httpx.post(
                FOUNDRY_BASE_URL,
                headers={
                    "x-api-key": FOUNDRY_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json=body,
                timeout=600.0,
            )
            resp.raise_for_status()
            data = resp.json()
            # Extract text block, skipping thinking/signature blocks (extended thinking)
            text_parts = [block["text"] for block in data.get("content", []) if block.get("type") == "text"]
            if text_parts:
                return "\n".join(text_parts)
            # No text block found — likely extended thinking with no output
            block_types = [block.get("type") for block in data.get("content", [])]
            raise ValueError(f"No text block in response (got types: {block_types})")
        except (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.HTTPStatusError, ValueError) as e:
            if attempt < retries:
                wait = 10 * (attempt + 1)
                print(f"    ⚠️ Retry {attempt+1}/{retries} after {type(e).__name__}: {str(e)[:80]}, waiting {wait}s...")
                _time.sleep(wait)
            else:
                raise


def repair_json(broken_json: str, max_tokens: int = 8192) -> str:
    """Lightweight JSON repair: send only the broken output + short fix instruction.
    Much cheaper than re-running the full original prompt (~10K vs 30K+ input tokens).
    """
    repair_prompt = f"""以下是一段格式錯誤的 JSON。請修復成合法 JSON 並原樣輸出，不要改變任何內容語意，不要加說明文字或 markdown。
只輸出修復後的 JSON：

{broken_json}"""
    content = call_claude(
        model=MODEL_SONNET,
        messages=[{"role": "user", "content": repair_prompt}],
        max_tokens=max_tokens,
        thinking=False
    ).strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    json_match = re.search(r'[\{\[][\s\S]*[\}\]]', content)
    if json_match:
        content = json_match.group(0)
    content = re.sub(r',\s*([}\]])', r'\1', content)
    return content

# # --- Connection Test (thinking=False for small max_tokens) ---
# test_text = call_claude(MODEL_SONNET, [{"role": "user", "content": "請用一句話回答：你是什麼模型？"}], max_tokens=50, thinking=False)
# print(f"✅ Azure Foundry connected (httpx direct).")
# print(f"   Sonnet: {MODEL_SONNET} | Opus: {MODEL_OPUS}")
# print(f"   Test: {test_text}")

# COMMAND ----------

# DBTITLE 1,P1: Create Delta Tables (DDL)
# MAGIC %sql
# MAGIC %md
# MAGIC > **⚠️ 已停用（2026-08-26）**：Tables 早已存在，DDL 不該進每日排程。僅供參考。
# MAGIC
# MAGIC ```sql
# MAGIC -- === Stage 0 Output: Cleaned raw news ===
# MAGIC CREATE TABLE IF NOT EXISTS micenter.mi3_datahub_prod.news_raw_cleaned (
# MAGIC   news_id        STRING NOT NULL COMMENT 'b_vendor_news.rmId',
# MAGIC   news_hash      STRING NOT NULL COMMENT 'sha2(normalized_title + url) for dedup',
# MAGIC   pub_date       DATE,
# MAGIC   source         STRING,
# MAGIC   source_weight  INT COMMENT 'Source credibility weight 1-5',
# MAGIC   title          STRING,
# MAGIC   lead           STRING COMMENT 'Title + first paragraph, truncated to ~400 tokens',
# MAGIC   full_text      STRING,
# MAGIC   url            STRING,
# MAGIC   fetch_ts       TIMESTAMP,
# MAGIC   brief_date     DATE NOT NULL COMMENT 'Pipeline processing date',
# MAGIC   status         STRING COMMENT 'new | processed | skipped',
# MAGIC   CONSTRAINT pk_news_raw PRIMARY KEY (news_hash)
# MAGIC )
# MAGIC COMMENT 'Stage 0: Deduplicated and cleaned vendor news for daily brief pipeline'
# MAGIC TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true');
# MAGIC
# MAGIC -- === Stage 1 Output: Match cards ===
# MAGIC CREATE TABLE IF NOT EXISTS micenter.mi3_datahub_prod.news_match_cards (
# MAGIC   brief_date     DATE NOT NULL,
# MAGIC   news_id        STRING NOT NULL,
# MAGIC   matched        BOOLEAN COMMENT 'Whether article passes filter for deep analysis',
# MAGIC   brief_only     BOOLEAN COMMENT 'Weak relevance — show as categorized brief with URL',
# MAGIC   topic_ids      ARRAY<STRING> COMMENT 'Matched topic IDs from bu_focus_topics',
# MAGIC   category       STRING COMMENT '整體|TV|NB|MNT|其他應用',
# MAGIC   importance     INT COMMENT '1-5 importance score',
# MAGIC   facets         STRING COMMENT 'JSON: supply/demand/price/tech/policy facets',
# MAGIC   new_entities   ARRAY<STRING> COMMENT 'Newly mentioned entities',
# MAGIC   is_rumor       BOOLEAN,
# MAGIC   event_key_hint STRING COMMENT 'Suggested event key for cross-day tracking',
# MAGIC   summary        STRING COMMENT 'One-line summary',
# MAGIC   reason         STRING COMMENT 'Reason for match/skip',
# MAGIC   prompt_version STRING,
# MAGIC   model_id       STRING,
# MAGIC   created_at     TIMESTAMP,
# MAGIC   CONSTRAINT pk_match_cards PRIMARY KEY (brief_date, news_id)
# MAGIC )
# MAGIC COMMENT 'Stage 1: LLM filter results with structured match cards'
# MAGIC TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true');
# MAGIC
# MAGIC -- === Stage 2 Output: Daily selection plan ===
# MAGIC CREATE TABLE IF NOT EXISTS micenter.mi3_datahub_prod.news_daily_selection (
# MAGIC   brief_date         DATE NOT NULL,
# MAGIC   selection_json     STRING COMMENT 'Full selection plan JSON',
# MAGIC   today_events       STRING COMMENT '[{event_key, conclusion}] for cross-day tracking',
# MAGIC   headline_candidate STRING COMMENT 'Headline candidate JSON or null',
# MAGIC   headline_approved  BOOLEAN,
# MAGIC   headline_review    STRING COMMENT 'Stage 2.5 review output JSON',
# MAGIC   prompt_version     STRING,
# MAGIC   model_id           STRING,
# MAGIC   created_at         TIMESTAMP,
# MAGIC   CONSTRAINT pk_daily_selection PRIMARY KEY (brief_date)
# MAGIC )
# MAGIC COMMENT 'Stage 2: Aggregated topic selection and event merging'
# MAGIC TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true');
# MAGIC
# MAGIC -- === Stage 3+4 Output: Final daily brief ===
# MAGIC CREATE TABLE IF NOT EXISTS micenter.mi3_datahub_prod.news_daily_brief (
# MAGIC   brief_date          DATE NOT NULL,
# MAGIC   md_content          STRING COMMENT 'Markdown full text (archive + RAG)',
# MAGIC   html_content        STRING COMMENT 'TipTap HTML (frontend display)',
# MAGIC   report_title        STRING COMMENT 'Report title for target table',
# MAGIC   highlights_json     STRING COMMENT 'Stage 3 raw highlights JSON',
# MAGIC   digest_md           STRING COMMENT 'Today digest/intro section',
# MAGIC   unmatched_count     INT,
# MAGIC   filter_card_version STRING,
# MAGIC   prompt_versions     STRING COMMENT 'JSON: {p1:v, p2:v, p3:v}',
# MAGIC   model_ids           STRING COMMENT 'JSON: {stage1:m, stage2:m, ...}',
# MAGIC   published           BOOLEAN,
# MAGIC   published_at        TIMESTAMP,
# MAGIC   created_at          TIMESTAMP,
# MAGIC   CONSTRAINT pk_daily_brief PRIMARY KEY (brief_date)
# MAGIC )
# MAGIC COMMENT 'Stage 3+4: Final assembled daily brief with Markdown and HTML'
# MAGIC TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true');
# MAGIC
# MAGIC -- === Target Table: Synced to application layer ===
# MAGIC CREATE TABLE IF NOT EXISTS micenter.mi3_datahub_prod.s_news_issue_reports (
# MAGIC   id              BIGINT GENERATED ALWAYS AS IDENTITY,
# MAGIC   brief_date      DATE NOT NULL,
# MAGIC   category_id     INT NOT NULL COMMENT '固定 = 1 (每周新聞)',
# MAGIC   category_key    STRING NOT NULL COMMENT '每周新聞',
# MAGIC   title           STRING NOT NULL,
# MAGIC   content         STRING COMMENT 'TipTap HTML content',
# MAGIC   status          STRING COMMENT 'draft | published',
# MAGIC   visible_pillars ARRAY<STRING> COMMENT 'DSBG',
# MAGIC   created_by      STRING COMMENT 'system_pipeline',
# MAGIC   created_at      TIMESTAMP,
# MAGIC   updated_by      STRING,
# MAGIC   updated_at      TIMESTAMP,
# MAGIC   published_at    TIMESTAMP,
# MAGIC   is_deleted      BOOLEAN,
# MAGIC   md_content      STRING COMMENT 'Markdown version (pipeline metadata, not pushed to app)',
# MAGIC   highlights_json STRING COMMENT 'Raw highlights (pipeline metadata)',
# MAGIC   model_ids       STRING COMMENT 'Model versions used (pipeline metadata)',
# MAGIC   CONSTRAINT pk_news_report PRIMARY KEY (brief_date)
# MAGIC )
# MAGIC COMMENT 'Target table aligned with app_custom_reports schema for frontend display'
# MAGIC TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true');
# MAGIC ```

# COMMAND ----------

# DBTITLE 1,Stage 0: Pre-processing (Dedup + Clean + Lead)
# === Stage 0: Pre-processing ===
# Read today's news, deduplicate, clean, truncate lead, MERGE into Delta

import tiktoken
from pyspark.sql import functions as F
from pyspark.sql.types import StringType, IntegerType

# --- Source weight mapping (higher = more credible/relevant) ---
SOURCE_WEIGHTS = {
    # Tier 5: Primary industry sources
    "DIGITIMES": 5, "TrendForce": 5, "The Elec": 5,
    # Tier 4: Major financial/tech media
    "工商時報": 4, "經濟日報網": 4, "經濟日報": 4, "電子時報": 4,
    "CNBC": 4, "Reuters": 4, "Bloomberg": 4, "Nikkei": 4,
    # Tier 3: General financial media
    "今周刊": 3, "資訊時報": 3, "時報資訊": 3, "面板新聞網": 3,
    "旺得富": 3, "中時新聞網": 3, "自由時報": 3,
    # Tier 2: General news
    "聯合報": 2, "中央社": 2, "MoneyDJ": 2,
}
DEFAULT_WEIGHT = 2

# --- Blacklist: Sources to exclude ---
SOURCE_BLACKLIST = set()  # Add source names to exclude if needed

# --- Helper: Normalize title for dedup ---
def normalize_title(title: str) -> str:
    """Remove whitespace, punctuation noise for dedup comparison."""
    if not title:
        return ""
    # Remove leading/trailing whitespace, full-width spaces, common prefixes
    t = re.sub(r'^[\s　、。]+|[\s　]+$', '', title)
    t = re.sub(r'^[《》【】\[\]\(\)]+[^《》【】\[\]\(\)]*[《》【】\[\]\(\)]+\s*', '', t)  # Remove category brackets like 《電週邊》
    t = re.sub(r'\s+', '', t)  # Collapse all whitespace
    return t.lower()

# --- Helper: Canonicalize URL ---
def canonicalize_url(url: str) -> str:
    """Remove tracking params (utm_*, CGUID, SID, etc.) for dedup."""
    if not url:
        return ""
    try:
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        # Keep only essential params
        clean_params = {k: v for k, v in params.items()
                       if not k.startswith('utm_') and k not in ('CGUID', 'SID', 'Daystr', 'SortStr', 'Sucaid', 'ToUrl', 'Title')}
        clean_query = urlencode(clean_params, doseq=True)
        return urlunparse(parsed._replace(query=clean_query))
    except Exception:
        return url

# --- Helper: Truncate lead to ~400 tokens ---
def make_lead(title: str, content: str, max_chars: int = 1200) -> str:
    """Title + first paragraph, truncated to max_chars (~400 CJK tokens)."""
    if not content:
        return title or ""
    # Take first paragraph (split on double newline or \n\n)
    first_para = content.split('\n\n')[0].split('\n')[0] if content else ""
    lead = f"{title}\n{first_para}" if title else first_para
    # Truncate
    if len(lead) > max_chars:
        lead = lead[:max_chars] + "..."
    return lead.strip()

# Register UDFs
normalize_title_udf = F.udf(normalize_title, StringType())
canonicalize_url_udf = F.udf(canonicalize_url, StringType())
make_lead_udf = F.udf(make_lead, StringType())
get_weight_udf = F.udf(lambda s: SOURCE_WEIGHTS.get(s, DEFAULT_WEIGHT) if s else DEFAULT_WEIGHT, IntegerType())

# --- Read source data: incremental by fetch_timestamp ---
# 抓上次處理後所有新進文章，不管 Date 是昨天還是今天
max_processed = spark.sql(
    f"SELECT COALESCE(MAX(fetch_ts), TIMESTAMP '1970-01-01') FROM {SCHEMA}.news_raw_cleaned"
).first()[0]

raw_df = (
    spark.table(f"{SCHEMA}.b_vendor_news")
    .filter(F.col("fetch_timestamp") > F.lit(max_processed))
    .filter(~F.col("SourceSName").isin(list(SOURCE_BLACKLIST)))
)

print(f"Incremental articles (fetch_ts > {max_processed}): {raw_df.count()}")

# --- Transform ---
cleaned_df = (
    raw_df
    .withColumn("_norm_title", normalize_title_udf(F.col("Title")))
    .withColumn("_canon_url", canonicalize_url_udf(F.col("Url")))
    .withColumn("news_hash", F.sha2(F.concat_ws("|", F.col("_norm_title"), F.col("_canon_url")), 256))
    .withColumn("news_id", F.col("rmId"))
    .withColumn("pub_date", F.to_date(F.col("Date")))
    .withColumn("source", F.col("SourceSName"))
    .withColumn("source_weight", get_weight_udf(F.col("SourceSName")))
    .withColumn("title", F.col("Title"))
    .withColumn("lead", make_lead_udf(F.col("Title"), F.col("NewsContent")))
    .withColumn("full_text", F.col("NewsContent"))
    .withColumn("url", F.col("Url"))
    .withColumn("fetch_ts", F.col("fetch_timestamp"))
    .withColumn("brief_date", F.lit(BRIEF_DATE))
    .withColumn("status", F.lit("new"))
    .select("news_id", "news_hash", "pub_date", "source", "source_weight",
            "title", "lead", "full_text", "url", "fetch_ts", "brief_date", "status")
)

print(f"After dedup (by hash): {cleaned_df.dropDuplicates(['news_hash']).count()}")

# --- MERGE INTO (idempotent) ---
cleaned_df.dropDuplicates(['news_hash']).createOrReplaceTempView("stg_cleaned")

print("Stage 0: Pre-processing complete.")

# COMMAND ----------

# DBTITLE 1,Stage 0: MERGE INTO Delta
# MAGIC %sql
# MAGIC MERGE INTO micenter.mi3_datahub_prod.news_raw_cleaned AS target
# MAGIC USING stg_cleaned AS source
# MAGIC ON target.news_hash = source.news_hash
# MAGIC WHEN NOT MATCHED THEN INSERT *;
# MAGIC
# MAGIC SELECT brief_date, status, COUNT(*) as cnt
# MAGIC FROM micenter.mi3_datahub_prod.news_raw_cleaned
# MAGIC WHERE brief_date = current_date()
# MAGIC GROUP BY brief_date, status;

# COMMAND ----------

# DBTITLE 1,Stage 1: Filter Card & Prompt Template
# === Stage 1: Prompts & Filter Card ===
from pydantic import BaseModel, Field
from typing import Optional

# --- Filter Card (§A v1.3-lite) ---
FILTER_CARD = """【AUO DSBG 新聞過濾基準 v1.3-lite】

■ 立場聲明
- 本報告立場 = AUO（友達光電），讀者為 DSBG（Display Strategy Business Group）
- 新聞中提及「友達」「AUO」= 我方，應以第一人稱角度評估影響
- 我方技術路線：LCD（含 Mini-LED backlight），不生產 OLED 面板
- 已退出業務：手機面板。手機相關新聞除非影響大尺寸產能分配，否則排除
- Innolux（群創）= 台灣同業競爭者（非我方關係企業）

■ 常設議題
T-01(高) 面板產能供需-尤其陸廠：BOE/華星/HKC 稼動率·控產·整併·關停·新投資；台韓減產退出
T-02(高) 面板價格：TV/MNT/NB 報價漲跌·研調(TrendForce/OMDIA/Sigmaintell)數字與分歧·open-cell
T-03(高) 品牌客戶動態：NB=Dell/Lenovo/Acer/ASUS/MSI；TV=Samsung/Hisense/TCL/SONY；MNT=Dell/Samsung/Acer
        → 出貨市佔·砍單拉貨·新品·產地遷移·財報庫存·轉單·供應鏈策略
T-04(高) 消費市場與總經：消費信心·通膨利率·能源·運費·美中關係 → 命中時必須附「對面板需求的含意」
T-05(高) 關稅貿易地緣：美對中關稅·USMCA·越南·客戶產地與採購策略調整
T-06(中) 技術 roadmap：OLED/LCD 價差·Mini-LED/Micro-LED 滲透·電競規格遷移(刷新率→解析度→ACR→OLED)·HSR
        （注意：AUO 不做 OLED，此議題從「競品威脅 / LCD 價差保衛」角度追蹤）
T-07(中) 上游材料：Memory 對 TV BOM·driver IC·POL·玻璃·背光成本
T-08(中) 終端需求事件：世足·Win10 EOL·AI PC 換機·黑五/618/雙eleven 促銷備貨
T-09(中) 競品法說財報：面板廠(BOE/華星/HKC/LGD/SDC/群創)與品牌客戶的法說·財報·CapEx

■ 近期特別關注（命中即高優先）
W-01 美關稅對中國製 TV 衝擊與品牌產地移轉
W-02 記憶體成本推升 TV BOM、終端漲價壓需求
W-03 中國面板業整併政策後續
W-04 MNT 面板連漲的延續性與品牌抗漲
W-05 Mini-LED 放量年（出貨 +87%、滲透率破 10%）
W-06 Hisense–LG 合作傳聞
W-07 85 吋大尺寸放量窗口與供需
W-08 Win10 EOL + AI PC 換機潮實際進度

■ 大類歸屬（一篇只歸一類）
整體=跨應用或宏觀（產能供需/總經/關稅/上游材料/面板廠法說）；TV / NB / MNT=明確單一應用；
其他應用=Auto/Signage/Tablet/Wearable

■ 重要性評分
命中 W=4-5；命中(高)議題=3-4；命中(中)議題=2-3；僅弱相關=1

■ 受控詞彙
品牌：Samsung·Hisense·TCL·SONY·Dell·Lenovo·Acer·ASUS·MSI
面板廠：BOE·TCL CSOT·HKC·LGD·SDC·Innolux·Sharp
動作：拉貨增加·砍單·新品發表·擴產·減產·停產·整併·價格調整·技術突破·合作·產地遷移·關稅調整·財報發布·缺貨
規格：LCD·OLED·QD-OLED·Mini-LED·Micro-LED·高刷新率·HSR·Driver IC·POL·Memory·尺寸(吋)
終端：TV·Monitor·NB·Tablet·Auto·Signage
"""

# --- §P1 Prompt Template ---
P1_PROMPT_TEMPLATE = """你是 AUO DSBG 的新聞過濾器。依據下方【過濾基準】，逐篇判斷新聞是否與 BU 關注議題相關，輸出結構化判定卡。

【過濾基準】
{filter_card}

【本批新聞】（每篇含 news_id / title / lead）
{news_batch}

【判定規則】
1. 對照常設議題（T-xx）與近期特別關注（W-xx），命中才標 matched=true；可同時命中多個議題。
2. 落在「排除」清單的一律 matched=false。
3. 拿不準但與顯示產業鏈有一定關聯性的，標 matched=true、importance 給 1-2 並在 reason 寫明猶豫點 — 寧可多收再由後續 Stage 篩選，不要在此階段漏掉潛在相關新聞。
4. **brief_only 判定**：未直接命中任何 T-xx / W-xx，但仍屬廣義面板產業鏈動態（如面板廠非核心業務、LED 照明、半導體設備、泛電子消費趨勢）→ 設 brief_only=true, matched=false。這類新聞不進深度分析但會以快訊形式呈現給讀者。判斷標準：「DSBG 同事花 5 秒掃到標題會想知道發生什麼事」即可列入。
5. 一篇只歸一個大類。
6. summary 用繁體中文一句話（≤40 字）講清楚「發生什麼事」。
7. facets 只能用受控詞彙表內的詞；表外的新實體放 new_entities。
8. 內文揭示「傳聞 / 未經證實 / 知情人士」→ is_rumor=true。
9. event_key_hint：6-12 字標準化短語，格式 = 主體+動作+對象或數字。
10. matched=false 且 brief_only=false 也要輸出完整物件（reason 必填）。

【三種判定結果】
- matched=true, brief_only=false：命中議題，進入重點選題流程
- matched=false, brief_only=true：弱相關但值得快訊呈現
- matched=false, brief_only=false：完全無關，排除

【輸出】只輸出 JSON array，每篇一個物件，不要任何說明文字：
{{
  "news_id": "",
  "matched": true,
  "brief_only": false,
  "topic_ids": ["T-02", "W-04"],
  "category": "整體|TV|NB|MNT|其他應用",
  "importance": 1,
  "facets": {{"customers": [], "actions": [], "specs": [], "end_products": []}},
  "new_entities": [],
  "is_rumor": false,
  "event_key_hint": "",
  "summary": "",
  "reason": ""
}}
"""

# --- Pydantic Models for Validation ---
class MatchCardItem(BaseModel):
    news_id: str
    matched: bool
    brief_only: bool = False
    topic_ids: list[str] = Field(default_factory=list)
    category: str = ""
    importance: int = Field(ge=1, le=5, default=1)
    facets: dict = Field(default_factory=dict)
    new_entities: list[str] = Field(default_factory=list)
    is_rumor: bool = False
    event_key_hint: str = ""
    summary: str = ""
    reason: str = ""

PROMPT_VERSION_P1 = "v2.2"  # v2.2: added brief_only channel for wider coverage
print(f"Filter card loaded ({len(FILTER_CARD)} chars)")
print(f"Prompt §P1 template ready (version {PROMPT_VERSION_P1})")

# COMMAND ----------

# DBTITLE 1,Stage 1: Batch Processing & LLM Calls
# === Stage 1: Batch Filtering with Claude Sonnet ===
import time
from pydantic import ValidationError

# --- Load today's cleaned articles (newest first, capped) ---
MAX_ARTICLES_STAGE1 = 120

articles_df = spark.table(f"{SCHEMA}.news_raw_cleaned").filter(
    (F.col("brief_date") == BRIEF_DATE) & (F.col("status") == "new")
).orderBy(F.col("fetch_ts").desc()).limit(MAX_ARTICLES_STAGE1).select("news_id", "title", "lead").toPandas()

print(f"Articles to filter: {len(articles_df)}")

# --- Batching logic (dynamic by character count as proxy for tokens) ---
def create_batches(articles_df, max_chars=6000, max_per_batch=12):
    """Group articles into batches based on lead character count."""
    batches = []
    current_batch = []
    current_chars = 0
    
    for _, row in articles_df.iterrows():
        article_chars = len(row['lead'] or '') + len(row['title'] or '') + 50  # overhead
        if current_batch and (current_chars + article_chars > max_chars or len(current_batch) >= max_per_batch):
            batches.append(current_batch)
            current_batch = []
            current_chars = 0
        current_batch.append(row.to_dict())
        current_chars += article_chars
    
    if current_batch:
        batches.append(current_batch)
    return batches

batches = create_batches(articles_df, max_chars=MAX_BATCH_CHARS, max_per_batch=MAX_ARTICLES_PER_BATCH)
print(f"Created {len(batches)} batches (sizes: {[len(b) for b in batches]})")

# --- LLM call with retry ---
def call_llm_filter(batch: list[dict], retry: int = 1) -> list[dict]:
    """Call Claude Sonnet 5 via Azure Foundry for batch filtering with Pydantic validation."""
    # Format news batch
    news_batch_str = "\n\n".join([
        f"[news_id: {a['news_id']}]\ntitle: {a['title']}\nlead: {a['lead']}"
        for a in batch
    ])
    
    prompt = P1_PROMPT_TEMPLATE.format(
        filter_card=FILTER_CARD,
        news_batch=news_batch_str
    )
    
    for attempt in range(retry + 1):
        try:
            content = call_claude(
                model=MODEL_SONNET,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=8192,
                thinking=False  # Stage 1: simple classification, no need for CoT
            ).strip()
            # Clean potential markdown wrapping
            if content.startswith("```"):
                content = content.split("\n", 1)[1].rsplit("```", 1)[0]
            
            results = json.loads(content)
            
            # Validate with Pydantic
            validated = []
            for item in results:
                card = MatchCardItem(**item)
                validated.append(card.dict())
            
            return validated
            
        except json.JSONDecodeError as e:
            if attempt < retry:
                # Lightweight repair: fix JSON syntax without re-running full prompt
                print(f"JSON repair...", end=" ")
                try:
                    repaired = repair_json(content, max_tokens=8192)
                    results = json.loads(repaired)
                    validated = []
                    for item in results:
                        card = MatchCardItem(**item)
                        validated.append(card.dict())
                    return validated
                except Exception:
                    time.sleep(1)
            else:
                print(f"  ⚠️ Batch failed after {retry+1} attempts: {str(e)[:100]}")
                return [{"news_id": a["news_id"], "matched": False, 
                         "reason": f"LLM parse error: {str(e)[:50]}"} for a in batch]
        except Exception as e:
            if attempt < retry:
                time.sleep(1)
            else:
                print(f"  ⚠️ Batch failed after {retry+1} attempts: {str(e)[:100]}")
                return [{"news_id": a["news_id"], "matched": False, 
                         "reason": f"LLM parse error: {str(e)[:50]}"} for a in batch]
    return []

# --- Process all batches ---
all_cards = []
for i, batch in enumerate(batches):
    print(f"  Processing batch {i+1}/{len(batches)} ({len(batch)} articles)...", end=" ")
    cards = call_llm_filter(batch)
    all_cards.extend(cards)
    matched_count = sum(1 for c in cards if c.get('matched', False))
    print(f"✅ {matched_count}/{len(cards)} matched")
    if i < len(batches) - 1:
        time.sleep(3)  # Rate limiting — avoid Azure Foundry disconnect

brief_only_count = sum(1 for c in all_cards if c.get('brief_only', False))
print(f"\nStage 1 complete: {len(all_cards)} cards, {sum(1 for c in all_cards if c.get('matched'))} matched, {brief_only_count} brief_only")

# COMMAND ----------

# DBTITLE 1,Stage 1: MERGE Match Cards into Delta
# === Stage 1: Write match cards to Delta ===
from pyspark.sql.types import StructType, StructField, StringType, BooleanType, IntegerType, ArrayType, TimestampType, DateType
from datetime import datetime

# Prepare records for Delta
match_records = []
for card in all_cards:
    match_records.append({
        "brief_date": BRIEF_DATE,
        "news_id": card.get("news_id", ""),
        "matched": card.get("matched", False),
        "brief_only": card.get("brief_only", False),
        "topic_ids": card.get("topic_ids") or [],
        "category": card.get("category", ""),
        "importance": card.get("importance", 1),
        "facets": json.dumps(card.get("facets", {}), ensure_ascii=False),
        "new_entities": card.get("new_entities") or [],
        "is_rumor": card.get("is_rumor", False),
        "event_key_hint": card.get("event_key_hint", ""),
        "summary": card.get("summary", ""),
        "reason": card.get("reason", ""),
        "prompt_version": PROMPT_VERSION_P1,
        "model_id": MODEL_SONNET,
        "created_at": datetime.now(),
    })

# Create DataFrame and MERGE — explicit schema to avoid CANNOT_DETERMINE_TYPE
schema = StructType([
    StructField("brief_date", DateType(), True),
    StructField("news_id", StringType(), True),
    StructField("matched", BooleanType(), True),
    StructField("brief_only", BooleanType(), True),
    StructField("topic_ids", ArrayType(StringType()), True),
    StructField("category", StringType(), True),
    StructField("importance", IntegerType(), True),
    StructField("facets", StringType(), True),
    StructField("new_entities", ArrayType(StringType()), True),
    StructField("is_rumor", BooleanType(), True),
    StructField("event_key_hint", StringType(), True),
    StructField("summary", StringType(), True),
    StructField("reason", StringType(), True),
    StructField("prompt_version", StringType(), True),
    StructField("model_id", StringType(), True),
    StructField("created_at", TimestampType(), True),
])
cards_df = spark.createDataFrame(match_records, schema=schema)
cards_df.createOrReplaceTempView("stg_match_cards")

spark.sql(f"""
    MERGE INTO {SCHEMA}.news_match_cards AS target
    USING stg_match_cards AS source
    ON target.brief_date = source.brief_date AND target.news_id = source.news_id
    WHEN MATCHED THEN UPDATE SET *
    WHEN NOT MATCHED THEN INSERT *
""")

# Summary
result = spark.sql(f"""
    SELECT matched, COUNT(*) as cnt 
    FROM {SCHEMA}.news_match_cards 
    WHERE brief_date = '{BRIEF_DATE}'
    GROUP BY matched
""").toPandas()
print("Stage 1 MERGE complete:")
print(result.to_string(index=False))

# COMMAND ----------

# DBTITLE 1,Stage 2: Aggregation & Topic Selection
# === Stage 2: Aggregation & Topic Selection (v3.0) ===

# --- §P2 Prompt Template (v3.0: headline/detail/importance/absorb/insight/threads) ---
P2_PROMPT_TEMPLATE = """你是 AUO DSBG 每日情報的選題編輯，擁有今日唯一的全局視野。請完成：同事件合併、續報判斷、條目分級、分類新聞豐富化、主線建構、訊號雷達、頭條初判。

【過濾基準】
{filter_card}

【今日判定卡】（Stage 1 matched=true 的新聞）
{matched_cards}

【分類新聞池】（Stage 1 brief_only=true 的新聞，含 news_id / category / summary）
{brief_only_cards}

【近 3 日已報導事件】（event_key + 當日結論）
{recent_events}

【任務】
1. 合併同一事件：先比對 event_key_hint，再讀 summary 確認。不同來源報同一件事 → 合併為一條。
2. 續報判斷：對照近 3 日清單 — 同一事件且有新進展 → 保留；無新進展 → drop。
3. 挑重點則：全日 3-5 條、每大類至多 2 條。每則 highlights 給 importance 3-5。
4. 分類新聞豐富化：將「其餘 matched 條目」+「分類新聞池 brief_only 條目」全部納入，依下列 7 類分組：
   - macro_economy：總體經濟（GDP/通膨/利率/匯率/消費信心/貿易政策）
   - industry：產業（面板產業整體供需/稼動率/產能/法說/整併/競爭格局）
   - semiconductor：半導體&零組件（Driver IC/Memory/PCB/被動元件/晶圓代工）
   - ai_manufacturing：AI &智慧製造（AI PC/AI伺服器/智慧工廠/邊緣運算/自動化）
   - panel：面板相關（面板報價/技術路線/Mini-LED/OLED/LCD/尺寸趨勢）
   - consumer_electronics：消費性電子（TV/NB/MNT/手機/穿戴/品牌客戶動態）
   - it：IT（雲端/資料中心/網通/軟體/資安）
   每條分類新聞產出：
   - headline：≤20 字標題句（主體 + 動態）
   - detail：30-60 字補充脈絡，**必須含對 DSBG/面板產業的 so-what**
   - importance：1-3（池內相對重要性）
   **每大類最多 6 則**（字數護欄的源頭控管）。
   **池內同事件合併**：同一事件多來源 → 合併一條，keep 資訊最完整者，其餘 news_id 放 absorb。
   每大類寫一句 insight（≤45 字）：類級趨勢判斷，不是條目複述。
5. 主線建構：產出 threads 2-3 條（title 8-15 字 / angle 一句話 / refs）。主線必須覆蓋所有 highlights。**選不出 ≥2 則新聞支撐的主線時允許只 1 條，禁止湊數發明主線**。
6. is_rumor=true 進訊號雷達。
7. 頭條初判（預設為「無」）：同時滿足 (a) 對 AUO 有直接且重大影響 (b) 跨多 BU/核心客戶或當天必須知道 才提名。
8. today_events：今日所有保留事件各寫一行。

【輸出】只輸出 JSON，不要任何說明文字：
{{
  "merged": [{{"keep": "news_id", "absorb": ["news_id"]}}],
  "headline_candidate": null,
  "highlights": [{{"news_ids": [""], "category": "", "topic_ids": [], "importance": 4, "angle": ""}}],
  "threads": [
    {{"title": "主線標題 8-15字", "angle": "一句話敘事角度",
      "refs": {{"highlight_idx": [0, 1], "brief_groups": ["consumer_electronics"]}}}}
  ],
  "briefs_grouped": {{
    "semiconductor": {{
      "insight": "本類趨勢一句（≤45字）",
      "items": [
        {{"news_id": "", "headline": "≤20字標題句", "detail": "30-60字脈絡含so-what",
          "importance": 2, "absorb": []}}
      ]
    }}
  }},
  "radar": [{{"news_id": "", "credibility": "高|中|低", "note": ""}}],
  "drop": [{{"news_id": "", "reason": ""}}],
  "today_events": [{{"event_key": "", "conclusion": ""}}]
}}
headline_candidate 有值時格式：{{"news_id": "", "justification_a": "", "justification_b": ""}}
"""

PROMPT_VERSION_P2 = "v3.0"  # v3.0: headline/detail/importance/absorb/insight/threads

# --- Load matched cards from Delta ---
matched_cards_df = spark.sql(f"""
    SELECT news_id, category, importance, topic_ids, facets, 
           event_key_hint, summary, is_rumor
    FROM {SCHEMA}.news_match_cards 
    WHERE brief_date = '{BRIEF_DATE}' AND matched = true
    ORDER BY importance DESC
""").toPandas()

# --- Load brief_only cards (new: feed into briefs pool) ---
brief_only_cards_df = spark.sql(f"""
    SELECT news_id, category, summary
    FROM {SCHEMA}.news_match_cards 
    WHERE brief_date = '{BRIEF_DATE}' AND brief_only = true
""").toPandas()

print(f"Matched cards for selection: {len(matched_cards_df)}")
print(f"Brief-only cards for briefs pool: {len(brief_only_cards_df)}")

# --- Load recent events (last 3 days) ---
recent_events_df = spark.sql(f"""
    SELECT brief_date, today_events 
    FROM {SCHEMA}.news_daily_selection 
    WHERE brief_date BETWEEN DATE_SUB('{BRIEF_DATE}', 3) AND DATE_SUB('{BRIEF_DATE}', 1)
    ORDER BY brief_date DESC
""").toPandas()

recent_events_str = "無（首次執行或近 3 日無資料）"
if not recent_events_df.empty:
    events_list = []
    for _, row in recent_events_df.iterrows():
        if row['today_events']:
            events_list.append(f"{row['brief_date']}: {row['today_events']}")
    if events_list:
        recent_events_str = "\n".join(events_list)

print(f"Recent events context: {recent_events_str[:100]}...")

# --- Call Stage 2 LLM ---
if len(matched_cards_df) == 0 and len(brief_only_cards_df) == 0:
    print("⚠️ No matched or brief_only cards — skipping Stage 2 (no report today)")
    selection_result = None
else:
    matched_cards_str = matched_cards_df.to_json(orient='records', force_ascii=False)
    brief_only_cards_str = brief_only_cards_df.to_json(orient='records', force_ascii=False) if len(brief_only_cards_df) > 0 else "無"
    
    prompt_p2 = P2_PROMPT_TEMPLATE.format(
        filter_card=FILTER_CARD,
        matched_cards=matched_cards_str,
        brief_only_cards=brief_only_cards_str,
        recent_events=recent_events_str
    )
    
    content = call_claude(
        model=MODEL_SONNET,
        messages=[{"role": "user", "content": prompt_p2}],
        max_tokens=18000,
        thinking=False  # Stage 2: disable thinking to avoid token budget exhaustion
    ).strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    
    # Extract JSON object and fix common LLM issues (trailing commas)
    json_match = re.search(r'\{[\s\S]*\}', content)
    if json_match:
        content = json_match.group(0)
    content = re.sub(r',\s*([}\]])', r'\1', content)
    
    try:
        selection_result = json.loads(content)
    except json.JSONDecodeError as e:
        # Lightweight repair: fix JSON syntax without re-running the expensive full prompt
        print(f"  ⚠️ JSON parse error: {e}. Running lightweight repair...")
        repaired = repair_json(content, max_tokens=16384)
        selection_result = json.loads(repaired)
    # Backward-compat: convert old formats to v3.0 {insight, items} structure
    if 'briefs' in selection_result and 'briefs_grouped' not in selection_result:
        briefs_grouped = {"macro_economy": [], "industry": [], "semiconductor": [], "ai_manufacturing": [], "panel": [], "consumer_electronics": [], "it": []}
        for b in selection_result['briefs']:
            briefs_grouped.setdefault('industry', []).append({"news_id": b.get("news_id", ""), "summary_short": b.get("fact", "")})
        selection_result['briefs_grouped'] = briefs_grouped

    # Normalize briefs_grouped: old flat list format -> v3.0 {insight, items}
    bg = selection_result.get('briefs_grouped', {})
    for grp_key, grp_val in bg.items():
        if isinstance(grp_val, list):
            # Old format: list of items -> convert to {insight, items}
            converted_items = []
            for item in grp_val:
                converted_items.append({
                    "news_id": item.get("news_id", ""),
                    "headline": item.get("headline", item.get("summary_short", "")[:20]),
                    "detail": item.get("detail", item.get("summary_short", "")),
                    "importance": item.get("importance", 1),
                    "absorb": item.get("absorb", []),
                })
            bg[grp_key] = {"insight": "", "items": converted_items}
    selection_result['briefs_grouped'] = bg

    # Ensure threads exists (soft-required: empty list is OK)
    if 'threads' not in selection_result:
        selection_result['threads'] = []

    # Ensure highlights have importance
    for h in selection_result.get('highlights', []):
        if 'importance' not in h:
            h['importance'] = 4  # default for highlights

    # Count total briefs across all groups
    briefs_grouped = selection_result.get('briefs_grouped', {})
    total_briefs = sum(len(v.get('items', [])) for v in briefs_grouped.values() if isinstance(v, dict))
    
    print(f"✅ Stage 2 complete:")
    print(f"   Highlights: {len(selection_result.get('highlights', []))}")
    print(f"   Threads: {len(selection_result.get('threads', []))}")
    print(f"   Briefs (grouped): {total_briefs} total")
    for grp, grp_data in briefs_grouped.items():
        items = grp_data.get('items', []) if isinstance(grp_data, dict) else []
        if items:
            print(f"     {grp}: {len(items)} | insight: {grp_data.get('insight', '')[:30]}")
    print(f"   Headline: {'Yes' if selection_result.get('headline_candidate') else 'No'}")
    print(f"   Today events: {len(selection_result.get('today_events', []))}")

# COMMAND ----------

# DBTITLE 1,Stage 2.5: Headline Review (Conditional) + MERGE
# === Stage 2.5: Headline Review (if candidate exists) + Write to Delta ===

headline_approved = None
headline_review = None

if selection_result and selection_result.get("headline_candidate"):
    # --- §P4 Headline Review ---
    candidate = selection_result["headline_candidate"]
    candidate_news_id = candidate["news_id"]
    
    # Get full text of headline candidate
    full_text_row = spark.sql(f"""
        SELECT full_text FROM {SCHEMA}.news_raw_cleaned 
        WHERE news_id = '{candidate_news_id}' AND brief_date = '{BRIEF_DATE}'
    """).first()
    
    candidate_full_text = full_text_row['full_text'] if full_text_row else ""
    
    p4_prompt = f"""你是 AUO DSBG 日報的總編輯，負責頭條的最終否決權。頭條規則：必須同時滿足
(a) 對 AUO 直接且重大影響、(b) 跨多 BU/核心客戶或當天時效；多數日子應該沒有頭條。

【候選與選題編輯的理由】
{json.dumps(candidate, ensure_ascii=False)}

【新聞全文】
{candidate_full_text[:3000]}

請以「預設否決」的立場審查。輸出 JSON：{{"approve": false, "reason": "", "lead_impact": "", "lead_action": ""}}"""
    
    # Opus 4 for critical editorial judgment (headline veto power)
    review_content = call_claude(
        model=MODEL_OPUS,
        messages=[{"role": "user", "content": p4_prompt}],
        max_tokens=2000
    ).strip()
    if review_content.startswith("```"):
        review_content = review_content.split("\n", 1)[1].rsplit("```", 1)[0]
    
    # Extract JSON and fix common LLM issues
    json_match = re.search(r'\{[\s\S]*\}', review_content)
    if json_match:
        review_content = json_match.group(0)
    review_content = re.sub(r',\s*([}\]])', r'\1', review_content)
    
    try:
        headline_review = json.loads(review_content)
    except json.JSONDecodeError as e:
        print(f"  ⚠️ Headline review JSON repair: {e}")
        repaired = repair_json(review_content, max_tokens=2000)
        headline_review = json.loads(repaired)
    headline_approved = headline_review.get("approve", False)
    print(f"Stage 2.5: Headline {'APPROVED ✅' if headline_approved else 'REJECTED ❌'}")
    if not headline_approved:
        print(f"   Reason: {headline_review.get('reason', '')}")
else:
    print("Stage 2.5: No headline candidate — skipped")

# --- MERGE Stage 2 results into Delta using SQL INSERT ---
if selection_result:
    _sel_json = json.dumps(selection_result, ensure_ascii=False).replace("'", "''")
    _events_json = json.dumps(selection_result.get("today_events", []), ensure_ascii=False).replace("'", "''")
    _hl_cand = selection_result.get("headline_candidate")
    _hl_sql = f"'{json.dumps(_hl_cand, ensure_ascii=False).replace(chr(39), chr(39)+chr(39))}'" if _hl_cand else "NULL"
    _rv_sql = f"'{json.dumps(headline_review, ensure_ascii=False).replace(chr(39), chr(39)+chr(39))}'" if headline_review else "NULL"
    _ap_sql = str(headline_approved).lower() if headline_approved is not None else "NULL"

    # Delete + Insert pattern (simpler than MERGE for single-row upsert)
    spark.sql(f"DELETE FROM {SCHEMA}.news_daily_selection WHERE brief_date = '{BRIEF_DATE}'")
    spark.sql(f"""
        INSERT INTO {SCHEMA}.news_daily_selection
        (brief_date, selection_json, today_events, headline_candidate, 
         headline_approved, headline_review, prompt_version, model_id, created_at)
        VALUES (
            DATE('{BRIEF_DATE}'),
            '{_sel_json}',
            '{_events_json}',
            {_hl_sql},
            {_ap_sql},
            {_rv_sql},
            '{PROMPT_VERSION_P2}',
            '{MODEL_SONNET}',
            current_timestamp()
        )
    """)
    print("\n\u2705 Stage 2 + 2.5 MERGE complete")
else:
    print("\u26a0\ufe0f No selection result to write")

# COMMAND ----------

# DBTITLE 1,Stage 3: Highlight Writing + Digest
# === Stage 3: Highlight Writing + Today Digest (v3.0) ===

PROMPT_VERSION_P3 = "v3.0"

if not selection_result:
    print("⚠️ No selection result — skipping Stage 3")
else:
    highlights = selection_result.get("highlights", [])
    briefs_grouped = selection_result.get("briefs_grouped", {})
    radar = selection_result.get("radar", [])
    
    # --- Gather full texts for highlight articles ---
    highlight_news_ids = []
    for h in highlights:
        highlight_news_ids.extend(h.get("news_ids", []))
    
    if highlight_news_ids:
        ids_str = ",".join([f"'{nid}'" for nid in highlight_news_ids])
        highlight_texts_df = spark.sql(f"""
            SELECT news_id, title, full_text, url, source 
            FROM {SCHEMA}.news_raw_cleaned 
            WHERE news_id IN ({ids_str}) AND brief_date = '{BRIEF_DATE}'
        """).toPandas()
    else:
        highlight_texts_df = None
    
    # --- Build highlights with full text ---
    highlights_with_text = []
    for h in highlights:
        entry = {"news_ids": h["news_ids"], "category": h["category"], 
                 "topic_ids": h.get("topic_ids", []), "angle": h["angle"]}
        if highlight_texts_df is not None:
            texts = highlight_texts_df[highlight_texts_df['news_id'].isin(h['news_ids'])]
            entry["full_texts"] = texts[['title', 'full_text', 'url', 'source']].to_dict('records')
        highlights_with_text.append(entry)
    
    # --- Look up URLs for briefs (v3.0: also collect absorb IDs) ---
    brief_news_ids = []
    for grp_data in briefs_grouped.values():
        items = grp_data.get('items', []) if isinstance(grp_data, dict) else (grp_data if isinstance(grp_data, list) else [])
        for b in items:
            if b.get('news_id'):
                brief_news_ids.append(b['news_id'])
            for absorbed_id in b.get('absorb', []):
                if absorbed_id:
                    brief_news_ids.append(absorbed_id)
    
    briefs_url_map = {}  # news_id -> {url, source, title}
    if brief_news_ids:
        bids_str = ",".join([f"'{nid}'" for nid in brief_news_ids])
        briefs_meta_df = spark.sql(f"""
            SELECT news_id, title, url, source 
            FROM {SCHEMA}.news_raw_cleaned 
            WHERE news_id IN ({bids_str}) AND brief_date = '{BRIEF_DATE}'
        """).toPandas()
        for _, row in briefs_meta_df.iterrows():
            briefs_url_map[row['news_id']] = {
                'url': row['url'] or '',
                'source': row['source'] or '',
                'title': row['title'] or ''
            }
    print(f"   Briefs URL lookup: {len(briefs_url_map)} / {len(brief_news_ids)} resolved")
    
    # --- Build selection overview (for digest synthesis) ---
    overview_parts = []
    for h in highlights:
        overview_parts.append(f"重點: {h['angle']} [{h['category']}] (importance={h.get('importance', 4)})")
    for grp_name, grp_data in briefs_grouped.items():
        items = grp_data.get('items', []) if isinstance(grp_data, dict) else []
        for b in items:
            overview_parts.append(f"分類新聞[{grp_name}]: {b.get('headline', b.get('summary_short', ''))}")
    for r in radar:
        overview_parts.append(f"雷達: {r.get('note', '')} [可信度:{r.get('credibility', '')}]")
    selection_overview = "\n".join(overview_parts)

    # --- Build briefs overview for Stage 3 (insight + headline list per category) ---
    briefs_overview_parts = []
    for grp_name, grp_data in briefs_grouped.items():
        if not isinstance(grp_data, dict):
            continue
        items = grp_data.get('items', [])
        if not items:
            continue
        insight = grp_data.get('insight', '')
        headlines = [i.get('headline', '') for i in items[:6]]
        briefs_overview_parts.append(f"{grp_name}: insight=\"{insight}\" | items=[{', '.join(headlines)}]")
    briefs_overview_str = "\n".join(briefs_overview_parts) if briefs_overview_parts else "無"

    # --- threads for digest narrative (soft-required: fallback if empty) ---
    threads = selection_result.get('threads', [])
    threads_str = json.dumps(threads, ensure_ascii=False) if threads else "無"
    
    # --- Headline lead (if approved) ---
    headline_lead = "無"
    if headline_approved and headline_review:
        headline_lead = f"影響：{headline_review.get('lead_impact', '')}。建議動作：{headline_review.get('lead_action', '')}"
    
    # --- §P3 Prompt v3.0 (no 💬; sequence numbers; ★ tag line; 🔗 related news; threads narrative) ---
    json_output_example = '{\n  "highlights": [{"news_ids": [""], "category": "", "order": 1, "md": "(\u8a72\u689d\u5b8c\u6574 markdown)"}],\n  "digest_md": "(\u4eca\u65e5\u5c0e\u8b80\u5b8c\u6574 markdown)"\n}'
    
    # Build threads section for prompt (fallback: omit if empty)
    threads_prompt_section = ""
    if threads_str != "無":
        threads_prompt_section = f"""\n【主線骨架】（導讀的主線必須與此一致，refs 指向 highlights 序號與分類新聞大類）
{threads_str}\n"""

    p3_prompt = f"""你是 AUO DSBG 每日情報的撰稿人，為以下 {len(highlights)} 條重點新聞撰寫日報條目，最後寫今日導讀。
讀者是 BU 業務與主管：每天只有 5 分鐘，想知道「發生什麼、跟我有什麼關係」。

【重點新聞全文與切入角度】
{json.dumps(highlights_with_text, ensure_ascii=False, default=str)[:8000]}

【今日全部入選條目一覽】
{selection_overview}

【分類新聞概覽（各類 insight + headline 清單）】
{briefs_overview_str}
{threads_prompt_section}
【頭條導語素材】
{headline_lead}

【每條重點則的格式（嚴格遵守）】
### {{N}}. 標題 — 一句話講完發生什麼事（≤25 字）
*{{大類}}｜{{★×importance 3-5 顆}}｜{{T-xx/W-xx 命中議題}}*

- 重點 bullet 2-3 條：短句事實，每條 ≤30 字
- 為什麼重要：對 AUO 的含意一句話

> 🔗 相關新聞：{{分類新聞 headline}}——一句關聯說明。（僅有強關聯時才寫，無則省略）

（來源：[媒體名](url)｜相關：客戶與產品線）

---

【來源連結規則】
- 每條重點的「來源」欄位請使用 markdown 連結格式：[媒體名](url)
- url 已在 full_texts 中提供，請直接取用
- 若同一條合併多篇新聞，則列出所有來源：[媒體A](url1)、[媒體B](url2)

【風格】繁體中文商業語氣，直述不渲染。推論與事實分開。傳聞在 bullet 標「目前僅屬傳聞」。

【今日導讀格式】
**今日主線：…（≤25 字粗體標題）**

總覽段 2-3 句：全景視角開場。

- **主線一｜…**：一句敘事 + `→ 詳見重點 N；分類新聞·大類名`
- **主線二｜…**：同上
- **周邊掃描**：點名今日訊號最密集的大類 + `→ 詳見分類新聞`

有頭條日：主線標題即頭條，第一條主線放頭條導語（影響 + 建議動作）。
**不要寫 💬 今日追蹤問題**。

【輸出】只輸出 JSON（格式範例）：
{json_output_example}
"""
    
    content = call_claude(
        model=MODEL_SONNET,
        messages=[{"role": "user", "content": p3_prompt}],
        max_tokens=8192,
        thinking=False  # Stage 3: writing task, no need for CoT
    ).strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    
    # Extract JSON and fix common issues
    json_match = re.search(r'\{[\s\S]*\}', content)
    if json_match:
        content = json_match.group(0)
    content = re.sub(r',\s*([}\]])', r'\1', content)
    
    try:
        stage3_result = json.loads(content)
    except json.JSONDecodeError as e:
        print(f"  ⚠️ Stage 3 JSON repair: {e}")
        repaired = repair_json(content, max_tokens=8192)
        stage3_result = json.loads(repaired)
    print(f"✅ Stage 3 complete:")
    print(f"   Highlights written: {len(stage3_result.get('highlights', []))}")
    print(f"   Digest length: {len(stage3_result.get('digest_md', ''))} chars")

# COMMAND ----------

# DBTITLE 1,Stage 4: Assembly + Write to Target Tables
# === Stage 4: Assembly (Markdown + TipTap HTML) + Write to Delta (v3.0) ===
from datetime import datetime
from math import ceil

if not selection_result or not stage3_result:
    print("⚠️ Missing data — skipping Stage 4")
else:
    # --- Brief category labels: (emoji, full_name, short_name) ---
    BRIEF_CATEGORY_LABELS = {
        "macro_economy": ("📊", "總體經濟", "總經"),
        "industry": ("🏭", "產業", "產業"),
        "semiconductor": ("🔬", "半導體 & 零組件", "半導體"),
        "ai_manufacturing": ("🤖", "AI & 智慧製造", "AI"),
        "panel": ("📺", "面板相關", "面板"),
        "consumer_electronics": ("📱", "消費性電子", "消費電子"),
        "it": ("💻", "IT", "IT"),
    }

    # --- v3.0 Helper: Sort categories by (max_importance DESC, count DESC) ---
    def sort_brief_sections(briefs_grouped):
        def sort_key(kv):
            items = kv[1].get('items', []) if isinstance(kv[1], dict) else []
            max_imp = max((i.get('importance', 1) for i in items), default=0)
            return (-max_imp, -len(items))
        return sorted(((k, v) for k, v in briefs_grouped.items()
                       if isinstance(v, dict) and v.get('items')), key=sort_key)

    # --- v3.0 Helper: Markdown to TipTap-safe HTML ---
    def md_to_tiptap_html(md_text: str) -> str:
        lines = md_text.strip().split('\n')
        html_parts = []
        in_list = False
        for line in lines:
            line = line.strip()
            if not line:
                if in_list:
                    html_parts.append('</ul>')
                    in_list = False
                continue
            if line.startswith('### '):
                if in_list:
                    html_parts.append('</ul>')
                    in_list = False
                html_parts.append(f'<h3>{line[4:]}</h3>')
            elif line.startswith('## '):
                if in_list:
                    html_parts.append('</ul>')
                    in_list = False
                html_parts.append(f'<h2>{line[3:]}</h2>')
            elif line.startswith('> '):
                if in_list:
                    html_parts.append('</ul>')
                    in_list = False
                bq = line[2:]
                bq = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" target="_blank">\1</a>', bq)
                bq = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', bq)
                bq = re.sub(r'\*(.+?)\*', r'<em>\1</em>', bq)
                html_parts.append(f'<blockquote><p>{bq}</p></blockquote>')
            elif line.startswith('- '):
                if not in_list:
                    html_parts.append('<ul>')
                    in_list = True
                item = line[2:]
                item = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" target="_blank">\1</a>', item)
                item = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', item)
                item = re.sub(r'\*(.+?)\*', r'<em>\1</em>', item)
                html_parts.append(f'  <li>{item}</li>')
            elif line == '---':
                if in_list:
                    html_parts.append('</ul>')
                    in_list = False
                html_parts.append('<hr>')
            else:
                if in_list:
                    html_parts.append('</ul>')
                    in_list = False
                line = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" target="_blank">\1</a>', line)
                line = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', line)
                line = re.sub(r'\*(.+?)\*', r'<em>\1</em>', line)
                html_parts.append(f'<p>{line}</p>')
        if in_list:
            html_parts.append('</ul>')
        return '\n'.join(html_parts)

    # --- Build highlights (MD + HTML) ---
    highlights_html = []
    highlights_md_parts = []
    for hl in stage3_result.get('highlights', []):
        md = hl.get('md', '')
        highlights_md_parts.append(md)
        highlights_html.append({'html': md_to_tiptap_html(md), 'category': hl.get('category', '')})

    digest_md = stage3_result.get('digest_md', '')
    digest_html = md_to_tiptap_html(digest_md)

    # --- Sort categories & build briefs sections (v3.0: three-line cards) ---
    sorted_categories = sort_brief_sections(briefs_grouped)
    briefs_html_parts = []
    briefs_md_parts = []
    category_counts = {}  # key -> actual rendered count (for nav bar)
    total_brief_count = 0

    for grp_key, grp_data in sorted_categories:
        emoji, full_name, short_name = BRIEF_CATEGORY_LABELS.get(grp_key, ('', grp_key, grp_key))
        items = sorted(grp_data.get('items', []), key=lambda x: -x.get('importance', 1))
        insight = grp_data.get('insight', '')

        # Build HTML for this category section
        cat_html = f'<hr>\n<h3>{emoji} <mark>{full_name}（{len(items)} 則）</mark></h3>\n'
        if insight:
            cat_html += f'<blockquote><p>本類趨勢：{insight}</p></blockquote>\n'

        # Build MD for this category
        cat_md = f'\n---\n\n### {emoji} {full_name}（{len(items)} 則）\n\n'
        if insight:
            cat_md += f'> 本類趨勢：{insight}\n\n'

        for item in items:
            nid = item.get('news_id', '')
            headline = item.get('headline', '')
            detail = item.get('detail', '')
            # Collect sources (including absorbed items)
            source_links_html = []
            source_links_md = []
            all_ids = [nid] + item.get('absorb', [])
            for sid in all_ids:
                meta = briefs_url_map.get(sid, {})
                if meta.get('url') and meta.get('source'):
                    source_links_html.append(f'<a href="{meta["url"]}" target="_blank">{meta["source"]}</a>')
                    source_links_md.append(f'[{meta["source"]}]({meta["url"]})')
                elif meta.get('url'):
                    source_links_html.append(f'<a href="{meta["url"]}" target="_blank">原文</a>')
                    source_links_md.append(f'[原文]({meta["url"]})')
            sources_html = '、'.join(source_links_html) if source_links_html else ''
            sources_md = '、'.join(source_links_md) if source_links_md else ''

            # Three-line card HTML: <p><strong>headline</strong><br>detail<br>(sources)</p>
            cat_html += f'<p><strong>{headline}</strong><br>{detail}<br>'
            if sources_html:
                cat_html += f'（{sources_html}）'
            cat_html += '</p>\n'

            # Three-line card MD
            cat_md += f'**{headline}**\n{detail}\n'
            if sources_md:
                cat_md += f'（{sources_md}）\n'
            cat_md += '\n'

        briefs_html_parts.append({'key': grp_key, 'html': cat_html, 'count': len(items), 'items': items})
        briefs_md_parts.append({'key': grp_key, 'md': cat_md, 'count': len(items)})
        category_counts[grp_key] = len(items)
        total_brief_count += len(items)

    # --- 10,000 char guard: trim from lowest importance upward ---
    weekdays = ['一', '二', '三', '四', '五', '六', '日']
    brief_date_str = f"{BRIEF_DATE}（{weekdays[BRIEF_DATE.weekday()]}）"
    report_title = f"DSBG 每日重點新聞 {BRIEF_DATE}"
    highlight_count = len(highlights_html)
    read_time = max(3, highlight_count * 2 + ceil(total_brief_count / 8))

    # Assemble briefs HTML (without nav bar yet)
    briefs_full_html = ''.join(bp['html'] for bp in briefs_html_parts)
    briefs_full_md = ''.join(bp['md'] for bp in briefs_md_parts)

    # Summary intro line
    top_cats = [BRIEF_CATEGORY_LABELS[bp['key']][2] for bp in briefs_html_parts[:2]]
    summary_intro = f'今日分類新聞 {total_brief_count} 則，{"與".join(top_cats)}訊號最密集；依重要性排序。'

    # Compose full HTML (no nav bar yet — post-render insertion)
    meta_html = f'<p><em>重點 {highlight_count} 則｜分類新聞 {total_brief_count} 則｜閱讀約 {read_time} 分鐘｜★ = 重要度</em></p>'
    full_html = f'{meta_html}\n{{NAV_BAR_PLACEHOLDER}}\n<h2>今日導讀</h2>\n{digest_html}\n<hr>\n<h2>今日重點</h2>\n'
    full_html += '\n'.join(hl['html'] for hl in highlights_html)
    full_html += f'\n<h2>分類新聞</h2>\n<p><em>{summary_intro}</em></p>\n{briefs_full_html}'

    # Check plain text length and TRIM if over limit
    plain_text = re.sub(r'<[^>]+>', '', full_html)
    trimmed_items = []
    for trim_imp in [1, 2]:
        if len(plain_text) <= 9500:
            break
        # Trim from last (least important) category first
        for bp in reversed(briefs_html_parts):
            if len(plain_text) <= 9500:
                break
            items_to_keep = []
            for item in bp['items']:
                if item.get('importance', 1) <= trim_imp:
                    trimmed_items.append(f"{bp['key']}: {item.get('headline', '')}")
                else:
                    items_to_keep.append(item)
            bp['items'] = items_to_keep
            bp['count'] = len(items_to_keep)
            category_counts[bp['key']] = len(items_to_keep)
        # Re-render after trim
        briefs_full_html = ''
        briefs_full_md = ''
        total_brief_count = 0
        for bp in briefs_html_parts:
            if not bp['items']:
                continue
            grp_key = bp['key']
            emoji, full_name, short_name = BRIEF_CATEGORY_LABELS.get(grp_key, ('', grp_key, grp_key))
            grp_data = briefs_grouped.get(grp_key, {})
            insight = grp_data.get('insight', '') if isinstance(grp_data, dict) else ''
            cat_html = f'<hr>\n<h3>{emoji} <mark>{full_name}（{len(bp["items"])} 則）</mark></h3>\n'
            if insight:
                cat_html += f'<blockquote><p>本類趨勢：{insight}</p></blockquote>\n'
            cat_md = f'\n---\n\n### {emoji} {full_name}（{len(bp["items"])} 則）\n\n'
            if insight:
                cat_md += f'> 本類趨勢：{insight}\n\n'
            for item in bp['items']:
                nid = item.get('news_id', '')
                headline = item.get('headline', '')
                detail = item.get('detail', '')
                source_links_html = []
                source_links_md = []
                for sid in [nid] + item.get('absorb', []):
                    meta = briefs_url_map.get(sid, {})
                    if meta.get('url') and meta.get('source'):
                        source_links_html.append(f'<a href="{meta["url"]}" target="_blank">{meta["source"]}</a>')
                        source_links_md.append(f'[{meta["source"]}]({meta["url"]})')
                sources_html = '、'.join(source_links_html)
                sources_md = '、'.join(source_links_md)
                cat_html += f'<p><strong>{headline}</strong><br>{detail}<br>'
                if sources_html:
                    cat_html += f'（{sources_html}）'
                cat_html += '</p>\n'
                cat_md += f'**{headline}**\n{detail}\n'
                if sources_md:
                    cat_md += f'（{sources_md}）\n'
                cat_md += '\n'
            briefs_full_html += cat_html
            briefs_full_md += cat_md
            total_brief_count += len(bp['items'])
        # Recompose
        read_time = max(3, highlight_count * 2 + ceil(total_brief_count / 8))
        meta_html = f'<p><em>重點 {highlight_count} 則｜分類新聞 {total_brief_count} 則｜閱讀約 {read_time} 分鐘｜★ = 重要度</em></p>'
        top_cats = [BRIEF_CATEGORY_LABELS[bp['key']][2] for bp in briefs_html_parts if bp['items']][:2]
        summary_intro = f'今日分類新聞 {total_brief_count} 則，{"與".join(top_cats)}訊號最密集；依重要性排序。'
        full_html = f'{meta_html}\n{{NAV_BAR_PLACEHOLDER}}\n<h2>今日導讀</h2>\n{digest_html}\n<hr>\n<h2>今日重點</h2>\n'
        full_html += '\n'.join(hl['html'] for hl in highlights_html)
        full_html += f'\n<h2>分類新聞</h2>\n<p><em>{summary_intro}</em></p>\n{briefs_full_html}'
        plain_text = re.sub(r'<[^>]+>', '', full_html)

    if trimmed_items:
        full_html += f'<p><em>（另有 {len(trimmed_items)} 則低重要性新聞未刊出）</em></p>\n'
        briefs_full_md += f'\n*（另有 {len(trimmed_items)} 則低重要性新聞未刊出）*\n'
        print(f"  ⚠️ Trimmed {len(trimmed_items)} items: {trimmed_items}")

    # --- Post-render: Build navigation bar (uses actual post-trim counts) ---
    nav_parts = []
    # Include ALL 7 categories; sorted ones first, then zero-count ones
    rendered_keys = [bp['key'] for bp in briefs_html_parts if bp.get('items')]
    for grp_key in rendered_keys:
        emoji, _, short_name = BRIEF_CATEGORY_LABELS[grp_key]
        count = category_counts.get(grp_key, 0)
        nav_parts.append(f'<code>{emoji} {short_name} {count}</code>')
    for grp_key, (emoji, _, short_name) in BRIEF_CATEGORY_LABELS.items():
        if grp_key not in rendered_keys:
            nav_parts.append(f'<code>{emoji} {short_name} 0</code>')
    nav_bar_html = f'<h2>{" | ".join(nav_parts)}</h2>'
    full_html = full_html.replace('{NAV_BAR_PLACEHOLDER}', nav_bar_html)

    # Build nav bar for MD
    nav_md_parts = []
    for grp_key in rendered_keys:
        emoji, _, short_name = BRIEF_CATEGORY_LABELS[grp_key]
        count = category_counts.get(grp_key, 0)
        nav_md_parts.append(f'`{emoji} {short_name} {count}`')
    for grp_key, (emoji, _, short_name) in BRIEF_CATEGORY_LABELS.items():
        if grp_key not in rendered_keys:
            nav_md_parts.append(f'`{emoji} {short_name} 0`')
    nav_bar_md = f'## {" | ".join(nav_md_parts)}'

    # --- Build full Markdown ---
    meta_md = f'*重點 {highlight_count} 則｜分類新聞 {total_brief_count} 則｜閱讀約 {read_time} 分鐘｜★ = 重要度*'
    full_md = f'# {brief_date_str} AUO DSBG 日報\n\n{meta_md}\n\n{nav_bar_md}\n\n## 今日導讀\n{digest_md}\n\n---\n\n## 今日重點\n\n'
    full_md += '\n\n---\n\n'.join(highlights_md_parts)
    full_md += f'\n\n## 分類新聞\n\n*{summary_intro}*\n{briefs_full_md}'

    # --- Final plain text check ---
    plain_text_len = len(re.sub(r'<[^>]+>', '', full_html))
    print(f"HTML plain text length: {plain_text_len} / 10000 chars")

    # --- Write to news_daily_brief ---
    _md = full_md.replace("'", "''")
    _html = full_html.replace("'", "''")
    _title = report_title.replace("'", "''")
    _hl_json = json.dumps(stage3_result, ensure_ascii=False).replace("'", "''")
    _digest = digest_md.replace("'", "''")
    _pv = json.dumps({"p1": PROMPT_VERSION_P1, "p2": PROMPT_VERSION_P2, "p3": PROMPT_VERSION_P3}).replace("'", "''")
    _mi = json.dumps({"stage1_filter": MODEL_SONNET, "stage2_selection": MODEL_SONNET, "stage2.5_headline": MODEL_OPUS, "stage3_writing": MODEL_SONNET}).replace("'", "''")
    unmatched_count = sum(1 for c in all_cards if not c.get('matched', False))

    spark.sql(f"DELETE FROM {SCHEMA}.news_daily_brief WHERE brief_date = '{BRIEF_DATE}'")
    spark.sql(f"""
        INSERT INTO {SCHEMA}.news_daily_brief
        (brief_date, md_content, html_content, report_title, highlights_json,
         digest_md, unmatched_count, filter_card_version, prompt_versions, model_ids,
         published, published_at, created_at)
        VALUES (
            DATE('{BRIEF_DATE}'), '{_md}', '{_html}', '{_title}', '{_hl_json}',
            '{_digest}', {unmatched_count}, 'v1.3-lite', '{_pv}', '{_mi}',
            false, NULL, current_timestamp()
        )
    """)

    # --- Write to s_news_issue_reports (bug fix: content=HTML, visible_pillars from config) ---
    _pillars_sql = "array('" + "','".join(VISIBLE_PILLARS) + "')"
    spark.sql(f"DELETE FROM {SCHEMA}.s_news_issue_reports WHERE brief_date = '{BRIEF_DATE}'")
    spark.sql(f"""
        INSERT INTO {SCHEMA}.s_news_issue_reports
        (brief_date, category_id, category_key, title, content, status,
         visible_pillars, created_by, created_at, is_deleted, md_content, highlights_json, model_ids)
        VALUES (
            DATE('{BRIEF_DATE}'), {CATEGORY_ID}, '{CATEGORY_KEY}', '{_title}', '{_html}',
            'published', {_pillars_sql}, 'ericmlyang', current_timestamp(), false,
            '{_md}', '{_hl_json}', '{_mi}'
        )
    """)

    print(f"\n✅ Stage 4 complete:")
    print(f"   Report: {report_title}")
    print(f"   HTML: {len(full_html)} chars | MD: {len(full_md)} chars")
    print(f"   Plain text: {plain_text_len} / 10000")
    print(f"   Written to news_daily_brief + s_news_issue_reports")

# COMMAND ----------

# DBTITLE 1,Stage 5: Add agent_analysis Column (Idempotent)
# MAGIC %md
# MAGIC # Add agent_analysis column if it doesn't exist (runtime-compatible)
# MAGIC columns = [c.name for c in spark.table("micenter.mi3_datahub_prod.s_news_issue_reports").schema]
# MAGIC if "agent_analysis" not in columns:
# MAGIC     spark.sql("ALTER TABLE micenter.mi3_datahub_prod.s_news_issue_reports ADD COLUMNS (agent_analysis STRING COMMENT 'Agent 每日數據推廣大使分析輸出')")
# MAGIC     print("✅ agent_analysis column added")
# MAGIC else:
# MAGIC     print("✅ agent_analysis column already exists")

# COMMAND ----------

# DBTITLE 1,Stage 5: Sync s_news_issue_reports → PostgreSQL
# ────────────────────────────────────────────────────────────────────
# Stage 5: s_news_issue_reports → PostgreSQL app_custom_reports
# 策略: DELETE by brief_date → INSERT（冪等，job 重跑安全）
# ────────────────────────────────────────────────────────────────────
import sys
sys.path.insert(0, "/Workspace/Users/eric.ml.yang@auo.com/mi3-data-center")
from modules.postgres.postgres_jdbc import sync_to_postgres, prepare_df_for_postgres
from pyspark.sql import functions as F

# ── 讀取當日 Delta 資料 ────────────────────────────────────────────────────
df_s_news = (
    spark.table(f"{SCHEMA}.s_news_issue_reports")
    .filter(F.col("brief_date") == F.lit(BRIEF_DATE))
)

if df_s_news.isEmpty():
    print(f"⚠️ Stage 5 skipped: s_news_issue_reports 對 {BRIEF_DATE} 無資料")
else:
    # ── 固定 created_by / updated_by 為員工編號 ─────────────────────────────
    df_s_news = df_s_news.withColumn("created_by", F.lit("1806011")).withColumn("updated_by", F.lit("1806011"))

    # ── 欄位排除 + ARRAY 轉換 ────────────────────────────────────────────
    # id: PG 側自增，md_content/highlights_json/model_ids: pipeline 內部用，不推
    df_pg = prepare_df_for_postgres(
        df_s_news,
        array_columns=["visible_pillars"],
        exclude_columns=["id", "md_content", "highlights_json", "model_ids", "agent_analysis"],
    )

    # ── Sync to PostgreSQL ───────────────────────────────────────────────
    PG_HOST = dbutils.secrets.get(scope="mi3-postgres", key="pg-host")
    PG_USER = dbutils.secrets.get(scope="mi3-postgres", key="pg-user")
    PG_PASS = dbutils.secrets.get(scope="mi3-postgres", key="pg-password")
    PG_DB   = dbutils.secrets.get(scope="mi3-postgres", key="pg-database")

    sync_to_postgres(
        df_pg, spark=spark,
        host=PG_HOST, port=5432, database=PG_DB, user=PG_USER, password=PG_PASS,
        table="app_custom_reports", schema="public",
        key_column="brief_date",
        key_value=str(BRIEF_DATE),
    )
    print(f"✅ Stage 5 complete: {BRIEF_DATE} 已同步到 app_custom_reports")

# COMMAND ----------

# DBTITLE 1,Print Latest Report Content (with tags)
# 印出最新一筆彙整的 content（含 HTML/Markdown tags）
row = spark.sql(f"""
    SELECT brief_date, title, content
    FROM {SCHEMA}.s_news_issue_reports
    WHERE is_deleted IS NOT TRUE
    ORDER BY brief_date DESC
    LIMIT 1
""").first()

if row:
    print(f"brief_date: {row.brief_date}")
    print(f"title: {row.title}")
    print("=" * 80)
    print(row.content)
else:
    print("⚠️ No records found")

# COMMAND ----------

# DBTITLE 1,Check Latest PostgreSQL News Record
# # === 撈取 PostgreSQL 最新兩筆新聞數據（所有欄位）並比較 ===
# import psycopg2
# from datetime import datetime
# import pytz

# tz = pytz.timezone("Asia/Taipei")
# now_taipei = datetime.now(tz)

# PG_HOST = dbutils.secrets.get(scope="mi3-postgres", key="pg-host")
# PG_USER = dbutils.secrets.get(scope="mi3-postgres", key="pg-user")
# PG_PASS = dbutils.secrets.get(scope="mi3-postgres", key="pg-password")
# PG_DB   = dbutils.secrets.get(scope="mi3-postgres", key="pg-database")

# try:
#     conn = psycopg2.connect(host=PG_HOST, port=5432, dbname=PG_DB, user=PG_USER, password=PG_PASS, sslmode="require")
#     cur = conn.cursor()

#     cur.execute("""
#         SELECT *
#         FROM public.app_custom_reports
#         WHERE brief_date IS NOT NULL
#         ORDER BY brief_date DESC, created_at DESC
#         LIMIT 2
#     """)
#     rows = cur.fetchall()
#     col_names = [desc[0] for desc in cur.description]

#     print(f"📅 查詢時間 (台北): {now_taipei.strftime('%Y-%m-%d %H:%M:%S')}")
#     print(f"📋 總欄位數: {len(col_names)}")
#     print(f"📋 欄位名稱: {col_names}")
#     print("=" * 80)

#     def display_row(row, label):
#         print(f"\n{'🔵' if '最新' in label else '🟡'} {label}:")
#         print("-" * 80)
#         for i, col in enumerate(col_names):
#             val = row[i]
#             val_type = type(val).__name__ if val is not None else 'NULL'
#             if col == 'content':
#                 display_val = f"[{len(str(val))} chars]" if val else 'NULL'
#             elif val is not None and len(str(val)) > 120:
#                 display_val = f"{str(val)[:120]}..."
#             else:
#                 display_val = str(val) if val is not None else 'NULL'
#             print(f"  {col:20s} ({val_type:10s}) = {display_val}")

#     if rows:
#         display_row(rows[0], "最新一筆")
#     if len(rows) > 1:
#         display_row(rows[1], "上一筆")

#         # === 比較兩筆差異 ===
#         print("\n" + "=" * 80)
#         print("📊 欄位差異比較：")
#         print("-" * 80)
#         diff_count = 0
#         for i, col in enumerate(col_names):
#             v1 = rows[0][i]
#             v2 = rows[1][i]
#             t1 = type(v1).__name__ if v1 is not None else 'NULL'
#             t2 = type(v2).__name__ if v2 is not None else 'NULL'

#             if col in ('brief_date', 'created_at', 'updated_at', 'id', 'title', 'content'):
#                 status = "(預期不同，略過)"
#             elif t1 != t2:
#                 status = f"⚠️ 類型不同! [{t1}] vs [{t2}]"
#                 diff_count += 1
#             elif v1 is None and v2 is None:
#                 status = "✓ 一致 (both NULL)"
#             elif v1 != v2:
#                 status = f"⚠️ 值不同! [{v1}] vs [{v2}]"
#                 diff_count += 1
#             else:
#                 status = f"✓ 一致 = {v1}"
#             print(f"  {col:20s} → {status}")

#         print(f"\n{'✅ 結論: 所有非預期欄位完全一致' if diff_count == 0 else f'⚠️ 結論: 發現 {diff_count} 個欄位不一致'}")

#     cur.close()
#     conn.close()
#     print("\n✅ PostgreSQL 連線正常")
# except Exception as e:
#     print(f"❌ Error: {type(e).__name__}: {e}")

# COMMAND ----------

# MAGIC %md
# MAGIC 以下完整欄位說明
# MAGIC ### `title`
# MAGIC - 必填，長度上限 200 字。
# MAGIC - 範例：`"每日新聞的數據探索示範｜2026-06-15"`、`"品牌財報焦點"`、`"2026-06-13 AUO DSBG 每周新聞"`
# MAGIC  
# MAGIC ### `content`
# MAGIC - 可為 `NULL`，但通常會填入報告正文。
# MAGIC - 實際資料顯示可接受三種格式：
# MAGIC   1. **純文字 / Markdown**：例如 `"# 2026-08-24（一） AUO DSBG 日報\n\n*重點 3 則｜快訊 21 則...*"`
# MAGIC   2. **富文本編輯器輸出的 HTML 片段**：例如 `"<p>&lt;p&gt;根據今日（2026-06-15）的每日議題彙整...&lt;/p&gt;</p>"`（可見到編輯器將標籤做了 HTML escape，屬正常情況）
# MAGIC   3. **完整 HTML 文件**（含 `<!DOCTYPE html>`、`<style>` 等），用於測試或直接貼入完整報告樣板，長度可達數萬字元（實際資料最大 47,693 字元）
# MAGIC  
# MAGIC ### `summary`
# MAGIC - 可為 `NULL`；若作者未手動填寫，前端顯示時應改用 `content` 自動截取的摘要。
# MAGIC - 上限 200 字，實務上多為簡短標題延伸，例如：`"品牌財報焦點"`、`"Dell"`、`"測試完整"`
# MAGIC  
# MAGIC ### `status`
# MAGIC - 僅允許兩個值：
# MAGIC   - `"draft"`（草稿，尚未發佈，`published_at` 為 `NULL`）
# MAGIC   - `"published"`（已發佈）
# MAGIC - 目前 18 筆中 17 筆為 `published`，1 筆為 `draft`。
# MAGIC  
# MAGIC ### `visible_pillars`
# MAGIC - PostgreSQL 陣列型別，
# MAGIC - 範例：`{"ADP","AMSC","AUO"}`（PostgreSQL 陣列字面值）-（代表對三個 Pillar 皆可見）。
# MAGIC  
# MAGIC ### `created_by` / `updated_by`
# MAGIC - 需帶入 `app_emp.emp_no`（員工編號字串），**非**員工姓名。
# MAGIC - 範例對照：
# MAGIC  
# MAGIC   | `emp_no` | 對應 `emp_name` |
# MAGIC   |---|---|
# MAGIC   | `1806011` | 楊士永 |
# MAGIC   | `1901035` | 呂國豪 |
# MAGIC   | `2106004` | 林璟 |
# MAGIC  
# MAGIC - `updated_by` 在尚未被修改過的草稿可為 `NULL`。
# MAGIC  
# MAGIC ### `created_at` / `updated_at` / `published_at`
# MAGIC - 皆為 `timestamp without time zone`，格式如 `2026-08-25 14:41:24.222528`。
# MAGIC - 邏輯關聯：
# MAGIC   - 新增時只會有 `created_at` 有值。
# MAGIC   - 修改後 `updated_at` 會更新。
# MAGIC   - 只有 `status` 變為 `published` 時 `published_at` 才會被寫入；`draft` 狀態下恆為 `NULL`。
# MAGIC   - 已發佈資料的 `published_at` 通常與最後一次 `updated_at` 相同或極接近（代表發佈當下的動作）。
# MAGIC  
# MAGIC ### `is_deleted`
# MAGIC - 軟刪除標記，查詢清單時應加上 `WHERE is_deleted = false`。
# MAGIC - 目前資料庫中的 18 筆皆為 `false`。
# MAGIC  
# MAGIC ### `category_key`
# MAGIC - **目前實際生效的分類欄位**，需為 `app_system_dict` 中 `group_key = 'custom_report_category'` 的合法 `item_key`：
