# meeting_extracted_pm_pack

PM 月度審核包：給 PM **從高層看「彙整結果哪裡要改」**。印成 HTML（瀏覽器開，純閱讀、無 JS）或 markdown，使用者整段複製。只讀、不寫表；LLM 只用在 B 節的客戶摘要。

`sample.html` 是假資料的版面樣本，用瀏覽器開可以先看版面。

- 輸入：`v_meeting_sb_reconcile_q`（A 節）；`v_meeting_items_q`、`v_meeting_mail_index`、`s_meeting_record_clean_bu`、`s_meeting_record_skipped_bu`（有才讀）、`g_meeting_items_sem_bu`（只取 `item_key / dup_key`）、`s_meeting_participants_bu`（只取 token / side / company，不取姓名）（B 節）
- 輸出：`output = html`（預設）時 [c12] 先 `displayHTML` 預覽、再印整份 HTML 原始碼，使用者複製存成 `.html` 給 PM；`md` 印 markdown；`both` 兩個都印。無落地
- 參數（widgets）：`catalog`、`schema`、`unit`、`months`（yyyy-MM，逗號分隔多月；空 = 本月）、`sections`（`A,B` / `A` / `B`）、`month_basis`（B 節條目歸月：`meeting` 會議日期 / `mail` 收信日期）、`include_dups`、`include_quote`、`max_text`（A 節每格字數，預設 150）、`max_per_group`、`max_rows`、`output`；LLM：`llm_summary`（預設 true）、`max_llm_groups`（每月最多幾組，0 = 不限）、`min_items_for_llm`（條目少於此不呼叫，預設 3）、`model`、`concurrency`、`prompt_cache`
- 排程：無，手動；每月 brief 填完、T3 → T4 → T5 跑完後跑一次
- 負責人 / 更新日期：（填）/ 2026-10-28

## 三層版面

| 層 | 內容 | 來源 | 不做什麼 |
|---|---|---|---|
| 總覽卡 | 每月每 app 一行：會議條目、客戶數、客戶不明、對照格、衝突 / 補充 / 一致 / 只有會議 / 只有填報 / 待審；固定請 PM 回答的三題（[c02] `PM_QUESTIONS`） | A、B 的彙總 | — |
| A 會議 × Sales Brief 對照結果 | 每月一張卡、每 app 一張表，一格一列：品牌｜面向｜關係｜填報｜會議摘要｜條目數｜審核。**預設只展開衝突與補充**，其餘折疊成一行計數；跨客戶訊號另列 | `v_meeting_sb_reconcile_q`（`effective_relation` = PM 改判後的值） | 不重算 relation、不列證據（證據清單是 T5） |
| B 當月會議紀錄彙整 | 每月一張卡，一行漏斗數字；**先分應用（MNT → NB → TV → ALL → 應用不明）**，應用底下每個客戶一張摘要卡：輪廓（條目 / 信 / 日期 / 前三主題 / 要求決定問題數 / 發言方 / S2）、**LLM 摘要 3–5 句 ＋ 值得注意**、規則挑的代表句 5 條；逐條全列折疊在最後 | `v_meeting_items_q` ⋈ 鏡頭表 `dup_key`；LLM 一組一次 | 不篩業務相關、不對 Sales Brief、不排除 S2（內部版）；只去同文重複 |

## B 節的摘要怎麼來

- **代表句（規則，零成本）**：[c04] `pick_highlights`：要求 / 決定 / 問題 → 商務主題（需求、allocation、價格、成本、產品規劃、商務關係、產能）→ S2 → confidence → 日期新；同句去重；每組 5 條。
- **摘要（LLM）**：[c08] prompt 0.1：一組一次，送該組條目（代表句排序前 60 條），要求只能用條目內的資訊、每句標明客戶方 / AUO 方、數字照抄、不出現人名 / token / email；輸出 JSON `{"summary", "watch"}`。[c08] `postprocess_summary` 後處理：含 `<Pnn>` / email 整組作廢（只剩代表句）、summary ≤ 500 字、watch ≤ 3 條。JSON 壞再問一次。
- **閘門**：`llm_summary = false` 全不呼叫；條目 < `min_items_for_llm` 的組不呼叫；`max_llm_groups` 限制每月呼叫組數（條目多的先）。費用：每組約 3k 輸入 ＋ 400 輸出 token，一個月幾十組 < USD 1；[c11] 印 `est_cost_usd`。
- 端點同 T4 / Stage A（Azure Foundry、secret `llm-api-keys / ms-foundry`、thinking 關、system prompt cache）。

## 兩種「月」

- A 節的月 = `brief_month`（Sales Brief 期別，D6 窗口）。
- B 節信件層漏斗永遠按**收信日**；條目層預設按**會議日期**（`month_basis = meeting`）。會議日期回溯到 2025-05、2026-01～08 最厚，9 / 10 月反而薄；要看「這個月收進來的信講了什麼」改 `month_basis = mail`。沒有會議日期的正本條目在 `meeting` 模式永遠不出現，總覽會印數量。

## 人名與敏感度

summary 已 token 化，`<Pnn>` 以陣營顯示（客戶方（acer）/ AUO 方 / 第三方（inx））。LLM 看到的也是陣營標籤，輸出若含 token / email 整組作廢。`quote` 預設不印：正文提到的第三人姓名規則補不到（規劃 Q1），只在 PM 內部看時開 `include_quote = true`。B 節含 S2 條目（紅色標示），不是外送版。

## 怎麼跑

1. `dbutils.widgets.removeAll()` → Run all。`months = 2026-09,2026-10`、`sections = A,B`、`output = html`、`llm_summary = true`。第一次可先 `max_llm_groups = 3` 看摘要品質再放開。
2. [c11] 印每月組數、LLM 成功 / 失敗 / 跳過數、費用與 WARN；[c12] 印整份 HTML 原始碼：從 `<!DOCTYPE html>` 到 `</html>` 全選複製，存成 `pm_pack_202609_202610.html`（UTF-8），寄給 PM 或放共用資料夾。
3. 按收信月跑 10 月有數千條，單 cell 輸出可能被截；那時 `sections = B`、一次一個月，或設 `max_per_group`。
4. PM 回的意見：A 節的格照 T5 README 的 UPDATE 寫進 `g_meeting_sb_reconcile_bu` 審核欄（T4 重跑不覆蓋）；B 節的意見記進 DIGEST_ISSUES 或 HANDOFF；摘要寫法要改就動 [c08] prompt、升 `PROMPT_VERSION`。

純函式測試：`tests/test_meeting_extracted_pm_pack.py`（[c02]～[c06]、[c08]）。
