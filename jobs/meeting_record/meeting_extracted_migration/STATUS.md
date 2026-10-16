# 會議紀錄萃取（meeting_extracted）現況與接手說明

> 最後更新：2026-10-15。給下一個接手的人或 Agent：**先讀完本檔再動手**。每完成一步就回來更新「進度」與「下一步」。

## 1. 這是什麼

把 `b_internal_meeting_record`（業務轉寄進來的會議紀錄信）清洗、去識別化、拆成原子條目，再對照 Sales Brief 填報。

- **規格（終點圖）**：PM_Head repo
  `projects/ForwardDeployedEngineer/15_experiments/MI/mi_datahub_table/ai_function_and_job_info/metting_record/01_meeting_to_sales_brief_進階規劃.md`（v0.4.1）。
  本檔只記**與規格不同的決定**與實際進度；規格沒被推翻的地方照規格做。
- 規格 §11.1「最小切片」決定 Phase 0–1 先做什麼；§2.3 規定 migration / 探勘 / 定期 Job 三類程式分開。

## 2. 檔案地圖

| 路徑 | 類別 | 說明 |
|---|---|---|
| `jobs/meeting_record/meeting_extracted_phase0_explore/` | Phase 0 探勘（一次性，已完成） | 只讀統計 notebook；`phase0_result.md` 是 2026-06-01～10-14 實跑結果（JSON） |
| `jobs/meeting_record/meeting_extracted_migration/` | 一次性 migration | 流水號 notebook，見本資料夾 `README.md`；**不得由 W1 / W2 呼叫** |
| `jobs/meeting_record/meeting_extracted_w1_t1_mail/` | 定期 Job（W1 task 1） | T1-a → T1-m → T1-c：寫 mail 表與 participants 表 |
| `jobs/meeting_record/meeting_extracted_w1_t1_clean/` | 定期 Job（W1 task 2） | T1-b：分段、token 化、content_type、content_hash / dup_of，寫 clean 表。**`HANDOFF.md` = 2026-10-16 中斷點，新 session 先讀** |
| `jobs/meeting_record/meeting_extracted_w1_t2_extract/` | 定期 Job（W1 task 3） | T2 L1 萃取（LLM，Azure Foundry）：prompt 內嵌 [c04]、後處理 [c05]、寫 items 表。2026-10-16 全量跑過一次（結果見該資料夾 README 末段） |
| `jobs/meeting_record/meeting_extracted_w2_*`（未建） | 定期 Job | Sales Brief 鏡頭月跑 T3 → T4 → T5 |
| `tests/test_meeting_extracted_*.py` | 本機測試 | 純函式 cell 測試 |

既有、與本案無關但同資料夾：`jobs/meeting_record/meeting_record_explore/`（看單封信原文，可用 pk_seq 查）、`meeting_record_weekly_report/`。

## 3. 已拍板的決定（偏離規格處，以此為準）

