# jobs/ir_calendar HANDOFF — 現況與接續點

給下一次任務或其他 Agent 的接續資訊。靜態說明（用途、參數、表設計）在各 `README.md` 與 `docs/`，這裡只記**動態狀態**：
Databricks 上貼到哪一版、還沒貼什麼、爬蟲端告警現況、下一步。每次改完 Databricks 更新本檔 §0 與 §1。

## §0 接續點（2026-10-29 中斷於步驟 6b：Databricks 已貼到 20261029b、render_only 已跑、**驗證 SQL 尚未貼回**）

**下次接續先做**：(1) 跑下面步驤 6b 的驗證 SQL，三個布林應 true、`template_version = 20261029b`；用 `displayHTML` 看南亞 Q3 報告第 01 / 02 節。(2) 步驟 7（同參數再跑應 0 列）→ 8（視角 dry_run）→ 9（TPE:1763、TYO）→ 10（排程）。(3) 爬蟲端：財報整檔重發（§0.3）、建議文件（§4-1）。MI_Crawler repo 的 `doc/20261029_給爬蟲端_…建議.md` 與 HANDOFF §0 補記**尚未 commit**（那是另一個 repo）。


### 0 本次要複製的清單（2026-10-29 合併 10-28 與 10-29 全部未貼項目；照順序做，做完把 ✅ 補上、§1 改成已貼）

repo 狀態：工作樹含 10-29 全部改動、未 commit；三支測試檔最後一次全綠（consume 46、parse 19、report 40）。
比對 / 複製方法：`python tools/nb.py export jobs/ir_calendar/<nb>/notebook.ipynb <tag>` 直接複製整個 cell；整支匯入用 Databricks「Import」選 repo 的 `.ipynb`。

