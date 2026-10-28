# HANDOFF — 2026-10-27 更新（下次 session 先讀這份）

總覽與決定（D1–D37）在 `../meeting_extracted_migration/STATUS.md`；這份只寫「現在停在哪、下一步做什麼」。

## 0. 接續點（2026-10-27 更新，最新；底下 §1–§6 是歷史脈絡）

### 0.0 現在停在哪（下次 session 從這裡接）

#### ▶ 下次啟動（2026-10-27：10 月 brief 填完，2026-10 整期 W1 → T3 → T4 0.4 → T5 已在 Databricks 重跑完、log 已寫；下一步 PM 審 9 / 10 月清單、Job 化）

**2026-10-28 現況（最新，先讀這段）**
- ✅ `submitted_end` 複查未變（MNT / NB 10-27 13:13、TV 10-22）→ 2026-10 的 T3 / T4 / T5 不用重跑，10-27 結果就是定稿。
- ✅ PM_Head `02_meeting_record_應用規劃.md` 升 v0.4：附錄 A 七段 SQL 實跑定稿（附錄 B）；重點：無正文 164 封 33%、有效 12,634 / 正本 6,210、customer 空值 38%、S2 506 條 4%、鏡頭 verified 只有 2 + 2、對照 171 格全待審、**條目會議日期回溯到 2025-05、2026-01～08 最厚、9 / 10 月最薄**（推翻「時間淺」）、NB 幾乎無會議資料。
- ✅ **`meeting_extracted_pm_pack` 已貼到 Databricks 並實跑**（commit `cc2ae06` 版；`months = 2026-09,2026-10`、`sections = A,B`、`output = html`、`llm_summary = true`、prompt 0.1）：
  B 節 9 月 MNT 7 組 91 條 / NB 1 組 28 條 / TV 4 組 125 條 / ALL 1 組 / 應用不明 2 組；10 月 MNT 6 組 92 條 / TV 4 組 23 條 / 應用不明 3 組；**LLM 摘要 20 組成功、8 組條目 < 3 跳過、0 失敗**。
  輸出存在 `meeting_extracted_pm_pack/測試結果.html`（293 KB、2 月份、34 張客戶卡；含 S2 與客戶名，`.gitignore` 已排除 `pm_pack/*.html`、只放行 `sample.html`）。**還沒給 PM、還沒看摘要品質。**
- 語意鏡頭審核：使用者已會用 `v_meeting_items_sem_q` 看、UPDATE `verified` 填；95 個 SEM 的初判四桶（重複 16 組 / 雜訊 4 / 疑似 event-intel / 真口徑）在 10-28 對話給過；SEM-043 已標 y 5 列；其餘等 PM。
- 10-28 順手：使用者 profile 磁碟（FSLogix 39 GB）滿了存不了檔 → 清 npm / pip 快取與 `.codex` packages / sessions，釋出約 6.5 GB。

**下一步（照順序）**
1. 使用者看 `測試結果.html` 的 20 組 LLM 摘要是否有編造 / 漏重點（對照卡片下方的代表句）；有問題貼回來調 [c08] prompt → 0.2。版面若要「一個應用一份」加 `apps` widget（改 [c01] [c11]）。
2. 給 PM：`測試結果.html`（總覽卡三題）＋ T5 9 / 10 月 md（掃人名）；PM 回饋 → A 節格照 T5 README 的 UPDATE 填、SEM 照四桶填 `verified`。
3. 之後同前：T4 prompt 0.5（等 PM 審 6 格 conflict）、006 Genie View、Job 化、正文人名遮罩。


**2026-10-27 做了什麼**：Sales Brief 10 月填完（`v_meeting_sb_period` 三 app 都有 2026-10：品牌清單與 9 月相同、`has_app_summary` true、76 格填報文字全填；
`submitted_end` MNT / NB **10-27 13:13 UTC（當天剛填）**、TV 10-22）。照順序重跑：
- W1 task 1 → 2 → 3 → Stage A（incremental、reextract none、max_segments 0）：**全 0 筆**，水位 10-20 之後沒有新信（原始表最後一封真信仍是 10-16）。
  task 2 每次 incremental 都會再挑出 181 封老面孔（164 空信 ＋ 17 重複）再跳過，不影響結果；Job 化時可讓 task 2 把這類 pk 記進水位。
- T3 2026-10 `submitted_at`：窗口 MNT 09-22～10-27、NB 09-23～10-27、TV 09-23～10-22，全 `basis=submitted_at` 無 WARN；300 列 / 相關 145（與 fallback 那次相同，沒新信所以窗口變了也沒條目掉出去）、
  `deactivated 0`、`brand_not_in_sb_rate` 100% → 10.3%（剩 MNT 的 Acer / lg / TPV / qisda → meeting_only）；[c30] 全過，表 736 列（09：436 / 243；10：300 / 145）。
- T4 0.4 2026-10 全量：**82 格 = both 18 + meeting_only 14 + sb_only 38 + ALL 12**；relation **conflict 0 / supplement 26 / corroborate 2 / meeting_only 14 / sb_only 40**（ALL 格 NB × price / other 無會議格 → sb_only，所以 app 層只呼叫 10 次）；
  `relation_retries 3` 全救回、`shareable_failed 0`、`rows_without_summary 0`、`summary_fallback 0`、signals 3 / cross_customer_flagged 6；34 次 USD 0.29、latency max 19 秒；[c30] 全過，`stale_cells_in_month 0`（上次 42 格 meeting_only 全被同鍵覆寫）、表 171 格。
- T5 2026-10：關卡全過無 WARN（相關 145 = 格內合計 145、has_sb_text true、版本單一 0.4）、待審 42（28 llm ＋ 14 meeting_only）、UNKNOWN 品牌格 5；`dry_run = false` 已寫 log `w2_t5_export:2026-10`（第二列，INSERT 並存）。
  T5 `signals 2`（有 cross_customer_note 的 ALL 格數）vs T4 `signals 3`（LLM 回的訊號條數）口徑不同，不是錯。md 使用者自己掃人名後給 PM。
**觀察**：10 月 conflict 0（9 月 6 格）。會議端只有 10-16 以前的信、條目少、填報又是剛寫的，可能真的沒衝突點；也可能 0.4 判法看心情。等 PM 審 9 月 6 格再決定 prompt 要不要動。NB 10 月會議端只 3 條，NB 格幾乎全 sb_only，是資料問題。
**明天要查**：MNT / NB `submitted_end` 是 10-27 當天填的，若之後有人改填報、`submitted_end` 往後移，T3 → T4 → T5 2026-10 要再重跑一次（SQL 在下面）。
```sql
SELECT app_name, brief_month, n_brands, submitted_end, prev_submitted_end, has_app_summary
FROM micenter.mi3_datahub_prod.v_meeting_sb_period WHERE brief_month = '2026-10' ORDER BY app_name;
```
**待辦（2026-10-27 收工；照順序，做完打勾）**
- [ ] **使用者，10-28 新增**：`meeting_extracted_pm_pack`（repo 完成、tests 10 passed、**Databricks 未貼**；只讀不寫、無 LLM）整支匯入後 `months = 2026-09,2026-10`、`sections = A,B`、`output = html` 跑一次，[c12] 印的 HTML 存成 .html 給 PM 用瀏覽器開（純閱讀、無 JS，版面沿 Sales Brief 快報；使用者 10-28 決定不要頁內意見面板、要給高層看得懂的三層版面；`sample.html` 是假資料樣本）：頂端總覽卡（每月每 app 數字 ＋ 問 PM 三題）→ A 節兩期對照結果（只展開衝突 / 補充，其餘折疊）→ B 節每客戶 × 應用一張卡（輪廓、**LLM 摘要 3–5 句（[c08] prompt 0.1，同 T4 端點，每月 < USD 1，`max_llm_groups` 閘門）**、規則代表句），逐條全列折疊在最後。第一次跑建議 `max_llm_groups = 3` 看摘要品質。同日語意鏡頭審核：使用者已知道流程（`v_meeting_items_sem_q` 看、UPDATE `verified` 填），95 個 SEM 的初判四桶（重複 16 組 / 雜訊 4 / 疑似 event-intel / 真口徑）在對話裡給過，SEM-043 已標 y 5 列；其餘等 PM。
- [ ] **使用者**：T5 2026-10 的 md（[c21]）掃正文人名後，連同 9 月 md 一起給 PM 審；重點 9 月 6 個 conflict（MNT × Dell × market_outlook、MNT × HP × other 是真的；NB × Acer × market_outlook、TV × TCL × price 是口徑不同的擲硬幣區）。
- [x] **使用者，10-28 已查**：MNT / NB `submitted_end` 仍是 10-27 13:13、TV 10-22，沒有變動 → 2026-10 的 T3 / T4 / T5 **不用重跑**，10-27 的結果就是定稿。同日跑了 PM_Head `02_meeting_record_應用規劃.md` 附錄 A 七段 SQL，數字已定稿進該檔 v0.4 §1.1 / 附錄 B（重點：無正文 164 封 33%；有效 12,634 / 正本 6,210；customer 空值 38%；S2 506 條 4%；鏡頭 verified 只有 2 + 2；對照 171 格全待審；條目會議日期回溯到 2025-05、2026-01～08 最厚、9 / 10 月最薄）。
- [ ] **commit**（使用者說要再做）：這次只改 HANDOFF；要一起 commit 的 notebook 先 `py -3.10 tools/nb.py strip`。
- [ ] **PM 回饋 → T4 prompt 0.5**：若 9 月 6 個 conflict 多數被改 supplement，[c04] 把「同一主體、同一口徑才能判 conflict」講硬並加反例 few-shot（素材 = `review_relation` 填了的格）；升 `PROMPT_VERSION_IN_CELL` 與 widget；兩期 `max_cells 0` 重跑覆寫非審核欄。T5 版面若 PM 有意見一併改 [c04]。
- [ ] **上游正文人名遮罩**：task 2 或 task 3 加「正文人名」規則 / 讓 L1 標人名（規格 S3）；目前只遮參與者表與 email，9 月 md 露出「Dawei」「彼得黃」。改完 task 3 版本升、只對新信生效（不補舊帳）。
- [ ] **Job 化**：W1 週 Job（task 1 → 2 → 3 → Stage A；job parameters `dry_run = false`、`run_mode = incremental`、`reextract = none`、`max_segments = 0`、Stage A `max_items = 0`）；
  T3 → T4 → T5 月 Job（`brief_month` 留空 = 本月、T4 `max_cells = 0`、三支 `dry_run = false`），排在 brief 送出後（各 app 20–27 日才填完，排月底最後一天或由人手動觸發）。
  順手：task 2 每次 incremental 會重挑 181 封空信 / 重複信再跳過，把這類 pk 記進水位。
