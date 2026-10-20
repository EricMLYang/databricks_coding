# ir_calendar_build_supplier_report

- 用途：對 `ir_calendar_parse_documents` 解析完的供應商財報 / 法說文件，依採購端模板產出一家公司一期的「財報＋法說整合報告」完整 HTML：
  給 AUO 採購主管的結論 → 財報資訊（KPI、財報重點、實績表、事業群、五年 / 五季營收 × OPM 圖、十項指標單欄圖、五年指標表）→ 法說會資訊（七章節、War Room、Watchlist）→ 資料來源與限制。
- 輸入（silver）：`s_ir_calendar_document_text`、`s_ir_calendar_document_file`、`s_ir_calendar_financials`、`s_ir_calendar_summary`、`s_ir_calendar_company`、`s_ir_calendar_conference`
- 輸出：
  - bronze `b_ir_calendar_supplier_report_llm`：每次 LLM 呼叫一列（原始回應），append-only
  - gold `g_ir_calendar_supplier_report`：一家公司一期一列（`html`、`llm_json`、燈號、版本），MERGE
  - Volume `<volume_root>/ir_calendar/reports/<分類小寫>/<公司代稱>/<代稱>_<期別>_supplier_report.html`
- 參數（widgets）：`catalog`、`schema`、`domain`、`volume_root`、`categories`（預設 `SUPPLIER`）、`company_keys`、`periods`、`max_reports`、`max_doc_chars`、`max_total_chars`、`model`、`prompt_version`、`concurrency`、`force_rebuild`、`render_only`、`dry_run`、`fail_on_error`、`job_run_id`
- 排程：接在 `ir_calendar_parse_documents` 之後（同 job 下一個 task）或每天一次；job cluster。`max_reports` 是費用閘門。
- 負責人 / 更新日期：（填）/ 2026-10-20

數字政策：表格與圖表只用 `s_ir_calendar_financials`，LLM 只寫文字並標來源；缺值「未取得」、文件沒提「未提及」，沒有示意值模式。
速動比、應收天數、應付天數目前無來源 → 「未取得」（`template/USER_GUIDE.md` §3）。圖表是純 Python inline SVG，離線可開、可列印。

LLM：Azure Foundry `claude-sonnet-5`，secret `llm-api-keys/ms-foundry`（同 `meeting_record` / `sales_report_mail`）。

- 模板與使用者說明：`template/20261010_供應鏈供應商財務體質報告模板.html`、`template/USER_GUIDE.md`
- 流程、參數說明、維護者須知、首次上線順序：notebook 第一個 markdown cell
- 表由 `ir_calendar_init_tables` [c19a] / [c19b] 建
- 本機測試：`py -3.10 -m pytest tests/test_ir_calendar_build_supplier_report.py`（載入 [c02]～[c07]：facts、工作清單、prompt 解析、SVG 標籤不重疊、HTML 章節順序）