| 步驟 | notebook | cell | 動作 | 貼完做什麼 / 預期 | 狀態 |
| --- | --- | --- | --- | --- | --- |
| 1 | `init_tables` | [c19a] ddl_b_ir_report_llm | 替換整個 cell | 不用跑（既有表） | ✅ 10-29 |
| 1 | `init_tables` | [c19b] ddl_g_ir_report | 替換整個 cell | 不用跑（既有表） | ✅ 10-29 |
| 1 | `init_tables` | [c21] add_columns | 替換整個 cell | 整支跑一次（`CREATE TABLE IF NOT EXISTS` 不動既有表）。[c21] 輸出應有：`add …b_ir_calendar_ir_report_llm：[report_kind]`、`add …g_ir_calendar_ir_report：[source_periods, summary_batch_id, docs_fed, report_kind, topics]`、`comment …g_ir_calendar_ir_report：[docs_digest]`；gold 0 列所以沒有 backfill 行。再跑一次全部 `ok 欄位已齊` | ✅ 10-29 已跑，輸出與預期相同（gold 五欄、bronze report_kind、comment 兩組） |
| 1b | `init_tables` | [c02] imports、[c19a] ddl_b_ir_report_llm、[c19b] ddl_g_ir_report、**新增 [c19c] rename_tables（插在 [c19b] 之後）**、[c21] add_columns | 替換整個 cell / 新增 | **10-29 改名 supplier_report → ir_report**（報告含 peer / semi 視角）。整支再跑一次：[c19c] 應印 `renamed …b_ir_calendar_supplier_report_llm → …b_ir_calendar_ir_report_llm` 與 gold 同款；[c20] 全部 `ok`；[c21] 全部 `ok 欄位已齊`（欄位在步驟 1 已加好，改名不影響） | ✅ 10-29（由步驟 6 成功讀寫 `g_ir_calendar_ir_report` 反推） |
| 2 | `consume_batches` | [c06] transform_silver | 替換整個 cell | — | ☐ |
| 2 | `consume_batches` | [c09] io_delta | 替換整個 cell | `rebuild_silver = true` 跑一次（其他參數同 job）。查 `s_ir_calendar_summary` 的 `TPE:1303` 2026Q2 應是 9-21 批次 `000002`（豐富度 = management_views / business_segments / qa_highlights / headline_metrics / key_numbers / core_points / risks 七欄的 size 合計；9-21 批次早於 10-10 的結構化欄位，`management_views` 本來就 NULL，看 `core_points` / `key_numbers`）。**避開排程時段** | ✅ 10-29 已跑：2026Q2 = `000002_20260921`（core_points 6 條，勝過 9-24 的 1 條）、2026Q3 = `000024_20261013`；`management_views` 皆 NULL 是爬蟲端 VM 版本未產結構化欄位（§4-2 已查清） |
| 3 | `parse_documents` | [c02] imports | 替換整個 cell | — | ☐ |
| 3 | `parse_documents` | [c03] pure_helpers | 替換整個 cell | 先 `dry_run = true` 跑；之後新解析的 `Financial_Statements` 在 bronze `parse_options` 應含 `pageRange: 1-30`。短於 30 頁的 PDF 會不會報錯看 bronze `status` | ☐ |
| 4 | `build_ir_report` | 整支 | 整支匯入（Databricks 上原本沒有），notebook 名稱 **`ir_calendar_build_ir_report`**（10-29 自 build_supplier_report 改名） | job parameters：`views = supplier`、`lookback_quarters = 0`、`max_reports = 1`、`dry_run = true`，**沒有 `prompt_version`**；`api` 類參數同其他 ir_calendar job；LLM secret `llm-api-keys/ms-foundry` | ✅ 10-29 已匯入 |
| 5 | `build_ir_report` | — | `dry_run = true`、`company_keys = TPE:1303` | 工作清單一列：`supplier  SUPPLIER  TPE:1303  Nan-Ya  2026Q3  1 檔 ['Presentation']  彙整=2026Q3`（或 `彙整=無`），**不得**出現「前期補位」；dry_run 行有 `system_chars`、每份文件餵入狀態、落地路徑 `…/reports/supplier/<slug>/<slug>_2026Q3_supplier_report.html` | ✅ 10-29：`supplier SUPPLIER TPE:1303 Nan-Ya-Plastics 2026Q3 1 檔 ['Presentation'] 彙整=2026Q3`；financials annual=5 quarterly=4、速動比=無、summary views 0/6（10-13 批次無結構化欄位）、docs=1 full 9,518 字、prompt_chars 11,528、system_chars 2,043；slug 實際是 `Nan-Ya-Plastics` |
| 6 | `build_ir_report` | — | `dry_run = false`、`max_reports = 1`、`company_keys = TPE:1303` | 開 Volume HTML 看章節 01–07 與「採購建議」四面向；gold 一列 `report_kind = supplier`、`topics = []`；bronze 1～2 列 `report_kind = supplier`、`prompt_version = 2.2` | ✅ 10-29 04:52 UTC：1 / 1 ok，LLM 1 次 success（in 8,263 / out 3,431 tokens，prompt 11,528 字）；gold 1 列 supplier / 2.2 / 20261029、html 66,184 字、topics 0；[c30] rows=1 dup_keys=0；HTML 在 `…/reports/supplier/Nan-Ya-Plastics/Nan-Ya-Plastics_2026Q3_supplier_report.html`（內容檢視待使用者回饋） |
| 6b | `build_ir_report` | [c02] imports、[c03] pure_facts、[c07] render_html | 替換整個 cell | **10-29 看完南亞報告後的修正（template 20261029b）**：本期季報未公告時第 01 / 02 節與法說節財報對照退用「最新已公告季」並標示（南亞 Q3 報告原本整欄「未取得」）；頁首無財報檔案時寫「本期財報尚未公布（無財報檔案）」。貼完 `render_only = true`、`company_keys = TPE:1303` 跑一次（不呼叫 LLM，用 gold 的 llm_json 重套版）：第 01 節應出現「最新已公告季：2026 Q2」、第 02 節標題帶「（最新已公告季 2026 Q2）」、gold `template_version = 20261029b` | ◐ 10-29 已貼三個 cell、render_only 已跑；驗證 SQL 待貼：
`SELECT template_version, html_chars, html LIKE '%最新已公告季：</b>2026 Q2%' AS a, html LIKE '%02　財報實績（最新已公告季 2026 Q2）%' AS b, html LIKE '%本期財報尚未公布（無財報檔案）%' AS c FROM micenter.mi3_datahub_prod.g_ir_calendar_ir_report WHERE company_key = 'TPE:1303' AND period = '2026Q3'` |
| 7 | `build_ir_report` | — | 再跑一次同參數 | 工作清單 0 列（來源沒變就跳過） | ☐ |
| 8 | `build_ir_report` | — | `dry_run = true`：`views = peer` + `company_keys = TPE:3481`；`views = semi` + `TPE:2330`；`views = supplier,semi` + `TPE:2330` | 群創一列 `peer`；台積電一列 `semi` 帶 `題目 A/C`；第三組兩列（同雜湊）。只看清單，不產 | ☐ |
| 9 | `build_ir_report` | — | 無彙整的 `TPE:1763`、無 financials 的 TYO 各一份 | 法說節「未提及」路徑、「未取得」路徑 | ☐ |
| 10 | Workflows | — | 把 `build_ir_report` 接在 `parse_documents` 後（`parse_documents` 也還沒排程） | 排程只跑 `views = supplier`、`max_reports` 先 5；trigger 設定記進 §3 | ☐ |

貼完回來要改：本表 ✅、§1 四支 notebook 的狀態、§3 的實際 trigger；實跑發現的假設不符（§0.0 的三個假設、§0.0a 的兩個邊界）記進 §4。
**不要貼**：`check_landing` / `check_api_status` / `inspect_record`（10-22 已是最新）。

### 0.0a 2026-10-29 行為定案：報告只用當季內容（使用者確認；repo 已改、**尚未貼 Databricks**）

使用者 10-29 檢視 10-28 的跨期補位後定案：**要最新一季的資訊，當季有的內容不同來源都納進來（含 AI 彙整），不要抓到上一季的過時資訊；
再跑時多了新來源就重做，來源沒變就不處理，直到下一季新檔案出現。** 10-28 的補位會把 Q2 財報 PDF / Q2 彙整混進 Q3 報告，彙整退用更沒有期數上限，不符合。