| # | 決定 | 取代規格的 |
|---|---|---|
| D1 | 資料夾一律放 `jobs/meeting_record/` 下、前綴 `meeting_extracted_` | §2.3 的 `migration/`、`phase0/`、`jobs/meeting_brief/`、`lib/` |
| D2 | **使用者只能把 notebook 內容複製貼上到 Databricks**，不能上傳檔案、不用 Git folder。設定、種子、詞表、prompt 一律內嵌在 notebook cell（CSV 格式字串或 Python 常數），本機用測試驗證內嵌內容合法 | §2.3 / §6 的 `config/*.yaml`、`prompts/*.md` |
| D3 | 共用純函式不另做 `lib/` 套件，放在各 notebook 的 cell | §2.3 `lib/` |
| D4 | `b_internal_meeting_record` **整表都算 BU**，不做單位過濾（主旨幾乎沒有 `[BU]` 標頭，部門代碼 14 種） | §6.8、`unit_filter.yaml` |
| D5 | 公司 / 別名對照表放 `micenter.mi3_datahub_prod.s_semantic_entity`、`s_semantic_entity_alias`（照 repo 命名慣例）；**不建在 `mi3_semantic`**（那只是 SemanticLayerPlan 預留位置、尚不存在）；不建 `b_` 層（種子即原始層） | §6.3 |
| D6 | `brief_month` 窗口：以 `g_sales_brief_market_intelligence` 每 app × 期別的 `max(submitted_at)` 為截止點（上期截止後～本期截止）。**必須可微調**：`window_mode`（submitted_at / calendar / fixed_day）、`grace_days`、個別 app × 期別 `overrides`；對照格記 `window_start / window_end` | §6.5 日曆月（待決 #3） |
| D7 | 待決 #1（三正文欄不一致）視為已解決：Phase 0 衝突 0%，pk 193 已確認三欄同一封信。一致性改抽樣 | §4.1 (a) 4 |
| D8 | LLM 費用不是限制；不需 Batch API 優化 | §10.1 |
| D9 | 公司種子（2026-10-15 使用者決定）：**Samsung 拆** `samsung_vd`（TV / MNT，Sales Brief 的 Samsung）與 `samsung`（非 VD / 分不出事業部；`samsung.com` 網域、素材只寫「Samsung / 三星」歸此）。**T3 規則：`customer = samsung` 且 `app ∈ {TV, MNT}` 視同 `samsung_vd`**。BenQ 與 Qisda **不合併**。`auodplus.com` 是集團子公司 → `entity_type = affiliate`、`side = auo`。LG `TV\|MNT`、BenQ `MNT`、Qisda `MNT`、Inventec `NB`、S-Core = Samsung SDS 子公司（partner）、Sumika = 住華（supplier）是推測值，使用者授權先用 | §6.3 初表 |
| D10 | 信件品質問題（38% 無 md、base64 圖片翻倍、23% 整封重複）**先在我們這邊做防呆**，不先找 ETL owner：T1-m 三個正文欄都套初洗、刪 base64、mail 層 `body_hash` 去重、`has_headers` 標記 | – |
| D11 | 中立層四張表 `CLUSTER BY (pk_seq)`，不做 partition；View 用 `CREATE OR REPLACE`，表改欄開新流水號 `ALTER TABLE ADD COLUMNS` | §3 型別由 Agent 定 |
| D12 | `oversize` 看**初洗後**的 `display_len` > 200k（base64 圖片刪掉後那 4 封其實正常）；規格是初洗前 | §4.0 關卡 |
| D13 | `segment_no` 用**文件順序**（上 → 下，第 n 個標頭區塊 = 第 n 段；段 0 = 第一個標頭前的文字或整筆未分段）；時間順序靠 `segment_date` 排，不改段序。參與者表與清洗表以此對齊 | §4.1 (c)「順序改為舊到新」 |
| D14 | W1 增量水位 = mail 表 `max(create_date)`，不建 `job_run_log`；`cleaner_version` 不同的舊列自動重洗。轉寄人 token 固定 `P01`，T1-m 直接填，不需 T1-c 回填 | §2.1、§4.0b 4 |
| D15 | 複雜逐封規則（標頭區塊、token 配發）用回傳 struct 的 Python UDF，不用 pandas UDF（本機測試環境無 pandas；日量百封級成本可忽略） | CLAUDE.md 效能原則的例外，cell 內註明 |
| D16 | 規則 6 攤表格：**不猜表頭**（欄數未知，`key: value;` 重組無法 deterministic），改成連續 ≥ 8 個短行（≤ 20 字，可夾空行）併成一行、` \| ` 分隔；quote 仍是 `clean_text` 子字串 | §4.1 (b) 6 |
| D17 | 規則 7 簡轉繁 **Phase 1 不做**（cluster library 無 OpenCC，內嵌字表易錯）；`clean_text` 保留原字，L1 輸出繁中即可。token 化不換「只寫英文名字」的稱呼（Hi Quinn），參與者表沒有這種寫法、硬換會吃掉一般英文字（Will、May） | §4.1 (b) 5、7 |
| D18 | `content_type` 150–300 字且沒有其他訊號的段：thread 段 → `thread_reply`、有型號 → `inline_minutes`、否則 `noise`（規格表沒涵蓋這段區間）。紀要段落用行首型號切，每段通常只有 1 個型號，所以「≥ 3 型號」規則對紀要段改看「段內有型號」。整封重複（`dup_of_pk` 非 NULL）、`none`、`oversize` 的信**不寫段**（跳過，log 計數） | §4.1 (d) |
| D20 | token 化後仍有 email 樣式（簽名檔、非標頭區塊的收件列、IMCEAEX 位址尾巴；參與者表沒有這些人）→ 遮成 `[email]`、只計數不擋；硬規則改成只檢查「參與者姓名殘留」。2026-10-15 第一次 Databricks dry_run 就是被這個擋下 | §4.1 (b) 5 硬規則 |
| D21 | 第一次 Databricks dry_run（2026-10-15）看到的兩件事：(1) 段 0 幾乎都是 AUO e-news 橫幅的 md 表格（293 字，214 封），清洗時刪掉「每格都是空 / 分隔線 / 純網址 / [image]」的表格列，段 0 就會因太短不留；(2) token 編號是 pk 內出現順序，同一段被不同信轉寄時 `<P02>` 會變 `<P05>`，`content_hash` 改在抹掉編號（`<P>` / `<G>`）後計算，否則跨信去重對不到（首跑 dup_of 只有 12%）。另修 `app_hint` 讀 `app_default`（表裡是 ARRAY，不是字串）。第二次 dry_run 看到段 0 其實是**轉寄人簽名檔塞在表格列**（左格橫幅圖網址、右格「英文名 中文名 職稱 email」），再加：裸網址 → `[url]`、外連圖 → `[image]`；「英文名第一個字 ＋ 空白 ＋ 該人 token」→ token（只換這個組合，不單獨換名字） | §4.1 (e) 1 |
| D19 | W1 task 2 增量不另設水位：mail 表有而清洗表沒有的 pk、mail 表 `cleaned_at` 比清洗表新的 pk、清洗表 `cleaner_version` 不同的 pk 都算本批；本批 pk 的段先 DELETE 再 append（重切後段數可能變，MERGE 留不住消失的段） | §2.1 |
| D22 | T2 的 LLM 端點照 §5.0「沿 Sales Brief Job」：Azure Foundry Anthropic Messages（URL、secret `llm-api-keys/ms-foundry` 與 `jobs/sales_report_mail` [c04] 相同），`model` widget 預設 `claude-sonnet-5`；用 `requests` 直打不裝套件；thinking 關；**不送 `temperature`**（2026-10-16 實測 claude-sonnet-5 回 400「temperature is deprecated」，§5.0 的 temperature 0 做不到）；system prompt 開 `cache_control`（`prompt_cache` widget 可關）。**Phase 1 不走 Batch API**（週量千段內，同步 ＋ `concurrency` 併發夠用；費用 §10.1 本來就不是限制）；llama 比較延後到 golden set 有了再做。**2026-10-16 Agent 自定，使用者尚未確認模型名與費用上限** | §5.0、§10 |
| D23 | items 表多一個 `extract_status = empty`：LLM 回 `items: []` 的段寫一列標記（`item_id` 流水號 000、summary 放 `segment_note`），否則每週 incremental 會對同一段重打。`failed_schema` / `failed_quote` 也照樣寫列（S3 命中的列 summary / quote 清空），View 只看 `ok`。`item_id` 流水號接著該段既有最大值編，「每次萃取新發」才不撞鍵 | §3.3、§4.2 |
| D24 | T2 增量鍵 = (segment, `cleaner_version`, `prompt_version`)，不含 `model`（換模型要重萃就升 `prompt_version`）。段落 collect 到 driver 逐段呼叫（ThreadPool），不用 UDF 內打 HTTP：好控流量 / 重試 / 記 usage，筆數受 `max_segments` 閘門限制。重萃：本批段既有條目 MERGE 標 `superseded = true` 再 append 新條目；端點失敗的段不產生列、舊條目不動、下次再撿 | §10 成本 / 冪等 |
| D25 | S3 關卡拆兩層：**寫進表的內容 S3 = 0** 由程式保證（[c05] 處理後 [c30] 用 SQL 再查）；LLM 輸出命中率只 WARN / 高到離譜才停，避免一個誤判擋掉整批。S3 掃描除了參與者全名，再加參與者**英文名首字整字比對**（D17 讓 clean_text 留著 Luke 這種稱呼，50 段 dry_run 看到被抄進 summary）。prompt 0.2 同步加「summary 不得帶人名、quote 挑不含人名的片段」。（命中的處置方式被 D26 取代） | §4.2 關卡「S3 命中 = 0」 |
| D26 | **S3 命中改遮罩修復、不作廢**（使用者 2026-10-16 決定：給高階主管看，不能因名字丟資訊）。[c05] `s3_mask`：summary / quote / segment_note / free_tags 裡的參與者姓名換成該人的 `<Pnn>`、email 換成 `<email>`，條目保留，新欄 `s3_masked` 記換了幾處；quote 驗證用換前或換後任一版本，`item_key` 用換後。比對規則收緊：ASCII 姓名寫法**整字**不分大小寫（舊版「不分大小寫子字串」讓 3 字母英文名落在一般單字裡，全量誤殺 583 條 = 4.5%）、英文名首字整字區分大小寫、含中文寫法子字串、長的先換。關卡：遮罩條目 > 5% WARN、> 20% 停。`s3_masked INT` 加進 002 spec，Databricks 上由 task 3 [c10] 缺欄時 `ALTER TABLE ADD COLUMNS` 補（一欄、冪等，不另開 migration 流水號；下個 003 一併列入）。`retry_failed = true` 語意改成「有效列含任一 `failed_*` 的段整段重打」，用來把被清掉的 583 條撿回（289 段、約 35–40 美元；**使用者 2026-10-16 決定測試期先不補跑**）。[c06] 加 HTTP 408 重試 | §4.2 (9)、§3.3 |
| D27 | **別名表更新後由 task 3 [c21] 補對，不重萃**：每次跑（非 dry_run）把有效 ok 列中 `customer` NULL、`customer_raw` 有值的原名重算一次，對得上的 MERGE 回 `customer`（`customer_raw` 不動）。本批 0 段也會做。001 v3（29 公司 / 93 別名，全部「推測」）新增 `entity_type = competitor`（HKC / BOE / Innolux，side = third_party；`customer` 刻意對不到）。LLM 沒填 `customer_raw` 的 5,676 條（多客戶週會紀要）不用程式補值（段的 `customer_hint` 是「命中最多者」，在多客戶紀要裡最容易錯），等 prompt 0.3「章節客戶帶到每一條」與 cleaner 0.2 一起全量重跑 | §6.3 |

