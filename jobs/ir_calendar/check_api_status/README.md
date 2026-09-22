# ir_calendar_check_api_status

- 用途：用系統端唯一的讀取 API（`GET <api_base_url>/ir-conferences/sync/status`）確認資料真的進去了：各表筆數、最後同步時間、上一批 upsert 的 created / updated / unchanged / failed 與失敗明細；再跟 Databricks 這邊送出去的內容對照。
- 輸入：系統 API status 端點、`b_ir_calendar_batch_log`、`s_ir_calendar_{company, conference}`、Volume `<volume_root>/ir_calendar/batches/<批次>/api/*.json`
- 輸出：stdout 的 PASS / FAIL / INFO 清單（[c20] 彙總）。**不寫任何表、不寫 Volume、不動游標**
- 參數（widgets）：`catalog`、`schema`、`domain`、`volume_root`、`api_base_url`、`api_key_secret`、`status_path`、`verify_ssl`、`api_time_zone`、`timeout_seconds`、`stale_hours`、`force_refresh`、`api_fiscal_period`、`recent_batches`、`sample_rows`
- 排程：不排程，人工執行
- 負責人 / 更新日期：（填）/ 2026-09-22

**對面是 prod**：整份 notebook 只發 **1 次 GET**（[c04] 把回應快取在 `_STATUS_CACHE`，後面的 cell 重跑不會再打）；要再打一次得把 `force_refresh` 切 `true`。路徑必須以 `status` 結尾，寫入端點被 assert 擋掉，逾時 `timeout_seconds` 就放棄且**不重試**。其餘檢查都在 Databricks 端（小表 count / limit、Volume 讀檔）。

「塞了幾筆」分三種：送出去的列數（[c12] `rows`、[c13] `rows=N`）、系統真的收下的（[c11] `created / updated / unchanged`，API 只記得上一批）、系統現在總共幾筆（[c10] `rowCount`，含管理頁手動新增）。歷次累計由 [c12a] 從整張 `b_ir_calendar_batch_log.api_results` 算出來，不碰系統。
要精確知道「系統裡有幾列是 Databricks 建立的」，API 查不到，請系統端直接下：
`SELECT count(*) FROM app_ir_conference WHERE created_by = 'SVC_DATABRICKS';`（公司表同理換表名）。

系統端沒有逐列查詢的 API（規格只開 3 支），所以「塞了哪些值」看得到的是表層統計與上一批結果；列的內容看 [c13]（Volume 上我們實際送出的 body）。`rowCount` 可能大於我們送的筆數（管理頁手動新增、軟刪除仍計入），故 [c12] 只在 `rowCount <` 本地期望值時判 FAIL。

實測系統的 envelope 把資料放在 `info`（規格寫 `data`，`[c03] PAYLOAD_KEYS` 兩種都收），且 `lastUpdatedAt` / `executedAt` 不帶時區、是**台北時間**（規格 §6 寫 UTC）——`api_time_zone` 預設 `taipei`。

`api_fiscal_period` 預設 `as_is`（照爬蟲原值送，例 `2026Q2`），要跟 `ir_calendar_consume_batches` 那次執行填一樣的模式，[c12] 的期望列數才對得上。`fiscal_period_for_api`（[c03]）是 consume [c03] 的副本，那邊改了這裡要一起改。
`status_path` 預設是定版規格的 `ir-conferences/sync/status`；規格文末原始版本寫 `ir/sync/status`，系統端若用後者改 widget 即可。

本機測試：`pytest tests/test_ir_calendar_check_api_status.py`（載入 [c02]、[c03]，並與 consume 的 `fiscal_period_for_api` 比對）。