| 改動 | 哪裡 | 內容 |
| --- | --- | --- |
| 期別候選改「文件 ∪ 彙整」 | `build_ir_report` [c04] `build_work` / `select_work` / 新 `slim_summary` | 每家最新一期 = 有文件**或**有彙整的最新期別；當季只有彙整、沒有任何已解析文件也產（`0 檔`）；只有場次日期不觸發。彙整也套 `categories` / `company_keys` 範圍 |
| 彙整只用同期 | [c04] `pick_summary_period` | 不再退用前期 |
| 補位預設關 | [c01] `lookback_quarters` 預設 `0`（機制保留，>0 才補且標期別） | 補位文件只補內容、不讓期別前進 |
| 只有彙整的公司代稱 | [c09] | `s_summary` 沒有 `company_slug` → 退用 `s_company.file_slug`，再沒有就 [c10] 用 `company_key` 當檔名 |
| 沒文件時的呈現 | [c07] `render_sources`；[c03] `source_periods` 含彙整期別 | 來源節列「本期尚無已解析文件」、限制節註明 LLM 沒讀到文件原文；`TEMPLATE_VERSION = 20261029`；prompt 文字不變仍 2.1 |
| 測試 | `tests/test_ir_calendar_build_ir_report.py` | 工作清單改成三個測試（當季為準 + 重做 / 跳過規則、只有彙整 + 下一季換期、補位 opt-in）、Spark 端到端加只有彙整與分類外的彙整、新增只有彙整的 facts / prompt / HTML 測試 |

**同日第四件：看完南亞實跑報告的修正**（[c02] [c03] [c07]，`TEMPLATE_VERSION = 20261029b`，測試 41 綠）：[c03] `build_actuals` 本期季報未公告時退用 ≤ period 的最新季別（`base_period` / `fallback`），[c07] 第 01 節 note、第 02 節標題、法說 03 節財報對照、限制節都標「最新已公告季」；頁首財報公布日在沒有財報檔案時改寫「本期財報尚未公布（無財報檔案）」。財務數字是時間序列，這個退用與文件 / 彙整「只用當季」不衝突。

**同日第三件：改名** `build_supplier_report` → `build_ir_report`（資料夾、notebook、測試檔、gold `g_ir_calendar_ir_report`、bronze `b_ir_calendar_ir_report_llm`；報告不只供應商）。Databricks 上兩張舊名表已建、0 列，由 `init_tables` 新 cell [c19c] `ALTER TABLE … RENAME TO` 改名（步驟 1b）；Volume 路徑本來就不含 supplier，不動。歷史設計文件 `docs/20260921_…lakehouse_design.md` 未改。

**同日第二件：報告視角（supplier / peer / semi）骨架已做進 notebook**（構想 `docs/20261029_ir_calendar_report_views_peer_semi_proposal.md`，使用者定案：semi 加掛名單由 Agent 依友達跨入領域判斷、重疊公司出兩份）：

| 改動 | 哪裡 | 內容 |
| --- | --- | --- |
| 視角常數與對應 | [c02] `REPORT_VIEWS` / `VIEW_BY_CATEGORY` / `VIEW_OVERRIDES`（8 家另掛 semi）/ `SEMI_TOPIC_BY_COMPANY` / `EXCLUDE_FROM_VIEW`（友達不產 peer）/ `company_views()` / `PROFILES`（三視角的 prompt 角色 / 讀者 / 四面向 / 結論焦點 / 版面標題） | 爬蟲分類不動；一家可多視角 |
| 工作清單 | [c04] | 以（公司、期別、視角）為單位，`work` 多 `report_kind` / `topics`；done 依視角 + 該視角 prompt 版；`select_work(views=…)` 取代 `categories` |
| prompt | [c05] `build_system_prompt(view)`、`PROMPT_VERSIONS = {supplier 2.2, peer 1.0, semi 1.0}`；輸出鍵 `procurement_actions` → `actions`（normalize 相容舊鍵）；semi 的題目標籤進 user prompt | widget `prompt_version` 拿掉 |
| 版面 | [c07] `view_titles(facts)`：報告名 / 結論標題 / 面向標題 / 08 節標題依視角；檔名 `<slug>_<期別>_<view>_report.html` | 財報 / 法說 / 來源節共用；peer 的「對手 vs 友達對照表」等視角專屬節**等使用者的模板**再加 |
| 落地 | [c10] gold 鍵 (company_key, period, report_kind)、bronze / gold 多 `report_kind`、gold 多 `topics`；Volume `reports/<view>/<slug>/`；[c11] 流程、dry_run 印視角與題目 | |
| 建表 | `init_tables` [c19a] [c19b] DDL 最後補欄、[c21] `ADD COLUMNS` + gold 舊列回填 `report_kind = supplier` | 表目前 0 列，回填不會動到東西 |
| 參數 | [c01] `categories` → `views`（預設 `supplier`）；`prompt_version` 移除 | |
| 測試 | `tests/test_ir_calendar_build_ir_report.py` 40 個全綠（新增 company_views / 多視角工作清單 / 視角 prompt / 視角版面；Spark 端到端含另掛 semi 與 gold 有無 `report_kind` 欄；DDL ↔ schema 含新欄） | |