## 4. Phase 0 結論（決定 T1 規則）

完整數字見 `../meeting_extracted_phase0_explore/phase0_result.md`。

| 發現 | 對設計的影響 |
|---|---|
| 量：6–9 月測試期 54 封；宣導後 10/1–10/12 已 436 封，持續增加 | 照正式量設計，不做 PoC 捷徑 |
| `mail_body_md` 非空只有 62%（規格門檻 80% 未過）；正文來源 md 286 / `mail_without_fw` 175 / `mail_body` 7 / 無 22 | `mail_without_fw` 是正式來源；它**沒有 From/To 標頭** → 這些信參與者只有轉寄人。要加 `has_headers` 欄。原因待問 ETL owner |
| md 來源中 92% 有 `**From:** / **Sent:**` 標頭；`Sent:` 日期 1,746 筆只有 2 筆解析失敗（含秒數格式） | 分段可行；T1-b 加 `MMMM d, yyyy h:mm:ss a` 格式；正規化要處理 U+00A0 |
| 粗估類型：紀要 257、未分類短信 153、noise 65、thread 13 | 信多半是給高層的紀要，往返少 → T1-b 以 ITEM 表頭 / 型號行分段為主 |
| md 超大：表格儲存格內 `data:image/...;base64,`，**每轉寄一次圖片數翻倍**（4→8→…→64）；`mail_body` 超大是大量 `[文字](網址)` 連結 | T1-m 初洗加：刪 base64 圖片、連結縮成文字 |
| `mail_without_fw` 也有 Word 殘渣（`Normal / DocumentEmail / EN-US …`） | 規格 §4.1 (b) 規則 2 改為三個正文欄都套 |
| 整封正文完全相同 23%；segment 重複 17.8%，同段最多出現 9 封 | 需要 **mail 層**（展示表 `body_hash / dup_of_pk`）與 segment 層（`content_hash / dup_of`）兩層去重 |
| 40.6% 的信對不到已知客戶；新網域 lge / benq / qisda / inventec / s-core / sumika | 已補進 001 種子；關卡持續列出對不到的網域 |
| 頂層 `mail_to / mail_cc / mail_bcc` 全空 | 參與者只能從 `mail_from` 與正文標頭解析 |
| Sales Brief：`brand_code` 實際值 MNT `Asus/Dell/HP/Samsung`、NB `Acer/Asus/Dell/HP/Lenovo/MSI`、TV `Hisense/Samsung/TCL/TPV`；四面向 = `summary_futureOutlook / techProduct / pricing / otherInfo`（brand 與 app summary 表都有）；`market_intelligence` 的 `field_key` 同四值 | 待決 #10 解決；facet 對照 market_outlook / product_tech / price / other |
| 沒有部門代碼對照表 | `dept_name` 先 NULL（待決 #13） |

