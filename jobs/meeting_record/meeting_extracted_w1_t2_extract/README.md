# meeting_extracted_w1_t2_extract

W1（中立層週跑）的第三支 task：**T2 L1 中立萃取（LLM）**。規格 PM_Head `metting_record/01_meeting_to_sales_brief_進階規劃.md` v0.4.1 §4.2、§5.0、§5.1、§6.1–§6.7、§3.3；偏離處見 `../meeting_extracted_migration/STATUS.md` D22–D26。

- 輸入：`s_meeting_record_clean_bu`（`content_type ∈ {inline_minutes, thread_reply}` 且 `dup_of IS NULL` 的段）、`s_meeting_participants_bu`（token / side / company 給 prompt；姓名只在 driver 做 S3 遮罩）、`s_semantic_entity_alias` / `s_semantic_entity`（`customer` 正規化）
- 輸出：`g_meeting_items_bu`（鍵 `item_id`；本批段既有條目 MERGE 標 `superseded = true`，新條目 append）；表由 002 建，`s3_masked` 欄由本支 [c10] 在缺欄時 `ALTER TABLE ADD COLUMNS` 補（D26）
- LLM：Azure Foundry Anthropic Messages 端點（URL 與 secret `llm-api-keys/ms-foundry` 同 `jobs/sales_report_mail/job_sales_brief_report` [c04]；規格 §5.0「沿 Sales Brief Job」）；`requests` 直打，不裝套件；thinking 關、`max_tokens` 16000（§5.1 的 4,000 實測紀要段會截斷；截斷再以精簡指示重打一次）、system prompt `cache_control`；**不送 `temperature`**（claude-sonnet-5 回 400，§5.0 的 temperature 0 做不到）
- 參數（widgets）：`catalog`、`schema`、`run_mode`（incremental / backfill）、`date_from` / `date_to`（backfill 用，對 `mail_date`）、`unit`、`prompt_version`（預設 0.2，要等於 [c04] `PROMPT_VERSION_IN_CELL`）、`model`（預設 `claude-sonnet-5`）、`max_segments`（費用閘門，預設 20，0 = 不限）、`concurrency`（預設 4）、`retry_failed`（true：有效列含任一 `failed_*` 的段整段重打）、`prompt_cache`、`dry_run`（預設 true；**dry_run 也會呼叫 LLM**，受 `max_segments` 限制）
- 增量：不設水位。可萃取段中，items 表沒有「同 `prompt_version` ＋ 同 `cleaner_version` ＋ `superseded = false`」列的段都算本批（含首次、升 prompt、重洗過的段）；`retry_failed = true` 時有效列含任一 `failed_*` 的段整段重打（舊條目標 superseded）。`max_segments` 先切 `mail_date` 最舊的段，跑幾次就追上。
- 排程：W1 每週一，接在 `meeting_extracted_w1_t1_clean` 之後（同一 Job 第 3 個 task）。首次 `run_mode = backfill`：`dry_run = true`、`max_segments = 5` 看樣本 → `max_segments = 50` 看關卡 → `dry_run = false`、`max_segments = 0` 全量。
- 負責人 / 更新日期：（填）/ 2026-10-16

## 規則摘要