**Databricks 替換清單（10-29 合併版，全部未貼）**：`init_tables` [c19a] [c19b] [c21] 替換整個 cell → 跑 [c21]（輸出應有 `add …ir_report_llm：[report_kind]`、`add …g_…ir_report：[source_periods, summary_batch_id, docs_fed, report_kind, topics]`）；
`consume_batches` / `parse_documents` 照 §0.0；`build_ir_report` 整支匯入 repo 現版，job parameters **不再有 `prompt_version`**，`views` 留 `supplier`、`lookback_quarters` 留 `0`。
首次 `dry_run` 看 `TPE:1303`：工作清單應是 `supplier … 2026Q3  1 檔 ['Presentation']  彙整=2026Q3`（爬蟲有 Q3 彙整）或 `彙整=無`，**不該**出現「前期補位」。
視角驗證（第一格「首次上線順序」第 7 步）：`views = peer` + `TPE:3481`、`views = semi` + `TPE:2330`（題目 A/C）、`views = supplier,semi` + `TPE:2330` 兩列。
排程 job 先只跑 `views = supplier`；peer / semi 等使用者給同業 / 半導體模板 HTML 後再補視角專屬節、才放進排程。

### 0.0 2026-10-28 改了什麼（repo 已改、測試全綠、**尚未貼 Databricks**；backlog §D；其中 D2-1 補位已於 10-29 改成預設關、彙整退用已拿掉，見 §0.0a）

起因：`build_ir_report` 一份報告只取同期文件與一份彙整，南亞 `TPE:1303` 2026Q3 只有法說簡報，Q2 財報 PDF 與 Q2 細版彙整（9-21）都進不了報告；文件因長度被略過也沒標示。

| 改動 | 哪裡 | 內容 |
| --- | --- | --- |
| 彙整薄的不蓋厚的（D2-2） | `consume_batches` [c06] [c09] | [c06] 加 `SUMMARY_RICHNESS_COLS` / `summary_richness_sql` / `summary_merge_condition` / `latest_summary`；[c09] `_merge` 多 `update_condition`，summary 用 `latest_summary` 去重、MERGE 條件「來源至少一樣豐富才更新」 |
| 財報本體限頁（D1-3） | `parse_documents` [c02] [c03] | `PAGE_RANGE_BY_DOC_KIND = {Financial_Statements: '1-30'}` → `parse_options` 加 `pageRange`（第三種選項組）。既有 bronze 不自動重解析 |
| 跨期補位 + 來源雜湊 + 餵入狀態（D2-1 / 2-3 / 2-4） | `build_ir_report` [c01] [c02] [c03] [c04] [c05] [c07] [c09] [c10] [c11] + 第一個 markdown | widget `lookback_quarters = 2`；[c04] 改成 driver 端純 Python 規劃（`plan_docs` / `pick_summary_period` / `source_digest` / `build_work`，`select_work` 多收 summary / conference 兩張表、回 list）；[c09] 照 `doc_paths` / `summary_period` 撈；[c03] docs 帶 `period` / `carried`、`source_periods`、`report_date_period`、法說日只在彙整同期才取；[c05] prompt **2.1**（規則 11 前期文件標期別）、文件標題帶期別、`doc_feed_status`；[c07] 來源節標期別與餵入狀態、頁首財報公布日標期別；[c10] gold 多 `source_periods` / `summary_batch_id` / `docs_fed`；[c11] 先打包再 LLM、dry_run 印餵入狀態；`TEMPLATE_VERSION = 20261028` |
| gold 加欄 | `init_tables` [c19b] [c21] | DDL 最後三欄；[c21] `ADD_COLUMNS` 加 gold 一組、`docs_digest` 註解改 |
| 測試 | `tests/test_ir_calendar_{consume,parse_documents,build_ir_report}.py` | 99 個全綠（consume 46、parse 19、report 34）：含南亞型補位、彙整退用、雜湊觸發重做、餵入狀態、薄不蓋厚、三種解析選項分組 |

**Databricks 替換清單（照順序；全部未貼）**

| 順序 | notebook | cell | 動作 | 貼完做什麼 |
| --- | --- | --- | --- | --- |
| 1 | `init_tables` | [c19b] ddl_g_ir_report、[c21] add_columns | 替換整個 cell | 跑 [c21]：輸出應有 `add …g_ir_calendar_ir_report：[source_periods, summary_batch_id, docs_fed]`、`comment …g_ir_calendar_ir_report：[docs_digest]` |
| 2 | `consume_batches` | [c06] transform_silver、[c09] io_delta | 替換整個 cell | `rebuild_silver = true` 跑一次；查 `s_ir_calendar_summary` 的 `TPE:1303` 2026Q2 應是 batch_path 9-21 那份（`management_views` 非空） |
| 3 | `parse_documents` | [c02] imports、[c03] pure_helpers | 替換整個 cell | 先 `dry_run = true`；新解析的 `Financial_Statements` 在 bronze `parse_options` 應含 `pageRange` |
| 4 | `build_ir_report` | 整支（第一個 markdown + [c01]～[c11] [c20] [c30]） | 整支匯入 | job parameters 不再有 `prompt_version`（10-29 內嵌 [c05] `PROMPT_VERSIONS`）；依第一格「首次上線順序」跑 `dry_run` → `TPE:1303` 一份 |