## 5. 進度

| 步驟 | 狀態 |
|---|---|
| Phase 0 探勘 | ✅ 完成（2026-10-14） |
| `001_semantic_entity` v1（公司 20、別名 68） | ✅ 2026-10-14 已在 Databricks 正式執行；無重複、無孤兒 |
| `001_semantic_entity` v2（公司 21、別名 72；D9 的種子） | ✅ 2026-10-15 已在 Databricks 正式執行（entity insert 1 / update 8、alias insert 4 / update 4；無重複、無孤兒） |
| `001_semantic_entity` v3（公司 29、別名 93；D27，全部推測） | ✅ 2026-10-16 已在 Databricks 正式執行（entity insert 8、alias insert 21；active 29 / 93，無重複、無孤兒）。task 3 [c21] 同日套用：對不上的原名 53 個 → 對上 17 個，更新 502 列；剩 36 個長尾原名（CN客戶、代理商、Z1S、SDIC、CSD…）不處理 |
| `002_meeting_neutral_tables` | ✅ 2026-10-15 已在 Databricks 正式執行：4 表（33 / 34 / 19 / 35 欄）＋ 3 View（38 / 7 / 28 欄）建立，[c30] 無 PROBLEM |
| W1 task 1 `meeting_extracted_w1_t1_mail`（T1-a / T1-m / T1-c） | ✅ 2026-10-15 Databricks 正式寫表（incremental 首跑 = 全窗 493 封）。dry_run 關卡全過：conflict 0、from_ok 0.998、md 0.586、has_headers 0.544、oversize 0、side_unknown 0、participants 40,321 列 / 9,364 token。使用者未貼 [c30] 輸出與 §6.1 診斷結果。**待查**（不擋）：`dup_of_pk` 3.4%（17 封）遠低於 Phase 0 的 112 封；1 封 `mail_from` 解析失敗；1 個 `auo.comhi` 網域 |
| W1 task 2 `meeting_extracted_w1_t1_clean`（T1-b） | ✅ 2026-10-16 Databricks 正式寫表（backfill 2026-06-01 起、`dry_run = false`）。[c30]：`batch_segments_in_table 1865 / stale 0 / dup_keys 0 / email_left 0 / dangling_dup_of 0 / table_total 1865`。dry_run 第 3 輪數字：493 封 → 454 封分段、1,865 段；thread_reply 981 / inline_minutes 583 / noise 228 / attachment_only 49 / appointment 24；可萃取 1,564 段（扣 dup_of 後約 1,180 段會送 T2）；dup_of 24.4%；段 0 留 199（**還沒抽查**，SQL 在 §6.2 第 6 點） |
| W1 task 3 `meeting_extracted_w1_t2_extract`（T2 L1） | 🟡 2026-10-16 建好並貼到 Databricks（13 個 cell、README、tests 15 passed）。dry_run 四輪（10 / 10 / 10 / 50 段）調完：quote 失敗 1%、S3 0、customer NULL 0、費用 3 美元 / 50 段。**2026-10-16 全量 backfill 已寫表**（`prompt_version 0.2`、1,181 段、11:43 開跑約 3 小時、69 美元）：13,185 列 / ok 12,248 / empty 119 / 截斷 46 / quote 失敗 1.5% / 端點錯 1（408）/ [c30] 一致。兩個問題：S3 誤殺 583 條（4.5%）→ D26 改遮罩，待 `retry_failed = true` 重打；`customer` NULL 52% → [c31a] 診斷待跑。D22–D26 |
| L1 prompt | 🟡 v0.2 內嵌在 task 3 [c04]（0.2：人名規則，D25）（§5.1 十個構件、§6 規則、詞彙表壓縮版、附錄 A 5 條 few-shot）；50 段 dry_run 樣本品質可接受（事實 / 要求分開、S2 判定合理、thread 段 speaker 正確） |
| golden set | ⬜（需 PM 標註） |
| W2（T3～T5） | ⬜ |

