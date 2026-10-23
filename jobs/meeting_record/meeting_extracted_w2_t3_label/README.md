# meeting_extracted_w2_t3_label

W2 Sales Brief 鏡頭的 T3（規格 §4.3、§7.1、§7.2）：中立層有效條目 → 歸期（D6 窗口）→ app / 品牌 / 四面向 / 是否進對照 → 寫標註表。全規則、無 LLM（Phase 1 不做 L2 fallback）。決定見 `../meeting_extracted_migration/STATUS.md` D6 / D9 / D35。

- 輸入：`g_meeting_items_bu`（002）、`s_semantic_entity` / `s_semantic_entity_alias`（001：`app_default`、`sb_brand`）、`s_meeting_sb_facet_map`（004 種子）、`v_meeting_sb_period`（004：品牌清單、`submitted_end`）
- 輸出：`g_meeting_items_sb_{unit}`（004）。MERGE on `(item_key, app_name)`；本期不在名單的舊列 `active = false`。
- 參數（widgets）：`catalog`、`schema`、`unit`、`brief_month`（空 = 本月）、`window_mode`（`submitted_at` / `calendar` / `fixed_day`）、`fixed_day`（25）、`grace_days`（0）、`window_overrides`（JSON，`"APP:yyyy-MM": {"start","end"}`）、`labeler_version`（= [c02] `LABELER_RULE_VERSION_IN_CELL`）、`dry_run`
- 排程：每月一次，brief 填完後跑，接 T4。
- 負責人 / 更新日期：（填）/ 2026-10-23

## 窗口（D6）

| 模式 | 迄 | 起 |
|---|---|---|
| `submitted_at`（預設） | 該期 `v_meeting_sb_period.submitted_end` 的日期；**缺 → 退回 `fixed_day` 並印 WARN** | 上一期（可跳月）截止 + 1；上一期也缺 → 上個月 `fixed_day` + 1 |
| `fixed_day` | 每月 `fixed_day` 日 | 上一期截止 + 1（同上） |
| `calendar` | 日曆月底 | 月初（不加 grace） |

兩端再加 `grace_days`（起迄一起移，期與期不重疊）。`window_overrides` 最優先，`brief_month_basis = override`。`app_unresolved` 的列用各 app 窗口的聯集歸期（不進對照，只計數）。

實務：brief 10 月底那週才填，所以 10 月可以先用 fallback 跑一次看格子，brief 進來後再跑一次（`submitted_at` 截止點整月重標覆寫）。TV 缺 2026-07 期，8 月窗口會從 6-26 到 8-25，7 月會議對到 8 月 brief（照 D6，不丟）。

## 規則鏈（[c04]，每步一個純函式）

1. `select_items`：ok、未 superseded、本 unit、有 `event_date`、落在窗口聯集內；一個 `item_key` 留一列（item_id 最小）。
2. `expand_app`：`app ∈ {TV, NB, MNT}` → `neutral`；`ALL` / NULL → 客戶 `app_default` 展開多列（`customer_default`）；客戶 NULL 或無預設 → `app_unresolved`。
3. `assign_window`：依 `app_name` 的窗口切 `event_date`。
4. `assign_brand`：`customer` → 別名表 `sb_brand`（`sb_brand`）；`samsung` 在 TV / MNT 視同 `samsung_vd`（`samsung_vd_rule`，D9）；對不上保留 entity_id（`customer_fallback`）；客戶 NULL（`none`）。
5. `assign_brand_in_sb`：該期該 app 的 `brands` 含 `brand` 才 true；期別列還沒有 → 全 false（[c10] 印 WARN）。
6. `assign_facet`：主標籤命中 → `rule_primary`；否則主標籤的 `follow_tag` 在 tags 裡、或其餘 tag 第一個有映射 → `rule_secondary`；都沒有 → NULL / `unresolved`。
7. `assign_relevance`：依 `topic_tags` 順序逐 tag 查 `relevance_rule`，第一個命中 → `relevance_basis = rule:tag`；沒命中 → 全是 never 的 tag → `never`，否則 `no_rule`。`sb_relevant` = 命中 ∧ app 已解 ∧ facet 非空。

## 怎麼跑

1. `dry_run = true`、`brief_month = 2026-09`（兩邊都有資料的月）→ 看 [c10] 窗口、[c12] 比例與格子預覽、樣本 12 條。
2. `dry_run = false` → 貼 [c12] log 與 [c30] 輸出。
3. 每月：`brief_month` 留空（本月）或指定；brief 填完後再跑一次同一期。
4. 改 [c04] 規則 → 升 `LABELER_RULE_VERSION_IN_CELL` 與 widget；改 004 [c05] 映射 → 重跑 004 → 重跑 T3（`labeler_version` 欄的 map 版本會變）。

關卡（[c12]）只印不停：`app_unresolved` > 30%、facet 推不出 > 30% 印 WARN；0 列不寫表也不停用舊列。

純函式測試：`tests/test_meeting_extracted_w2_t3_label.py`（[c02]～[c04]；窗口用純日期算，規則鏈在本機 Spark 以假表實跑）。