**這次的假設**（之後實測不符就回來改）：
- ~~補位只分兩類（財報本體／逐字稿 + 簡報 + 新聞稿），預設往前 2 期（widget `lookback_quarters`）。~~ 10-29 改成預設 `0`（§0.0a）。
- 彙整「豐富度」= 七個結構化欄位條目數合計；爬蟲若刻意重發條目較少的修正版會被擋，要改得先刪舊列再 `rebuild_silver`。
- 財報本體限前 30 頁是估計值（封面 / 會計師報告 / 四大表）；短於 30 頁的 PDF `pageRange` 超出範圍會不會報錯官方文件沒說，首次跑看 bronze `status`。

未做：D1-1 / D1-2（上線後 SQL 檢查 payload 形狀與每頁字元數）、D2-6（同業 / SEMI 的 prompt 面向待定）。

### 0.1 這次改了什麼（repo 已 commit；Databricks 2026-10-22 已貼步驟 1、2、4，只剩步驟 3 `build_ir_report` **未匯入**）

兩件事同時做：**換報告版面**（`doc/20261021_SCM財報和法說報告html格式v20261007.html` 取代 20261010 版）與**接爬蟲新版欄位**
（MI_Crawler 交代文件 `doc/20261021_給Databricks_notebook開發者_新版SCM報告欄位交代_HANDOFF.md`、規劃 `doc/20261021_爬蟲對齊新版SCM報告版面_規劃與實測.md`）。

| 改動 | 哪裡 | 內容 |
| --- | --- | --- |
| 換爬蟲：silver 加欄 | `init_tables` [c13] [c19] [c21] | `s_financials` 加 21 欄（`cash`、三類流動金融資產、`short_term_investments`、應收／應付（含票據、關係人）、`inventory`、`equity_parent`、`investing_cash_flow_ytd`、`pretax_margin`、`net_margin_parent`、`quick_assets`、`quick_ratio`、`dso_days`、`dpo_days`、`days_basis`）；`s_summary` 加 `reported_period`、`business_segments`、`qa_highlights`；[c21] 對既有表 ADD COLUMNS，另改 5 個既有欄位註解（`management_views.topic` 詞彙換六類） |
| 換爬蟲：silver 轉換 | `consume_batches` [c04] [c06] | `FIN_AMOUNTS/RATIOS` 拆 V1/V2（select 順序照 DDL：V1 → 血緣 → V2）、`days_basis` 字串欄、`SUMMARY_PAYLOAD.summary` 加三鍵；`transform_summary` / `_financial_rows` 的 select 接在最後 |
| 換版面 | `build_ir_report` [c01] [c02] [c03] [c05] [c06] [c07] [c09] [c10] [c11] [c30] + 第一個 markdown | `TEMPLATE_VERSION = 20261021`、prompt **2.0**（無燈號／分數／War Room／Watchlist；法說六主題用爬蟲固定詞彙、事業群六欄）；`INDICATORS` 11 項全接欄位（速動比／應收付天數／母公司淨利率）；第 02 節本季 vs 去年同季＋同比變動；法說 01–06 先用 `management_views`、07 用 `qa_highlights`、03 事業群先用 `business_segments`，缺的才 LLM；頁首財報公布日取 `document_file.doc_date`、法說報告期間取 `reported_period`；[c09] 同期沒彙整退用最近一期；gold `light`/`score` 一律 NULL（DDL 不動）；新模板檔與 `USER_GUIDE.md` 放 `template/` |
| 檢視 | `inspect_record` [c03] | `summary_report` 多印法說報告期間、事業群表、Q&A |
| 測試 | `tests/test_ir_calendar_{consume,build_ir_report,inspect_record}.py` | 86 個全綠（consume 45、report 30、inspect 11）：含 DDL ↔ transform 欄位順序、新欄位值、彙整優先於 LLM、十項圖單欄、標籤不重疊 |
| 範例 | `範例財報/` | 五家用新版面 + 爬蟲新版實測資料的純 Python 版（`build_report.py`），黃底數 Corning 2／南亞 5／長興 3／奇美 14／永光 13；`模板覆蓋度評估.md` |

### 0.2 要複製到 Databricks 的檔案與 cell（照順序）