## 6. 下一步

### 6.1 使用者端（Databricks）

1. ✅ 2026-10-15 `dry_run = true` 跑過，關卡全過（結果見第 5 節）。
2. 改 `dry_run = false` 跑 → 貼 [c30] 輸出。
3. 寫表後跑下面三段診斷 SQL（輸出只有 pk / 筆數 / 長度 / 遮罩後形狀，無人名），貼回來：

```sql
-- 診斷 1：去重落差（Phase 0 整封相同 112 封 vs W1 dup_of_pk 17 封）。看 body_hash 為 NULL 的信有多少是初洗後縮到 150 字以下
SELECT body_source_field, count(*) AS mails,
       sum(CASE WHEN body_hash IS NULL THEN 1 ELSE 0 END) AS hash_null,
       sum(CASE WHEN body_hash IS NULL AND raw_len >= 150 THEN 1 ELSE 0 END) AS shrunk_below_150,
       sum(CASE WHEN dup_of_pk IS NOT NULL THEN 1 ELSE 0 END) AS dups
FROM micenter.mi3_datahub_prod.s_meeting_record_mail_bu
GROUP BY 1 ORDER BY 1;

-- 診斷 2：用 Phase 0 口徑（原始正文去空白後 sha1）重算整封相同的群，和 W1 口徑比
WITH src AS (
  SELECT m.pk_seq, m.body_source_field, m.display_len, m.body_hash,
         sha1(regexp_replace(CASE m.body_source_field
                WHEN 'mail_body_md' THEN b.mail_body_md
                WHEN 'mail_without_fw' THEN b.mail_without_fw
                ELSE b.mail_body END, '\\s+', '')) AS h_raw
  FROM micenter.mi3_datahub_prod.s_meeting_record_mail_bu m
  JOIN micenter.mi3_datahub_prod.b_internal_meeting_record b USING (pk_seq)
  WHERE m.body_source_field <> 'none'
)
SELECT body_source_field,
       count(*) - count(DISTINCT h_raw) AS raw_dup_copies,
       count(*) - count(DISTINCT coalesce(body_hash, cast(pk_seq AS string))) AS w1_dup_copies,
       sum(CASE WHEN display_len < 150 THEN 1 ELSE 0 END) AS short_after_clean
FROM src GROUP BY 1 ORDER BY 1;

-- 診斷 3：mail_from 解析失敗的那封與 auo.comhi 的形狀（字元遮成 x，只留 / @ . 與數字位數）
SELECT 'from_fail' AS kind, b.pk_seq, regexp_replace(b.mail_from, '[^/]', 'x') AS shape
FROM micenter.mi3_datahub_prod.s_meeting_record_mail_bu m
JOIN micenter.mi3_datahub_prod.b_internal_meeting_record b USING (pk_seq)
WHERE m.forwarder_emp_id IS NULL
UNION ALL
SELECT 'comhi', pk_seq, regexp_replace(display_name_raw, '[^@.<>; ]', 'x')
FROM micenter.mi3_datahub_prod.s_meeting_participants_bu
WHERE email_domain = 'auo.comhi';
```

