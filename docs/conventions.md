# 開發慣例

適用於本 repo 內所有 Agent 產出與使用者手寫的內容。與 `CLAUDE.md` 重疊處以本文件為細節版。

## 1. Notebook（`.ipynb`）

### 1.1 Cell 標籤

- 每個 **code cell 第一行**為標籤：`# [cNN] 名稱`。`NN` 兩位數，名稱用 snake_case，描述該 cell 的用途。
- SQL magic cell：第一行 `%sql`，第二行 `-- [cNN] 名稱`。
- Markdown cell 不加標籤，用內容識別。
- 標籤是 cell 的穩定 ID。**插入新 cell 用字母尾碼**（`[c05a]`、`[c05b]`），不重新編號既有 cell；刪除 cell 後編號留空即可。
- 同一 notebook 內標籤不可重複。

### 1.2 標準 cell 順序（見 `jobs/_template/notebook.ipynb`）

| 標籤 | 用途 | 本機可測 |
|---|---|---|
| （markdown） | 標題、用途、輸入 / 輸出、負責人、更新日期 | – |
| `[c01] params` | `dbutils.widgets` 定義與讀取，含 catalog / schema | 否 |
| `[c02] imports` | import 與共用常數 | 是 |
| `[c03] load_*` | 讀取來源 table | 否 |
| `[c04]`、`[c05]`… `transform_*` | 純函式 `DataFrame -> DataFrame`，cell 內無 I/O | **是** |
| `[c1x] run` | 呼叫 transform 串接流程 | 否 |
| `[c2x] write_*` | 寫入 Delta，明示 append / overwrite / MERGE | 否 |
| `[c3x] check_*` | 寫入後驗證（筆數、null、重複鍵） | 否 |

### 1.3 局部修改的回覆格式

```markdown
## 變更點摘要
- ...

### [c05] transform_orders → 替換整個 cell
說明一兩句。
```python
# [c05] transform_orders
（完整 cell）
```

### [c05a] transform_dedupe → 新增於 [c05] 之後
```python
# [c05a] transform_dedupe
（完整 cell）
```

### [c07] old_step → 刪除

## 假設與需確認事項
- ...
```

動作只有四種：`替換整個 cell`、`新增於 [cNN] 之後`、`刪除`、`不變`。code block 內容永遠是完整 cell，含第一行標籤。

### 1.4 工具

```text
python tools/nb.py list   <nb>                 # 列出所有 cell：index、type、標籤、第一行、行數
python tools/nb.py show   <nb> <tag>           # 印出某 cell 原始碼
python tools/nb.py set    <nb> <tag> <file|->  # 用檔案（或 stdin）內容替換該 cell
python tools/nb.py insert <nb> <after_tag> <file|-> [--markdown]   # 在某 cell 之後插入新 cell
python tools/nb.py delete <nb> <tag>
python tools/nb.py strip  <nb>                 # 清除 outputs / execution_count（commit 前執行）
python tools/nb.py export <nb> <tag> [<tag>...]  # 串接 cell 原始碼輸出到 stdout（去掉 magic 行）
```

## 2. Python / PySpark

- 目標 DBR 17.3 LTS（Spark 4.0）。ANSI mode 預設開啟；需要寬鬆行為用 `try_cast`、`try_divide`、`try_element_at` 並註明原因。
- 優先 DataFrame API；`from pyspark.sql import functions as F`；避免 `select("*")` 後再加欄位造成 schema 不明。
- 純函式簽名：`def transform_xxx(df: DataFrame, *, param: type = default) -> DataFrame`。
- Table 名稱用 f-string 從參數組合：`f"{catalog}.{schema}.orders"`。
- 寫入：`df.write.mode("overwrite").saveAsTable(...)` 或 `DeltaTable.merge`，在 cell 內註明選擇理由。
- Lint：`ruff check .`；格式：`ruff format .`。

### 2.1 Table 命名與分層

`<層級>_<領域>_<名稱>`，層級前綴固定四種：

| 前綴 | 意義 | 例 |
|---|---|---|
| `b_` | 原始層（bronze）：外部來源原樣落地，目前爬蟲機來的都是這層 | `b_ir_calendar_record` |
| `s_` | 銀質（silver）：清洗、去重、標準化，給查詢 | `s_ir_calendar_conference` |
| `g_` | 金質（gold）：彙總、給報表 / Genie 用 | `g_ir_calendar_monthly_summary` |
| `app_` | 其他系統（應用系統 DB）同步過來的表 | `app_company` |

領域名由 widget `domain` 帶入，層級前綴在 code 內固定，code 只寫短名。

各層的規則（實例：`docs/20260921_ir_calendar_lakehouse_design.md`）：

| 層 | 寫入 | schema | 內容 |
|---|---|---|---|
| `b_` | **append-only**；同一批重跑用「刪該批再 append」保持冪等，不 MERGE、不去重 | 固定，不隨來源欄位變動：來源原文整包放 `payload`（STRING JSON），外加批次血緣（`batch_id`、`seq`、`ingested_at`…） | 一個來源 feed 一張表，不同 record_type 用欄位區分，不各建一張 |
| `s_` | MERGE，鍵值明確唯一；同鍵多列取最新批次 | 型別化欄位，只列要用的；來源多的欄位忽略、少的補 NULL | 由 `b_` 的純函式 transform 產生，**隨時可整表重算**，不從 Volume / 來源重刷 |
| `g_` | overwrite 或 MERGE，看報表性質 | 依報表 | 只從 `s_` 建，不直接讀 `b_` |
| job 遙測（batch log 之類） | 允許 MERGE 覆蓋 | — | 放 `b_`，因為它記的是這一層的搬運結果 |

時間欄位：`TIMESTAMP` 一律存 UTC 瞬間，來源無時區字串在 silver 轉換時補時區；`DATE` 為曆日、不做時區處理。

## 3. SQL（`sql/`）

- 一檔一題，檔名 `YYYYMMDD_主題.sql`。
- 檔頭註解：用途、來源 table、作者、日期、注意事項。
- Databricks SQL 語法；大 query 拆 CTE，每個 CTE 前一行註解說明。
- 三段式 table 名稱；避免 `SELECT *` 於最終輸出。

## 4. 本機測試（`tests/`）

- 只測純 DataFrame 轉換。用 `tests/nbload.py` 依標籤載入 notebook 內的 cell：

  ```python
  from nbload import load_cells
  mod = load_cells("jobs/my_job/notebook.ipynb", ["c02", "c05"])
  out = mod.transform_orders(spark.createDataFrame(...))
  ```

- `spark` fixture 為 `local[2]`，session 範圍；不要在測試中讀寫檔案或 table。
- 本機 pyspark 版本若非 4.0，ANSI 相關行為可能不同，測試結果需保留此提醒。

## 5. Genie Space（`genie/`）

每個 Genie Space 一個 `.md`，內容：目的與使用者、資料集（table 與欄位語意）、instructions 草稿、sample questions、已知限制與不該問的問題。

## 6. Scratch（`scratch/`）

使用者貼上待修改的 code 放這裡，預設不追蹤於 git。Agent 的修改結果以 cell 為單位回覆，或另存到 `jobs/`。
