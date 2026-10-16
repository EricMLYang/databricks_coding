# meeting_extracted_w1_t2_extract

W1（中立層週跑）的第三支 task：**T2 L1 中立萃取（LLM）**。規格 PM_Head `metting_record/01_meeting_to_sales_brief_進階規劃.md` v0.4.1 §4.2、§5.0、§5.1、§6.1–§6.7、§3.3；偏離處見 `../meeting_extracted_migration/STATUS.md` D22–D24。

- 輸入：`s_meeting_record_clean_bu`（`content_type ∈ {inline_minutes, thread_reply}` 且 `dup_of IS NULL` 的段）、`s_meeting_participants_bu`（token / side / company 給 prompt；姓名只在 driver 做 S3 掃描）、`s_semantic_entity_alias` / `s_semantic_entity`（`customer` 正規化）
- 輸出：`g_meeting_items_bu`（鍵 `item_id`；本批段既有條目 MERGE 標 `superseded = true`，新條目 append）；表由 002 建
- LLM：Azure Foundry Anthropic Messages 端點（URL 與 secret `llm-api-keys/ms-foundry` 同 `jobs/sales_report_mail/job_sales_brief_report` [c04]；規格 §5.0「沿 Sales Brief Job」）；`requests` 直打，不裝套件；thinking 關、`max_tokens` 16000（§5.1 的 4,000 實測紀要段會截斷；截斷再以精簡指示重打一次）、system prompt `cache_control`；**不送 `temperature`**（claude-sonnet-5 回 400，§5.0 的 temperature 0 做不到）
- 參數（widgets）：`catalog`、`schema`、`run_mode`（incremental / backfill）、`date_from` / `date_to`（backfill 用，對 `mail_date`）、`unit`、`prompt_version`（預設 0.2，要等於 [c04] `PROMPT_VERSION_IN_CELL`）、`model`（預設 `claude-sonnet-5`）、`max_segments`（費用閘門，預設 20，0 = 不限）、`concurrency`（預設 4）、`retry_failed`、`prompt_cache`、`dry_run`（預設 true；**dry_run 也會呼叫 LLM**，受 `max_segments` 限制）
- 增量：不設水位。可萃取段中，items 表沒有「同 `prompt_version` ＋ 同 `cleaner_version` ＋ `superseded = false`」列的段都算本批（含首次、升 prompt、重洗過的段）；`retry_failed = true` 時上次 `failed_*` 的段也重打。`max_segments` 先切 `mail_date` 最舊的段，跑幾次就追上。
- 排程：W1 每週一，接在 `meeting_extracted_w1_t1_clean` 之後（同一 Job 第 3 個 task）。首次 `run_mode = backfill`：`dry_run = true`、`max_segments = 5` 看樣本 → `max_segments = 50` 看關卡 → `dry_run = false`、`max_segments = 0` 全量。
- 負責人 / 更新日期：（填）/ 2026-10-16

## 規則摘要