### 6.2 W1 task 2：`meeting_extracted_w1_t1_clean`（T1-b）— 已建，待跑

4. ✅ notebook 已在 Databricks，dry_run 三輪調完（D20、D21）。
5. ✅ 2026-10-16 `dry_run = false` 寫表，[c30] 全過（數字見第 5 節）。
6. **待做**：抽查段 0（199 段留下來，不確定是轉寄人附註還是殘渣）：

```sql
-- 段 0 的分布
SELECT content_type, count(*) AS n, percentile_approx(clean_len, 0.5) AS len_p50
FROM micenter.mi3_datahub_prod.s_meeting_record_clean_bu WHERE segment_no = 0 GROUP BY 1;
-- 抽 8 段看前 160 字（已 token 化；貼之前掃一眼有沒有人名）
SELECT pk_seq, content_type, clean_len, substring(clean_text, 1, 160) AS head
FROM micenter.mi3_datahub_prod.s_meeting_record_clean_bu WHERE segment_no = 0 ORDER BY rand(7) LIMIT 8;
```
7. 規則細節見該資料夾 `README.md`；之後要改規則就升 `cleaner_version`（下一版 0.2），incremental 會自動重洗舊版本的 pk。

### 6.3 W1 task 3：`meeting_extracted_w1_t2_extract`（T2 L1）— 已在 Databricks，全量跑中

