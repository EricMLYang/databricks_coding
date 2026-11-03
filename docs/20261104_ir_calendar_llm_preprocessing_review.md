# ir_calendar 檢討：LLM 前要不要多幾個程式處理步驟（文件長文瓶頸）

日期：2026-11-04｜對象：`jobs/ir_calendar`（parse_documents → build_ir_report）｜對照：`jobs/meeting_record` 的分步設計（`OVERVIEW.md`）
結論先講：**要，加三步（兩步程式、一步小 LLM），不用做到 meeting_record 那麼細。** 現在的瓶頸不是錢，是「截尾丟掉了最需要的段落」；錢是第二個問題，三視角之後會放大三倍。

## 1. 現況：文件是怎麼進 LLM 的

```
consume_batches  Volume 落檔（PDF / HTM）
parse_documents  ai_parse_document 逐檔 → bronze payload → silver s_document_text（一檔一列 text_md 全文）＋ s_document_element（一元素一列：type / page / content）
build_ir_report  [c09] 讀 text_md 全文 → [c05] pack_documents：依 DOC_KIND_PRIORITY（逐字稿 > 簡報 > 新聞稿 > 財報）排序，
                 每檔 text[:40000]、合計 120,000 字就停（截尾／略過只在來源節標示）→ 一次 LLM（sonnet，max_tokens 12k）
                 → 結論、事實、展望、判讀、財報重點、事業群表、法說七節、Q&A、caveats 全部一次產出 → gold + HTML
```

實際文件長度（範例財報 bundle 與 2026-11-03 沙箱）：

| 文件 | 頁數 | 解析字元 | 進 prompt 的字元（現行上限 40,000） |
| --- | --- | --- | --- |
| 台股合併財報 PDF（長興 / 奇美 / 永光） | 44–70 | 99k–152k | 前 40k，**後 60–110k 被截掉** |
| Corning 10-Q（EDGAR htm） | 46 | 148k | 前 40k |
| Corning 簡報（EX-99 htm） | 20 | 53k | 前 40k |
| 南亞簡報 PDF | 15 | 9.5k | 全進 |

## 2. 瓶頸到底在哪（三件事）

**2-1 截尾是「照位置切」，切掉的正是報告要的段落。**
台股合併財報的順序固定：核閱報告 → 四大表 → 附註一～六（沿革、會計政策、重要會計項目說明，這三節占全文六到七成，全是樣板）→ 附註七～十三（關係人、質押、承諾、期後事項）→ **附註十四 部門資訊**（事業群營收與損益，模板第 03 節與 01 節後兩格要的）。
`text[:40000]` 剛好餵到會計政策就停，部門資訊永遠在被截掉的那一段。10-Q 也一樣：MD&A（管理層討論，最有價值的敘事）在財務報表附註之後，40k 進不到。
所以「01 財報重點後兩格缺事業群數字」不只是爬蟲沒抽到，Databricks 端是**付了解析費、文字也在 silver 裡，但 LLM 沒看到**。
11-03 決定財報不限頁、整份解析之後，這件事只會更明顯（文字更長、截得更多）。

**2-2 一次大呼叫把「讀文件抽事實」和「寫判讀」綁在一起。**
- 輸入 120k 字 ≈ 6–9 萬 token（中文接近一字一 token、markdown 表格更多），sonnet 一次 USD 0.2–0.3；JSON 壞或 max_tokens 截斷要重打時，[c11] 把整個 user prompt 再送一次，費用翻倍。
- 三視角（supplier / peer / semi）各是一次呼叫，同一家公司同一批文件送三次；192 家 × 4 季若多視角，一年量級 USD 1,000 上下。不是大錢，但九成 token 花在讓模型讀會計政策樣板。
- LLM 的輸出又被要求「不得編數字、引用標來源」，可是它讀的是沒有頁碼／元素 id 的連續文字，來源只能標到檔名，驗不了。

