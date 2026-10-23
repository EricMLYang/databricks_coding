# meeting_extracted_migration

會議紀錄萃取（PM_Head `metting_record/01_meeting_to_sales_brief_進階規劃.md` v0.4.1 §2.3）的一次性 migration。每支 notebook 以流水號命名，**不得由 W1 / W2 呼叫**；重跑必須冪等（`CREATE TABLE IF NOT EXISTS` ＋ MERGE）。每次正式執行寫一列 `b_meeting_migration_log`。

接手先讀 [STATUS.md](STATUS.md)（決定、Phase 0 結論、進度、下一步）。

所有 migration 都**自帶資料、不讀外部檔案**，整支 notebook 複製貼上到 Databricks 即可執行。

| 流水號 | 內容 | 重跑時機 |
|---|---|---|
| `001_semantic_entity` | 建 `s_semantic_entity`、`s_semantic_entity_alias`；從 [c05] 內嵌種子 MERGE | 改 [c05] 後重跑（預設 `dry_run = true` 先看差異） |
| `002_meeting_neutral_tables` | 建中立層五張表（`s_meeting_record_mail_bu`、`s_meeting_record_clean_bu`、`s_meeting_participants_bu`、`g_meeting_items_bu`、`s_meeting_record_skipped_bu`（D34 隔離表，2026-10-23 加；既有環境重跑 002 即建））與三個 View（`v_meeting_items_q`、`v_meeting_item_models`、`v_meeting_mail_index`）；只建結構 | 改 [c05] View 後重跑；表欄位要改 → 開新流水號 `ALTER TABLE ADD COLUMNS`（例外：items 表 `s3_masked`（D26）、`customer_basis`（D33）兩欄由 task 3 [c10] 缺欄時自動補；spec 已同步） |
| `005_semantic_ledgers` | 建方向 C Stage B 的台帳：`g_semantic_record`（SEM id）、`g_semantic_record_evidence`、`g_background_intel`（INT id）＋ `v_semantic_record_q`、`v_background_intel_q`（退場候選旗標）；只建結構。004 留給 Sales Brief 鏡頭 | 改 [c05] View 後重跑；表欄位要改 → 開新流水號 |
| `003_meeting_semantic_lens` | 建語意鏡頭表 `g_meeting_items_sem_bu`（方向 C，§8.3）與兩個 View：`v_meeting_items_sem_cand`（候選規則 SQL 先算、Stage A 輸入）、`v_meeting_items_sem_q`（消費介面）；只建結構 | 改 [c05] View 後重跑；表欄位要改 → 開新流水號 |
| `004_meeting_sb_lens` | 建 W2 Sales Brief 鏡頭：標註表 `g_meeting_items_sb_bu`（§3.4）、對照格表 `g_meeting_sb_reconcile_bu`（§3.5）、面向映射種子表 `s_meeting_sb_facet_map`（§7.1 + §7.2，從 [c05] 內嵌 CSV MERGE）＋ 四個 View（`v_meeting_sb_brief_text`、`v_meeting_sb_period`、`v_meeting_items_sb_q`、`v_meeting_sb_reconcile_q`） | 改 [c05] 種子（升 `FACET_MAP_VERSION`）或 [c06] View 後重跑；表欄位要改 → 開新流水號 |

## 001_semantic_entity

