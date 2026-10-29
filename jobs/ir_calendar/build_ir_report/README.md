# ir_calendar_build_ir_report

- 用途：對 `ir_calendar_parse_documents` 解析完的供應商財報 / 法說文件，依採購端新版面（`template/20261021_SCM財報和法說報告html格式v20261007.html`）產出一家公司一期的「財報＋法說整合報告」完整 HTML：
  給 AUO 採購主管的結論 → 財報資訊 01–06（KPI、實績表、事業群、五年 / 五季營收 × OPM 圖、近五年 11 項指標表 + 十張單欄圖）→ 法說會資訊 01–07（六主題 + Q&A；另 08 採購觀察）→ 資料來源與限制。
- 輸入（silver）：`s_ir_calendar_document_text`、`s_ir_calendar_document_file`、`s_ir_calendar_financials`、`s_ir_calendar_summary`、`s_ir_calendar_company`、`s_ir_calendar_conference`
- 輸出：
  - bronze `b_ir_calendar_ir_report_llm`：每次 LLM 呼叫一列（原始回應），append-only
  - gold `g_ir_calendar_ir_report`：一家公司一期一視角一列，鍵 (company_key, period, report_kind)（`html`、`llm_json`、版本；`light` / `score` 自新版面起 NULL；2026-10-28 加 `source_periods` / `summary_batch_id` / `docs_fed`；2026-10-29 加 `report_kind` / `topics`），MERGE
  - Volume `<volume_root>/ir_calendar/reports/<分類小寫>/<公司代稱>/<代稱>_<期別>_supplier_report.html`
- 參數（widgets）：`catalog`、`schema`、`domain`、`volume_root`、`views`（預設 `supplier`；`supplier` / `peer` / `semi`）、`company_keys`、`periods`、`lookback_quarters`（`0`）、`max_reports`、`max_doc_chars`、`max_total_chars`、`model`、`concurrency`、`force_rebuild`、`render_only`、`dry_run`、`fail_on_error`、`job_run_id`
- 排程：接在 `ir_calendar_parse_documents` 之後（同 job 下一個 task）或每天一次；job cluster。`max_reports` 是費用閘門。
- 負責人 / 更新日期：（填）/ 2026-10-29

數字政策：表格與圖表只用 `s_ir_calendar_financials`，LLM 只寫文字並標來源；缺值「未取得」、文件沒提「未提及」，沒有示意值模式。
來源範圍（2026-10-29 定案）：**只用當季內容、最新一季為準**。期別候選 = 文件或爬蟲彙整任一有當季資料的期別（`periods` 空 = 每家最新一期）；當季只有彙整、沒有文件也產；彙整只用同期不退用前期；
文件跨期補位 `lookback_quarters` 預設 `0`（開啟時補位文件標期別、不讓期別前進）。每份文件在 prompt / 報告來源節 / gold 標期別與餵 LLM 狀態（全文 / 截尾 / 因長度略過）。
重跑：`docs_digest` = 文件 sha256 + 彙整批次 + 場次 revision，多了新來源就重做、沒變就跳過，直到下一季出現新來源。
報告視角（2026-10-29）：`supplier`（採購）/ `peer`（面板同業，友達為主體）/ `semi`（半導體，友達跨入先進封裝 / 光通訊）；公司 → 視角由 [c02] `company_views`（分類預設 + `VIEW_OVERRIDES`）決定，一家可多視角、一視角一份報告；supplier 用 v1 版面（財報 01–06 + 法說 01–07）；**peer / semi 用 v2 版面**（2026-10-29 改版）：[c02] 規則常數（同業組 / 計分卡 / 重疊 / 威脅等級；題目關鍵字 / 產業參考帶 / 持續性 / 雷達環）→ [c03a] 對照與持續性 facts → [c05a] 各自的 LLM JSON（`PEER_SCHEMA` / `SEMI_SCHEMA`）→ [c06a] 多線 / 散點 / 柱 → [c07a] 同業競爭對照 10 節、新事業產業雷達 9 節。版面稿 `template/20261029_同業競爭對照_v2_示意.html`、`template/20261029_新事業產業雷達_v2_示意.html`；構想與外部範本依據 `docs/20261029_ir_calendar_report_views_peer_semi_proposal.md` §7–§8。
法說七節與事業群表先用爬蟲 summary 的結構化欄位（`management_views` 六主題、`business_segments`、`qa_highlights`，2026-10-21 爬蟲新版），缺的才由 LLM 讀文件補位。
速動比、應收天數、應付天數、母公司淨利率來自 `s_financials` 的 2026-10-21 新欄（`quick_ratio / dso_days / dpo_days / net_margin_parent`），舊批次為「未取得」。圖表是純 Python inline SVG，離線可開、可列印。

LLM：Azure Foundry `claude-sonnet-5`，secret `llm-api-keys/ms-foundry`（同 `meeting_record` / `sales_report_mail`）。

- 模板與使用者說明：`template/20261021_SCM財報和法說報告html格式v20261007.html`、`template/USER_GUIDE.md`（舊版面 `template/20261010_…html` 只留對照）
- 流程、參數說明、維護者須知、首次上線順序：notebook 第一個 markdown cell
- 表由 `ir_calendar_init_tables` [c19a] / [c19b] 建；`s_financials` / `s_summary` 的新欄由 [c21] `ADD COLUMNS` 補
- 五家範例公司的純 Python 版產出（同版面、無 LLM）與覆蓋度評估：`../範例財報/`
- 本機測試：`py -3.10 -m pytest tests/test_ir_calendar_build_ir_report.py`（載入 [c02]～[c07]：facts、工作清單（當季為準 / 只有彙整也產 / 補位預設關 / 來源雜湊 / 視角）、v2 對照與持續性 facts、v2 prompt / normalize、v2 圖與版面、prompt 解析、文件餵入狀態、SVG 標籤不重疊、HTML 章節順序、彙整 / LLM 合併規則、gold DDL ↔ schema）