- [ ] **月報版面**：DIGEST_ISSUES §4 五題（關鍵 4.2 第一層按場合還是主題）；digest §3 右欄與狀態欄接對照表、§2 LLM 摘要。還沒問到：三份 10 月 digest 的 [c10a] 漏斗數字與觀感。
- 固定每月流程（brief 填完後）：查 `v_meeting_sb_period` 該期三 app 都有列且 `submitted_end` 非 NULL → W1 四支 incremental 補信 → T3 → T4 → T5 同一 `brief_month`。repo 這次沒改 notebook，Databricks 與 repo 同步。

#### ▶ 2026-10-23 收工版本（上一個接續點，保留脈絡）
#### ▶ 2026-10-23 原文（2026-10-23 收工：W2 T3 → T4 0.4 → T5 兩期在 Databricks 全跑通；下一步 PM 審 9 月清單、月底 brief 填完重跑、Job 化）

**Databricks 現況**：T4 0.2 已對 2026-09（88 格：supplement 25 / corroborate 3 / conflict 1 / meeting_only 21 / sb_only 38；34 次呼叫 USD 0.33；[c30] 全過）
與 2026-10（42 格全 meeting_only；16 次 USD 0.20；[c30] 全過；brief 未填預期內）寫表。看到的毛病：9 月 NB × ALL × price 回空 relation 被作廢、
shareable 失敗 9 月 2 格 / 10 月 1 格、10 月一批摘要 6 格 `max_tokens` 截斷 → `rows_without_summary` 10、一次呼叫 latency 211 秒（34 條的 TV × TCL × other）。
**repo 已做（未 commit、未貼）**：
- T4 **0.3**（README「prompt 版本」節）：shareable 失敗帶 S2 數值清單 repair 一次、relation 空重問一次、`T4_MAX_TOKENS` 8000 ＋ 摘要批截斷拆單格、
  格子標頭加填報送出日；[c12] 多印 `shareable_repaired / relation_retries / summary_batches_split`。tests 11 passed。
- **T5 `meeting_extracted_w2_t5_export`**（新，12 cells、README、tests 6 passed、決定 D37）：讀 `v_meeting_sb_reconcile_q` ＋ `v_meeting_items_sb_q` 本期 →
  [c03] 關卡彙總（硬：0 格 / prompt 版本混雜 / llm 格沒摘要 / relation 不合法 → assert；軟：meeting_only 沒摘要、外送版失敗 > 20%、T3 相關數 ≠ 格內合計、沒填報）→
  [c04] §4.6 例外清單 md（每 app 一節，conflict → supplement → meeting_only → ALL → corroborate，sb_only 一行；每格填報｜摘要｜外送版｜理由｜前 N 條證據｜其餘 id｜審核欄；
  other 格證據依主標籤分組；用 `effective_relation` 分節）→ [c20] `dry_run = false` 寫 `b_meeting_migration_log` 一列（slug `w2_t5_export:<月>`）→ [c21] `print(md)`。
  不打 LLM。OVERVIEW §3 / §4 表已更新。
**貼上狀態（2026-10-23 更新）**：☑ T4 0.4 已貼、兩期已用 0.4 重跑寫表　☑ T5 已匯入、[c04] 修版已貼　☑ T5 兩期 `dry_run = false` 已跑：2026-09 log 89 格 / 0 WARN（15:13）、2026-10 log 42 格 / 1 WARN（沒填報文字，預期內；15:14），[c30] 都過。**W2 Sales Brief 鏡頭 T3 → T4 → T5 全部在 Databricks 跑通**；剩 Job 化。md 貼給 PM 前手動遮「Dawei」「彼得黃」。
**T5 9 月 md 看過**：版面照 §4.6 走、順序對、sb_only 計數對、PM SQL 在開頭。兩個版面小修已在 repo：other 格證據依標籤分組但同標籤被拆成好幾段（照證據順序切段）→ 改成同標籤集中；原文裡的 `|`（表格殘留）被跳脫成 `\|` 很醜 → 換成 ／。**上游漏洞（不是 T5 的事，記下來）**：md 裡出現兩個沒被 token 化的人名：pk 279 seg 4 的「PE/Dawei」（羅馬拼音名）、pk 283 seg 2 的「彼得黃」（中文名）；task 2 的姓名遮罩只靠參與者表與 email，正文裡提到的第三人抓不到 → 之後在 task 2 或 task 3 加「正文人名」規則 / 讓 L1 標人名（規格 S3），PM 收到 md 前先手動遮這兩處。**prompt 遵循**：NB × Acer × market_outlook 的 rationale 寫「把握不足仍標記衝突」，直接違反「沒把握選 supplement」；TV × TCL × price 也明知機種不同仍判 conflict。等 PM 審完 9 月 6 個 conflict 再決定要不要在 [c04] few-shot 加反例。
**T4 0.4 兩期結果（Databricks 現況）**：2026-09 89 格：conflict 6 / supplement 21 / corroborate 3 / meeting_only 21 / sb_only 38；`shareable_failed 0`（驗證規則修好，不用 repair）、`relation_retries 3`（都救回）、signals 5；37 次 USD 0.38；[c30] 全過。2026-10 42 格全 meeting_only：`rows_without_summary 0`（`summary_fallback 3` 把 3 個 ALL 格補上）、signals 3；16 次 USD 0.25；[c30] 全過。表共 131 格。**注意 conflict 數一路 1 → 4 → 6（0.2 → 0.3 → 0.4）**：0.4 強調填報較新後 LLM 更敢判 conflict，6 格對不對交 PM 審，T5 清單第一節就是它們；PM 若多數改 supplement，下一版 prompt 把「口徑不同不得判 conflict」再講硬。
**T4 0.3 兩期結果**：2026-09 89 格全到（NB × ALL × price 靠 relation 重問救回：`relation_retries 1`）：conflict 4 / supplement 22 / corroborate 4 / meeting_only 21 / sb_only 38；signals 5、cross_customer_flagged 10；36 次呼叫 USD 0.36；[c30] 全過。2026-10 42 格全 meeting_only、摘要 32 / 32 全填（8000 tokens 後沒再截斷，`summary_batches_split 0`）；17 次 USD 0.24；[c30] 全過。表共 131 格。
**兩個小點已查清、repo 修成 T4 0.4（未貼）**：(a) shareable repair 救不回的原因：兩期都是 TV × TCL × other，S2 數值有「10」「15」「20」「27」，[c03] 用子字串比對撞到「10月」「T550QVN10.F」「2026」，LLM 怎麼改寫都過不了 → 0.4 改成「值＋單位、有數字邊界」比對（README 0.4）。(b) 10 月 3 列沒摘要 = 3 個填報空的 ALL 格 LLM 回空摘要 → 0.4 [c05] 用各品牌格摘要拼 fallback。另 0.3 的 Dell 格 rationale 仍把 8/27 會議當成比填報新 → 0.4 填報段標頭寫明「送出日約 X，比下面每一條會議都新」。tests 13 passed。
**9 月 4 個 conflict 看過**：MNT × Dell × market_outlook（24M vs 22–23M）、MNT × HP × other（IC 庫存 12 週 vs 9 週）是真的；NB × Acer × market_outlook（單條「Notebook 業務下跌 58%」vs BP 10M）0.2 判 supplement、0.3 判 conflict，number_caveat 自己也說口徑不同，是 LLM 的擲硬幣區，交 PM 審（few-shot 素材）；NB × ALL × market_outlook 的 conflict 是承 Acer 那格來的。
**Databricks 要做（照順序）**：
1. T4 替換 [c01] [c03] [c04] [c05] [c11] [c12]（0.4）→ `dbutils.widgets.removeAll()` → 2026-09 `max_cells = 0`、`dry_run = false` 重跑 → 貼 [c12]（看 `shareable_failed` 應 0 或 `shareable_repaired` 1 / 1）與 [c30] → 2026-10 同樣重跑（看 `rows_without_summary` 應 0、`app_mode.summary_fallback`）。
2. ✅ 已完成（T5 兩期 log 寫入）。兩份 md 貼給 PM 前手動遮「Dawei」「彼得黃」。
3. 之後：(a) PM 審 9 月清單的回饋 → 調 T4 prompt / T5 版面；(b) 10 月底 brief 填完 → T3 → T4 → T5 2026-10 重跑；(c) 月報版面（DIGEST_ISSUES §4 五題）；(d) Job 化
   （W1 週 Job；T3 → T4 → T5 月 Job）。還沒問到：三份 10 月 digest 的 [c10a] 漏斗數字與觀感。
**commit**：使用者要求時才 commit；commit 前 `py -3.10 tools/nb.py strip` T4 / T5。

#### ▶ 2026-10-23 晚版（上一個接續點，保留脈絡）

