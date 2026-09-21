# ir_calendar_consume_batches

- 用途：把爬蟲 VM 發布在內網目錄的批次搬進 Databricks：實體檔案落 Volume、每個檔案原樣進 bronze、從 bronze 算出 silver、`api/*.json` 轉送系統 API。取代舊的 `01_DELL_get_finance_report_file`。
- 輸入：內網 HTTPS 目錄 `<root_url>`（`health.json`、`batches/`），只用 GET
- 輸出：
  - Volume `<volume_root>/<分類目錄>/<公司代稱>/<檔名>`、`<volume_root>/ir_calendar/{batches/<批次>/, _cursor.json}`
  - bronze `b_ir_calendar_record`（append-only）、`b_ir_calendar_batch_log`
  - silver `s_ir_calendar_{conference, summary, document_file, company}`（MERGE；`rebuild_silver = true` 可整表重算）
  - 系統 API `<api_base_url>/companies/sync`、`<api_base_url>/ir-conferences/sync`
- 參數（widgets）：`catalog`、`schema`、`domain`、`root_url`、`volume_root`、`api_base_url`、`api_key_secret`、`verify_ssl`、`dry_run`、`write_tables`、`rebuild_silver`、`max_batches`、`health_max_age_hours`、`job_run_id`
- 排程：跟著 VM 班次（08:10 / 17:10 掃描、09:40 / 18:40 抓檔之後各一次），或每小時；job cluster
- 負責人 / 更新日期：（填）/ 2026-09-21

流程、參數說明、維護者須知、首次上線順序見 notebook 第一個 markdown cell；分層設計見 `docs/20260921_ir_calendar_lakehouse_design.md`。
來源程式：`PM_Head/projects/MI_Crawler/ir_calendar/deploy/databricks/consume_batches.py`（本 notebook 為其 job 版，另加 bronze / silver 寫入）。
本機測試：`pytest tests/test_ir_calendar_consume.py`（載入 [c02]～[c06]，用本機 pyspark 跑 silver transform）。
