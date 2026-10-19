# meeting_extracted_w1_t1_clean

W1（中立層週跑）的第二支 task：**T1-b 分段 → token 化 → 分類 → 段層去重**。規格 PM_Head `metting_record/01_meeting_to_sales_brief_進階規劃.md` v0.4.1 §4.1 (b) 4–7、(c)、(d)、(e)；偏離處見 `../meeting_extracted_migration/STATUS.md` D13、D16–D18。全是規則、無 LLM。

- 輸入：`s_meeting_record_mail_bu`（`body_display` 與標頭欄）、`s_meeting_participants_bu`（token 對照）、`s_semantic_entity_alias` / `s_semantic_entity`（hint 用）
- 輸出：`s_meeting_record_clean_bu`（本批 pk DELETE 後 append；鍵 `pk_seq, segment_no, sub_no`）；表由 002 建
- 參數（widgets）：`catalog`、`schema`、`run_mode`（incremental / backfill）、`date_from` / `date_to`（backfill 用，對 `mail_date`）、`unit`、`cleaner_version`（預設 0.1）、`sample_limit`、`dry_run`（預設 true）
- 增量：不設水位。mail 表有而清洗表沒有的 pk、mail 表 `cleaned_at` 比清洗表新的 pk、清洗表 `cleaner_version` 不同的 pk 都算本批。
- 排程：W1 每週一，接在 `meeting_extracted_w1_t1_mail` 之後（同一 Job 第 2 個 task）。首次 `run_mode = backfill`，先 `dry_run = true` 看 [c12] 關卡，再 `false`。
- 負責人 / 更新日期：（填）/ 2026-10-15

## 規則摘要

| 步驟 | cell | 規則 |
|---|---|---|
| 不分段的信 | [c10] | `body_source_field = none`、`dup_of_pk` 非 NULL（整封重複）、`oversize` 直接跳過，不寫段 |
| 分段 | [c04] `split_segments` | 有標頭區塊 → thread：每個區塊（含緊接在前的 `-----Original Message / Appointment-----` 行）起一段，`segment_date` = 該段 `Sent:`；沒有 → 紀要：行首型號 `^[BMT]\d{3}[A-Z]{3}\d{2}\.…` 為界，`ITEM` 行後的 `m月d日` 給其後各段當日期（年取 `mail_date`，晚於 mail_date 超過 7 天視為去年）；都切不開 → 整筆一段 0。段 0（第一個界線前的文字）清洗後 < 150 字不留。取不到日期 → `mail_date` 且 `date_inferred = true`。`segment_no` = 文件順序（D13） |
| 標頭改寫（規則 4） | [c05] `rewrite_header` | `<Pnn>:`（token 來自參與者表該段的 `from` 列）＋ `Sent: yyyy-mm-dd hh:mm` ＋ `Subject:`；To / Cc / Bcc / When / Where 刪 |
| token 化（規則 5） | [c05] `build_token_map` / `apply_tokens` | 參與者表該 pk 的每個人：原字串、中文名、英文名、「姓, 名」、email → `<Pnn>`；群組只換 email → `<Gnn>`；轉寄人帳號 → `<P01>`、工號刪。長字串先換；ASCII ≥ 3 字且前後不接字母數字（單字區分大小寫），中文 ≥ 2 字 |
| 殘留 email（D20） | [c05] | token 化後仍有 email 樣式（簽名檔、非標頭區塊的收件列、IMCEAEX 尾巴，參與者表沒有）→ 遮成 `[email]`；[c12] 印 `emails_masked`，不擋 |
| 版面殘渣（D21） | [c05] `strip_urls` / `drop_junk_table_rows` / `first_name_patterns` | 裸網址 → `[url]`、外連圖 → `[image]`；md 表格列每格都是空 / `---` / `[url]` / `[image]` → 整列刪；「英文名第一個字 ＋ 空白 ＋ 該人 token」→ token（簽名檔「Alex 王小美」）。轉寄人簽名檔段 0 因此 < 150 字不留 |
| 攤平（規則 6，D16） | [c05] `flatten_short_lines` | 連續 ≥ 8 個短行（≤ 20 字，可夾空行）併成一行用 ` \| ` 分隔；不猜表頭 |
| 簡轉繁（規則 7，D17） | — | Phase 1 不做（cluster 無 OpenCC）；`clean_text` 保留原字 |
| `content_type` | [c05] `classify` | 依序：`ITEM` / ≥ 3 型號 / 「meeting minutes」且 ≥ 800 → `inline_minutes`；thread 段 ≥ 300 → `thread_reply`；有 `When:` 且 < 300 → `appointment`；< 300 且有附件或「如附件」→ `attachment_only`；< 150 → `noise`；150–300 無其他訊號：thread 段 `thread_reply`、有型號 `inline_minutes`、否則 `noise`（D18） |
| hints | [c05] `customer_hint` / `app_hint` | 客戶：別名表 name / sb_brand（side = customer）命中數，主旨 ×3，長別名先吃（Samsung VD ≠ Samsung），平手 NULL。應用：型號前綴 → 尺寸＋Hz 語境 → 主旨關鍵字 → 客戶預設（單一 app）→ NULL |
| `parties` | [c05] | 該段參與者的 email 網域（thread 段用該段標頭、其他用頂層）＋ 段內出現的 email 網域 |
| 去重 | [c05] `content_hash_of`、[c06] `with_dup_of` | `content_hash = sha1(normalize(clean_text 抹掉 token 編號))`（D21：`<P02>` → `<P>`，不同信的編號不同；< 150 字 NULL）；同 hash 取 `(create_date, pk_seq, segment_no, sub_no)` 最早者，其餘 `dup_of = pk-seg-sub`；候選池含表中既有正本段 |
| `sub_no` | — | §11.1 Phase 1 不切，一律 0；> 12k 字的段只在 log 計數 |

## 關卡（[c12]）

會停：本批 0 段；**`clean_text` 殘留參與者姓名**（S3 硬規則；email 已在 [c05] 全數換 token 或遮掉，[c30] 寫入後再用 SQL 查一次）；`dup_of` > 80%。[c11] 把本批 pk 先 collect 到 driver 釘住（2026-10-19：原本 `_w1_clean_batch_pks` 是 lazy view，寫表後 [c30] 再求值變 0 筆，關卡在空集合上通過）。只印：`emails_masked`、跳過的信（none / 整封重複 / oversize）、每封段數、`content_type` 分布、可萃取段數、壓縮率、`clean_len` P50 / P95、超長段、`date_inferred` 比例、hint 覆蓋率。

## 測試

`tests/test_meeting_extracted_w1_t1_clean.py`：[c03]～[c05] 純 Python（thread / 紀要分段與偏移、ITEM 日期、標頭改寫、token 化三種寫法與誤殺防護、攤平、分類、hints、殘留檢查），[c06] 用本機 Spark 跑整條 pipeline（schema 直接取自 002 的 spec、參與者列來自第一支的 UDF）。假資料全部虛構。另有一條比對本支 [c03] 與第一支 [c04] 的 `find_header_blocks` 結果一致。
