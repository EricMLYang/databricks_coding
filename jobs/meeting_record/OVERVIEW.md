# 會議紀錄萃取流程總覽（技術主管版）

把業務轉寄進來的會議紀錄信，清洗、去識別、拆成原子條目，再分成「業務語意 / 背景情報 / 單點事件」彙整成台帳，最後對照 Sales Brief 填報。所有表在 `micenter.mi3_datahub_prod`；規格 PM_Head `metting_record/01_meeting_to_sales_brief_進階規劃.md` v0.4.1；偏離規格的決定與進度在 `meeting_extracted_migration/STATUS.md`。更新日期 2026-10-19。

```
b_internal_meeting_record（ETL 原始信）
  │ W1 中立層（每週一支 Job，三個 task）
  ├─ task 1 mail     規則   → s_meeting_record_mail_bu（一封信）＋ s_meeting_participants_bu（誰在信裡）
  ├─ task 2 clean    規則   → s_meeting_record_clean_bu（一段，已去識別）
  └─ task 3 extract  LLM    → g_meeting_items_bu（一條「誰、何時、說了什麼」）
        │
        ├─ v_meeting_items_q / v_meeting_item_models / v_meeting_mail_index   ← Genie、閱讀器
        │
        │ 方向 C 語意鏡頭（每週）
        ├─ Stage A       LLM 判一成 → g_meeting_items_sem_bu（semantic / intel / event）
        ├─ PM 審核       人工      → 同表 verified = y / n
        └─ Stage B       規則      → g_semantic_record（SEM）/ g_semantic_record_evidence / g_background_intel（INT）
              │
              └─ 貼回 PM_Head semantic_record.md / background_intel.md → 編譯進各 Genie / Agent prompt
  │
  │ W2 Sales Brief 鏡頭（每月；未建）
  └─ T3 標註 → T4 對照（LLM）→ T5 關卡 → PM 審核例外清單 → 月報
```

一次性 migration（`001` 公司別名種子、`002` 中立層表與 View、`003` 鏡頭表、`005` 台帳）只建結構與種子，不在流程裡。W1 / W2 不呼叫 migration。

## 1. W1 中立層：信 → 條目

| | task 1 `w1_t1_mail` | task 2 `w1_t1_clean` | task 3 `w1_t2_extract` |
|---|---|---|---|
| **輸入** | `b_internal_meeting_record`；001 別名表 | mail 表、participants 表 | clean 表（只送 `inline_minutes` / `thread_reply`、非重複段）；participants（只給 token，不給姓名） |
| **產出** | `s_meeting_record_mail_bu`（MERGE on `pk_seq`）、`s_meeting_participants_bu` | `s_meeting_record_clean_bu`（鍵 `pk_seq, segment_no, sub_no`） | `g_meeting_items_bu`（鍵 `item_id`；承接鍵 `item_key`） |
| **程式動作** | 選正文來源（md → 去轉寄 → 原文 → HTML 備援，≥ 150 字）；刪 Word/CSS 殘渣、免責聲明；找 `From/Sent/Subject` 區塊；參與者編號 P01..Pnn、email 網域對別名表定 side / company；整封去重 `body_hash` | 切段（thread 依標頭；紀要依行首型號與 `ITEM 日期`）；姓名 / email 全換 `<Pnn>` / `<Gnn>`、殘留 email 遮 `[email]`；網址 / 圖片佔位；分類 `inline_minutes` / `thread_reply` / `appointment` / `attachment_only` / `noise`；客戶 / 應用提示；段層去重 `content_hash` | 本批段選取（新段、升版段、`retry_failed`）；quote 三層比對必須存在於 `clean_text`；S3 遮罩（人名 → token、email → `<email>`）；`customer_raw` 查別名表 → `customer`；受控 `topic_tags`；敏感度 S0/S1/S2 關鍵字；`item_key = sha1(pk‖seg‖quote)`；重萃舊列標 `superseded` |
| **LLM 動作** | 無 | 無 | 每段一次 claude-sonnet-5（Azure Foundry）：中立紀律、原子化、`statement_type`、quote 逐字抄；截斷精簡重打；JSON 壞再問一次 |
| **關卡 [c12]** | 0 封、`body_conflict` > 10%、`mail_from` 解析 < 95% 停 | 0 段、`clean_text` 殘留姓名、`dup_of` > 80% 停 | prompt 版號不符、端點失敗過半、S3 遮罩 > 20%、schema 失敗 > 10%、quote 失敗 > 15% 停 |
| **費用** | 0 | 0 | 全量 1,181 段 ≈ USD 70；每週增量數美元。`max_segments` 是閘門，`dry_run` 也會呼叫 |

現況（2026-10-19）：495 封 / 1,817 段 / 12,774 條有效條目。已知缺口：142 封 ETL 截斷四欄都無正文（找 ETL owner）；`customer` 空值 48%（LLM 沒帶章節客戶，prompt 0.3 解）；舊版 S3 誤刪 583 條（重萃一起撿回）。

## 2. 方向 C：條目 → 語意台帳