規則見該資料夾 `README.md`；決定 D22–D25。模型 / 端點 / 費用使用者已確認：`claude-sonnet-5`、Azure Foundry（同 Sales Brief Job）、全量一次跑完（實測 3 美元 / 50 段 → 全量約 70 美元，比 §10.1 估的高一倍多，主因輸出 token）。

7. ✅ dry_run 10 段 ×3 輪、50 段 ×1 輪調完（經過見 `../meeting_extracted_w1_t1_clean/HANDOFF.md` §3）。
8. ✅ 關卡：quote 失敗 1%（三層比對後）、schema 失敗 < 1%、S3 0、customer NULL 0。
9. ✅ 2026-10-16 全量 backfill 寫表（數字見第 5 節與 task 3 README 末段）。
10. ✅ [c31a] 診斷跑過（2026-10-16）：S3 清掉 583 條在 221 段、`retry_failed` 會重打 289 段 / 7,137 列；customer NULL 6,407 條中 5,676 條 `customer_raw` 本身 NULL（紀要段 50%、thread 27%），其餘是別名表沒有的名字（AOC 202、SEHC 106、SEC 92、HKC 68、inno 58、SAMEX 55、BOE 18…）；123 封「同信部分有客戶」= 多客戶週會紀要。[c31a] 已從 repo 刪除（Databricks 也刪）。
11. 🟡 **D26 遮罩版已在 repo，Databricks 待同步**（[c02] [c05] [c06] [c07] [c10] [c11] [c12] [c21 新] [c30]；[c31a] 刪）。**補跑先不做**（使用者：測試期）。之後要撿回就 `run_mode = backfill`、`retry_failed = true`、`dry_run = false`、`max_segments = 0`（289 段、35–40 美元、`concurrency = 8` 約 1 小時）。
12. ✅ 001 v3 跑完、task 3 一輪 incremental 跑完（2026-10-16）：[c21] 更新 502 列 customer；同一輪順便撿回全量時 HTTP 408 的那段（1 段、1 條、5 秒），D26 遮罩版在 Databricks 已生效。
13. ✅ 人名抽查（2026-10-16）：有效 ok 列 summary / quote 的大寫英文字高頻 80 ＋ 低頻 120 掃過，使用者確認無人名。
14. 之後：prompt 0.3（章節客戶帶到每一條、`customer_raw` 不留空）與 cleaner 0.2 一起出，一次全量重跑（約 70 美元）；W1 Job 三個 task 串起來週跑（`run_mode = incremental`）；加 §2.4 設定一致性檢查。