**T4 2026-09 dry_run（prompt 0.1、max_cells 12）結果**：grid 89 = both 19 / meeting_only 21 / sb_only 37 / ALL(sb) 12；items 243（送 LLM 179）；UNKNOWN 品牌格 2 條（MNT 1 / NB 1）。12 格 cell 模式：supplement 8 / corroborate 1 / conflict 3；bad_relation 0、shareable_failed 1（[c05] 已置 NULL）、USD 0.117（12 次呼叫；全量估 19 + 4 + 8 ≈ 31 次、USD 0.3）。品質：supplement / corroborate 都合理、摘要沒編造；3 個 conflict 有 2 個站不住：TV × TCL × price（填報 85 吋、會議 55 吋 T550 機種，LLM 自己也寫「機種不同」）、NB × Acer × market_outlook（單一條目「業務下跌 58%」主體不明 vs 填報 2026 BP 10M；其餘條目是 IGPU / DGPU 個人看法，T3 把它們標進 market_outlook 是 T3 facet 規則偏寬，先不動）。MNT × Dell × market_outlook 的 conflict（24M vs 22–23M）是真的。一格摘要出現 `<P06>` token。
**repo 已改（未貼 Databricks）**：[c04] prompt 0.2（conflict 加同一主體 / 同一口徑限制、人寫客戶方 / AUO 方、S2 自我核對）、[c01] widget 預設 0.2、[c11] ALL 格預算邊界（有會議格但摘要沒產的 ALL 格不再誤寫 sb_only）、[c12] 多印 `deferred_no_summary`；tests 10 passed；README「prompt 版本」節。
**Databricks 要做（照順序）**：替換 T4 [c01] [c04] [c11] [c12] → `brief_month = 2026-09`、`max_cells = 12`、`dry_run = true` 再跑一次（USD 0.12）→ 看那兩格是否變 supplement、摘要沒有 `<P` token、shareable_failed 0 → `max_cells = 0`、`dry_run = false` → 貼 [c12] log 與 [c30]。再跑 2026-10（全 meeting_only）。之後接 T5（下面 (b)）。

#### ▶ 2026-10-23 收工版（上一個接續點，保留脈絡）

**停在哪**：W2 Sales Brief 鏡頭做到 T4。repo 已 commit / push（004 ＋ T3 ＋ T4 ＋ tests ＋ 文件）。Databricks 上：004 已執行、T3 已對 2026-09 / 2026-10 寫表；**T4 `meeting_extracted_w2_t4_reconcile` 還沒複製到 Databricks**。10 月 Sales Brief 要 10 月底那週才填，所以 T4 先對 2026-09 驗。

**下次第一件事：把 T4 貼上去跑（照順序）**
1. 整支匯入 `jobs/meeting_record/meeting_extracted_w2_t4_reconcile/notebook.ipynb`（13 cells；[c07] 讀 secret `llm-api-keys / ms-foundry`，同 Stage A）。
2. `brief_month = 2026-09`、`max_cells = 12`、`dry_run = true`。會真的呼叫 LLM 約 12 次（幾毛美元），不寫表。貼回來：[c10] 的 scope 一行（both / meeting_only / sb_only / ALL 各幾格）、[c12] 的 log（relation 分布、shareable_failed、費用）與例外清單預覽。要看的是 relation 判得合不合理、摘要有沒有編造條目沒有的事、shareable 有沒有洩 S2 數字。
3. 合理 → `max_cells = 0`、`dry_run = false`（9 月估約 30 次呼叫、USD 1 以內）→ 貼 [c12] log 與 [c30]。不合理 → 回報樣本，改 [c04] prompt（升 `PROMPT_VERSION_IN_CELL` 與 widget）再來一次。
4. 再跑 `brief_month = 2026-10`、`dry_run = false`：brief 還沒填，全部格都 `meeting_only`、只產摘要；[c10] 會印 WARN，預期內。
5. 10 月底 brief 填好後：T3 `brief_month = 2026-10` 重跑（截止點從 fixed_day 換成真實 submitted_at、brand_in_sb 會有值）→ T4 2026-10 重跑同一期（覆寫非審核欄）。

**接著做（repo 端）**：(a) 看 9 月 T4 結果調 prompt；(b) **T5**：關卡彙總 ＋ PM 例外清單 md（規格 §4.6：每 app 一節，conflict → supplement → meeting_only → ALL → corroborate，sb_only 一行計數；每格 sb_text｜meeting_summary｜前 3 條證據｜其餘 item_id｜sensitivity_max｜pk_seq），印出來給使用者貼給 PM；(c) 月報版面（DIGEST_ISSUES §4 五題）；(d) Job 化。還沒問到的：三份 10 月 digest 的 [c10a] 漏斗數字與觀感。

**要知道的事實**（細節在下面同日的段落與 STATUS D35 / D36）：T3 標註表 9 月 436 列（相關 243）、10 月 300 列（相關 145）；10 月 brand NULL 的相關條目 36 條 → T4 當 `UNKNOWN` 品牌格不丟；TV × TCL × other 一期 65 條 → T4 的 other 格每個主標籤最多 8 條；Spark 4 ANSI 不能 `sum(boolean)`（T3 [c12] 踩過，T4 已避開）；TV 缺 2026-07 期（8 月窗口照 D6 涵蓋 6-26～8-25）。

---