| 步驟 | notebook（repo 路徑 `jobs/ir_calendar/<資料夾>/notebook.ipynb`） | cell | 動作 | 貼完做什麼 |
| --- | --- | --- | --- | --- |
| 1 ✅ | `init_tables` | [c13] ddl_s_summary | 替換整個 cell | — |
| 1 ✅ | `init_tables` | [c19] ddl_s_financials | 替換整個 cell | — |
| 1 ✅ | `init_tables` | [c21] add_columns | 替換整個 cell | 整支跑一次：輸出應有 `add …s_ir_calendar_financials：[21 欄]`、`add …s_ir_calendar_summary：[reported_period, business_segments, qa_highlights]`、`comment …`；再跑一次全部 `ok 欄位已齊` |
| 2 ✅ | `consume_batches` | [c04] table_schemas | 替換整個 cell | — |
| 2 ✅ | `consume_batches` | [c06] transform_silver | 替換整個 cell | 先 `dry_run = true` 跑一次；再 `rebuild_silver = true` 跑一次（舊批次新欄多為 NULL，正常；爬蟲新版整檔重發後再 rebuild 一次就有值） |
| 3 | `build_ir_report` | 整支（2026-10-28 又改了 [c01] [c02] [c03] [c04] [c05] [c07] [c09] [c10] [c11] + 第一個 markdown） | 整支重新匯入最省事（Databricks 上原本就**未貼**） | 先貼 §0.0a 的 `init_tables` [c19a] [c19b] [c21] 並跑 [c21]；job parameters：`views = supplier`、無 `prompt_version`；依 notebook 第一格「首次上線順序」：`dry_run` → `max_reports = 1`（`TPE:1303`）→ 無彙整的 `TPE:1763` → 無 financials 的 TYO → 視角驗證 |
| 4 ✅ | `inspect_record` | [c03] pure_helpers | 替換整個 cell | 只讀，隨時可貼 |
| 5（10-28） | `init_tables` | [c19b] [c21] | 替換整個 cell，跑 [c21] | gold 補三欄 |
| 5（10-28） | `consume_batches` | [c06] [c09] | 替換整個 cell | `rebuild_silver = true` 跑一次（彙整改取內容多的） |
| 5（10-28） | `parse_documents` | [c02] [c03] | 替換整個 cell | 財報本體限前 30 頁；先 `dry_run` |
| — | `check_landing` / `check_api_status` | — | 不用動 | — |

比對方法：本機 `python tools/nb.py show <notebook> <tag>` 與 Databricks 上同標籤 cell 逐字對；`python tools/nb.py export <nb> <tag>` 可直接複製。

### 0.3 相依與先後

- ~~爬蟲端新版尚未 rsync 上 VM~~ **10-29 從 bronze 確認新版已在 VM 跑**：`ir_summary` 自批次 `000045_20261022T193001` 起帶 `reported_period`（10-21 新版欄位），10-16～10-21 批次只有 `management_views`（10-10 版），更早的沒有。10-29 `rebuild_silver` 後這些批次的結構化欄位已進 silver。**財報新欄位（quick_ratio / dso_days…）還沒有**：`ir_financials` 只有 `000030_20261016`（24 家、舊格式），財報排程每月 1 / 16 只補新期別，要整檔重發得做爬蟲 HANDOFF §1 第 3 步手動回補，但該 HANDOFF 警告 `MAX_ATTEMPTS` 會誤殺未申報的 Q3、修好前不要手動連跑 → 爬蟲端決定；報告端這幾項先「未取得」。
- `s_summary.management_views.topic` 在 10-21 前的批次是舊七類詞彙，報告會把它們收在「爬蟲彙整的其他主題」摺疊區，法說七節走 LLM 補位；新批次才會直接填。
- `build_ir_report` 的 gold `light` / `score` 欄位保留但寫 NULL；[c30] 不再印這兩欄。
- 五家範例（`範例財報/`）用的是沙箱 dev 批次 `dev_20261021T103341`，**不在 Databricks**；真正上線後拿 Databricks 的 bundle 重跑 `build_report.py` 即可對照。

### 0.4 之前的接續點（仍有效）

- 2026-10-22：步驟 1–2 已貼；`rebuild_silver` 已寫入（`s_financials` 261 列、`s_summary` 89 列，`updated_at` 全為 2026-10-22 09:06 UTC），新欄位存在、非 NULL 數 0（爬蟲新版未上 VM，正常）。
- Databricks `ir_calendar_consume_batches` 排程正常消費，2026-10-22 台北 12:18 已到 seq = 44（`000044_20261022T094001`），37–44 全 SUCCESS、皆小增量。告警分級那組 cell 已貼；`batch_log.crawler_alerts` 落表待驗（§4-2）。
- `parse_documents` 2026-10-20 手動跑過 10 份供應商文件；還沒排程（建議接成 `consume_batches` job 的下一個 task，`max_files = 50`）。
- 爬蟲端 2 筆實體檔案放棄待人工補（§2）。

## §1 Databricks 上各 notebook 的版本狀態

「已貼」= 使用者確認或從輸出推得；「未知」= repo 查不到、要到 Databricks 比對；「未貼」= 確定還是舊版。

