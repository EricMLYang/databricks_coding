# ir_calendar_build_supplier_report

- 用途：對 `ir_calendar_parse_documents` 解析完的供應商財報 / 法說文件，依採購端新版面（`template/20261021_SCM財報和法說報告html格式v20261007.html`）產出一家公司一期的「財報＋法說整合報告」完整 HTML：
  給 AUO 採購主管的結論 → 財報資訊 01–06（KPI、實績表、事業群、五年 / 五季營收 × OPM 圖、近五年 11 項指標表 + 十張單欄圖）→ 法說會資訊 01–07（六主題 + Q&A；另 08 採購觀察）→ 資料來源與限制。
- 輸入（silver）：`s_ir_calendar_document_text`、`s_ir_calendar_document_file`、`s_ir_calendar_financials`、`s_ir_calendar_summary`、`s_ir_calendar_company`、`s_ir_calendar_conference`
- 輸出：
  - bronze `b_ir_calendar_supplier_report_llm`：每次 LLM 呼叫一列（原始回應），append-only
  - gold `g_ir_calendar_supplier_report`：一家公司一期一列（`html`、`llm_json`、版本；`light` / `score` 自新版面起 NULL；2026-10-28 加 `source_periods` / `summary_batch_id` / `docs_fed`），MERGE
  - Volume `<volume_root>/ir_calendar/reports/<分類小寫>/<公司代稱>/<代稱>_<期別>_supplier_report.html`
- 參數（widgets）：`catalog`、`schema`、`domain`、`volume_root`、`categories`（預設 `SUPPLIER`）、`company_keys`、`periods`、`lookback_quarters`（`2`）、`max_reports`、`max_doc_chars`、`max_total_chars`、`model`、`prompt_version`（`2.1`）、`concurrency`、`force_rebuild`、`render_only`、`dry_run`、`fail_on_error`、`job_run_id`
- 排程：接在 `ir_calendar_parse_documents` 之後（同 job 下一個 task）或每天一次；job cluster。`max_reports` 是費用閘門。
- 負責人 / 更新日期：（填）/ 2026-10-28

數字政策：表格與圖表只用 `s_ir_calendar_financials`，LLM 只寫文字並標來源；缺值「未取得」、文件沒提「未提及」，沒有示意值模式。
來源完整性（2026-10-28）：本期缺財報本體 / 缺法說類文件時往前最多 `lookback_quarters` 期補同類文件；彙整同期優先、否則最近的前一期；每份文件在 prompt / 報告來源節 / gold 標期別與餵 LLM 狀態（全文 / 截尾 / 因長度略過）；
`docs_digest` 含文件 sha256 + 彙整批次 + 場次 revision，任一變了自動重做。
來源完整性（2026-10-28）：本期缺財報本體 / 缺法說類文件時往前最多 `lookback_quarters` 期補同類文件；彙整同期優先、否則最近的前一期；每份文件在 prompt / 報告來源節 / gold 標期別與餵 LLM 狀態（全文 / 截尾 / 因長度略過）；
`docs_digest` 含文件 sha256 + 彙整批次 + 場次 revision，任一變了自動重做。
法說七節與事業群表先用爬蟲 summary 的結構化欄位（`management_views` 六主題、`business_segments`、`qa_highlights`，2026-10-21 爬蟲新版），缺的才由 LLM 讀文件補位。
速動比、應收天數、應付天數、母公司淨利率來自 `s_financials` 的 2026-10-21 新欄（`quick_ratio / dso_days / dpo_days / net_margin_parent`），舊批次為「未取得」。圖表是純 Python inline SVG，離線可開、可列印。

LLM：Azure Foundry `claude-sonnet-5`，secret `llm-api-keys/ms-foundry`（同 `meeting_record` / `sales_report_mail`）。

- 模板與使用者說明：`template/20261021_SCM財報和法說報告html格式v20261007.html`、`template/USER_GUIDE.md`（舊版面 `template/20261010_…html` 只留對照）
- 流程、參數說明、維護者須知、首次上線順序：notebook 第一個 markdown cell
- 表由 `ir_calendar_init_tables` [c19a] / [c19b] 建；`s_financials` / `s_summary` 的新欄由 [c21] `ADD COLUMNS` 補
- 五家範例公司的純 Python 版產出（同版面、無 LLM）與覆蓋度評估：`../範例財報/`
- 本機測試：`py -3.10 -m pytest tests/test_ir_calendar_build_supplier_report.py`（載入 [c02]～[c07]：facts、工作清單（跨期補位 / 彙整退用 / 來源雜湊）、prompt 解析、文件餵入狀態、SVG 標籤不重疊、HTML 章節順序、彙整 / LLM 合併規則、gold DDL ↔ schema）