**2026-10-22 進度（使用者暫停作業）**：digest 加了 [c10a] 資料漏斗（repo 完成、tests 8 passed、**Databricks 未貼**）。使用者問「md 條目有沒有被篩過」→ 有：上游只取可萃取段 / 有效 ok / 鏡頭表 active；[c10] 客戶（指定時客戶 NULL 全進不來）× 應用（含 ALL）× 會議日期月份（沒日期的永遠不出現）；[c03] 去同文重複；§3 每主題 `max_per_topic`、§4 30、§6 10、§5 跨月取 12。[c10a] 一張表一次 agg，印信件層（收信日：收信 / 同信重複 / 清洗段 / 可萃取段）→ 條目層（會議日期：有效 ok、鏡頭 active、客戶篩後、應用篩後、去重後）→ 報表實際列出（§3 / §4 / §6 / 至少出現一次 / 完全沒出現 / §5）。[c03] 的挑選邏輯抽成 `kept_rows` / `group_topics` / `timeline_pick` / `review_pick` 讓 `build_sections` 與 `shown_stats` 共用；[c02] 多 `import unicodedata`（`format_funnel` 按顯示寬度對齊）。README 加「條目怎麼被篩掉」。
✅ **2026-10-23 使用者已全部貼到 Databricks**：digest [c02] [c03] [c10a]、task 3 [c01] [c10] [c11]（reextract = customer 版）。使用者再次確認**不補舊數據**（task 3 一律 `reextract = none`）。
**2026-10-23 D34：壞信不擋整批（repo 完成、tests 31 passed、Databricks 未貼）**。跑 10 月新信時發現：10-16 之後原始表只有 2 封（639 已處理；640 是測試信，`mail_from` 工號前多一個英文字母、英文姓名），task 1 [c12] 的「`mail_from` 解析 ≥ 95%」在單封批次變 0% 直接 assert 停，水位卡在 10-16 23:39，task 2 / 萃取 全部 0 筆。使用者要求：壞的信 pass、要有紀錄、流程不卡。改法：002 [c04] 加隔離表 `s_meeting_record_skipped_bu`（pk、原因、`mail_from` 形狀、人工 `note`；S1）；task 1 [c06] `SKIP_RULES` / `split_skipped`（目前一條 `from_unparsed`）、[c10] 水位 = mail ∪ 隔離表 ＋ widget `reprocess_pks`、[c11] 先隔離再去重、[c12] 三個 assert 改 WARN（0 封也不停）、[c20] 隔離表 MERGE 不蓋 note ＋ 寫進 mail 表的 pk 從隔離表移除、[c30] 檢查沒有 pk 同時在兩表；task 2 [c12] 0 段只印。`MAIL_FROM_RE` 沒放寬（那種工號是否真實待使用者確認）。**Databricks 要貼**：002 替換 [c04] 後 `dry_run = false` 重跑（只會新建隔離表）→ task 1 替換 [c01] [c06] [c10] [c11] [c12] [c20] [c30] → task 2 替換 [c12]。跑順序：task 1（640 進隔離表、水位推到 10-20）→ task 2 → 萃取 → Stage A 都會是 0 筆正常結束 → digest NB / MNT / TV × 2026-10。
✅ **2026-10-23 使用者已貼 D34 並跑完**：002 重跑（隔離表建好）、task 1（640 進隔離表、水位推到 10-20）、task 2 / 萃取 / Stage A 全部 0 筆正常結束。10 月沒有新的真信；10 月 digest 的內容 = 10-16 之前進來、會議日期落在 10 月的條目。
**使用者 2026-10-23 決定：digest NB / MNT / TV × 2026-10 跑完就進 W2（下方「🔜 後續順序」第 2 點）。** §3「客戶 × 主題」分組 / [c12] LLM 摘要兩處先不做，等 W2 的對照結果一起看版面（第 3 點）。
**2026-10-23 W2 開工：004 migration repo 完成（Databricks 未貼）**。使用者說 10 月 Sales Brief 要 10 月底那週才填（brand_summary 目前到 9 月），所以這週先做 004 / T3 / T4 程式，T4 對 2026-10 的實跑等月底；T4 邏輯先拿 2026-09 dry_run 驗（不寫表、不算補舊帳）。探勘不用再跑：Phase 0 已有 brand_summary / app_summary / market_intelligence 的欄位與品牌值（STATUS 待決 #10 已解）；`numeric_entry` 不用。
`004_meeting_sb_lens`（`../meeting_extracted_migration/`，13 cells、tests 12 passed、README §004、決定 D35）：表 `g_meeting_items_sb_bu`（鍵 `(item_key, app_name)`、D6 窗口欄、中立層複製欄、`active`）、`g_meeting_sb_reconcile_bu`（鍵 app × brand × facet × brief_month；PM 審核欄不覆蓋）、`s_meeting_sb_facet_map`（[c05] 種子 14 列：§7.1 facet ＋ §7.2 `relevance_rule` 代號 ＋ `follow_tag`）；View `v_meeting_sb_brief_text`（brand_summary ∪ app_summary 四欄 unpivot，ALL = app 層）、`v_meeting_sb_period`（每 app × 期別品牌清單 ＋ `submitted_end / prev_submitted_end`）、`v_meeting_items_sb_q`（標註 ⋈ 中立層）、`v_meeting_sb_reconcile_q`（§4.6 排序、`effective_relation`、`review_pending`）。✅ **2026-10-23 004 已在 Databricks 執行**（[c30] 無 PROBLEM：表 32 / 32 / 7 / 5 欄、View 7 / 11 / 40 / 36 欄、facet_map active 14）。`v_meeting_sb_period` 現況：MNT / NB / TV 最新期 2026-09，`submitted_end` 8 月前都是 25 日 00:00（補登），8 月起真實送出 21–26 日；**TV 缺 2026-07**（8 月窗口依 D6 會從 6-26 涵蓋到 8-25）；**2026-10 還沒有列**（brief 10 月底那週才填）→ T3 查不到截止點時退回 `fixed_day`（預設 25 日）並 WARN，brief 進來後重跑 T3 整月重標。
**2026-10-23 T3 `meeting_extracted_w2_t3_label` repo 完成（11 cells、README、tests 12 passed；Databricks 未貼）**：[c03] 窗口純日期函式（`submitted_at` 缺截止點退回 `fixed_day` 並 WARN、上一期可跳月、grace 兩端同移、overrides 最優先、`app_unresolved` 用各 app 窗口聯集）；[c04] 七個純 DataFrame 函式 `select_items`（去重 item_key）→ `expand_app` → `assign_window` → `assign_brand`（D9）→ `assign_brand_in_sb` → `assign_facet`（primary → follow_tag → 其餘 tag）→ `assign_relevance`（照種子 `relevance_rule` 代號）→ `to_label_rows`；[c10] 印各 app 窗口與天數、本期沒品牌清單就 WARN；[c12] 只印：比例、各 basis 分布、**格子預覽**（app × brand × facet 相關條目數）、dry_run 樣本 12 條；[c20] MERGE on `(item_key, app_name)` 全欄覆寫；[c21] 本期不在名單的 active 列停用（0 列跳過）；[c30] 驗證。`labeler_version` 欄 = `widget+map<004 log 的 facet_map_version>`。
**Databricks 要做**：整支匯入 T3 → `brief_month = 2026-09`、`dry_run = true` → 看 [c10] 三個 app 的窗口（MNT 8-25～9-21、NB 8-27～9-22、TV 8-26～9-22）、[c12] 的 `app_unresolved_rate` / `facet_null_rate` / `brand_not_in_sb_rate` / 格子預覽與樣本 → 合理就 `dry_run = false` → 貼 [c12] log 與 [c30]。再跑 `brief_month = 2026-10`（會 WARN 退回 fixed_day 25 日；brief 填完後重跑）。
✅ **2026-10-23 T3 2026-09 dry_run 跑過（[c12] 改 boolean 先 cast int 後）**：436 列 / 420 條 / 23 封；app_unresolved 6.9%（= customer NULL 7.3%）、facet 推不出 20.6%（90 列 = `never` 90 列，只有 engineering / schedule / terminology / admin）、brand 不在 brief 26.8%（Acer / Lenovo / TPV / TCL 在 MNT、lg、qisda → meeting_only 格）、相關 243（55.7%）。格子預覽：TV × TCL × other **65 條**、MNT × Dell × other 19、MNT × Acer（不在 MNT brief）× market_outlook 16 …；brand NULL 但 app 已解的相關條目 MNT 1 / NB 1。樣本規則判定都對。**T4 決定**：`other` 格改「每個主標籤最多 8 條」送 L3（其餘面向 8 條）；brand NULL 的相關條目 Phase 1 只計數不產格。
✅ **2026-10-23 T3 兩期已寫表**：2026-09 [c30] 全過（436 列、相關 243）；2026-10 300 列 / 297 條 / 21 封、相關 145、customer NULL 30.7%（10 月信多內部會議）、brand NULL 的相關條目 36（MNT 20 / TV 16）、brand_in_sb 全 false（brief 未填，預期）。
**2026-10-23 T4 `meeting_extracted_w2_t4_reconcile` repo 完成（13 cells、README、tests 10 passed；Databricks 未貼；決定 D36）**：[c03] pick_items（other 格每標籤 8 條）/ shareable 驗證 / numbers 解析；[c04] 一個 system prompt 三種模式（cell / summary / app，§5.3 ＋ §7.1 ＋ §7.3 ＋ S2 規則 ＋ A.4 few-shot）；[c05] 後處理（relation 不合法 = 該格作廢、evidence 只留送過的、signals ≥ 2 品牌）；[c06] 會議格（collect_list struct）⋈ 填報格 full outer → grid collect 到 driver；[c07] llm_client 同 Stage A；[c11] 依「格子 → 摘要批 → app 層」順序吃 `max_cells` 預算，ThreadPool；[c20] MERGE 不碰五個審核欄、`created_at` 只 INSERT；[c30] 驗證。
**Databricks 要做**：整支匯入 T4 → `brief_month = 2026-09`、`max_cells = 12`、`dry_run = true`（會真的呼叫 LLM 約 12 次、幾毛美元）→ 看 [c10] scope（both / meeting_only / sb_only / ALL 各幾格）、[c12] log（relation 分布、shareable_failed、費用）與例外清單預覽 → relation 判得合理就 `max_cells = 0`、`dry_run = false` → 貼 [c12] log 與 [c30]。再跑 2026-10（全部 meeting_only，只產摘要；brief 填完後 T3 → T4 重跑同一期）。
**下次接續**：(1) 問三份 10 月 digest 的 [c10a] 漏斗數字與觀感（還沒問到）；(2) 看 T4 2026-09 dry_run 的 relation 判定與摘要品質，調 [c04] prompt（升 PROMPT_VERSION_IN_CELL）；(3) **T5**：關卡彙總寫 log ＋ PM 例外清單 md（§4.6：每 app 一節，conflict → supplement → meeting_only → ALL → corroborate，sb_only 一行計數；每格 sb_text｜meeting_summary｜前 3 條證據｜其餘 item_id｜sensitivity_max｜pk_seq），印出來給使用者貼給 PM；(4) 10 月 brief 填完（10 月底那週）→ T3 2026-10 → T4 2026-10 → 月報版面（DIGEST_ISSUES §4 五題）→ Job 化。原 T4 設計草稿：格子集合 =（`v_meeting_sb_period.brands` ∪ 會議端 sb_relevant 的 brand ∪ ALL）× 四面向；單邊程式判、兩邊都有才 L3（prompt 照規格 §5.3 三種模式，沿用 Stage A [c06] 的 llm_client）；shareable 驗證；MERGE 不碰審核欄。(4) T5 關卡 ＋ PM 例外清單 md（§4.6）。W2 只保證 2026-10 起。原「🔜 後續順序」第 1 點（10 月信跑 task 1 → 2 → 3 → Stage A，再 digest NB / MNT / TV × 2026-10）；先問使用者要不要先改 §3「客戶 × 主題」分組 / [c12] LLM 摘要（建議先做零成本的分組）。跑 digest 時先看 [c10a] 漏斗，確認 10 月條目量（10 月轉寄的 9 月會議落在 9 月）。