- 輸入：[c05] `seed_data` 的 `ENTITY_SEED` / `ALIAS_SEED`（CSV 格式字串，正本，隨 notebook 進 git）
- 輸出：`{catalog}.{schema}.s_semantic_entity`（鍵 `entity_id`）、`s_semantic_entity_alias`（鍵 `(alias_type, alias_norm)`）、`b_meeting_migration_log`
- 參數（widgets）：`catalog`、`schema`、`dry_run`
- 種子規則：`app_default` 以 `|` 分隔（TV / NB / MNT）；`email_domain` 小寫、以後綴比對（`auo.com` 涵蓋 `ab1.corpnet.auo.com`）；從 [c05] 拿掉的列在表中標 `is_active = false`，不刪。驗證規則見 [c03]。
- 改種子的流程：本機改 [c05] → `pytest tests/test_meeting_extracted_migration_001.py`（會驗種子合法）→ 把 [c05] 貼到 Databricks → `dry_run = true` 看差異 → `false` 執行。
- 為什麼不建 `b_` 層：幾十列人工維護資料，notebook 裡的種子就是原始層，git 歷史就是變更紀錄。
- 為什麼不放 `mi3_semantic`：那是 `SemanticLayerPlan.md` 預留的位置，尚未建立；之後若建，在那邊建 View 指向這兩張表即可。
- 2026-10-15 種子決定：Samsung 拆 `samsung_vd`（Sales Brief 的 Samsung）與 `samsung`（非 VD / 分不出事業部；`samsung.com` 網域歸此）；BenQ 與 Qisda 分開；`auodplus.com` 為 `affiliate`（集團子公司，side = auo）。LG / BenQ / Qisda / Inventec 的 `app_default` 與 S-Core / Sumika 身分是推測值（note 標「推測」）。
- 2026-10-16 v3（29 公司 / 93 別名）：task 3 全量後 `customer_raw` 對不上的名單補進來，全部標「推測」待使用者更正——`AOC → tpv`；`SEHC / SEC / SAMEX / SIEL → samsung`（分不出事業部，T3 依 app 歸 VD）；Wistron / Foxconn / Amtran / Wacom 建 `customer`（ODM / SI，app 多數未定）；NVIDIA `partner`；HKC / BOE / Innolux 建新類別 `competitor`（side = third_party，`customer` 欄對不到是刻意的）。跑完 001 後，task 3 跑一輪 `dry_run = false`、`retry_failed = false` 就會由 [c21] 把既有條目的 `customer` 補對，不重萃。
- 負責人 / 更新日期：（填）/ 2026-10-16

純函式測試：`tests/test_meeting_extracted_migration_001.py`（[c02]～[c05]）。

## 002_meeting_neutral_tables

- 輸入：[c04] `table_specs`（表：欄名 / 型別 / COMMENT / 鍵 / cluster_by）、[c05] `view_specs`（View：select 清單與 body SQL）。兩者是正本。
- 輸出：規格 §3.0b / §3.1 / §3.2 / §3.3 五張表（含 D34 隔離表）＋ §3.6 三個核心 View；`b_meeting_migration_log` 也 `IF NOT EXISTS`（以防跑在新 schema）。
- 參數（widgets）：`catalog`、`schema`、`dry_run`（`true` 只驗 spec、印 DDL）。
- 加的欄（STATUS.md §4）：mail 表 `body_hash / dup_of_pk / has_headers`；clean 表 `content_hash / dup_of / display_start / display_end`；items 表 `item_key / supersedes_item_id`。[c03] `validate_specs` 強制這些欄存在，也強制任何 View 不暴露 S3 欄（姓名、email、工號、原文）。
- 五張表 `CLUSTER BY (pk_seq)`（liquid clustering；全部以 pk_seq 回溯 / MERGE，日量百封級不做 partition）。
- 冪等：表 `IF NOT EXISTS`、View `CREATE OR REPLACE`。[c30] 比對實際欄位 vs spec，缺欄印 `ALTER TABLE ADD COLUMNS` 語句並 fail，不自動執行。
- 不在本支：column mask / GRANT、分應用 View、Sales Brief 鏡頭表（§3.4 / §3.5）→ 之後的 003。
- 負責人 / 更新日期：（填）/ 2026-10-15

純函式測試：`tests/test_meeting_extracted_migration_002.py`（[c02]～[c05]；View SQL 在本機 Spark 以假資料實跑）。

## 003_meeting_semantic_lens