| notebook | cell | repo 版本來源 | Databricks 狀態 | 備註 |
| --- | --- | --- | --- | --- |
| `init_tables` | [c13] ddl_s_summary、[c19] ddl_s_financials、[c21] add_columns | **2026-10-21 新版欄位** | 已貼、已跑（2026-10-22） | 新欄位已加到既有表 |
| `init_tables` | [c02] / [c11] / [c15] / [c19a] | 10-11 / 10-20 | 已貼、已跑 | 12 張表齊；[c19a]/[c19b] 兩張表存在、0 列 |
| `init_tables` | [c19b] ddl_g_ir_report、[c21] add_columns | **2026-10-28 gold 三欄** | 已貼、已跑（2026-10-29，與 10-29 視角欄一起） | — |
| `consume_batches` | [c04] table_schemas | **2026-10-21 新版欄位** | 已貼（2026-10-22） | `rebuild_silver` 已跑 09:06 UTC；爬蟲新版整檔重發後再 rebuild 一次 |
| `consume_batches` | [c06] transform_silver、[c09] io_delta | **2026-10-28 彙整薄不蓋厚** | **未貼**（Databricks 上是 10-21 版 [c06]、原版 [c09]） | 貼完 `rebuild_silver = true` 一次 |
| `consume_batches` | [c02] [c03] [c05] [c11] [c20] | SEMI / 10-11 §3.1 | 已貼（2026-10-20） | 告警分級；只有 FATAL 才 raise |
| `check_landing` | [c02] imports、[c13] check_silver | SEMI + 10-11 §2.2 | 已貼（2026-10-20） | 不受這次影響（[c13] 只查鍵與列數） |
| `inspect_record` | [c03] pure_helpers | **2026-10-21** | 已貼（2026-10-22） | 只讀 |
| `parse_documents` | [c03a] [c05] [c07] [c08] [c10] | 10-11 §3.2 | 未知 | `.htm` 改純 Python 抽文字不計費；貼完先 `dry_run = true` |
| `parse_documents` | [c02] [c03] | **2026-10-28 財報限頁** | **未貼** | 含 10-11 的 HTML 分流；貼完先 `dry_run = true` |
| `check_api_status` | — | — | 不用動 | |
| `init_tables` | [c19a] ddl_b_ir_report_llm、[c19b]、[c21] | **2026-10-29 視角欄 report_kind / topics** | 已貼、已跑（2026-10-29）：gold +5 欄、bronze +report_kind | — |
| `init_tables` | [c02] imports（TABLES 改名）、[c19a] [c19b]（DDL 鍵改名）、**[c19c] rename_tables（新）**、[c21]（ADD_COLUMNS 鍵改名） | **2026-10-29 改名 supplier_report → ir_report** | 已貼、已跑（10-29；`build_ir_report` 能讀 `g_ir_calendar_ir_report` 即證明 RENAME 成功） | — |
| `build_ir_report` | 整支 | **2026-10-29 當季為準 + 視角骨架 + 20261029b 退用最新已公告季（prompt supplier 2.2、peer 1.0、semi 1.0）** | **已匯入、已貼 [c02] [c03] [c07] 20261029b**（10-29）；南亞 2026Q3 supplier 一份已實跑 + render_only 重套 | job parameters `views = supplier`、`lookback_quarters = 0`、無 `prompt_version`；排程未設 |

完整的 10-11 cell 清單與上線順序：`docs/20261011_ir_calendar_crawler_change_updates.md`「要複製到 Databricks 的 cell」。

## §2 爬蟲端告警現況（2026-10-20 09:56 health.json）

```
[WARN ] 實體檔案放棄 2 筆，需人工補
         - TYO:5201:2026Q2 缺 financial_report      ← AGC
         - TYO:5214:2026Q2 缺 financial_report      ← 日本電氣硝子
[INFO ] 實體檔案待抓 269 筆（health.docs.pending）
```

- 放棄 2 筆：爬蟲端（MI_Crawler VM）人工補檔。補齊後 `health.json` 的 alert 消失，job 端不用改。
- 待抓 269 筆：VM 抓檔佇列。若之後幾次跑都不下降，是 VM 抓檔卡住，找爬蟲端。
- 2026-10-20 之前 Databricks 跑的是舊版 [c20]（任何告警都 raise），所以這兩筆 WARN 一直讓 job 紅燈；已修正。
- 「法說漏抓」目前兩端都不通知，決定與待辦見 `backlog.md` §B。

## §3 排程

- 實際：2026-10-16/17 的 batch_log `processed_at` 落在台北 09:19 / 12:18 / 20:18，`consume_batches` 有在跟 VM 班次跑；`parse_documents` **尚未排程**（2026-10-20 手動跑第一次）；`build_ir_report` 未上線。
- 設計：`consume_batches` 跟 VM 班次（掃描 08:10 / 17:10、抓檔 09:40 / 18:40 之後各一次）或每小時；`parse_documents` → `build_ir_report` 接在其後。
- **實際 Databricks job 的 trigger 設定 repo 沒有紀錄**，要到 Workflows 看，或查 `b_ir_calendar_batch_log.processed_at` 的時間分布。
- 手動跑的注意事項：參數要與 job 相同（尤其 `api_base_url` / `api_key_secret`，留空會略過 API 但游標照推，之後不補送）；避開排程時段；只驗邏輯用 `dry_run = true`。

## §4 下一步

