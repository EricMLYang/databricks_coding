# ir_calendar_init_tables

- 用途：一次性建立法說行事曆（ir_calendar）批次消費流程用的 Delta table：bronze 3 張 + silver 6 張。可重跑（`CREATE TABLE IF NOT EXISTS`）。
- 輸入 table：無
- 輸出 table：`{catalog}.{schema}.b_ir_calendar_{record, batch_log, document_parse}`、`s_ir_calendar_{conference, summary, document_file, company, document_text, document_element}`
- 參數（widgets）：`catalog`、`schema`、`domain`（預設 `ir_calendar`）、`recreate`（只有 `YES_DROP_ALL` 才 DROP）
- 排程：無，手動跑一次；先於 `ir_calendar_consume_batches` / `ir_calendar_parse_documents`
- 負責人 / 更新日期：（填）/ 2026-09-21

分層設計見 `docs/20260921_ir_calendar_lakehouse_design.md`；主鍵、加欄位方式見 notebook 第一個 markdown cell。
DDL 欄位與各 job 的 schema / transform 是否一致由 `tests/test_ir_calendar_consume.py`（[c10]～[c15]）、`tests/test_ir_calendar_parse_documents.py`（[c16]～[c18]）檢查。