| | Stage A `sem_stage_a` | PM 審核 | Stage B `sem_stage_b` |
|---|---|---|---|
| **輸入** | `v_meeting_items_sem_cand`（003：有效條目 ＋ SQL 先驗 ＋ 同文重複 `dup_key`） | `v_meeting_items_sem_q` | 鏡頭表 `verified`；005 三張台帳 |
| **產出** | `g_meeting_items_sem_bu`（MERGE on `item_key`，不碰 `verified` / `review_note` / `sem_id`） | 同表 `verified` / `review_note` | `g_semantic_record`、`g_semantic_record_evidence`、`g_background_intel`；鏡頭表回填 `sem_id`；兩份 md ＋ diff |
| **程式動作** | 先驗 `default`（89%）直接 event；同文重複複製正本判定；route_hint 不在投影代號表改 `pa:semantics` | semantic 每週約 5 條標 y / n；intel 不逐條審，看到不對標 n | semantic：`dup_of` 命中既有 SEM 補證據，否則發 SEM id；intel：同 app ＋ term 相同就更新 `as_of`（不倒退），否則發 INT id，`intel_auto` 未審也併為 `unreviewed`；退場候選（`as_of` 超過兩季）只列不改；PM 維護欄永不覆蓋 |
| **LLM 動作** | 先驗命中的 11%（`definition` / `term_hint` / `intel_tag`）批判 category / term / route_hint / as_of | 無 | 無 |
| **費用** | 全量 USD 1.36；每週幾十條 | — | 0 |

三分法：一年後還成立 → semantic（累積，幾乎不退場）；未來幾個月解讀數字會用到 → intel（滾動，帶 `as_of`）；其餘 event（一次性，不進 prompt）。現況：event 12,048 / intel 448 / semantic 190。

## 3. W2 Sales Brief 鏡頭（004 / T3 / T4 / T5 2026-10-23 建好；規格 §3.4–§4.6）

| 步驟 | 動作 | 產出 |
|---|---|---|
| T3 標註（規則） | 條目歸 `brief_month`；`customer` → Sales Brief 品牌；`topic_tag_primary` → 四面向（market_outlook / product_tech / price / other）；`sb_relevant` 規則 | `g_meeting_items_sb_bu` |
| T4 對照（LLM） | 格子 = app × 品牌 × 面向 × 月；單邊為空程式判 `meeting_only` / `sb_only`；兩邊都有才呼叫 LLM 判 `corroborate` / `supplement` / `conflict` | `g_meeting_sb_reconcile_bu`（不覆蓋 PM 審核欄） |
| T5 ＋ 匯出 `w2_t5_export`（規則） | 關卡（0 格 / prompt 版本混雜 / llm 格沒摘要 → 停；其餘 WARN）寫 `b_meeting_migration_log`（D37）；PM 例外清單 md：每 app 一節，conflict → supplement → meeting_only → ALL 格 → corroborate，sb_only 一行計數，每格填報｜摘要｜外送版｜理由｜前 3 條證據｜其餘 id｜審核欄 | 印出的 md（貼給 PM）/ 月報 |

Phase 1 不做：L2 facet fallback、ALL 格跨客戶訊號、可外送摘要。費用每月 < USD 5。前置：月報版面定案（`meeting_extracted_digest_preview` 五題）、prompt 0.3 重萃解 customer 空值。

## 4. LLM 用在哪、沒用在哪、有沒有濫用

**原則**：LLM 只做「規則寫不出來」的兩件事——讀懂一段話拆成原子事實、判一條事實是語意還是情報。清洗、去識別、去重、驗證、正規化、彙整、審核全部是規則或人工。

| 呼叫點 | 誰 | 送什麼 | 不送什麼 | 第一輪費用 | 之後 |
|---|---|---|---|---|---|
| task 3 L1 萃取 | claude-sonnet-5 | 每段一次：`clean_text` ＋ 主旨、日期、參與者 token / side、程式 hint | `noise` / `appointment` / `attachment_only` 段；跨信重複段（`dup_of`）；姓名 / email | 1,181 段 ≈ USD 70（八成是輸出 token） | 每週增量數美元 |
| Stage A 分類 | claude-sonnet-5 | 先驗命中的 11%，20 條一批 | 先驗 `default` 的 89% 直接 event；同文重複複製正本 | 915 條 ≈ USD 1.4 | 每週幾十條 |
| W2 T4 對照 | claude-sonnet-5 | 兩邊都有的格子一格一次（最多 8 條；other 格每標籤 8 條）；只有會議的格 6 格一批只產摘要；app 層每 app × facet 一次；shareable 失敗 / relation 空各多救一次 | 單邊為空的格子程式判；sb_only 不呼叫 | 9 月 34 次 USD 0.33、10 月 16 次 USD 0.20 | 每月 < USD 1 |

**刻意不用 LLM 的地方**：來源選擇與清洗（task 1）、切段與 token 化（task 2）、quote 驗證（程式比對 `clean_text`，LLM 改寫就作廢）、S3 遮罩、客戶正規化（別名表）、敏感度（關鍵字）、整封 / 段層 / 同文去重（hash）、Stage B 彙整與 SEM / INT 發號、`verified` 定案（永遠人工）。

