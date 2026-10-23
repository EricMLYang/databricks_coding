# meeting_extracted_w2_t4_reconcile

W2 Sales Brief 鏡頭的 T4（規格 §4.4、§5.3、§7.3）：T3 標好的相關條目 × Sales Brief 填報文字 → 對照格表。單邊程式判、兩邊都有才呼叫 L3；app 層（ALL）格彙整跨客戶訊號。決定見 `../meeting_extracted_migration/STATUS.md` D35 / D36。

- 輸入：`v_meeting_items_sb_q`（004；T3 標註 ⋈ 中立層，只取本期 `sb_relevant`）、`v_meeting_sb_brief_text`（004；填報端一格一列，含 ALL）
- 輸出：`g_meeting_sb_reconcile_{unit}`（004）。MERGE on `(app_name, brand, facet, brief_month)`；**不碰** `reviewer / review_verdict / review_relation / review_note / review_carried_from`；`created_at` 只在首次寫。
- 參數（widgets）：`catalog`、`schema`、`unit`、`brief_month`（空 = 本月）、`prompt_version`（= [c04] `PROMPT_VERSION_IN_CELL`）、`model`、`max_items_per_cell`（8）、`max_items_per_tag_other`（8）、`max_cells`（LLM 呼叫數閘門；0 = 不限）、`summary_batch`（6）、`concurrency`、`app_level`、`prompt_cache`、`dry_run`
- 排程：每月一次，T3 之後、brief 填完後。
- 負責人 / 更新日期：（填）/ 2026-10-23

## 格子與三種呼叫

| 格子 | 來源 | relation | LLM |
|---|---|---|---|
| 兩邊都有 | 會議格 ⋈ 填報格 | `corroborate` / `supplement` / `conflict`（`relation_basis = llm`） | **格子模式**：一格一次，同時產兩種摘要、rationale、evidence、number_caveat |
| 只有會議（含 `UNKNOWN` 品牌格、該期無此品牌的格） | 會議格 | `meeting_only`（`rule`） | **摘要模式**：`summary_batch` 格一次，只產兩種摘要 |
| 只有填報 | 填報格 | `sb_only`（`rule`） | 無 |
| ALL（app 層） | 各品牌格的 `meeting_summary` ＋ app_summary 原文 | 三選一；填報空 → `meeting_only` | **app 層模式**：每 app × facet 一次；`signals`（≥ 2 品牌）→ `cross_customer_note`，參與品牌格 `cross_customer_flag = true` |

`UNKNOWN` 品牌格（D36）：T3 標了 `sb_relevant` 但 `brand` NULL（客戶 NULL、app 已解）的條目，10 月佔相關條目四分之一，不丟，當一個永遠 `meeting_only` 的品牌格給 PM 看；也參與 app 層訊號。

每格送 LLM 的條目：`confidence` 降冪最多 `max_items_per_cell`；`other` 格改每個 `topic_tag_primary` 最多 `max_items_per_tag_other`（D36；TV × TCL × other 一期 65 條，照 8 條會漏整類）。沒送的只計數（`n_items` vs `n_items_sent`），`meeting_item_ids` 仍列全部（evidence 排前面）。

程式說了算（[c05]）：relation 不合法 = 該格作廢、下次再判；evidence 只留送過的 id；`meeting_summary_shareable` 含任何 S2 條目 `numbers.value` → NULL、`shareable_failed = true`；app 層 `signals` 只留 ≥ 2 個已知品牌的；email 樣式換 `<email>`。

## 怎麼跑

1. 第一次（或改 prompt 後）：`dry_run = true`、`max_cells = 12`、`brief_month = 2026-09`（兩邊都有資料）→ 看 [c12] log 與例外清單預覽（格子模式先吃預算，看 relation 判得合不合理）。
2. 全量：`max_cells = 0`、`dry_run = false` → 貼 [c12] log 與 [c30]。9 月全量估：兩邊都有的格約 15、摘要批約 5、app 層 12 → 約 30 次呼叫、USD 1 以內。
3. 每月：brief 填完 → T3 → T4（`brief_month` 留空 = 本月）。brief 沒填時跑，所有格都 `meeting_only`，只產摘要。
4. 改 [c04] prompt → 升 `PROMPT_VERSION_IN_CELL` 與 widget；重跑整期會覆寫非審核欄，PM 的審核欄留著。
5. PM 審核：直接在表上填 `review_verdict`（agree / fix_relation / drop）、`review_relation`、`review_note`；`v_meeting_sb_reconcile_q` 的 `relation_rank` / `review_pending` 給清單排序。匯出 md 的例外清單（§4.6）是 T5。

關卡（[c12]）：全部呼叫失敗或失敗過半 → 停、不寫；其餘只印（shareable 驗證失敗、摘要缺、預算跳過）。[c30]：本批格都在、版本對、鍵無重複、審核列數沒變少、llm 格都有摘要；本期上次有、這次沒產的格只印數量不刪。

純函式測試：`tests/test_meeting_extracted_w2_t4_reconcile.py`（[c02]～[c06]；不打 LLM，回覆用手寫 dict 模擬；grid 在本機 Spark 以假表實跑）。