### 6.4 之後

0. W1 第一個 task 加 §2.4 一致性檢查（別名表涵蓋近 90 天網域）——目前以 [c12] 的 unmatched_domains 代替。
1. ✅ L1 prompt v0.2 與 T2 已建並跑（task 3）。
2. cleaner 0.2（task 2）：去掉落單的 `**` 粗體殘渣（會進 quote）；只有與會名單的段歸 `attachment_only`（pk 112 那類被當 thread_reply 送 LLM 回 empty）。升版後 incremental 自動重洗，T2 會重萃那些段（舊條目標 superseded）。
3. thread 近似段（152-7 / 152-8）萃出重複條目：Phase 1 接受，T3 時以相似度合併或段層近似去重。
4. golden set 模板，請 PM 標；有了再做 llama 比較（D22）、算 §9.2 指標。
5. 003 migration：Sales Brief 鏡頭表（§3.4、§3.5）、`v_meeting_participants_q` column mask、分應用 View。
6. W2：T3 標註（程式規則 + `sb_facet_map`，Phase 1 不做 L2）→ T4 對照（L3，單邊程式判）→ T5 關卡與 `job_run_log`；PM 審核匯出 md（§4.6）。

## 7. 待使用者回覆

- **部門代碼名稱**（待決 #13）：使用者 2026-10-15 決定**先不提供**（名稱可能變動），`dept_name` 一律 NULL，不擋流程。Phase 0 轉寄人部門代碼 14 種，依封數：`DTDBB0` 183、`DTDAB0` 93、`DTDDC0` 71、`DTDBA0` 69、`DTDDB0` 28、`DTDAA0` 18、`DNB000` 11、`ABSBA0` 7、`DITA00` 4、`DNBAC0` 2、`DNBBF0` 1、`DTDCA0` 1、`DGMA0A` 1、`DTVAB0` 1。之後要填再開 003 建 `s_meeting_dept_code`（種子內嵌，形式同 001）。
- （已答）Samsung 拆 VD / 非 VD、BenQ 與 Qisda 分開、auodplus 為集團子公司 → D9；其餘推測值先用。
- （已答）信件品質問題先在我們這邊防呆 → D10；需要再去向 ETL owner 說明。

## 8. 開發注意事項

- 本機測試用 `py -3.10 -m pytest`（預設 python 3.13 會 worker crash）；本機 pyspark 3.5、Databricks 是 Spark 4.0。
- 改 `.ipynb` 用 `py -3.10 tools/nb.py`，**不要用 sed 改 notebook JSON**。含 `\n`、`\uXXXX` 的程式碼先寫成檔案再 `nb.py set <nb> <tag> <file>`；在這台機器上 shell heredoc 會把跳脫轉成實際字元。
- `pyproject.toml` 讓 ruff 排除 `*.ipynb`；明確傳 notebook 路徑給 ruff 會報 `dbutils / spark` 未定義，屬正常。
- 使用者在 serverless 跑：不用 `.cache()` / `persist`。
- 隱私：`s_meeting_record_mail_bu`、`s_meeting_participants_bu` 以外的表與 View 不得出現姓名、email、工號；**外部公司人員資訊不進 repo**（含測試資料、結果檔、本檔）。Phase 0 類輸出只回傳統計、網域、AUO 部門代碼。
- commit 前 `py -3.10 tools/nb.py strip <nb>`。