**2026-10-21 進度（最新）**：✅ 修復 MERGE 跑過（7 列更新）；✅ [c05] 已換到 Databricks。之後跑了 `max_segments = 10` 與 `100` 兩批（94 ＋ 1,528 條、[c30] 全過、USD 7.2），**但都是把最舊的 0.3 段重打一次**：0.3 的段仍是 400、customer NULL 池子（0.2 且 NULL）只剩 9 段。原因：排除「本版已萃過的段」那條是 commit `da5b4e1`（10-20 傍晚）才進 [c10]，**Databricks 上的 [c10] 沒跟著換**，4,795 條 0.3 後仍 NULL 的條目每輪都被當待重萃。第四批跑到 [c11] `segments 100` 時中斷、沒寫表。repo 加了護欄：[c11] 印「已用本版 prompt 萃過的段數」，customer_null 批次不為 0 就在打 LLM 前 assert 停。表不用修（重打的只是舊 0.3 列被 superseded）。
**全表現況**：清洗表 1,817 段（cleaner 0.1；可萃取 1,257 段全部有有效條目）；items 有效 0.2 5,745 列（857 段）/ 0.3 7,526 列（400 段）；active ok 12,601、customer NULL 4,839（38%）。0.3 ok 7,310 條裡 2,576 條有 customer（35%）。
✅ 10-21 Databricks 已換 [c10] [c11]，再跑印 `segments 0 | already extracted: 0`：**customer_null 重萃結束**（0.3 共 400 段 / 7,526 列）。那 9 段 0.2 NULL 池子不在可萃取清洗段裡（10-19 重切後段型別或 dup_of 變了的舊條目），選不到、不影響。
✅ customer_basis SQL：0.2 ok 5,291（NULL 105）/ 0.3 ok 7,343（llm 2,650、NULL 4,693 = 64%，規則補不到的內部會議段）；合計 NULL 4,798 / 12,634 = 38%。
✅ **Stage A 10-21 跑完**：新增 3,891 列（rule 1,262 / llm 200 / dup 2,429）、USD 0.33、[c30] 全過（dup_item_key 0、verified 4 → 4）；鏡頭表 active 12,583 = event 12,032 / semantic 173 / intel 378。WARN disagree 75%（先驗 intel 173 → LLM 判 event 140）：先驗 intel 規則偏寬，不擋，之後調 003 [c02] 或 prompt。
✅ **Stage B 0.3 dry_run 看過**（10-21）：semantic_auto 94 個新 SEM（SEM-002..095）＋ 補證據、intel 新 22 個（INT-202..223）＋ 同主題更新約 90 次、關鍵審核清單 259 條（semantic 171 / intel 88）、退場候選 62 個。觀察：近義 SEM 未合併（分貨 code ×5、SR 效期 ×3、VECA 流程 ×3、SEM-048 = SEM-001）、雜訊 SEM（SEM-091 測試信、SEM-089 內部專案、SEM-004 Excel W 欄）→ PM 標 n，依使用者優先序重複暫不管。**修了一處**：`update_intel` 原本不管日期一律用本次條目蓋 summary / source（INT-007 的 11 月摘要被 10 月那封蓋掉）→ [c04] 改成條目 date 比台帳舊就只計次不覆蓋；tests 7 passed。
✅ **Stage B 0.3 已換 [c04]、`dry_run = false` 寫表，數字全過**（10-21）：[c20] written sem_new 94 / sem_updated 0 / evidence 171 / intel_new 22 / intel_updated 11（被更新到的 INT 個數；dry_run 的「約 90 次」是 update_intel 動作數，口徑不同）/ lens_sem_id 258；[c21] status sync 0 列（PM 還沒審）；[c30] dup_sem_id 0 / dup_intel_id 0 / dup_evidence_key 0 / dup_intel_topic 0 / lens_filled 258 = expected 258 / evidence_mismatch [] / unreviewed_with_y 0；totals **SEM 95 / evidence 173 / INT 223**（全 unreviewed，除 SEM-001、INT-001 / 002）。兩份 md 全文用 `print(md_sem_after)` / `print(md_int_after)` 印，仍不貼回 PM_Head（見下方 16 條說明）。
✅ **digest 10-21 跑過 acer × MNT**（Databricks 上已是 D33 版，[c10] 有「參與者表只取 token / side / company」那行）：month 2026-08 / rows 56 / intel+semantic 29 / tokens 76、4 封 3 場。(1) `<P07>` → 「客戶方（acer）」「AUO 方」OK；(2) S2 6 / 56 條且全是真的報價 / 數量，AUO roadmap 已不在 S2；(3) **AUO roadmap 發言方沒改到**：8/14「AUO Monthly Meeting_LVDS QHD/UHD 100Hz」15 條仍是「acer 說明友達三模計劃…」、發言方客戶。SQL 確認那 10 條 `prompt_version = 0.2, speaker_side = customer`：該段條目全有 customer = acer，`customer_null` 選不到，預期內。
**repo 已加（10-21，未貼 Databricks）**：task 3 `reextract = customer` ＋ widgets `reextract_customers`（entity_id 逗號分隔）/ `reextract_apps`（空 = 全部）：指定客戶 × 應用、有舊版 ok 條目的段重萃，排除本版已萃過；[c11] 護欄同樣管它（[c01] [c10] [c11]）。digest [c03]：標籤兩側中文鄰字的空格拿掉（「客戶方（acer） 請求」→「客戶方（acer）請求」）、§7 資料缺口第 2 條改成「約四成條目沒有客戶（內部會議或只提型號）」。tests 21 passed。
**🔜 使用者 10-21 收工時定的後續順序（下次 session 從第 1 點接）**：
1. **先把 10 月的信彙整成 3 個應用（NB / MNT / TV），拿去跟 USER 討論。** 做法：(a) 10-19 之後的信還沒進流程，手動照順序跑 task 1 → task 2 → task 3（`incremental`、`reextract = none`、`max_segments = 0`）→ Stage A，每支 `dry_run = false`；Stage B 可跳過。(b) digest 跑三次：`customer` 空、`app` = NB / MNT / TV、`month = 2026-10`、`max_per_topic` 調到 30；digest 的「月」是會議日期，10 月轉寄的 9 月會議落在 9 月。(c) 現況限制：§2「本月重點」還是示意、沒有 LLM 摘要；§3 不限客戶時按主題分組、看不出哪家說的。要給 USER 看之前可先改 digest：不指定客戶時 §3 改「客戶 × 主題」分組、加 [c12] LLM 摘要（按客戶 3–5 句、附條目 id；三個應用約 USD 1–2）——使用者還沒決定要不要先做這兩處，下次先問。
2. **開始 W2 Sales Brief 對照**（OVERVIEW §3、規格 §3.4–§4.6）：004 migration（`g_meeting_items_sb_bu`、`g_meeting_sb_reconcile_bu`、`sb_facet_map` 種子）→ T3 規則標註（brief_month / 品牌 / 四面向 / sb_relevant，不用 LLM）→ T4 對照（格子 = app × 品牌 × 面向 × 月；單邊程式判，兩邊都有才 LLM 判 corroborate / supplement / conflict，每月 < USD 5）→ T5 關卡 ＋ PM 例外清單。Sales Brief 端現成表：`g_sales_brief_app_summary` / `brand_summary` / `market_intelligence` / `numeric_entry`（sales_report_mail job 週產）。**W2 只保證 2026-10 起**：使用者不補舊帳，9 月以前 customer NULL 38% 對不到格子。
3. **建月報版面**：DIGEST_ISSUES §4 五題（關鍵是 4.2 第一層按場合還是主題）；digest §3 右欄與狀態欄接對照表、§2 LLM 摘要。拿第 1 點的三份表格跟 USER 定。
4. **流程 Job 化**：W1 三 task ＋ Stage A ＋ Stage B 串一個 Job 週跑；job parameters 統一 `dry_run = false`、`max_segments = 0`、`reextract = none`、`run_mode = incremental`；每支 widget 預設 `dry_run = true`，手動跑要改，換版先 `dbutils.widgets.removeAll()`。

**git**：2026-10-23 D34（隔離表 ＋ task 1 / task 2 不擋整批 ＋ tests）與本 HANDOFF 一起 commit、push（使用者要求）；上一次是 10-21 `7dc0e0e`。

**使用者 10-21 決定：不再補舊帳。** `reextract = customer` 的 acer × MNT dry_run 跑了 67 段（護欄 0）但沒寫表；0.2 版剩下的段（857 段扣掉已重萃的）維持原樣，digest / 台帳裡舊月份的 AUO roadmap 條目仍會是「客戶說明友達…」。之後只走週跑新流程（`reextract = none`）；要補再用 `reextract = customer` 或 `all`。下面 1–3 點改為「如果之後要補」才做。
**（如果之後要補）照順序**：
1. task 3 換 [c01] [c10] [c11] → `reextract = customer`、`reextract_customers = acer`、`reextract_apps = MNT`、`max_segments = 0`、`dry_run = true` 看段數（估幾十段、USD 1–3）→ `dry_run = false` → [c30]。
2. Stage A `dry_run = false` 再跑（新 item_key 進鏡頭表）→ Stage B 0.3 `dry_run = false`（SEM / INT 會再多幾個）。
3. digest 換 [c03] 重跑 acer × MNT：8/14 那 15 條應變「AUO 說明…」、發言方 AUO。
4. 寫 `jobs/meeting_record/USER_BRIEF.md`（非技術版一頁：故事 ＋ md 裡三個例子 ＋ 三個限制）給使用者向 USER 交代。

**2026-10-21 早上接續（最新）**：昨晚 400 段那批**跑完且 [c20] 已寫表**（7,481 列、batch_active_rows = expected_rows），但 [c30] 停在
`dup_item_id 7`（其餘檢查 mixed_prompt_version 0 / email 0 / dangling 0 / customer_without_basis 0 都過；`customer_basis_dist`
llm 7,237 / segment_hint 143 / mail_party 380 / NULL 4,829，active ok 12,589，NULL 比例 48% → 38%）。
**原因**：[c05] `build_item_rows` 的 `empty` 列流水號用 `nnn_offset` 本身（設計是首次萃取固定 000），重萃時 offset = 該段既有最大流水號，
新 empty 列就跟那條舊列（已 superseded）撞 `item_id`；這批 400 段有 7 段 prompt 0.3 回 empty → 7 對重複。只影響 `item_id` 唯一性，
有效 View（`NOT superseded`）本來就不重複，Stage A 以 `item_key` 承接也不受影響。
**repo 已修**：[c05] empty 改 `nnn + 1`（與 failed_schema 一致）、tests 15 passed、README。**Databricks 要做（照順序）**：
1. 先跑下面「看重複」SQL（預期 14 列、7 對：每對一條 0.2 ok superseded ＋ 一條 0.3 empty active）；再跑「修復」MERGE（只改 active 的 empty 列，
   把流水號改成該段 max + 1；舊列 id 不動，鏡頭表引用不受影響）；再跑一次「看重複」→ 0 列。不用重跑 [c30]（其餘檢查已過）。
2. task 3 **替換 [c05]** 後再跑下一批：`reextract = customer_null`、`max_segments = 100`、`dry_run = false`（[c10] 會印剩幾段，預期 409 − 400 = 9 段
   加端點失敗的段；印 `segments 0` 就是追完了）。
3. 之後接原本的第 1 點 SQL（prompt_version × customer_basis）→ Stage A → Stage B 0.3 → digest。

```sql
-- 看重複
SELECT item_id, extract_status, prompt_version, superseded, customer, extracted_at
FROM micenter.mi3_datahub_prod.g_meeting_items_bu
WHERE item_id IN (SELECT item_id FROM micenter.mi3_datahub_prod.g_meeting_items_bu GROUP BY item_id HAVING count(*) > 1)
ORDER BY item_id, superseded;

-- 修復：active 的 empty 列改成該段既有最大流水號 + 1（try_cast：ANSI 下 regexp 沒抓到時不丟錯）
MERGE INTO micenter.mi3_datahub_prod.g_meeting_items_bu t
USING (
  SELECT i.item_id AS old_id,
         concat(regexp_replace(i.item_id, '-\d{3}$', ''), '-', lpad(cast(mx.nnn_max + 1 AS STRING), 3, '0')) AS new_id
  FROM micenter.mi3_datahub_prod.g_meeting_items_bu i
  JOIN (SELECT item_id FROM micenter.mi3_datahub_prod.g_meeting_items_bu GROUP BY item_id HAVING count(*) > 1) dup
    ON dup.item_id = i.item_id
  JOIN (SELECT pk_seq, segment_no, sub_no, max(try_cast(regexp_extract(item_id, '-(\d{3})$', 1) AS INT)) AS nnn_max
        FROM micenter.mi3_datahub_prod.g_meeting_items_bu GROUP BY ALL) mx
    ON mx.pk_seq = i.pk_seq AND mx.segment_no = i.segment_no AND mx.sub_no = i.sub_no
  WHERE i.extract_status = 'empty' AND NOT i.superseded
) s
ON t.item_id = s.old_id AND t.extract_status = 'empty' AND NOT t.superseded
WHEN MATCHED THEN UPDATE SET t.item_id = s.new_id;
```