- 輸入：[c04] `table_specs`（`g_meeting_items_sem_bu`）、[c05] `view_specs`（兩個 View）。正本。前置：002 的表要存在（View 引用 `g_meeting_items_bu`、`s_meeting_record_clean_bu`）。
- 輸出：規格 §8.3 草案的鏡頭表（`_prompt_weekly_extract.md` v1.1 YAML items 區轉 Delta ＋ 回溯 / lineage 欄）＋ `v_meeting_items_sem_cand` ＋ `v_meeting_items_sem_q`；`b_meeting_migration_log` IF NOT EXISTS。
- 參數（widgets）：`catalog`、`schema`、`dry_run`。
- 鏡頭表**一列一個 `item_key`**：中立層重萃後 `item_id` 變、`item_key` 不變，PM 的 `verified` / `review_note` 跟著 `item_key`；Stage A MERGE 時不覆蓋這兩欄。`active = false` 表示中立層已沒有這個 key 的有效條目（quote 變了），不刪。
- 候選規則（§8.3，Stage A 的先驗）在 [c02] 常數 ＋ [c05] `category_rule` / `rule_basis`：`definition` → semantic；`terms_mentioned` 非空且 quote 含「指 / 定義 / 算法 / 口徑」→ semantic（`term_hint`）；`statement_type ∈ {opinion, fact}` 且主標籤 ∈ {demand, commercial_relation, supply_chain, capacity, **price, cost, allocation**（D30）} → intel（`intel_tag`）；其餘 event（`default`）。`weight_hint = low` 是紀要段（§8.3 紀律調整；實測 79%，只當欄位）。
- 同文重複（D30）：view 的 `dup_key` = quote 只留中英數字、小寫、≥ 20 字後相同 → 同 unit 最早（段日期、item_key）那條的 item_key；自己最早或無重複 NULL。表也有 `dup_key` 欄（Stage A 寫入）。view 另有 `sem_active` / `sem_stage_a_version` 給 Stage A 判「待判」。
- `week` = `extracted_at` 的 ISO 週（`YEAROFWEEK-Www`）；`source` = `subject_clean segment_date — speaker_side`；`tags` = topic_tags ∪ free_tags ∪ customer；`app` NULL → ALL。
- 跑完先用 STATUS §6.5 的探索 SQL 看分布，再決定 Stage A job 的 LLM 只判哪些（例：`default` 全部直接寫 event 不呼叫 LLM）。
- 負責人 / 更新日期：（填）/ 2026-10-19

純函式測試：`tests/test_meeting_extracted_migration_003.py`（[c02]～[c05]；兩個 View 在本機 Spark 以 002 / 003 spec 建的假表實跑，驗四條候選規則與派生欄）。

## 005_semantic_ledgers

- 輸入：[c04] `table_specs`（三張台帳表 ＋ log）、[c05] `view_specs`（兩個 View）。正本。不依賴其他表。
- 為什麼是表不是 md（D31）：規格的兩份 md 在 PM_Head git，Databricks 寫不進去；表當正本，md 由 Stage B 產生。
- `g_semantic_record` 一列一 SEM id（`status` / `synced_to` / `pm_note` 由 PM 維護）；`g_semantic_record_evidence` 鍵 `(sem_id, item_key)`；`g_background_intel` 一列一主題（`app` ＋ `term_norm`），`status` / `pm_note` 由 PM 維護。
- `v_background_intel_q.retire_candidate` = active 且 `as_of` 距今超過 `RETIRE_QUARTERS`（2）季；`as_of` 格式不符 → NULL 不算。
- 負責人 / 更新日期：（填）/ 2026-10-19

純函式測試：`tests/test_meeting_extracted_migration_005.py`（[c02]～[c05]；View 在本機 Spark 以假表實跑，退場判斷用相對今天的季）。

## 004_meeting_sb_lens