| 步驟 | cell | 規則 |
|---|---|---|
| 本批段 | [c07] `select_batch_segments`、[c10] | 可萃取段扣掉已萃過的；`dup_of` 非 NULL 不送（跨信重複不重呼叫，§10）；`clean_len > 12k` 整段照送只記 log（§11.1） |
| prompt | [c04] | system：角色與中立紀律、收錄 / 原子化規則、`statement_type`、`topic_tags` 詞表、發言人、日期、詞彙表壓縮版、quote 規則、輸出 schema、附錄 A few-shot。user：主旨、段落日期與依據、類型、程式 hint（僅參考）、網域、參與者 token 清單（token / side / 公司，標轉寄人與群組）、`clean_text`。**不帶姓名 / email** |
| 呼叫 | [c06] `call_l1`、[c11] | 每段一次；HTTP 429 / 5xx / 連線錯誤退避 3 次；JSON / schema 失敗把上一輪輸出當 assistant turn、帶錯誤訊息再問 1 次；端點失敗的段不產生列（下次再撿）。ThreadPool `concurrency` 併發 |
| 解析 | [c05] `parse_llm_json` | 容忍 markdown 圍欄與前後說明；頂層要有 `items: []`；> 40 條視為失敗 |
| 驗證 | [c05] `build_item_rows` / `quote_in_text` | `statement_type` 不在詞表 / summary 或 quote 空 → `failed_schema`；quote 三層比對（去空白 → NFKC → 去標點符號 md 殘渣小寫，字母數字仍要逐字同）都不是 `clean_text` 子字串 → `failed_quote`；quote 可用「…」串接同段片段（附錄 A 寫法），每片依序要找到。失敗照樣寫列，View 只看 `ok` |
| S3 | [c05] `s3_hits` / `first_name_res` | summary / quote 含 email 樣式、本信參與者姓名、或參與者英文名首字（整字、區分大小寫）→ `failed_schema`，**內容清空再寫**；[c12] 命中率 > 5% 才停、否則 WARN（D25）；[c30] 用 SQL 再查寫進表的內容 |
| 發言人 | [c05] `resolve_speaker` | token 要在本信清單；轉寄人 / 群組 / 不存在 → NULL 並計數；`speaker_side` 以參與者表為準，token NULL 才用 LLM 的（限 4 值）；token NULL 時 `confidence` 上限 0.7（§6.7） |
| 客戶 | [c05] `normalize_customer` | `customer_raw` 保留原名；`customer` 用別名表（name / sb_brand、side = customer、＋ entity_id 本身）：先精確、再子字串長的先吃；短 ASCII 別名（VD）只做整字比對；對不上 NULL 計數 |
| 詞表 | [c05] | `topic_tags` 不在 §6.2 詞表 → 移到 `free_tags`，取前 3 個，`topic_tag_primary = topic_tags[0]`；`app` 不合法 → 由型號前綴推，否則 NULL / `unknown` |
| 日期 | [c05] | `event_date` 缺或壞 → `segment_date`，`date_basis` = `segment_header`（段日期是推測的就 `mail_date_fallback`）；`event_month = yyyy-MM`；`time_refs` / `numbers` 原樣存 JSON 字串 |
| 敏感度 | [c05] `sensitivity_of` | §6.6 關鍵字：S2（Allocation、限簽、ppm / dppm、US$、報價、rebate、incentive、Deal、結價、MDF、數字＋K）> S1（BP、FCST、LTF、一定盈、策略、方向、TAM）> S0 |
| 鍵 | [c05] `item_key_of` / `item_id_of` | `item_key = sha1(pk ‖ seg ‖ normalize(quote))`；`item_id = BU-MTG-<pk>-<seg>-<sub>-<nnn>`，nnn 接著該段既有最大流水號編（每次萃取新發、不撞） |
| 重萃 | [c07] `with_supersedes`、[c20] | 新條目對同段既有 `ok` 且未 superseded 的條目比 `item_key` → `supersedes_item_id`；寫表時本批段既有條目 MERGE 標 `superseded = true`，再 append |
| 空段 | [c05] | items 空 → 一列 `extract_status = empty`（summary 放 `segment_note`，流水號 000）當「已萃過」標記，下次不重打（D23） |

## 關卡（[c12]）

會停：[c04] `PROMPT_VERSION_IN_CELL` ≠ widget（§2.4）；端點全部失敗或失敗過半（不寫半批）；**S3 命中率 > 5%**（命中的列內容已清空）；schema 失敗 > 10%、quote 失敗 > 15%（§10 告警）。WARN：schema > 5%、quote > 10%（§4.2）、`customer` NULL > 20%（別名表要補）。只印：每段條目數、發言人被置 NULL 的原因、tag 移到 free、日期補值、超長段、token 用量 / p50 延遲 / 費用估算（Sonnet 5 標價）。dry_run 另印 15 條樣本與對不上的 `customer_raw`。

## 測試

`tests/test_meeting_extracted_w1_t2_extract.py`：[c02]～[c05] 純 Python（prompt 無姓名、JSON 解析容錯、quote 比對、item_key 穩定、敏感度、客戶正規化、發言人規則、S3 掃描、整段後處理含失敗情境），[c07] 本機 Spark（段落選取含 retry_failed、流水號、supersedes；schema 取自 002 spec）。不打 LLM。