**Databricks 上正在跑 / 剛跑完**：task 3 `meeting_extracted_w1_t2_extract`（prompt 0.3）`reextract = customer_null`、`dry_run = false`、`max_segments = 0`、`concurrency = 4`——只重萃「有 customer NULL 有效條目」的 409 段（5,695 條），估 USD 13、約 30 分鐘。10 段 dry_run 已看過：70 條全 ok、customer_raw 有名字就填、發言方 auo 正確、費用 0.31。使用者下班前啟動全量，**跑到一半中斷，沒寫表**（[c11] 全部跑完才到 [c20]）。改成分批：`max_segments = 100` 重複跑到 [c10] 印 `segments 0`（[c10] 的 customer_null 範圍已改成排除本版已萃過的段，否則合理 NULL 的段每輪會再被選）。用 `SELECT count(*) ... WHERE prompt_version = '0.3' AND NOT superseded` 看進度。
**2026-10-20 晚第二次啟動：一批 400 段（沒分批），33 分鐘跑到 100/400（calls 117、retries 17 精簡重打、端點錯 0），使用者關機離開；雲端會繼續跑。** 下次開工先跑那段 SQL：
- 0.3 的列約 4,000 以上 → [c20] 已寫（使用者用 Run all）；直接看 notebook 裡 [c12] [c30] 的輸出，接第 1 點驗證。
- 0 列 → 要嘛 [c11] 跑完但沒人跑 [c20]（session 還在就接著跑 [c12] → [c30]），要嘛 session 已收掉 → 照分批 `max_segments = 100` 重跑；[c10] 的 customer_null 範圍會自動跳過已萃過的段。

**D33 批次同步狀態**（repo 全部 commit 在本次 commit；Databricks）：

| notebook | Databricks |
|---|---|
| task 3 w1_t2_extract | ✅ 全支同步（[c01] [c04] [c07] [c10] [c22] v2 [c23]）10-21 已換 [c10] [c11]；**`reextract = customer` 版的 [c01] [c10] [c11] 還沒貼**。第一版 [c22] 補錯 4,646 條已由 v2 自動退回；現況規則補 523 條（segment_hint 143 / mail_party 380）、敏感度降級 458 列 |
| Stage A sem_stage_a | ✅ [c22] 同步、跑過一次（952 列同步到鏡頭表） |
| Stage B sem_stage_b 0.3 | ✅ 10-21 [c04] 重貼後 `dry_run = false` 寫表，[c30] 全過（SEM 95 / evidence 173 / INT 223） |
| digest_preview | ✅ D33 版已跑 acer × MNT（10-21）；**[c02] [c03] 改了還沒貼、[c10a] 資料漏斗新增於 [c10] 之後（10-22）** |
| 002 spec | 不用跑（`customer_basis` 由 task 3 [c10] ALTER 補了） |

**下次開工第一件事（照順序）**：

1. **驗證全量重萃結果**：請使用者貼 task 3 [c12] log（看 `segments` ≈ 409、`segments_endpoint_error`、`schema_fail_rate` ≤ 0.05、`quote_fail_rate` ≤ 0.10、`customer_null_rate`、`est_cost_usd`）與 [c30]（`batch_active_rows = expected_rows`、`dup_item_id 0`、`customer_without_basis 0`、`customer_basis_dist`）。端點失敗的段用 `reextract = customer_null` 再跑一次會自動撿（它們仍有 NULL）。
   然後跑：
   ```sql
   SELECT prompt_version, customer_basis, count(*) n FROM micenter.mi3_datahub_prod.g_meeting_items_bu
   WHERE NOT superseded AND extract_status = 'ok' GROUP BY ALL ORDER BY ALL;
   ```
   預期 0.3 的列約 4–5 千、其中 customer NULL 比第一版 dry_run 的 47% 低或相當（剩下的是 AUO 內部事項、只有型號沒客戶）。
2. **Stage A 再跑一次**（`dry_run = false`）：新 item_key 進鏡頭表、舊 key [c21] 停用、[c22] 同步。看 [c12] 的 LLM 候選數（先驗命中的才打 LLM，幾百條、幾美元）與 [c30]。
3. **Stage B 0.3**：`dbutils.widgets.removeAll()` → [c01] 看到 `semantic_auto: True, stage_b_version: 0.3` → `dry_run = true`：預期 semantic 約 188 條（扣重萃後停用的）併成 unreviewed SEM、[c12]「關鍵審核清單」列口徑候選 / 與先驗不同 / 低信心 → `dry_run = false` → 貼 [c20] [c21] [c30]（`unreviewed_with_y 0`）。
4. **digest** 重跑 `customer = acer, app = MNT`：看 `<P07>` 變「客戶方（acer）」、S2 條目數下降、AUO roadmap 條目發言方變 AUO（8 月那兩封若在 409 段內才會改）。
5. 跑完更新本檔 §0 與 STATUS §5。

**之後要決定的（不擋）**：
- 重萃後仍 NULL 的 customer：要不要加「型號 → 客戶」規則（同型號在其他條目的客戶占 ≥ 90% 且 ≥ 3 條才補，成本 0；風險是 open cell 一型號多客戶）。看 `customer_basis_dist` 再決定。
- `model_nos` 收了口語型號（65吋12.6、43U04.5），型號橋表會髒；下個 prompt 版本限制只收完整料號、口語放 free_tags。[c12] 的「別名表要補」WARN 文字已不準。
- PM_Head `background_intel.md` 現有 16 條不在台帳，Stage B md 貼回會蓋掉（見下方）。
- 月報版面五題（`DIGEST_ISSUES.md` §4）；PM 何時開始審關鍵清單；ETL 截斷 142 封找 owner；撿回 583 條（USD 35–40）。
- 下一個要建的 notebook：by 客戶 × 應用（週 / 月）抓條目請 LLM 彙整（使用者的第一個應用）。

### 0.1 2026-10-20 日間脈絡


**git**：最後 commit `28c72d9`（已 push）＝ 方向 C Stage B（D31 / D32）＋ 月報預覽 ＋ 寄信指南。再往前：`12aaaf8`（003 ＋ Stage A）、`16e5635`（task 1 cleaner 0.2）。讀的順序：這份 §0 → `STATUS.md` §5（進度表）→ §6.5（方向 C）→ §7（待使用者）。

**Databricks 上現在有的**（`micenter.mi3_datahub_prod`）：

| 物件 | 狀態 |
|---|---|
| W1 三支（mail / clean / extract） | ✅ cleaner 0.2 / prompt 0.2 寫表：495 封、1,817 段、items 有效 ok 12,774 |
| 003 鏡頭表 `g_meeting_items_sem_bu` ＋ 2 View | ✅ 最新版（dup_key、INTEL_TAGS 加 price / cost / allocation） |
| Stage A `meeting_extracted_sem_stage_a` | ✅ 全量寫過：12,686 列（event 12,048 / intel 448 / semantic 190），LLM USD 1.36 |
| 005 台帳三表 ＋ 2 View | ✅ 2026-10-20 [c05] 同步、整支重跑（retire_candidate 改非 retired 都算） |
| Stage B `meeting_extracted_sem_stage_b` | ✅ **0.2 已同步並於 2026-10-20 寫表**：intel_auto 併入 446 條 → 199 個新 INT（INT-003..201）、247 次同主題更新、鏡頭表 sem_id 回填 446；[c30] 全過（dup_intel_topic 0、unreviewed_with_y 0）；台帳現況 SEM 1 / evidence 2 / INT 201（全 unreviewed，除 INT-001 / 002）。觀察：同 term 跨 app 各發 id（RT8250GSP ×3）、近義主題未合併（TSMC F2/F5 EOL 一家 ≥ 7 個 id），留給 PM 標 n 退場或之後加 term 歸一 |
| 月報預覽 `meeting_extracted_digest_preview` | repo 有，**Databricks 未匯入** |

**2026-10-20 下午 D33 批次（repo 完成、tests 57 passed、未 commit、Databricks 未同步）**：使用者定的優先序——資訊缺失 / 誤會優先（customer 空值、發言方歸屬、`<P07>` 露在報表、S2 誤標 AUO roadmap）→ PM 審核再減 → 其他低負擔。改了五支：task 3（prompt 0.3、`reextract`、[c22] 補客戶、[c23] 重算敏感度、`customer_basis` 欄）、Stage A（[c22] 同步中立欄）、Stage B 0.3（`semantic_auto`、關鍵審核清單）、digest（token → 陣營）、002 spec。task 3 第一版已在 Databricks 跑過（補欄、補客戶 4,789 + 327、敏感度改 458），抽查發現段層 hint 在內部 EC meeting 補錯（TPV 是 ODM）→ [c22] 收緊成要佐證並自動退回，**Databricks 要再貼一次 [c22] 重跑**。**同步順序**：task 3 整支匯入 → `dry_run = false`、`max_segments = 0`、`reextract = none` 跑一輪（0 段 LLM；[c10] ALTER 補欄、[c22] 補客戶、[c23] 重算敏感度，看三行數字）→ Stage A 整支匯入、`dry_run = false` 跑（[c22] 同步）→ Stage B 整支匯入、removeAll、`dry_run = true` 看關鍵審核清單（預期 semantic 188 條併成 unreviewed SEM）→ `false` → digest 整支匯入重跑 acer × MNT 看發言方 / `<P07>`。prompt 0.3 全量重萃（USD 70）另外決定，開 `reextract = all`。

