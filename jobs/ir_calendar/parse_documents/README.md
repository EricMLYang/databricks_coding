# ir_calendar_parse_documents

- 用途：把 `ir_calendar_consume_batches` 落到 Volume 的財報檔案（PDF / HTM），依**公司分類 × 公司**逐檔用 Databricks `ai_parse_document` 做初步解析，原始結果進 bronze、整理成全文與元素表進 silver，供後續進階處理（`ai_query` 摘要、表格抽取、RAG）或人工查閱。取代參考腳本 `財報檔案處理參考/job_25_all_parse_content_new.py`（一種文件類型一張表 + meta 表旗標）。
- 輸入：`s_ir_calendar_document_file`（Volume 檔案索引：分類、公司、`doc_kind`、`sha256`）、Volume 實體檔案。不掃目錄、不拆檔名。
- 輸出：
  - bronze `b_ir_calendar_document_parse`：一檔一版（`volume_path, sha256`）一列，`payload` = `ai_parse_document` JSON 全文 + status / 頁數 / 元素數
  - silver `s_ir_calendar_document_text`（一檔一列，全文 markdown）、`s_ir_calendar_document_element`（一元素一列）
  - 分類與公司都是欄位：新分類不用改表、不用改 code
- 參數（widgets）：`catalog`、`schema`、`domain`、`categories`、`company_keys`、`doc_kinds`、`max_files`、`chunk_size`、`max_retries`、`pause_seconds`、`max_attempts`、`force_reparse`、`rebuild_silver`、`dry_run`、`fail_on_error`、`job_run_id`
- 排程：接在 `ir_calendar_consume_batches` 之後（同 job 下一個 task 或每天一次）；job cluster。`ai_parse_document` 按頁計費，`max_files` 是費用閘門；財報本體只解前 30 頁（[c02] `PAGE_RANGE_BY_DOC_KIND`，2026-10-28）。
- 負責人 / 更新日期：（填）/ 2026-09-22

`.htm` / `.html` 不送 `ai_parse_document`（不支援 HTML），改由 [c03a] 純 Python 抽文字，`parser = html_text`、不計費（2026-10-11，同上交代文件 §3.2）。

流程、參數說明、維護者須知、首次上線順序見 notebook 第一個 markdown cell；表設計見 `docs/20260921_ir_calendar_lakehouse_design.md` 第 8 節。
表由 `ir_calendar_init_tables` [c16]～[c18] 建。
本機測試：`pytest tests/test_ir_calendar_parse_documents.py`（載入 [c02]～[c06] 與 [c03a]，用假的 `ai_parse_document` JSON 與 EDGAR 樣式 HTML 跑 transform）。
