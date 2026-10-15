# jobs/ir_calendar backlog

對應爬蟲端 MI_Crawler `main` 2026-10-15 的兩個 commit（`087ee34` 新增 SEMI 分類 14 家、`706f3b7` SK hynix 簡報來源）。
來源文件：MI_Crawler `ir_calendar/doc/20261015_給Databricks_notebook與後端開發者_新增SEMI分類交代.md`、`doc/20261015_新增半導體類公司與切回Kiro_規劃.md`。
2026-10-15 已逐支 notebook 對照過，下面只列**要動 job 的**；沒列的（`init_tables`、`parse_documents`、`inspect_record`、`check_api_status`）確認不用改。

## A. 必做：新分類 `SEMI`（半導體）→ Volume 目錄 `semiconductor/`

**2026-10-15 已改（本機，尚未貼到 Databricks）**：A1 `consume_batches` [c02]、A2 `check_landing` [c02]、A3 測試（`pytest tests/test_ir_calendar_consume.py` 全綠）。Databricks 上要重新複製的只有這兩個 [c02]。

爬蟲主檔 179 → 193 家，新增 14 家全部 `category = "SEMI"`（NVIDIA、AMD、Broadcom、Intel、Micron、Marvell、Coherent、Amkor、日月光投控、力成、欣興、南亞科、SK hynix、中際旭創）。既有三類與 179 家分類值不變。

| # | notebook | cell | 改什麼 | 不改的後果 |
| --- | --- | --- | --- | --- |
| A1 | `consume_batches` | [c02] `CATEGORY_DIR` | 加 `"SEMI": "semiconductor"` | 14 家的檔案落 `<volume_root>/uncategorized/<代稱>/`，`s_ir_calendar_document_file.volume_path` 也記成那個路徑 |
| A2 | `check_landing` | [c02] `CATEGORY_DIRS` | 加 `"semiconductor"` | [c16]「沒有檔案掉進 uncategorized」判 FAIL；分類目錄統計少一行 |
| A3 | `tests/test_ir_calendar_consume.py` | `volume_target` 測試 | 補一組 `category="SEMI"` → `semiconductor/` | 無守門 |

- `check_api_status` 沒有分類常數，**不用改**（爬蟲端交代文件原本寫要改，已更正）。
- `init_tables` 不用重跑：五張 silver 的 `category` / `category_name` 都是 STRING，DDL 註解已寫「新分類直接進來」。
- `parse_documents` 不用改：分類與公司取 `s_document_file` 欄位，不掃目錄。
- 若 A1 來不及在爬蟲端 VM 上版前改好，已落到 `uncategorized/` 的檔案要手動搬到 `semiconductor/`，並更新 `s_ir_calendar_document_file.volume_path`（或對那幾筆 `rebuild_silver`）。

**順序**：A1／A2 要在爬蟲端 VM 第一次發出帶 SEMI 的批次之前改好。系統後端 2026-10-15 回覆分類可任意新增、不需事先建列，所以主檔批次不用等後端；第一批送出後跑 `check_api_status` 看 [c11] `lastCompaniesBatch` 的 14 筆是 `created` 不是 `failed` 即可。

## B. 建議：法說漏抓目前兩端都不會通知

**2026-10-15 決定**：B2 維持 WARN（不改 [c03]），已在 `tests/test_ir_calendar_consume.py` alert 分級表加一列釘住「`法說漏抓` 前綴 = WARN」；要升 FATAL 時改 [c03] `alert_level` 與那一列。B3 未做：`health.json` 的 `window_not_found` 項目格式 repo 內查不到，且 `check_landing` 沒有 `root_url` 參數讀不到 `health.json`，等 B1 定案再說。

現況：爬蟲端視窗過了找不到日期 → entry 轉 `NOT_FOUND`，只寫進 `health.json` 的 `window_not_found`，**不進 `alerts`**；job 端 [c03] `crawler_alerts` 只讀 `alerts`，六支 notebook 都沒有碰 `window_not_found`。所以一家公司該開法說卻沒抓到，job 不會紅燈、告警區塊也不會印。財報漏抓（`實體檔案放棄`）反而有 WARN，兩者不對稱。

分兩步，job 端的改動很小：

| # | 誰 | 改什麼 | 說明 |
| --- | --- | --- | --- |
| B1 | 爬蟲端（MI_Crawler `outputs.write_health`） | 把「有歷年同季錨點、本季卻 NOT_FOUND」的公司寫成一則 alert，例如 `法說漏抓 3 家（歷年同季有開）：TPE:3481:2026Q3, …` | 用錨點過濾是為了排除「本來就不開」的公司，不然每季會有幾十筆噪音。job 端對不認得的訊息預設 WARN 且每次都印、寫進 `batch_log.crawler_alerts`，**B1 做完 job 不改任何一行就看得到** |
| B2 | job 端 `consume_batches` [c03] `alert_level` | 決定 `法說漏抓` 前綴要不要升 FATAL | 建議先維持 WARN 跑一季看噪音量，再決定；升 FATAL 只要在 `alert_level` 的前綴清單加一個字串，並在 `tests/test_ir_calendar_consume.py` 的 alert 分級表加一列 |
| B3（選做） | job 端 `check_landing` | 新增一個 check：讀 `health.json` 的 `window_not_found`，跟 `s_ir_calendar_conference` 歷年同季有列的公司 join，印出「歷史有、今年沒有」清單 | 等於把爬蟲端 `tools/report_gap.py` 的邏輯搬到 Databricks 用 silver 算；優點是不依賴爬蟲端的 anchor state，缺點是新公司前幾季沒有歷史，看不出來 |

## C. 備忘：這次上版不需要 job 配合、但會看到的變化

- `master/company_category.json` 變 4 列（bronze 歸檔，無 silver）。
- `master/company.json`／`api/companies_sync.json` 多 14 列，`s_ir_calendar_company` MERGE 多 14 列。`stockCode` 已驗過 193 家無跨市場重複。
- 14 個新代稱：`Nvidia`、`AMD`、`Broadcom`、`Intel`、`Micron`、`Marvell`、`Coherent`、`Amkor`、`ASE-Holding`、`Powertech`、`Unimicron`、`Nanya-Tech`、`SK-hynix`、`Innolight`。與既有 `Innolux`（群創）、`SKC` 是不同公司，不要合併目錄。
- 美股 5 家非曆年會計年度（NVIDIA／Marvell 1 月底、Broadcom 10 月底、Micron 8 月底、Coherent 6 月底）：`ir_financials` 的年度 `fiscal_year` 以期末日所在年為標籤（NVIDIA 2027-01 結束的年度 = `2027FY`），季別以期末日歸曆年季，與 Dell／HP 既有做法相同；`s_ir_calendar_financials` 不用改。
- SK hynix 法說簡報來源是 IR 站的 Azure Blob CDN，從開發機回 403，VM 上待驗證；若 VM 也 403 就不會有該公司的 Presentation 檔，只有 DART 財報（需 VM 填 `DART_API_KEY`）。
- `health.json` 沒有新欄位，告警文字沒變，[c03] 分級不受影響。
