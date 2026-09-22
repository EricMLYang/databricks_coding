# jobs/ir_calendar/

法說行事曆（ir_calendar）系列：爬蟲 VM → Volume / bronze → silver → 系統 API。
資料夾名省略 `ir_calendar_` 前綴，**Databricks 上的 job 名稱仍是各 README 標題那一個**。

| 資料夾 | Job 名稱 | 用途 | 排程 |
| --- | --- | --- | --- |
| `init_tables/` | `ir_calendar_init_tables` | 一次性建 bronze 3 張 + silver 6 張 Delta table，可重跑 | 無，手動跑一次 |
| `consume_batches/` | `ir_calendar_consume_batches` | 主流程：搬批次進 Volume / bronze、算 silver、轉送系統 API | 跟著 VM 班次 |
| `check_landing/` | `ir_calendar_check_landing` | 只讀檢查：bronze / silver / Volume 三邊對得上 | 人工 |
| `check_api_status/` | `ir_calendar_check_api_status` | 只讀檢查：系統端 status API 與送出內容對照（1 次 GET） | 人工 |
| `parse_documents/` | `ir_calendar_parse_documents` | Volume 財報檔案依分類 × 公司用 `ai_parse_document` 初步解析 → bronze `b_ir_calendar_document_parse` / silver `s_ir_calendar_document_{text, element}` | 接在 consume_batches 之後，或每天一次 |

順序：`init_tables` → `consume_batches` → `parse_documents` →（視情況）`check_landing` / `check_api_status`。

- 分層與 table 設計：`docs/20260921_ir_calendar_lakehouse_design.md`
- 純函式測試：`tests/test_ir_calendar_consume.py`、`tests/test_ir_calendar_check_api_status.py`、`tests/test_ir_calendar_parse_documents.py`
- `check_landing` / `check_api_status` 內的常數是 `consume_batches` 的副本，那邊改了這裡要一起改。
- `財報檔案處理參考/`：舊環境的解析腳本，只當參考，不部署。
