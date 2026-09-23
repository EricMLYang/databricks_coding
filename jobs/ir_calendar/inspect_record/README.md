# ir_calendar_inspect_record

- 用途：人工檢視一筆 `s_ir_calendar_summary`（法說彙整）與同公司同期別一份財報的 `s_ir_calendar_document_text` / `s_ir_calendar_document_element` 內容；先印原始欄位，再印可直接給 user 的整理版 markdown（[c30]）。**只讀，不寫任何東西。**
- 輸入：`s_ir_calendar_summary`、`s_ir_calendar_document_text`、`s_ir_calendar_document_element`
- 輸出：stdout
- 參數（widgets）：`catalog`、`schema`、`domain`、`company_key`（空 = 最近更新的 summary）、`period`（空 = 最新一期）、`volume_path`（空 = 同公司同期別最近解析的一份）、`doc_kind`、`text_preview_chars`、`element_limit`、`element_chars`
- 排程：不排程，人工執行（all-purpose 或 job cluster 都可以）
- 負責人 / 更新日期：（填）/ 2026-09-23

純函式測試：`tests/test_ir_calendar_inspect_record.py`（[c02]～[c03]）。