- 輸入：[c04] `table_specs`（三張表 ＋ log）、[c05] `seed_data`（`FACET_MAP_SEED`，CSV 格式字串）、[c06] `view_specs`（四個 View）。正本。前置：002 的 `g_meeting_items_bu` 與 Sales Brief 三張表 `g_sales_brief_brand_summary` / `g_sales_brief_app_summary` / `g_sales_brief_market_intelligence`（sales_report_mail job 的來源表）要存在；[c10] 會檢查，缺就停。T3 另外還要 001 的 `s_semantic_entity` / `_alias`（`sb_brand`、`app_default`）。
- 參數（widgets）：`catalog`、`schema`、`dry_run`（預設 `true`：驗 spec 與種子、印 DDL 與種子差異）。
- 標註表 `g_meeting_items_sb_bu` **一列一個 `(item_key, app_name)`**（規格 §3.4 寫 `item_id`；比照 003 改承接鍵，重萃後列不漂移）。中立層 `app = ALL / NULL` 的條目依客戶 `app_default` 展開成多列；推不出唯一 app 標 `app_unresolved`。`brief_month` 不是日曆月：D6 窗口，`window_start / window_end` 記在列上。中立層欄位複製一份（statement_type / topic_tags / speaker_side / event_date / summary / sensitivity / confidence）讓 T3 規則與 PM 清單不必回 join；quote / numbers / model_nos 由 `v_meeting_items_sb_q` join 回來。`active = false` 表示整月重標時這個 key 已不在名單（重萃或換期），不刪。
- 對照格表 `g_meeting_sb_reconcile_bu` 鍵 `(app_name, brand, facet, brief_month)`；`brand = ALL` 是 app 層格。`meeting_summary` 含 S2 只給 PM，`meeting_summary_shareable` 才可外送（`shareable_failed` 記驗證結果）。PM 審核欄 `reviewer / review_verdict / review_relation / review_note` T4 MERGE 不覆蓋。多了 `meeting_item_keys`、`n_items / n_items_sent`（每格最多送 8 條）。
- 面向映射種子 `s_meeting_sb_facet_map`：一列一個受控 tag（剛好 = task 3 [c02] `TOPIC_TAGS` 的 14 個，tests 會比）。`facet` NULL = 不映射；`relevance_rule` 是 §7.2 規則代號（`always` / `spec_statement` / `capacity_timeref` / `quality_request_or_customer` / `never`），T3 照代號判、不另寫 if；`follow_tag`：`schedule` 與 `product_plan` 共存時隨它映入。改種子 → 升 [c02] `FACET_MAP_VERSION` → 重跑 → T3 整月重標。
- View：`v_meeting_sb_brief_text` 把 brand_summary（品牌格）與 app_summary（ALL 格）四欄 unpivot 成一格一列（`summary_futureOutlook / techProduct / pricing / otherInfo` ↔ `market_outlook / product_tech / price / other`；空白 → NULL、`sb_source = none`；同格多列取 `create_time` 最新）；`v_meeting_sb_period` 給每 app × 期別的品牌清單與 `submitted_start / submitted_end / prev_submitted_end`（market_intelligence；D6 截止點）；`v_meeting_items_sb_q` 標註列 ⋈ 中立層（`item_still_valid` 標 item_id 已被重萃）；`v_meeting_sb_reconcile_q` 加 `relation_rank`（§4.6 順序）、`effective_relation`、`review_pending`、`is_app_level`。
- Phase 1 不做 L2 fallback：`facet_basis` 只會是 `rule_primary / rule_secondary / unresolved`。
- 負責人 / 更新日期：（填）/ 2026-10-23

純函式測試：`tests/test_meeting_extracted_migration_004.py`（[c02]～[c06]；種子驗證與詞表比對；四個 View 在本機 Spark 以 002 / 004 spec 與 Phase 0 探勘到的 Sales Brief 欄位建假表實跑）。
