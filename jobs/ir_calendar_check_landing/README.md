# ir_calendar_check_landing

- 用途：`ir_calendar_consume_batches` 在 `api_base_url` 留空跑完之後，驗證 bronze / silver / Volume 三邊對得上，再決定要不要補送系統 API。**只讀，不寫任何東西。**
- 輸入：`b_ir_calendar_batch_log`、`b_ir_calendar_record`、`s_ir_calendar_{company, conference, summary, document_file}`、Volume `<volume_root>`
- 輸出：stdout 的 PASS / FAIL / INFO 清單（[c20] 彙總）
- 參數（widgets）：`catalog`、`schema`、`domain`、`volume_root`、`batch_id`（空 = 最新一批）、`sample_rows`、`file_check_limit`、`verify_sha256`
- 排程：不排程，人工執行
- 負責人 / 更新日期：（填）/ 2026-09-21

檢查項目表、補送 API 的步驟見 notebook 第一個 markdown cell。
常數（`LAYER_PREFIX`、`CATEGORY_DIRS`、`SILVER_KEYS`）是 `ir_calendar_consume_batches` [c02] / [c04] 的副本：那邊改了這裡要一起改。