**控費手段已到位**：system prompt `cache_control`（task 3 約 5.7k token 全走 cache 讀）；thinking 關；`max_segments` / `max_items` 閘門，`dry_run` 先看樣本再全量；端點失敗的段不寫列、下次再撿，不重打成功的段；`item_key` 承接審核，重萃不掉人工成果；只用一個模型、一個端點（沿 Sales Brief Job）。

**判斷：沒有濫用，但有三個費用風險要管**

1. **prompt 每升一版 = 全量重萃 USD 70**。這是最大的單筆支出，而且會重複發生。現在的作法是把 prompt 0.3 與 cleaner 0.2 綁在一起只付一次，對。再往前一步是 golden set（規格 §9.1，還沒做）：有了 50 段標準答案，改 prompt 先跑 50 段比指標，確定有進步才全量。
2. **customer 48% 空值打算用 prompt 0.3 解**，這是用 USD 70 買一個「每條帶章節客戶」的行為。付錢前可先評估規則解法：task 2 已有段層 `customer_hint`，多客戶週會紀要若章節標題有客戶名，規則往下傳到每條的成本是 0；規則蓋不到的再交 prompt。
3. **輸出 token 占八成**：一段紀要拆 20 幾條、每條帶 summary / quote / tags / numbers，`max_tokens` 16k。這是原子化的必要成本，不是浪費；但表示換便宜模型（規格 D22 的 llama 比較）省的是輸出單價，值得在 golden set 之後做一次，前提是 quote 逐字率不能掉。

小的改善：`empty` 段 119 個（多是只有與會名單的附件轉寄被當 `thread_reply`）每個都付了一次呼叫，cleaner 0.2 歸成 `attachment_only` 就不送；Stage A 的 `fact / cost`、`fact / price` 目前走 `default` 直接 event，若 PM 覺得漏 intel，擴先驗只多幾百條、幾美元。

## 5. 後續彙整與 Genie 怎麼用

**彙整**
- 台帳是正本（Delta），md 是投影：Stage B 印出 `md_sem_after` / `md_int_after` 貼回 PM_Head，有 confirmed 的 SEM 變更時再由 agent 編譯進各 prompt（`SemanticLayerPlan.md` §1.2 第 4 步），與週審脫鉤；`g_semantic_record.synced_to` 記同步狀態。
- 月報（`digest_preview`）：資料範圍、本月重點、主題對照、事件時間軸、背景情報與口徑、待確認、資料缺口；W2 做完第 3 節接真對照。
- 所有審核欄以 `item_key` 承接，重萃 / 升版不掉審核紀錄。

**Genie Space「客戶會議紀錄」（規格 §8.1，View 已可掛）**

| View | 給 Genie 回答什麼 |
|---|---|
| `v_meeting_items_q` | 「acer 最近對 MNT 價格說了什麼」「哪些客戶提到 allocation」；有 `customer / app / statement_type / topic_tags_str / event_date / speaker_side / sensitivity`，無人名 |
| `v_meeting_item_models` | 「M270QAN06.A 相關的所有陳述」（型號橋表） |
| `v_meeting_mail_index` | 「上週收到哪些客戶的會議紀錄」（一封信一列，計數與分布，無正文） |
| `v_meeting_items_sem_q` | 「有哪些待審的語意候選」「PM 判定和規則不一致的條目」 |
| `v_semantic_record_q` / `v_background_intel_q` | 「Dell FY 怎麼算」「HP AIO 現在的背景情報、哪些快過期」 |

Genie 設定重點：只掛 View 不掛原表（S3 遮罩、有效列過濾、陣列欄已轉字串）；`sensitivity = S2` 的條目依使用者等級決定是否開放；分應用 `_tv / _nb / _mnt` View 等權限需求真的來再建；台帳的 SEM 條目經編譯進 Genie Instructions 當口徑紅旗。

## 6. 維護最常動的地方

| 情境 | 動哪裡 | 費用 |
|---|---|---|
| 新客戶 / 網域對不到 | `001` [c05] 種子 → 重跑 001 → task 3 跑一輪 [c21] 補對 | 0 |
| 信件新垃圾樣式 | task 1 [c03]；先 SQL 量受影響筆數（清洗不得丟資訊） | 0，升 `cleaner_version` 會重洗重萃 |
| 紀要格式變、切不開段 | task 2 [c04] `split_segments` | 同上 |
| 萃取品質（漏客戶、拆太碎） | task 3 [c04] prompt，升版號 | 全量重萃 ≈ USD 70 |
| semantic / intel 判不準 | Stage A [c04] prompt 或 003 先驗 View，`reclassify = true` | 幾美元 |
| 近似主題合併 | Stage B 目前只做 term 精確比對，留給 PM；要自動化加 LLM | 待評 |

通則：每支 notebook [c12] 是關卡、[c30] 是寫入後驗證；純函式 cell 都有 `tests/` 對應；跑在 serverless，不 cache；外部人員姓名 / email 只存在 mail 表與 participants 表，其餘表與 View 一律 token。
