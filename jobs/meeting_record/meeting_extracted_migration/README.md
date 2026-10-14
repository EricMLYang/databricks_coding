# meeting_extracted_migration

會議紀錄萃取（PM_Head `metting_record/01_meeting_to_sales_brief_進階規劃.md` v0.4.1 §2.3）的一次性 migration。每支 notebook 以流水號命名，**不得由 W1 / W2 呼叫**；重跑必須冪等（`CREATE TABLE IF NOT EXISTS` ＋ MERGE）。每次正式執行寫一列 `b_meeting_migration_log`。

所有 migration 都**自帶資料、不讀外部檔案**，整支 notebook 複製貼上到 Databricks 即可執行。

| 流水號 | 內容 | 重跑時機 |
|---|---|---|
| `001_semantic_entity` | 建 `s_semantic_entity`、`s_semantic_entity_alias`；從 [c05] 內嵌種子 MERGE | 改 [c05] 後重跑（預設 `dry_run = true` 先看差異） |

## 001_semantic_entity

- 輸入：[c05] `seed_data` 的 `ENTITY_SEED` / `ALIAS_SEED`（CSV 格式字串，正本，隨 notebook 進 git）
- 輸出：`{catalog}.{schema}.s_semantic_entity`（鍵 `entity_id`）、`s_semantic_entity_alias`（鍵 `(alias_type, alias_norm)`）、`b_meeting_migration_log`
- 參數（widgets）：`catalog`、`schema`、`dry_run`
- 種子規則：`app_default` 以 `|` 分隔（TV / NB / MNT）；`email_domain` 小寫、以後綴比對（`auo.com` 涵蓋 `ab1.corpnet.auo.com`）；從 [c05] 拿掉的列在表中標 `is_active = false`，不刪。驗證規則見 [c03]。
- 改種子的流程：本機改 [c05] → `pytest tests/test_meeting_extracted_migration_001.py`（會驗種子合法）→ 把 [c05] 貼到 Databricks → `dry_run = true` 看差異 → `false` 執行。
- 為什麼不建 `b_` 層：幾十列人工維護資料，notebook 裡的種子就是原始層，git 歷史就是變更紀錄。
- 為什麼不放 `mi3_semantic`：那是 `SemanticLayerPlan.md` 預留的位置，尚未建立；之後若建，在那邊建 View 指向這兩張表即可。
- 負責人 / 更新日期：（填）/ 2026-10-14

純函式測試：`tests/test_meeting_extracted_migration_001.py`（[c02]～[c05]）。
