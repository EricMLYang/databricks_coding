# ir_calendar_resend_api

- 用途：把已經進 Databricks、但沒 POST 到系統的批次補送出去。用與 consume 相同的 `Idempotency-Key`，效果等價。
- 輸入：`b_ir_calendar_batch_log`、Volume `<volume_root>/ir_calendar/batches/<批次>/api/*.json`（或 `b_ir_calendar_record.payload`）
- 輸出：POST `<api_base_url>/companies/sync`、`<api_base_url>/ir-conferences/sync`；回應補寫回 `b_ir_calendar_batch_log.api_results`
- 不動 Volume、bronze、silver、`_cursor.json`
- 參數（widgets）：`catalog`、`schema`、`domain`、`volume_root`、`api_base_url`、`api_key_secret`、`verify_ssl`、`batch_ids`、`payload_source`、`dry_run`（預設 true）、`force`、`update_batch_log`、`job_run_id`
- 排程：不排程，人工執行
- 負責人 / 更新日期：（填）/ 2026-09-21

**來源 VM 上批次還在的話，優先倒 `_cursor.json` 重跑 `ir_calendar_consume_batches`** — 那是設計好的路徑，遙測與流程都完整。這支是來源已清掉、或不想重新下載整批時的替代方案。

`ENDPOINT_BY_PATH`（[c02]）與 `api_result`（[c03]）是 `ir_calendar_consume_batches` [c02] / [c05] 的副本，那邊改了這裡要一起改。
`API_RESULT_SCHEMA`（[c02]）必須與 `b_ir_calendar_batch_log.api_results` 的欄位名與順序完全一致，否則 MERGE 會失敗。
