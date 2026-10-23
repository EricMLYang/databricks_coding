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

## prompt 版本

- 0.1（2026-10-23）：第一版。2026-09 dry_run 12 格：supplement 8 / corroborate 1 / conflict 3、shareable_failed 1、USD 0.12。
- 0.2（2026-10-23）：看 0.1 結果後改三處。(1) conflict 加「同一主體、同一口徑」限制：機種不同（85 吋 vs 55 吋）、範圍不同（客戶整體 vs 單一業務）、主體不明或只有一條條目 → supplement 並在 rationale 寫差在哪（0.1 把 TV × TCL × price、NB × Acer × market_outlook 判成 conflict）。(2) 摘要裡的人改寫「客戶方 / AUO 方 / 與會者」（照 speaker_side），不再出現 `<Pnn>` token；無關條目直接略過、不評論相關不相關。(3) 外送版加 S2 自我核對清單（0.1 有 1 格洩數字被 [c05] 置 NULL）。
  同次修 [c11]：ALL 格只在該 app × facet 完全沒有會議格時才寫 `sb_only`；有會議格但預算沒跑到摘要的 ALL 格留到下次（原本會被誤寫成 `sb_only`），[c12] `app_mode.deferred_no_summary` 印數量。
- 0.3（2026-10-23）：看 0.2 的 9 月全量（34 次呼叫、USD 0.33）與 10 月（16 次、USD 0.20）後補三個救援。(1) **shareable 失敗 repair**：[c05] 驗證失敗的格，[c11] 帶著格內全部 S2 `numbers.value` 清單再請 LLM 只重寫外送版一次（[c04] `build_shareable_repair_prompt`），仍失敗才 NULL；9 月 2 格、10 月 1 格原本直接 NULL。(2) **relation 空重問**：格子 / app 層回 relation 空或不合法，附 `RELATION_RETRY_NOTE` 重問一次（9 月 NB × ALL × price 回空字串被作廢）。(3) **摘要批截斷拆單格**：[c07] `T4_MAX_TOKENS` 4000 → 8000，摘要批仍 `max_tokens` 截斷時拆成單格各送（10 月一批 6 格截斷 → 10 列沒摘要）。另 [c04] 格子標頭加「填報送出日約 window_end」（0.2 的 Dell 格 rationale 把 8/27 會議當成比 9 月填報新）。[c12] 多印 `shareable_repaired`（救回 / 嘗試）、`relation_retries`、`summary_batches_split`。repair / 重問的呼叫計費用、不吃 `max_cells`。
- 0.4（2026-10-23）：0.3 兩期的 shareable repair 都救不回（0 / 1），查出是 [c03] 驗證用子字串比對：TV × TCL × other 的 S2 數值有「10」「15」「20」「27」，撞到「10月」「T550QVN10.F」「2026」這類正常字，LLM 怎麼改寫都過不了。改成**值＋單位、有數字邊界**（`_number_pattern`：「10K」「US$7」「400 dppm」算洩漏；「10月」「QVN10.F」「2010」不算；沒單位的值要前後都不是數字），repair prompt 列的也是「值＋單位」。另 (a) 填報段標頭寫「{期} 期，送出日約 {window_end}，比下面每一條會議條目都新」（0.3 只寫在格子標頭，Dell 格 rationale 仍把 8/27 會議當較新）；(b) app 層 LLM 回空摘要時（10 月 3 個填報空的 ALL 格）[c05] 用各品牌格摘要拼「品牌：摘要；…」當 fallback，外送版只在每個品牌格都有外送版時才拼，[c12] `app_mode.summary_fallback` 印數量。

純函式測試：`tests/test_meeting_extracted_w2_t4_reconcile.py`（[c02]～[c06]；不打 LLM，回覆用手寫 dict 模擬；grid 在本機 Spark 以假表實跑）。
