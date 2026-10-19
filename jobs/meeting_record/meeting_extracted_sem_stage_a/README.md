# meeting_extracted_sem_stage_a

方向 C（規格 §8.3 / `_prompt_weekly_extract.md` v1.1）Stage A 的 Databricks 版：把中立層條目判成 `semantic` / `intel` / `event`，寫鏡頭表。決定見 `../meeting_extracted_migration/STATUS.md` D30 與 §6.5。

- 輸入：`v_meeting_items_sem_cand`（003；中立層有效條目 ＋ SQL 先驗 `category_rule` / `rule_basis` ＋ 同文重複 `dup_key` ＋ 鏡頭表已判狀態）
- 輸出：`g_meeting_items_sem_{unit}`（003）。MERGE on `item_key`；**不碰** `verified` / `review_note` / `sem_id` / `dup_of`。
- 參數（widgets）：`catalog`、`schema`、`unit`、`week`（空 = 所有未判）、`stage_a_version`（= [c04] `STAGE_A_VERSION_IN_CELL`）、`model`、`max_items`（LLM 費用閘門；0 = 不限）、`batch_size`、`concurrency`、`reclassify`、`prompt_cache`、`dry_run`
- 排程：每週一次，接在 W1 三支之後。
- 負責人 / 更新日期：（填）/ 2026-10-19

## 三路分工（D30）

| 待判列 | 怎麼判 | 費用 |
|---|---|---|
| `rule_basis = default`（約 89%） | 直接 `category = event`、`extract_note = rule:default`、`model = rule` | 0 |
| `definition` / `term_hint` / `intel_tag` | LLM 一批 `batch_size` 條：category / term / route_hint / as_of / extract_note / confidence | 第一輪約 1,650 條 ≈ 85 次呼叫 < USD 5 |
| `dup_key` 非空（同文重複） | 複製最早那條的判定（本次判的或鏡頭表既有）；最早那條還沒判 → 等下次 | 0 |

程式說了算的部分（[c05]）：category 只能三選一；intel 的 `route_hint = background_intel:<app>`、`as_of` 不合格式就用 `event_month`；semantic 的 `route_hint` 不在 SemanticLayerPlan §1.3 投影代號表就改 `pa:semantics`；event 兩欄 NULL；term 空就拿 summary 開頭；quote / summary 逐字抄 view。

## 怎麼跑

1. 第一次（或改 prompt 後）：`dry_run = true`、`max_items = 40` → 看 [c12] 的 `llm_rule_vs_category`（先驗 vs LLM）與 20 條樣本。
2. 全量：`max_items = 0`、`dry_run = false` → 貼 [c12] log 與 [c30] 輸出。
3. 每週：預設值（`max_items` 可留 0；週量幾十條）。
4. 改 [c04] prompt → 升 `STAGE_A_VERSION_IN_CELL` 與 widget；要重判舊列用 `reclassify = true`（PM 欄不動）。

## 維護（[c21]，每次跑）

候選 view 已沒有的 key → `active = false`（不刪；view 0 列時跳過）；中立層 item_id 變了 → 刷新。PM 在表上填 `verified` / `review_note`，`v_meeting_items_sem_q` 的 `rule_disagree` 給抽審排序。

純函式測試：`tests/test_meeting_extracted_sem_stage_a.py`（[c02]～[c05]、[c07]；不打 LLM）。