**下次開工第一件事（照順序）**：
1. ✅ 2026-10-20 Stage B 0.2 ＋ 005 已同步、寫表（見上表）。**先不要把 `md_int_after` 貼回 PM_Head**：`PM_Head/projects/ForwardDeployedEngineer/15_experiments/MI/mi_datahub_table/business_semantics/semantics_task/background_intel.md` 現有 16 條（MNT 11 / TV 5）來自 Sales Brief YAML 週萃取（W31 / W33），不在 `g_background_intel` 裡；Stage B md 是台帳投影，貼上會蓋掉它們。待決：(a) 一次性把這 16 條種進台帳（INT id 接著發、status 照「待審」標 unreviewed）再貼；或 (b) 兩段各自維護。另外 201 個主題全 unreviewed，PM 沒審前貼進 prompt 來源檔意義不大。
2. ✅ 同上。
3. 匯入 `meeting_extracted_digest_preview`，跑 `customer = acer, app = MNT`，拿去跟 user 談版面（README 列了要問的五題）；版面定了才開 W2（004 ＋ T3–T5）。
4. `jobs/meeting_record/SENDER_GUIDE.md` 填負責人後發給寄信的同仁。

**使用者的待決（不擋，但要問）**：ETL 截斷 142 封（STATUS §7，找 ETL owner）；撿回 583 條（USD 35–40）；prompt 0.3 全量重萃（USD 70，customer 48% 空值的解法）；PM 什麼時候開始審 semantic 190 條。

**之後的路線**（使用者 2026-10-19 確認）：Stage B → 方向 C 收尾（會議系列表、prompt 編譯）→ **W2 Sales Brief 對照**（最大塊）→ 資料品質修補 → W1 ＋ Stage A ＋ Stage B 串 Job 週跑。Genie Space 隨時可掛當 demo。

---

> **2026-10-19 插入的緊急項（D28 ＋ D29）**：段 0 抽查發現 task 1 來源選擇丟了 156 封信的正文。追到底：ETL 對這些信三個文字欄都只剩 Word 屬性殘渣，正文只在 `mail_body_html` → 加 HTML 備援（偏離規格 §4.0）。task 1 cleaner 0.2 已在 repo（[c01] [c02] [c03] [c12]、tests 19 passed、README），**Databricks 待同步**；同步後 task 1 → 2 → 3 各跑一輪 incremental（task 3 那輪要錢，估 20 美元）。順序與要看的數字在 STATUS §6.1 第 0 點。這件事排在補跑 583 條與 prompt 0.3 之前，因為它改變全量重跑的段數與費用。

## 1. 現在的狀態

| 項目 | 狀態 |
|---|---|
| W1 task 1 `meeting_extracted_w1_t1_mail` | ✅ **cleaner 0.2（D28 ＋ D29）2026-10-19 已同步、backfill 寫表**：495 封、html 4 / none 164、dup 0.034。142 封正文不在任何欄位 → ETL（STATUS §7）。STATUS §6.1 三段診斷 SQL 使用者還沒跑（去重落差 17 vs 112 未解，不擋；D28 重洗後 `body_hash` 會變，數字要重看） |
| W1 task 2 `meeting_extracted_w1_t1_clean`（本資料夾） | ✅ 2026-10-16 Databricks `dry_run = false` 寫表完成，[c30]：1,865 段 / stale 0 / dup_keys 0 / email_left 0 / dangling 0。✅ 2026-10-19 跟著 task 1 0.2 重切：314 封 / 1,817 段 / 段 0 剩 51。🟡 [c11] 本批 pk 改釘 driver（[c30] lazy view 空跑的修正）在 repo、Databricks 待同步 |
| W1 task 3 `meeting_extracted_w1_t2_extract`（T2 L1，LLM） | ✅ **2026-10-16 全量 backfill 已寫表**（prompt 0.2、1,181 段、約 3 小時、69 美元；13,185 列 / ok 12,248 / [c30] 一致）。🟡 **D26 S3 改遮罩**（舊版命中即作廢，誤殺 583 條 = 4.5%）＋ D27 [c21] 別名補對 ＋ [c11] 進度 log：✅ 2026-10-16 已同步到 Databricks 並跑過一輪 incremental（撿回 408 那段 1 條、[c21] 更新 502 列）。**補跑（撿回 583 條，289 段、35–40 美元）使用者決定測試期先不做**。[c31a] 診斷已跑、已刪。D22–D27 |
| `001_semantic_entity` v3 | ✅ 2026-10-16 Databricks 跑完（29 公司 / 93 別名，全部推測，README 001 有對應表；使用者未提出更正）。task 3 [c21] 套用：更新 502 列 customer，剩 36 個長尾原名對不上 |
| 本機測試 | `py -3.10 -m pytest tests/test_meeting_extracted_w1_t2_extract.py tests/test_meeting_extracted_migration_001.py tests/test_meeting_extracted_migration_002.py` 31 passed、ruff clean；task 1 / task 2 的 tests 沒動 |
| git | 上一個 commit `8b8e2b8`（2026-10-16，已 push）。**之後未 commit**：task 1 D28 / D29（notebook [c01] [c02] [c03] [c12]、README、tests）、002 [c04] `body_source_field` COMMENT 加 `mail_body_html`（Databricks 上的 COMMENT 不用改，003 再對齊）、STATUS D28 / D29、本檔 |

## 2. 下一步（照順序）

0a. **方向 C 開工（2026-10-19）**：`003_meeting_semantic_lens` 在 repo（鏡頭表 ＋ 候選 View ＋ 消費 View、tests 9 passed），**Databricks 已執行（2026-10-19）**，探索 SQL 已跑、分布記在 STATUS §6.5，**Stage A job `meeting_extracted_sem_stage_a` 已建並全量寫表（D30；12,686 列、event 12,048 / intel 448 / semantic 190、USD 1.36）**。**Stage B 也建好並在 Databricks 驗過（D31）**：005 三張台帳表、`meeting_extracted_sem_stage_b` 兩輪寫入（新 SEM / INT、補證據）全過。方向 C 流程完整。接手：PM 逐週標 verified → 跑 Stage B；待決是否讓 intel 免逐條審。另有 `meeting_extracted_digest_preview`（月報版面預覽，跟 user 討論版面用）與 `jobs/meeting_record/SENDER_GUIDE.md`（寄信注意事項）；版面討論結果決定 W2 T3–T5。
0. **D28 / D29 同步 ＋ 三個 task 各跑一輪 incremental**（STATUS §6.1 第 0 點）。✅ task 1 dry_run 跑過三次（D28 版、D29 版、CSS 400 字上限版——第三次誤救 42 封 CSS 垃圾、`dup_of_pk` 11%，`HTML_DROP_RE` 已修，見 STATUS §6.1 第 0b 點的處置）：**只救回 4 封**，其餘 142 封四個欄位都沒正文（`mail_body_html` 只有 `<head>`）→ **ETL 截斷，找 ETL owner**（STATUS §7、證據 SQL §6.1 第 0c 點）。D28 / D29 版照樣 `dry_run = false` 寫表（這些信變 `none`、task 2 跳過，不再有 27 字假段），再 task 2 → task 3 各一輪 incremental。✅ **2026-10-19 三個 task 都跑完寫表**（task 2 1,817 段；task 3 90 段 / 545 列 / 約 5 美元；[c30] 都一致）。剩：STATUS §6.1 第 0c 點 ETL 證據 SQL → 找 ETL owner；commit。
1. ✅ Databricks 已同步（task 3 14 cell、001 v3、002 [c04]），001 v3 與 task 3 incremental 一輪都跑完（2026-10-16）。
2. ✅ 001 v3 推測對應使用者沒改；[c21] 更新 502 列。
3. ✅ **summary 人名抽查**（2026-10-16）：高頻 80 字＋低頻 120 字（1–2 封、2–30 次）都掃過，使用者確認**沒有人名**（像名字的 Leo / Gina / Yang / Will / Mizu / Riku 都是代號或術語）。prompt 0.2 的人名規則對非參與者也有效；之後 prompt 0.3 仍加一句「非參與者的人名一律改寫為角色」當保險。
4. **補跑撿回 583 條**（使用者決定時機；**先做第 0 點**，因為重洗後 `retry_failed` 的段數可能變）：`run_mode = backfill`、`retry_failed = true`、`dry_run = false`、`max_segments = 0`、`concurrency = 8`；289 段、35–40 美元、約 1 小時。
5. **prompt 0.3 ＋ cleaner 0.2 一起出**：prompt 0.3 加「條目所在章節 / 標題指明客戶，或整段是單一客戶會議，每條都填 customer_raw」；cleaner 0.2 去 `**` 殘渣、只有名單的段歸 `attachment_only`。兩者都會讓全量重萃（約 70 美元），所以一起做一次。做之前先做段 0 抽查（STATUS §6.2 第 6 點）。
6. W1 三個 task 串成一個 Job 週跑（`run_mode = incremental`）；加規格 §2.4 設定一致性檢查。
7. 之後：golden set 模板（有了才做 llama 比較、§9.2 指標）、004 migration（Sales Brief 鏡頭表、column mask、分應用 View；`s3_masked` 已由 task 3 [c10] ALTER 補，004 只需列入 spec）、W2 T3–T5（STATUS §6.4）。

## 3. 掛著的問題（都不擋）