**2-3 同一份內容已經有兩道 LLM。**
爬蟲端 `summarize_ir`（VM、Copilot sonnet-5.5、帶網搜）已經對簡報＋媒體做了結構化彙整（`management_views` / `business_segments` / `qa_highlights` / `headline_metrics`），Databricks 端 `build_ir_report` 又把簡報全文餵一次要 LLM 再填同樣的欄位，規則 9 說「彙整只是參考、以原文為準」。兩邊都在抽，誰是正本沒有定。

## 3. 和 meeting_record 的分步比一比：哪些值得學、哪些不用

meeting_record 之所以切成 W1 三個 task ＋ Stage A/B ＋ T3–T5，是因為：來源髒（轉寄信、人名、重複）、要去識別、條目要原子化給 PM 逐條審、每條要承接審核。ir_calendar 沒有這些：文件是公開的、結構固定、一家一季只有 2–4 份、沒有人名問題、沒有逐條人工審核。所以**不需要九步，但 meeting_record 的核心分工原則完全適用**：

| meeting_record 的原則 | ir_calendar 現況 | 要不要學 |
| --- | --- | --- |
| 清洗、切段、分類是規則（task 1 / 2），LLM 不碰 | 沒有切段；全文直接進 prompt | **要**：財報／10-Q／簡報的章節結構比會議紀錄規整得多，規則切段更容易 |
| LLM 一段一次、只做「讀懂一段話拆成事實」（task 3） | 一次讀 3 份文件、同時寫 7 節＋結論 | **要**：拆成「每份文件抽事實」與「每份報告寫判讀」兩層 |
| quote 必須存在於 clean_text，LLM 改寫就作廢 | 來源只標檔名，無法驗 | **要**：抽取結果帶 element_id / page，程式驗 quote 在元素內容裡 |
| 不送的東西明講（noise / 重複段不送） | 截尾只在來源節標「已截尾」 | **要**：略過的段落記表，報告列「略過：附註四 會計政策 …」 |
| 關卡 [c12]、閘門 `max_segments`、`dry_run`、golden set | 有 `max_reports` / `dry_run`，無 golden set | 關卡要；golden set 等 prompt 要升版再做 |
| 去識別、三分法鏡頭、PM 逐條審、Stage B 台帳 | — | 不用 |

## 4. 建議的分步（在 parse_documents 與 build_ir_report 之間加一支 notebook）

```
parse_documents（不限頁，不改）
   │ s_ir_calendar_document_element
   ▼
digest_documents（新；一支 notebook、三個步驟，一個 job task）
   ├─ 步驟 1 切段分類（規則）  element → section：依標題字典 + 元素型別把每份文件切成章節，標 section_kind
   ├─ 步驟 2 挑段落（規則）    依 doc_kind × section_kind 的保留表決定 keep / skip（＋理由），每份有字元預算；表格只留保留章節內的
   └─ 步驟 3 文件摘錄（LLM）   每份文件一次：只送 keep 的段落，固定 JSON 抽事實（事業群數字、指引、產能、Q&A、AUO 相關、期後事項），
                              每條帶 element_id；程式驗 quote 在該元素內 → bronze b_…_document_digest_llm（原始回應）→ silver s_…_document_digest
   ▼
build_ir_report（改）  讀 s_financials ＋ s_summary（爬蟲彙整）＋ s_document_digest（不再讀 text_md 全文）→ 一次 LLM 只寫結論與判讀
```

**步驟 1 切段分類（規則）**——`DataFrame -> DataFrame` 純函式，可測：
- 章節邊界：`element_type` 為標題類（D1-2 先確認 ai_parse_document 的型別名；HTML 路徑 [c03a] 本來就有 h 標籤）；沒標題型別時退用「短行＋符合標題字典」。
- 標題字典（中英各一組 regex）→ `section_kind`：
  `statements`（資產負債表／綜合損益表／現金流量表／Balance Sheets／Statements of Operations）、`accounting_policy`（重大會計政策／Significant Accounting Policies）、`account_notes`（重要會計項目之說明／Notes 的逐科目）、`segment`（部門資訊／營運部門／Segment Information）、`related_party`、`commitments`（承諾及或有事項／Commitments and Contingencies）、`subsequent`（期後事項／Subsequent Events）、`mdna`（Management's Discussion and Analysis）、`risk`（Risk Factors）、`controls`、`exhibits`、`outlook`（展望／Guidance／Outlook）、`capacity`（擴產／產能）、`qa`（Q&A／Questions and Answers）、`disclaimer`（Safe Harbor／前瞻性聲明）、`reconciliation`（非 GAAP 調節表）、`other`。