1. **貼 §0.0 / §0.0a 的 10-28、10-29 改動**：`init_tables` [c19a] [c19b] [c21] → 跑 [c21]；`consume_batches` [c06] [c09] → `rebuild_silver`；`parse_documents` [c02] [c03]；然後**匯入 `build_ir_report` 整支**（§0.2 步驟 3，`views = supplier`、無 `prompt_version`）。
   視角後續：等使用者給同業 / 半導體模板 HTML → 補 peer「對手 vs 友達同期對照表」（[c09] 撈 `BENCHMARK_COMPANY` 的 financials、[c03] 對照列、[c07] 新節）與 semi 專屬節 → 再把 `views = peer,semi` 放進排程。爬蟲端建議（補 4 家 SEMI、第六主題說明）已寫 `MI_Crawler/ir_calendar/doc/20261029_給爬蟲端_報告視角擴充與新增公司建議.md`。
   上線後做 backlog D1-1 / D1-2：對一列 `b_ir_calendar_document_parse.payload` 形狀；查 `s_document_text` 每頁字元數與 `s_document_element` 的 `doc_kind × element_type` 分布。
2. ~~查 `TPE:1303` 2026Q3 彙整為何 `management_views` 為 NULL~~ **10-29 已查清**：bronze 三批（9-21 / 9-24 / 10-13）`payload:summary` 都有 `found = true`、`core_points`（6 / 1 / 3 條），但都沒有 `management_views` 等結構化欄位 → 這三批都早於新版部署（彙整自 10-16 批次起才有 `management_views`、10-22 起才有 `reported_period`，見 §0.3），不是 job 問題。等 VM 更新、整檔重發後再 `rebuild_silver` 一次即有值（§4-4）。查法：`payload:summary.<欄位>`（結構化欄位在 `summary` 子物件下，頂層只有 `fallback`）。
3. **驗 `crawler_alerts` 落表**：下一批 SUCCESS 後
   ```sql
   SELECT batch_id, processed_at, explode(crawler_alerts) AS alert
   FROM micenter.mi3_datahub_prod.b_ir_calendar_batch_log
   ORDER BY processed_at DESC LIMIT 20
   ```
   有 `[WARN] 實體檔案放棄…` 與 `[INFO] …` 列即完成。若 MERGE 報缺欄位，回頭跑 `init_tables` [c21]。
4. ~~爬蟲新版上 VM 後確認欄位~~ 10-29 已確認彙整新欄位到了（§0.3）。剩**財報新欄位**：等爬蟲端整檔重發 `ir_financials`（手動回補或 11/1 排程後新期別）→ `consume_batches` 正常消費即進 silver（或再 `rebuild_silver`）→ `build_ir_report` 對 `TPE:1303` `force_rebuild` 一份看第 06 節速動比 / 應收付天數是否有值。查法：`SELECT batch_id, count(*), sum(CASE WHEN payload LIKE '%quick_ratio%' THEN 1 ELSE 0 END) FROM …b_ir_calendar_record WHERE record_type = 'ir_financials' GROUP BY batch_id ORDER BY 1 DESC`。
5. 到 Databricks 比對 §1 標「未知」的 cell（`parse_documents`），把狀態改成已貼 / 未貼。
6. 確認 Workflows 上實際 trigger，記進 §3；`parse_documents` → `build_ir_report` 排進 `consume_batches` job 後面兩個 task。
7. 跟爬蟲端追 TYO:5201 / TYO:5214 的 2026Q2 財報補檔，以及 269 筆待抓是否下降。
8. `backlog.md` §B1（法說漏抓 alert）等爬蟲端做；B3 選做。待決（交代文件 §6）：`auo_topics` 四支箭定義、`positive_signals / watch_items / open_questions` 續留 silver（目前續留，報告第 08 節有用）。

## §5 測試用查詢（匯出一家公司一期給 Agent 套模板）

Cell A（SQL）：候選清單
```sql
SELECT t.company_key, t.company_slug, t.period, count(*) AS docs, collect_set(t.doc_kind) AS doc_kinds,
       sum(t.text_chars) AS chars, max(f.n_fin) AS financial_rows
FROM micenter.mi3_datahub_prod.s_ir_calendar_document_text t
LEFT JOIN (SELECT company_key, count(*) AS n_fin FROM micenter.mi3_datahub_prod.s_ir_calendar_financials GROUP BY company_key) f
  ON f.company_key = t.company_key
WHERE t.category = 'SUPPLIER' AND t.parse_status IN ('success', 'partial')
GROUP BY t.company_key, t.company_slug, t.period
ORDER BY financial_rows DESC NULLS LAST, chars DESC LIMIT 30
```

Cell B（Python）：把 company / financials / summary / conference / docs（每份文件全文截 20,000 字、最多 3 份）包成一個 JSON 印出，
`=====BUNDLE_BEGIN=====` 到 `=====BUNDLE_END=====` 之間整段貼給 Agent。程式碼：`build_ir_report/dev/export_bundle.py`（整檔貼進一個 Python cell，改 `COMPANY_KEY, PERIOD`）；形狀 = `build_ir_report` [c09] `load_company_bundle` 的回傳。
貼回 repo 時存成 `範例財報/<公司>/<公司>.md`，爬蟲 payload（`inspect_record` 印出）存成 `<公司>_爬蟲_<期別>.md`，`python3 build_report.py` 重產。