- task 1 `dup_of_pk` 3.4%（17 封）vs Phase 0 整封相同 112 封：口徑不同，診斷 SQL 在 STATUS §6.1，使用者還沒跑。
- task 1 有 1 封 `mail_from` 解析失敗、1 筆 `auo.comhi` 網域。
- task 2 紀要若整封是 md 表格切不開，整筆一段送 T2（3.2k 字那類）；Phase 1 接受。簡轉繁沒做（D17）。
- task 3 第一次 dry_run（2026-10-16，10 段）：端點與 cache 正常（system 約 5.7k token 全走 cache_read）；pk 112 五段是「附件轉寄 ＋ 與會名單」被 task 2 當 `thread_reply`（名單撐過 300 字）→ LLM 回 `empty`，可接受，cleaner 0.2 考慮「只有名單的段」歸 `attachment_only`；4 段紀要輸出超過 4,000 token 截斷 → 已把 `L1_MAX_TOKENS` 提到 16,000、截斷時改用 COMPACT_HINT 重打。
- task 3 第二次 dry_run（10 段，改完 max_tokens 後）：90 條全 ok、quote 失敗 0、S3 0、customer 全對上、截斷 1 次後精簡重打成功；費用 0.64 美元（八成是輸出 token，約 5.2 萬），全量估 80–100 美元，比 §10.1 高一倍多。樣本品質可接受（pk 120 整封紀要拆 22 條，事實 / 要求有分開，S2 判定合理）。**發現 clean_text 有 md 粗體殘渣**（`** **`、`1****月`）會進 quote，不影響驗證但難看 → cleaner 0.2 待辦：去掉落單的 `**`。thread 段（有 `<Pnn>` 發言人）還沒出現在樣本，等 50 段那輪看 speaker_token。
- task 3 第三次 dry_run（50 段）：482 條、schema 失敗 1、quote 失敗 104 → [c05] 比對改三層（去空白 / NFKC / 去標點符號）＋「…」串接片段後剩 5（1%）；thread 段 speaker_token 正確（P09 → customer）；**summary 抄進未 token 化的英文名（Luke, Juno）** → prompt 升 0.2 加人名規則、S3 掃描加英文名首字整字比對、關卡改 D25。費用 3 美元 / 50 段 → 全量估 70 美元。
- task 3 全量（1,181 段）：S3 舊版「不分大小寫子字串」比對把 3 字母英文名落在一般單字裡也算命中，清掉 583 條（4.5%）→ D26 改整字比對 + 遮罩修復（姓名 → `<Pnn>`、email → `<email>`），`retry_failed = true` 撿回；`customer` NULL 52%（50 段 dry_run 為 0）原因未明，[c31a] 診斷待跑；1 段 HTTP 408（Foundry 讀 request body 逾時）→ [c06] 加 408 重試。
- **thread 近似段**：同一 thread 的兩段（152-7、152-8）內容近似但不完全相同，`content_hash` 抓不到，各萃出一組相同的事 → 條目重複。Phase 1 接受；之後可考慮段層近似去重或 T3 以 `item_key` 外的相似度合併。
- task 3 詞彙表壓縮版實測 system ≈ 5.7k token；`terms_mentioned` 只收 LLM 給的、不回查詞表。`sensitivity` 關鍵字「數字＋K」可能把「10K 片」以外的也抓成 S2，看樣本再收。

## 4. Commit 提醒

`8b8e2b8` 之後的 D28 改動未 commit，要先問使用者。流程：

```
py -3.10 tools/nb.py strip jobs/meeting_record/meeting_extracted_w1_t1_mail/notebook.ipynb
py -3.10 -m ruff check tests/test_meeting_extracted_w1_t1_mail.py
py -3.10 -m pytest tests/test_meeting_extracted_w1_t1_mail.py -q
```

建議 commit 訊息：`meeting_extracted: task 1 cleaner 0.2 — choose_body by cleaned length (D28) + mail_body_html fallback (D29); 146 mails had body only in HTML`

不 commit / push，除非使用者要求。

## 5. 使用者的固定要求（別忘）

- **ETL 截斷待處理**（2026-10-19）：142 封信四個正文欄都沒內容，程式救不回；等 ETL 修好要用 `run_mode = backfill` 重跑該日期窗（水位是 `create_date`，原地更新撿不到）。
- **清洗不得丟資訊**（2026-10-19，D28 之後明講）：任何「選來源 / 丟段 / 刪行」的規則都要以清洗後還剩多少內容為準；新規則上線前先用 SQL 量受影響筆數。D29 之後也包括：來源欄全空時要去看還有哪個欄位有內容（這次是 `mail_body_html`），不能只在規格列的欄位裡打轉。
- 使用者只能**複製貼上**到 Databricks；每次改 notebook 後回覆最後附「Databricks 同步清單」（哪個檔、哪個 cell 替換 / 新增於哪之後 / 刪除 / 整支匯入），不解釋工具指令。
- 跑在 serverless：不 `cache` / `persist`。
- 本機測試用 `py -3.10`，Windows console 要 `PYTHONIOENCODING=utf-8`。`tests/` 整包 ruff 有 ir_calendar 舊檔的 E501，與本案無關。
- 不 commit / push，除非使用者要求；commit 前 `nb.py strip`。
- 外部公司人員資訊不進 repo；tests 用假名與 `.example` 網域。prompt 不帶姓名 / email。

## 6. 下一階段開發指引（彙整語意 / 下游應用）

W1 中立層三個 task 都已正式寫表，下一階段是「拿中立層做事」。規格對應：§8 三個下游方向、§3.4–§3.7 鏡頭表與 View、§4.3–§4.5 W2。

### 6.1 現在手上有什麼（Databricks `micenter.mi3_datahub_prod`）

| 資產 | 狀態 | 給誰用 |
|---|---|---|
| `s_meeting_record_mail_bu`（493 封）、`s_meeting_participants_bu` | ✅ 正式 | 含真實姓名 / email，只給 task 3 與原文閱讀器（§8.4） |
| `s_meeting_record_clean_bu`（1,865 段、cleaner 0.1） | ✅ 正式 | token 化後正文；quote 的 ground truth |
| `g_meeting_items_bu`（13,186 列有效、ok 12,249、prompt 0.2、model claude-sonnet-5） | ✅ 正式但**測試期**：583 條被舊版 S3 清掉未撿回；`customer` NULL 約 48%（主因 LLM 沒填） | 一切下游的唯一入口是 View，不直接掛表 |
| `v_meeting_items_q`、`v_meeting_item_models`、`v_meeting_mail_index` | ✅ 002 已建 | 方向 A / C / D 現在就能接 |
| `s_semantic_entity` / `s_semantic_entity_alias`（v3：29 公司 / 93 別名） | ✅ | customer 正規化、customer_hint、T3 的 sb_brand |

### 6.2 建議的下一階段順序

1. **先補資料品質，再開鏡頭**（兩個都要花 LLM 錢，使用者決定時機）：
   - 撿回 583 條：task 3 `run_mode = backfill`、`retry_failed = true`、`dry_run = false`、`max_segments = 0`、`concurrency = 8`（289 段、35–40 美元、約 1 小時）。
   - prompt 0.3 ＋ cleaner 0.2 一起出、一次全量重跑（約 70 美元）。prompt 0.3 要加：(a) 條目所在章節 / 標題指明客戶或整段是單一客戶會議 → 每條都填 `customer_raw`；(b) 非參與者的人名一律改寫為角色；(c) 同步升 [c04] `PROMPT_VERSION_IN_CELL` 與 widget 預設。cleaner 0.2：去掉落單 `**`、只有與會名單的段歸 `attachment_only`、看段 0 抽查結果決定是否再加規則（STATUS §6.2 第 6 點）。
2. **方向 C 彙整語意（§8.3）**：Stage A 的會議來源改讀 `v_meeting_items_q`。**(a)(b)(c) 2026-10-19 已做成 003（repo）**，剩 Databricks 執行 ＋ 探索 SQL ＋ Stage A job。原規劃：(a) 003 migration 建 `g_meeting_items_sem_bu`（schema 草案在 §8.3，欄位：item_id / item_key / week / category / app / term / summary / quote / date / source / tags / as_of / dup_of / route_hint / extract_note / verified / review_note）；(b) 候選規則用 SQL 先算（semantic：`statement_type = definition` 或 `terms_mentioned` 非空且 quote 含「指 / 定義 / 算法 / 口徑」；intel：`statement_type ∈ {opinion, fact}` 且 `topic_tag_primary ∈ {demand, commercial_relation, supply_chain, capacity}`；其餘 event），看分布再決定 LLM 只判哪些；(c) PM 審核以 `item_key` 承接（重萃後 `item_id` 會變，`item_key` 不變）。會議紀要（`content_type = inline_minutes`）可降權。
3. **W2 Sales Brief 鏡頭（§4.3–§4.5）**：**004** migration（003 已給方向 C）建 `g_meeting_items_sb_bu`、`g_meeting_sb_reconcile_bu`、`v_meeting_sb_reconcile_q`、`v_meeting_report_cells`、`v_meeting_participants_q`（外部人員 column mask）、分應用 View；T3 程式規則（`sb_facet_map`、§7.2 `sb_relevant`，Phase 1 不做 L2）→ T4 對照（兩邊都有才呼叫 L3，單邊程式判）→ T5 關卡寫 `job_run_log`；PM 審核匯出 md（§4.6）。前置：Phase 0 探勘 Sales Brief 三張文字表的欄位與品牌值（待決 #10）。
4. **方向 A Genie Space「客戶會議紀錄」（§8.1）**：三個 View 已可掛；等 W2 的 reconcile View 再補。施工單用 `build/_template.md` 開 `build/X3_客戶會議紀錄.md`。
5. **W1 Job 化**：三個 task 串成一個 Databricks Job 週跑（`run_mode = incremental`，task 1 → 2 → 3）；加規格 §2.4 設定一致性檢查（目前以 task 3 [c12] 的 `unmatched` 類計數代替）。
6. **golden set**（§9.1）：有了才算 §9.2 指標、做 llama 比較（D22）。

### 6.3 接手前要知道的坑

- `item_id` 每次重萃新發、舊列標 `superseded = true` 不刪；任何鏡頭表 / 審核欄一律以 `item_key` 承接。
- `customer_raw` NULL 而 `customer` 有值 = task 3 [c21] 事後補對（D27）；`s3_masked` NULL = 遮罩功能上線前的列（D26）。
- 近似 thread 段（同 thread 兩段內容接近）會萃出重複條目，中立層不處理；鏡頭層用 `item_key` 以外的相似度合併。
- 別名表只對 `side = customer` 的 entity 正規化 `customer`；同業（HKC / BOE / Innolux，`competitor`）刻意不對到。
- 表欄位要改：原則開新 migration 流水號；D26 的 `s3_masked` 是例外（task 3 [c10] 自動 ALTER），003 時把 spec 對齊即可。
- 任何輸出、測試資料、文件都不得出現外部人員姓名 / email；prompt 只帶 token。