- 輸出表 `s_ir_calendar_document_section`：`(volume_path, sha256, section_no)`、`section_kind`、`title`、`page_from/to`、`element_ids`、`chars`、`keep`、`skip_reason`、`rule_version`。

**步驟 2 挑段落（規則）**——保留表（第一版，之後照 D1-2 看到的真資料調）：

| doc_kind | 保留 | 略過（記理由） | 每份預算 |
| --- | --- | --- | --- |
| Financial_Statements（台股 PDF） | `segment`、`subsequent`、`commitments`、`related_party`（只留表）、核閱報告的保留意見段 | `statements`（數字已在 s_financials）、`accounting_policy`、`account_notes`、質押明細 | 10–15k 字 |
| Financial_Statements（10-Q / 10-K htm） | `mdna` 全段、Notes 的 `segment` / `commitments` / `subsequent` | 財務報表本體、`controls`、`exhibits`、`risk`（10-K 的風險因子太長，只留標題清單） | 30–40k 字 |
| Presentation / Press_Release | 除 `disclaimer`、`reconciliation` 外全留；有 `outlook` / `segment` / `capacity` 的頁排前 | 前瞻聲明頁、GAAP 調節表 | 30–40k 字 |
| Earnings_Transcript（爬蟲 `wanted` 加 transcript 之後） | prepared remarks ＋ Q&A 全留，按發言者切 | 接線生開場、免責 | 50–60k 字；超過時 Q&A 優先 |

合計一家一季 ≤ 60k 字（現在 120k），而且**沒有一段是因為位置被截掉的**。被略過的章節連同理由存表，報告來源節改列「已讀 n 段／略過 m 段：附註四 會計政策（樣板）、…」。

**步驟 3 文件摘錄（LLM，每份文件一次）**：
- 輸入：該文件 keep 段落（帶 `[e123 p.37]` 標記）＋ 結構化財報數字（只給對照用）。
- 輸出固定 JSON：`segments[]`（事業群／產品線：名稱、營收原文字串、YoY、利潤率、cite）、`guidance[]`、`capacity[]`、`business_lines[]`、`investment[]`、`qa[]`、`auo_mentions[]`、`subsequent_events[]`、`key_numbers[]`（文件裡提到的數字，含期別與口徑）、`caveats[]`；每條 `cite = [element_id]`。
- 程式驗證：cite 的元素存在、引用的數字字串出現在該元素內容裡（學 meeting_record 的 quote 三層比對）；不過就標 `unverified`，不丟。
- 存法：bronze `b_ir_calendar_document_digest_llm`（每次呼叫一列、原始回應、input/output token）＋ silver `s_ir_calendar_document_digest`（鍵 `volume_path, sha256, prompt_version`）。**同一份文件三個視角共用一份摘錄**，文件不變就不重抽。
- 模型：先 sonnet-5.5；這一步是「抽取＋逐字引用」不是判讀，等有 golden set 再試 haiku。system prompt 走 `cache_control`。

**build_ir_report 改法**：[c05] `pack_documents` 換成 `pack_digests`（摘錄 JSON 轉成文字段落，每條帶 cite）；prompt 規則 4 改成「引用只能來自結構化數據、爬蟲彙整或文件摘錄，並標 cite」；[c07]／[c07a] 來源節加「已讀／略過章節」清單；暫留 widget `use_full_text`（預設 false）讓過渡期可以 A/B 同一家公司兩種餵法。prompt 升 2.3。

