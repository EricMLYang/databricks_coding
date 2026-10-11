# ir_calendar notebook 對應爬蟲端 2026-10-08～10 變更的修改（2026-10-11）

依據：MI_Crawler `ir_calendar/doc/20261010_給Databricks_notebook開發者_爬蟲端變更交代.md`。
本次處理 §2.1（彙整五個新欄位）、§3.1（告警分級）、§3.2（`.htm` 不送 `ai_parse_document`）。
§2.2（`ir_financials` 建 silver）**未做**；§3.3 分類與鍵沒變，`check_landing` / `check_api_status` 不用改。

## 修改簡述

### §3.1 爬蟲端告警分級（`consume_batches`）

- 以前 `health.status == "ALERT"` 就讓 job 失敗；擴到 175 家後「實體檔案放棄」會變常態，job 會一直紅燈。
- 現在 [c03] `crawler_alerts` 把告警分三級：
  - **FATAL**（job 失敗）：`health.json` 讀不到 / 超過 `health_max_age_hours` / `generated_at` 解析不了、`來源 … 連續失敗`、`LLM CLI 不可用`、`缺公司代稱`、`找不到已落地檔案`
  - **WARN**（只印）：`實體檔案放棄 N 筆`（附 `health.docs.give_up` 全部明細）與其他不認得的訊息（爬蟲端新增告警預設不會讓 job 紅）
  - **INFO**：`health.docs.pending` 筆數
- 「完成：處理 N 批」之後固定印 `==== 爬蟲端告警 … ====` 區塊；沒有告警也印 `==== 爬蟲端告警：無 ====`。批次失敗時也會先印再拋例外。
- 同一份清單寫進 `b_ir_calendar_batch_log.crawler_alerts ARRAY<STRING>`（新欄位）。只有處理到批次的那次才會寫；沒新批次時只印。
  查歷史：`SELECT batch_id, processed_at, explode(crawler_alerts) FROM b_ir_calendar_batch_log`。
- [c20] 只有 FATAL 才 `raise`。

### §3.2 `.htm` 改走純 Python 抽文字（`parse_documents`）

- `ai_parse_document` 不支援 HTML；EDGAR 的 8-K EX-99、10-Q / 10-K 本體（HP、Dell、康寧、3M）以前每次都失敗。
- 依副檔名分流：`.htm` / `.html` 走新 cell [c03a] `html_to_payload`（標準庫 `html.parser`，不呼叫 API、不計費）：
  剝 SGML 包頭、略過 head / script / style 與 iXBRL 隱藏區、段落 / 標題 / 清單 → 元素、`<table>` → markdown 表格
  （colspan 展開、`$` / `)` / `%` 併回數字、跨欄表頭對到有資料的欄）、`page-break` 樣式換頁。
- 輸出與 `ai_parse_document` 同形狀 JSON，silver 不用分流；bronze / silver 的 `parser = html_text`、`parser_version = 1.0`。
- 以前送過 `ai_parse_document` 的 `.htm`（即使已達 `max_attempts`）會自動重排一次，attempt 歸零。
- HTML 組失敗不重試、組間不等 `pause_seconds`。

### §2.1 法說彙整五個新欄位（`init_tables` / `consume_batches`）

- `s_ir_calendar_summary` 加五欄：
  `headline_metrics ARRAY<STRUCT<metric, period, value, yoy, note>>`、`management_views ARRAY<STRUCT<topic, view>>`、
  `positive_signals` / `watch_items` / `open_questions ARRAY<STRING>`。`value` / `yoy` 保留字串不轉數值。
- 舊批次沒有這些鍵 → NULL。新欄位在 DDL 裡排在 `updated_at` 之後（與既有表 `ADD COLUMNS` 的位置一致），MERGE 依欄名對應。

### 既有表補欄位（`init_tables` [c21]）

- 新 cell [c21] `add_columns`：`CREATE TABLE IF NOT EXISTS` 不會改既有表，上線後加的欄位在這裡 `ALTER TABLE ADD COLUMNS`，已存在就略過，可重跑。
- 本次登記：`b_ir_calendar_batch_log.crawler_alerts`、`s_ir_calendar_summary` 五欄。

## 要複製到 Databricks 的 cell

「替換」是整個 cell 蓋掉，「新增」是插在指定 cell 之後。

| 檔案 | cell | 動作 | 對應 |
|---|---|---|---|
| `jobs/ir_calendar/init_tables/notebook.ipynb` | [c11] ddl_b_batch_log | 替換 | §3.1 |
| 同上 | [c13] ddl_s_summary | 替換 | §2.1 |
| 同上 | **[c21] add_columns** | 新增於 [c20] 之後 | §3.1、§2.1 |
| `jobs/ir_calendar/consume_batches/notebook.ipynb` | [c03] pure_helpers | 替換 | §3.1 |
| 同上 | [c04] table_schemas | 替換 | §3.1、§2.1 |
| 同上 | [c05] row_builders | 替換 | §3.1 |
| 同上 | [c06] transform_silver | 替換 | §2.1 |
| 同上 | [c11] run_once | 替換 | §3.1 |
| 同上 | [c20] main | 替換 | §3.1 |
| `jobs/ir_calendar/parse_documents/notebook.ipynb` | [c02] imports | 替換 | §3.2 |
| 同上 | [c03] pure_helpers | 替換 | §3.2 |
| 同上 | **[c03a] html_text** | 新增於 [c03] 之後 | §3.2 |
| 同上 | [c05] transform_parse | 替換 | §3.2 |
| 同上 | [c07] io_parse | 替換 | §3.2 |
| 同上 | [c08] io_delta | 替換 | §3.2 |
| 同上 | [c10] run_once | 替換 | §3.2 |
| 上面三個 notebook | 第一個 markdown cell | 選做（只改說明） | — |

其餘 cell 不變；`check_landing`、`check_api_status`、`inspect_record` 不用動。
本機取單一 cell 內容：`python3 tools/nb.py show <notebook> <tag>`。

## 上線順序

1. **`init_tables` 先**：貼好 [c11]、[c13]、[c21]，跑 [c01] → [c02] → [c21]，應印出
   `add …b_ir_calendar_batch_log：['crawler_alerts']` 與 `add …s_ir_calendar_summary：[五欄]`。
   這步必須在新版 `consume_batches` 之前：batch_log / summary 的 MERGE 不開 schema evolution，少欄位會失敗。
2. 換 `consume_batches` 的 cell，照常排程。若部署前 bronze 已收到帶新欄位的彙整，跑一次 `rebuild_silver = true` 補算。
3. 換 `parse_documents` 的 cell，先 `dry_run = true` 確認 `.htm` 出現在清單且 attempt = 0，再正式跑。
   跑完抽一份 3M / HP 的 `s_ir_calendar_document_text.text_md` 看表格是否可讀。

## 驗證與限制

- 本機：`pytest tests/test_ir_calendar_consume.py tests/test_ir_calendar_parse_documents.py`（61 passed）。
- HTML 抽取只在合成的 EDGAR 樣式樣本上測過，尚未用真實 10-K / EX-99 檔驗證。
- `.htm` 重排條件是「最新一列不是 `html_text` 解的」，若 `ai_parse_document` 曾對某些 `.htm` 成功，那筆會被 `html_text` 結果取代。