| 步驟 | cell | 規則 |
|---|---|---|
| 本批段 | [c07] `select_batch_segments`、[c10] | 可萃取段扣掉已萃過的；`dup_of` 非 NULL 不送（跨信重複不重呼叫，§10）；`clean_len > 12k` 整段照送只記 log（§11.1） |
| prompt | [c04] | system：角色與中立紀律、收錄 / 原子化規則、`statement_type`、`topic_tags` 詞表、發言人、日期、詞彙表壓縮版、quote 規則、輸出 schema、附錄 A few-shot。user：主旨、段落日期與依據、類型、程式 hint（僅參考）、網域、參與者 token 清單（token / side / 公司，標轉寄人與群組）、`clean_text`。**不帶姓名 / email** |
| 呼叫 | [c06] `call_l1`、[c11] | 每段一次；HTTP 408 / 429 / 5xx / 連線錯誤退避 3 次；JSON / schema 失敗把上一輪輸出當 assistant turn、帶錯誤訊息再問 1 次；端點失敗的段不產生列（下次再撿）。ThreadPool `concurrency` 併發 |
| 解析 | [c05] `parse_llm_json` | 容忍 markdown 圍欄與前後說明；頂層要有 `items: []`；> 40 條視為失敗 |
| 驗證 | [c05] `build_item_rows` / `quote_in_text` | `statement_type` 不在詞表 / summary 或 quote 空 → `failed_schema`；quote 三層比對（去空白 → NFKC → 去標點符號 md 殘渣小寫，字母數字仍要逐字同）都不是 `clean_text` 子字串 → `failed_quote`；quote 可用「…」串接同段片段（附錄 A 寫法），每片依序要找到。失敗照樣寫列，View 只看 `ok` |
| S3 | [c05] `name_patterns_of` / `s3_mask` | summary / quote / segment_note / free_tags 裡的 email 換成 `<email>`、本信參與者姓名換成該人的 `<Pnn>`（D26，**條目保留不作廢**，`s3_masked` 記換了幾處）。姓名寫法：原字串、中文名、英文名、「姓, 名」整字不分大小寫（字間可為空白 / `-` / `_` / `.`）、英文名首字整字區分大小寫（Luke 抓得到，willing 不會被 Will 誤殺）、含中文的寫法子字串；長的先換。quote 驗證用換前或換後任一版本；`item_key` 用換後的 quote。[c12] 遮罩條目比例 > 5% WARN、> 20% 停；[c30] 用 SQL 再查 email |
| 發言人 | [c05] `resolve_speaker` | token 要在本信清單；轉寄人 / 群組 / 不存在 → NULL 並計數；`speaker_side` 以參與者表為準，token NULL 才用 LLM 的（限 4 值）；token NULL 時 `confidence` 上限 0.7（§6.7） |
| 客戶 | [c05] `normalize_customer` | `customer_raw` 保留原名；`customer` 用別名表（name / sb_brand、side = customer、＋ entity_id 本身）：先精確、再子字串長的先吃；短 ASCII 別名（VD）只做整字比對；對不上 NULL 計數 |
| 詞表 | [c05] | `topic_tags` 不在 §6.2 詞表 → 移到 `free_tags`，取前 3 個，`topic_tag_primary = topic_tags[0]`；`app` 不合法 → 由型號前綴推，否則 NULL / `unknown` |
| 日期 | [c05] | `event_date` 缺或壞 → `segment_date`，`date_basis` = `segment_header`（段日期是推測的就 `mail_date_fallback`）；`event_month = yyyy-MM`；`time_refs` / `numbers` 原樣存 JSON 字串 |
| 敏感度 | [c05] `sensitivity_of` | §6.6 關鍵字：S2（Allocation、限簽、ppm / dppm、US$、報價、rebate、incentive、Deal、結價、MDF、數字＋K）> S1（BP、FCST、LTF、一定盈、策略、方向、TAM）> S0 |
| 鍵 | [c05] `item_key_of` / `item_id_of` | `item_key = sha1(pk ‖ seg ‖ normalize(quote))`；`item_id = BU-MTG-<pk>-<seg>-<sub>-<nnn>`，nnn 接著該段既有最大流水號編（每次萃取新發、不撞） |
| 重萃 | [c07] `with_supersedes`、[c20] | 新條目對同段既有 `ok` 且未 superseded 的條目比 `item_key` → `supersedes_item_id`；寫表時本批段既有條目 MERGE 標 `superseded = true`，再 append |
| 空段 | [c05] | items 空 → 一列 `extract_status = empty`（summary 放 `segment_note`，流水號 000）當「已萃過」標記，下次不重打（D23） |
| 別名補對 | [c05] `renormalize_customers`、[c21] | 每次跑（非 dry_run）把有效 ok 列中 `customer` NULL、`customer_raw` 有值的原名 distinct 後用本次別名索引重算，對得上的 MERGE 回 `customer`；`customer_raw` 不動。001 改種子後不用重萃，`dry_run = false`、`retry_failed = false` 跑一輪（本批 0 段、0 次 LLM）就套上（D27） |
| 進度 | [c11] | `as_completed` 每 50 段印 `progress done/total | 秒 | calls | retries | endpoint errors`；結果仍照段順序存 |

## 關卡（[c12]）

會停：[c04] `PROMPT_VERSION_IN_CELL` ≠ widget（§2.4）；端點全部失敗或失敗過半（不寫半批）；S3 遮罩條目比例 > 20%（prompt 人名規則失效或參與者表異常）；schema 失敗 > 10%、quote 失敗 > 15%（§10 告警）。WARN：S3 遮罩 > 5%、schema > 5%、quote > 10%（§4.2）、`customer` NULL > 20%（別名表要補）。只印：每段條目數、發言人被置 NULL 的原因、tag 移到 free、日期補值、超長段、token 用量 / 延遲 p50 / mean / max / 費用估算（Sonnet 5 標價）。dry_run 另印 15 條樣本與對不上的 `customer_raw`。

## 測試

`tests/test_meeting_extracted_w1_t2_extract.py`：[c02]～[c05] 純 Python（prompt 無姓名、JSON 解析容錯、quote 比對、item_key 穩定、敏感度、客戶正規化、發言人規則、S3 遮罩、整段後處理含失敗情境），[c07] 本機 Spark（段落選取含 retry_failed、流水號、supersedes；schema 取自 002 spec）。不打 LLM。

## 2026-10-16 全量 backfill 結果（prompt 0.2、1,181 段、69 美元）

13,185 列 / ok 12,248 / empty 119 段 / 截斷 46 段（多數精簡重打成功）/ quote 失敗 1.5% / 端點錯 1 段（HTTP 408）。問題：(1) 舊版 S3「命中即作廢」清掉 583 條（4.5%，3 字母英文名子字串誤殺），散在 221 段 → D26 改遮罩；撿回要 `retry_failed = true` 重打 289 段（約 7,100 條、35–40 美元、1.5–2 小時），**使用者決定測試期先不補跑**；(2) `customer` NULL 52%：88% 是 LLM 沒填（多客戶週會紀要的條目沒帶章節客戶，等 prompt 0.3 與 cleaner 0.2 一起全量重跑），12% 是別名表沒有的名字（AOC、SEHC、SEC、HKC、inno、SAMEX…）→ 001 v3 ＋ [c21] 補對。