**數字交叉核對（backlog D3-4）**：留在程式。步驟 3 回來的 `key_numbers` 與 `s_financials` 對同一期別、同一科目比，差異超過 1% 標 `mismatch` 給報告的 caveats；LLM 不做裁決。爬蟲 `headline_metrics` 的自結數同一套規則。

## 5. 爬蟲彙整 vs Databricks 摘錄：誰是正本

建議分工（寫進 README 與 prompt）：
- **爬蟲 `ir_summary`**：法說「當下」的彙整——簡報＋媒體＋逐字稿摘要，有網搜、有媒體說法不一的備註；沒有文件（奇美、永光）時它是唯一來源。
- **Databricks `document_digest`**：文件本文的逐段抽取，有 element 級出處、可程式驗證；文件到了就以它為準。
- `build_ir_report` 兩者都讀，規則：**同一主題文件摘錄 > 爬蟲彙整**，彙整只補文件沒有的（媒體、逐字稿）；衝突時兩者並列、標來源，不裁決。
這樣簡報就不會被兩邊各讀一次：爬蟲端讀的是簡報 PDF 文字（VM 端自己解析，品質不穩，南亞 Q3 就「簡報 PDF 無法解析」），Databricks 端讀的是 `ai_parse_document` 的結果；真正重疊的是簡報一份，可接受。

## 6. 費用與品質預期

| | 現在 | 加三步之後 |
| --- | --- | --- |
| 每家每季 LLM 輸入 | 120k 字 × 視角數（1–3） | 摘錄：每份文件 10–40k 字一次（3 視角共用）；報告：每視角 10–15k 字 |
| 重試成本 | 整包 120k 再送一次 | 摘錄失敗只重送那一份；報告重試只有 10–15k |
| 部門資訊、MD&A、期後事項 | 多半在被截掉的尾段 | 一定進 prompt |
| 引用可驗證 | 只到檔名 | element_id ＋ 程式驗 quote |
| 略過的內容 | 來源節一行「已截尾」 | 逐章節列理由 |
| 解析費（ai_parse_document 按頁） | 不變 | 不變（不限頁是 11-03 的決定；省的是 LLM 端） |

金額上一視角的差別不大（都是每家每季零點幾美元），**三視角與重試才是倍數**；真正的收益是 2-1 的正確性。

## 7. 落地順序（小步、每步可驗）

1. **D1-1 / D1-2 先做**（Databricks 上跑 `parse_documents` 三份：台股財報、10-Q、簡報）：確認 `element_type` 有哪些值、標題能不能辨識、每頁字元數。章節規則靠這個，沒看到真資料前不要寫死字典。
2. **規則原型可以先在本機做**：2026-11-03 沙箱抓到的 Corning / 3M 10-Q 與 EX-99（htm）走 [c03a] html_text 就有元素；台股 PDF 等 D1-2。寫 `split_sections()` / `select_sections()` 純函式＋`tests/test_ir_calendar_digest.py`，先用這四份當測資。
3. **新 notebook `ir_calendar_digest_documents`**（從 `jobs/_template/` 複製）：[c03] 純規則、[c05] 摘錄 prompt、[c08] 沿 build_ir_report 的 llm_client、[c10] bronze/silver 寫入、[c12] 關卡（每份 keep 字元 ≤ 預算、skip 理由全有、JSON 失敗 < 10%、cite 驗證失敗 < 15% 才往下）、閘門 `max_docs` / `dry_run`；`init_tables` 加兩張表。
4. **build_ir_report 接摘錄**（prompt 2.3、`use_full_text` 過渡 widget），同一家公司兩種餵法各跑一次比結論與事業群表，再把預設切過去。
5. 爬蟲端配合（不擋）：`wanted` 加 `transcript`；`ir_summary` 的 `sources[]` 標哪些是簡報、哪些是媒體，讓規則 5 的「文件 > 彙整」有依據。

這五步做完，parse_documents 的「不限頁」才真的有意義：解析出來的每一頁都有機會被用到，而不是付錢解析再丟九成。
