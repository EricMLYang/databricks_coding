# meeting_extracted_w1_t1_mail

W1（中立層週跑）的第一支 task：**T1-a 取數 → T1-m 初洗 → T1-c 參與者**。規格 PM_Head `metting_record/01_meeting_to_sales_brief_進階規劃.md` v0.4.1 §4.0 / §4.0b / §4.1b；偏離處見 `../meeting_extracted_migration/STATUS.md` D10–D14。全是規則、無 LLM。

- 輸入：`b_internal_meeting_record`（含 `mail_body_html`，**只在三個文字欄都沒正文時當備援**，D29）、`s_semantic_entity_alias` / `s_semantic_entity`（001 建）
- 輸出：`s_meeting_record_mail_bu`（MERGE on `pk_seq`）、`s_meeting_participants_bu`（本批 pk DELETE 後 append）；表由 002 建
- 參數（widgets）：`catalog`、`schema`、`source_table`、`run_mode`（incremental / backfill）、`date_from` / `date_to`（對 `mail_date`；backfill 與首跑用）、`unit`（預設 bu）、`cleaner_version`（預設 0.2）、`sample_limit`（開發用）、`dry_run`（預設 true）
- 增量水位：mail 表的 `max(create_date)`；`cleaner_version` 不同的舊列也會被重洗。
- 排程：W1 每週一。首次：`run_mode = backfill`、`date_from = 2026-06-01`，先 `dry_run = true` 看 [c12] 關卡，再 `false`。
- 負責人 / 更新日期：（填）/ 2026-10-19

## 規則摘要

| 步驟 | cell | 規則 |
|---|---|---|
| 來源選擇 | [c03] `choose_body` | 依 md → `mail_without_fw` → `mail_body` 順序取**第一個初洗後 ≥ 150 字**的文字欄；三個都不到才把 `mail_body_html` 轉文字（`html_to_text`）再初洗，≥ 150 字就用（`body_source_field = mail_body_html`）；四個都不到取初洗後最長的非空者；全空 → `none`（0.2，D28 / D29。0.1 是「md 不到 150 字就用非空的 `mail_without_fw`」；ETL 對 146 封信三個文字欄都只剩 Word 屬性殘渣，正文只在 HTML） |
| HTML → 文字 | [c03] `html_to_text` | 只用 stdlib regex：刪 `<head>` / `<style>` / `<script>` / 條件註解（**沒關閉的一律吃到結尾**：ETL 截斷的 HTML 停在 `<style><!--` 中間，整封視為無內容，否則幾萬字 CSS 會變正文）；原始碼換行視為軟換行；`</p>` `</div>` `<br>` `</tr>` → 換行、`</td>` → ` \| `（`<tr>` 起手 `\| `，成 md 表格列）；`<img data:…>` → `[image]`、cid 圖刪；`<a>` 留文字；其餘標籤刪；entity 還原。Outlook 空段落會變空白行、`<b>From:</b> … <br>` 變純文字標頭行，[c04] 標頭規則接得上 |
| 初洗 | [c03] `clean_display` | HTML entity、U+00A0；刪 `![…](cid:…)`；base64 圖片 → `[image]`；`[文字](網址)` → 文字；Word / CSS 殘渣行（0.2：加 `<!--` / `-->` / `/* … */` 獨立行；整行刪只限 400 字內的行）；免責 / ESG / 外部信警語**從命中行起到段尾**刪（0.2；0.1 整段刪，HTML 轉出的文字段落間常沒空行會連坐正文）；四個來源欄都套 |
| 一致性 | [c03] `body_conflict` | 選用來源 vs 其他非空來源：token Jaccard < 0.3 且客戶集合不相交 → true（不擋） |
| 去重鍵 | [c03] `body_hash` | `sha1(normalize(body_display))`，normalize = NFKC、去標點空白、小寫；< 150 字 NULL |
| 標頭區塊 | [c04] `find_header_blocks` | md `**From:**` 與純文字行首 `From:` 兩種；From 起到下一 From 前的 Sent / To / Cc / Bcc / Subject / When / Where；只有 From 沒 Sent 也沒 Subject 不算；回傳字元偏移（T1-b 分段共用） |
| 日期 | [c04] `parse_datetime` | 英文長格式（星期、秒可有可無）與 `yyyy年m月d日 上午/下午 h:mm`；`When:` 取區間開始 |
| 參與者 | [c05] | 轉寄人 = `P01`（永遠第一個）；頂層 to / cc / bcc 為 segment 0；第 n 個標頭區塊 = segment n（文件順序）；辨識鍵 email → 中文名 → 英文名；群組（全大寫、PM / Team / HQ.）用 `Gnn`；IMCEAEX 假位址 email 設 NULL |
| side / company | [c06] `resolve_side` | `email_domain` 後綴比對別名表，最長命中優先；轉寄人一律 auo；entity side = ignore → unknown |
| mail 層去重 | [c06] `with_dup_of_pk` | 同 `body_hash` 取 `create_date` 最早者為正本；候選池含表中既有列 |

## 關卡（[c12]）

會停：本批 0 封；`body_conflict` > 10%；`mail_from` 解析 < 95%。只印：md 比例、來源分布、`has_headers` 比例、`display_len` P50 / P95、壓縮率、oversize、`dup_of_pk` 比例、`side = unknown` 比例、對不到的網域 top 20（> 20% 時提示補 001 [c05]）。

## 測試

`tests/test_meeting_extracted_w1_t1_mail.py`：[c02]～[c05] 純 Python（標頭兩種格式、token 合併、日期、初洗規則），[c06] 用本機 Spark 跑整條 pipeline（schema 直接取自 002 的 spec）。假資料全部虛構。
