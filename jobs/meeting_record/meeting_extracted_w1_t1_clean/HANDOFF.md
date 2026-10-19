# HANDOFF — 2026-10-19 晚收工（下次 session 先讀這份）

總覽與決定（D1–D32）在 `../meeting_extracted_migration/STATUS.md`；這份只寫「現在停在哪、下一步做什麼」。

## 0. 接續點（2026-10-19 收工版，最新；底下 §1–§6 是歷史脈絡）

**git**：最後 commit `28c72d9`（已 push）＝ 方向 C Stage B（D31 / D32）＋ 月報預覽 ＋ 寄信指南。再往前：`12aaaf8`（003 ＋ Stage A）、`16e5635`（task 1 cleaner 0.2）。讀的順序：這份 §0 → `STATUS.md` §5（進度表）→ §6.5（方向 C）→ §7（待使用者）。

**Databricks 上現在有的**（`micenter.mi3_datahub_prod`）：

| 物件 | 狀態 |
|---|---|
| W1 三支（mail / clean / extract） | ✅ cleaner 0.2 / prompt 0.2 寫表：495 封、1,817 段、items 有效 ok 12,774 |
| 003 鏡頭表 `g_meeting_items_sem_bu` ＋ 2 View | ✅ 最新版（dup_key、INTEL_TAGS 加 price / cost / allocation） |
| Stage A `meeting_extracted_sem_stage_a` | ✅ 全量寫過：12,686 列（event 12,048 / intel 448 / semantic 190），LLM USD 1.36 |
| 005 台帳三表 ＋ 2 View | ✅ 建好；**`v_background_intel_q` 要重跑 005 [c21]**（D32 改了 retire_candidate） |
| Stage B `meeting_extracted_sem_stage_b` | ✅ 0.1 在 Databricks 驗過（SEM-001、INT-001 / 002、補證據）；**repo 已是 0.2（D32），Databricks 要重新整支匯入** |
| 月報預覽 `meeting_extracted_digest_preview` | repo 有，**Databricks 未匯入** |

**下次開工第一件事（照順序）**：
1. 重新整支匯入 `meeting_extracted_sem_stage_b/notebook.ipynb`（0.2）；005 整支重跑 `dry_run = false`（只會 replace View）。
2. Stage B `dry_run = true`：預期 intel 約 448 條（扣同文重複）以 `intel_auto` 併入 unreviewed、semantic 0；看 [c12] 的 md diff。再 `false`，貼 [c20] [c21] [c30]。
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

