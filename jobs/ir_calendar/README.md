# jobs/ir_calendar/

法說行事曆（ir_calendar）系列：爬蟲 VM → Volume / bronze → silver → 系統 API。
資料夾名省略 `ir_calendar_` 前綴，**Databricks 上的 job 名稱仍是各 README 標題那一個**。

| 資料夾 | Job 名稱 | 用途 | 排程 |
| --- | --- | --- | --- |
| `init_tables/` | `ir_calendar_init_tables` | 一次性建 bronze 3 張 + silver 7 張 Delta table，可重跑 | 無，手動跑一次 |
| `consume_batches/` | `ir_calendar_consume_batches` | 主流程：搬批次進 Volume / bronze、算 silver、轉送系統 API | 跟著 VM 班次 |
| `check_landing/` | `ir_calendar_check_landing` | 只讀檢查：bronze / silver / Volume 三邊對得上 | 人工 |
| `check_api_status/` | `ir_calendar_check_api_status` | 只讀檢查：系統端 status API 與送出內容對照（1 次 GET） | 人工 |
| `parse_documents/` | `ir_calendar_parse_documents` | Volume 財報檔案依分類 × 公司用 `ai_parse_document` 初步解析 → bronze `b_ir_calendar_document_parse` / silver `s_ir_calendar_document_{text, element}` | 接在 consume_batches 之後，或每天一次 |
| `inspect_record/` | `ir_calendar_inspect_record` | 只讀檢視：一筆 summary + 一份文件的 text / element 內容，並印出給 user 的整理版 | 人工 |
| `build_supplier_report/` | `ir_calendar_build_supplier_report` | 供應商「財報＋法說整合報告」（新版面 20261021）：`s_document_text` + `s_financials` + `s_summary` 結構化欄位 → LLM 寫結論與補位、程式畫 SVG 圖 → gold `g_ir_calendar_supplier_report` + Volume HTML；模板與使用者說明在 `template/`，純 Python 範例在 `範例財報/` | 接在 parse_documents 之後，或每天一次 |

順序：`init_tables` → `consume_batches` → `parse_documents` → `build_supplier_report` →（視情況）`check_landing` / `check_api_status`。

- **接續點 / Databricks 上各 cell 貼到哪一版 / 告警現況：`HANDOFF.md`**（每次改完 Databricks 更新）；待辦：`backlog.md`
- 分層與 table 設計：`docs/20260921_ir_calendar_lakehouse_design.md`
- 2026-10-11 對應爬蟲端變更（告警分級、`.htm` 抽文字、彙整五欄、財報數據 silver）與 Databricks 複製清單：`docs/20261011_ir_calendar_crawler_change_updates.md`
- 純函式測試：`tests/test_ir_calendar_consume.py`、`tests/test_ir_calendar_check_api_status.py`、`tests/test_ir_calendar_parse_documents.py`
- `check_landing` / `check_api_status` 內的常數是 `consume_batches` 的副本，那邊改了這裡要一起改。
- `財報檔案處理參考/`：舊環境的解析腳本，只當參考，不部署。
