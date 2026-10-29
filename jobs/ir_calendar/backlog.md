# jobs/ir_calendar backlog

對應爬蟲端 MI_Crawler `main` 2026-10-15 的兩個 commit（`087ee34` 新增 SEMI 分類 14 家、`706f3b7` SK hynix 簡報來源）。
來源文件：MI_Crawler `ir_calendar/doc/20261015_給Databricks_notebook與後端開發者_新增SEMI分類交代.md`、`doc/20261015_新增半導體類公司與切回Kiro_規劃.md`。
2026-10-15 已逐支 notebook 對照過，下面只列**要動 job 的**；沒列的（`init_tables`、`parse_documents`、`inspect_record`、`check_api_status`）確認不用改。

## A. 必做：新分類 `SEMI`（半導體）→ Volume 目錄 `semiconductor/`

**2026-10-15 已改（本機，尚未貼到 Databricks）**：A1 `consume_batches` [c02]、A2 `check_landing` [c02]、A3 測試（`pytest tests/test_ir_calendar_consume.py` 全綠）。Databricks 上要重新複製的只有這兩個 [c02]。

爬蟲主檔 179 → 193 家，新增 14 家全部 `category = "SEMI"`（NVIDIA、AMD、Broadcom、Intel、Micron、Marvell、Coherent、Amkor、日月光投控、力成、欣興、南亞科、SK hynix、中際旭創）。既有三類與 179 家分類值不變。

| # | notebook | cell | 改什麼 | 不改的後果 |
| --- | --- | --- | --- | --- |
| A1 | `consume_batches` | [c02] `CATEGORY_DIR` | 加 `"SEMI": "semiconductor"` | 14 家的檔案落 `<volume_root>/uncategorized/<代稱>/`，`s_ir_calendar_document_file.volume_path` 也記成那個路徑 |
| A2 | `check_landing` | [c02] `CATEGORY_DIRS` | 加 `"semiconductor"` | [c16]「沒有檔案掉進 uncategorized」判 FAIL；分類目錄統計少一行 |
| A3 | `tests/test_ir_calendar_consume.py` | `volume_target` 測試 | 補一組 `category="SEMI"` → `semiconductor/` | 無守門 |

- `check_api_status` 沒有分類常數，**不用改**（爬蟲端交代文件原本寫要改，已更正）。
- `init_tables` 不用重跑：五張 silver 的 `category` / `category_name` 都是 STRING，DDL 註解已寫「新分類直接進來」。
- `parse_documents` 不用改：分類與公司取 `s_document_file` 欄位，不掃目錄。
- 若 A1 來不及在爬蟲端 VM 上版前改好，已落到 `uncategorized/` 的檔案要手動搬到 `semiconductor/`，並更新 `s_ir_calendar_document_file.volume_path`（或對那幾筆 `rebuild_silver`）。

**順序**：A1／A2 要在爬蟲端 VM 第一次發出帶 SEMI 的批次之前改好。系統後端 2026-10-15 回覆分類可任意新增、不需事先建列，所以主檔批次不用等後端；第一批送出後跑 `check_api_status` 看 [c11] `lastCompaniesBatch` 的 14 筆是 `created` 不是 `failed` 即可。

## B. 建議：法說漏抓目前兩端都不會通知

**2026-10-15 決定**：B2 維持 WARN（不改 [c03]），已在 `tests/test_ir_calendar_consume.py` alert 分級表加一列釘住「`法說漏抓` 前綴 = WARN」；要升 FATAL 時改 [c03] `alert_level` 與那一列。B3 未做：`health.json` 的 `window_not_found` 項目格式 repo 內查不到，且 `check_landing` 沒有 `root_url` 參數讀不到 `health.json`，等 B1 定案再說。

現況：爬蟲端視窗過了找不到日期 → entry 轉 `NOT_FOUND`，只寫進 `health.json` 的 `window_not_found`，**不進 `alerts`**；job 端 [c03] `crawler_alerts` 只讀 `alerts`，六支 notebook 都沒有碰 `window_not_found`。所以一家公司該開法說卻沒抓到，job 不會紅燈、告警區塊也不會印。財報漏抓（`實體檔案放棄`）反而有 WARN，兩者不對稱。

分兩步，job 端的改動很小：

| # | 誰 | 改什麼 | 說明 |
| --- | --- | --- | --- |
| B1 | 爬蟲端（MI_Crawler `outputs.write_health`） | 把「有歷年同季錨點、本季卻 NOT_FOUND」的公司寫成一則 alert，例如 `法說漏抓 3 家（歷年同季有開）：TPE:3481:2026Q3, …` | 用錨點過濾是為了排除「本來就不開」的公司，不然每季會有幾十筆噪音。job 端對不認得的訊息預設 WARN 且每次都印、寫進 `batch_log.crawler_alerts`，**B1 做完 job 不改任何一行就看得到** |
| B2 | job 端 `consume_batches` [c03] `alert_level` | 決定 `法說漏抓` 前綴要不要升 FATAL | 建議先維持 WARN 跑一季看噪音量，再決定；升 FATAL 只要在 `alert_level` 的前綴清單加一個字串，並在 `tests/test_ir_calendar_consume.py` 的 alert 分級表加一列 |
| B3（選做） | job 端 `check_landing` | 新增一個 check：讀 `health.json` 的 `window_not_found`，跟 `s_ir_calendar_conference` 歷年同季有列的公司 join，印出「歷史有、今年沒有」清單 | 等於把爬蟲端 `tools/report_gap.py` 的邏輯搬到 Databricks 用 silver 算；優點是不依賴爬蟲端的 anchor state，缺點是新公司前幾季沒有歷史，看不出來 |

## C. 備忘：這次上版不需要 job 配合、但會看到的變化

- `master/company_category.json` 變 4 列（bronze 歸檔，無 silver）。
- `master/company.json`／`api/companies_sync.json` 多 14 列，`s_ir_calendar_company` MERGE 多 14 列。`stockCode` 已驗過 193 家無跨市場重複。
- 14 個新代稱：`Nvidia`、`AMD`、`Broadcom`、`Intel`、`Micron`、`Marvell`、`Coherent`、`Amkor`、`ASE-Holding`、`Powertech`、`Unimicron`、`Nanya-Tech`、`SK-hynix`、`Innolight`。與既有 `Innolux`（群創）、`SKC` 是不同公司，不要合併目錄。
- 美股 5 家非曆年會計年度（NVIDIA／Marvell 1 月底、Broadcom 10 月底、Micron 8 月底、Coherent 6 月底）：`ir_financials` 的年度 `fiscal_year` 以期末日所在年為標籤（NVIDIA 2027-01 結束的年度 = `2027FY`），季別以期末日歸曆年季，與 Dell／HP 既有做法相同；`s_ir_calendar_financials` 不用改。
- SK hynix 法說簡報來源是 IR 站的 Azure Blob CDN，從開發機回 403，VM 上待驗證；若 VM 也 403 就不會有該公司的 Presentation 檔，只有 DART 財報（需 VM 填 `DART_API_KEY`）。
- `health.json` 沒有新欄位，告警文字沒變，[c03] 分級不受影響。


## D. 待辦（2026-10-28）：`parse_documents` 驗證與 `build_ir_report` 來源完整性

**2026-10-28 狀態**：D1-3、D2-1～D2-5 已在 repo 改好（測試全綠），**尚未貼 Databricks**（貼法見 HANDOFF §0.2）；D1-1 / D1-2 是上線後的 SQL 檢查；D2-6 待使用者定同業 / SEMI 的面向。

**2026-10-29 定案（使用者）**：報告**只用當季內容、最新一季為準**，不要上一季的過時資訊。D2-1 的跨期補位改成預設關（`lookback_quarters = 0`，機制保留）、彙整不再退用前期；
改為「期別候選 = 文件 ∪ 彙整」，當季只有彙整也產報告，文件後到時雜湊變了自動重做。詳見 HANDOFF §0.0a。D2-2 / D2-3 / D2-4 不變。

### D1 `parse_documents`：先驗證、再省費用（未做）

| # | 做什麼 | 說明 |
| --- | --- | --- |
| D1-1 | 對一列 bronze `payload` 形狀 | [c04] `PARSE_PAYLOAD` 是照官方文件假設的，10-20 手動跑過 10 份後沒紀錄對過。`SELECT payload:metadata, payload:document.elements[0] FROM b_ir_calendar_document_parse LIMIT 1`；不合就改 [c04] 再 `rebuild_silver` |
| D1-2 | 看解析密度與元素型別 | `s_document_text` 每檔 `text_chars / page_count`（過低 = 掃描檔 OCR 失敗或純圖簡報）；`s_document_element` 依 `doc_kind × element_type` 計數，財報要看得到 table、簡報要有 figure description。人工開一份台股財報的損益表 markdown、一份簡報的圖表描述 |
| D1-3 ✅ repo | `Financial_Statements` 只解前面幾頁 | 台股合併財報上百頁按頁計費，但 `build_ir_report` 每份文件截 `max_doc_chars = 40000`、財報排優先序最後，等於付錢解析再丟九成。`ai_parse_document` 支援 `pageRange`（參考腳本 `job_25_all_parse_content_new.py` 有提到），對 `Financial_Statements` 限頁數。等 D1-2 看到真的有大檔再改 [c03] `parse_options` |

不換解析器：數字全部來自 `s_financials`，解析文字只餵 LLM 寫敘事；`ai_parse_document` 有 OCR / 表格 / 圖表描述，job cluster 不用裝套件。第二條路（pdfplumber 之類）只在 D1-2 發現整批掃描檔讀不出來時個案處理。

### D2 `build_ir_report`：同一家公司的所有來源都要進最終報告（未做；見 2026-10-28 檢討）

現況一份報告 = (company_key, period)，[c09] 文件、法說場次只取**同期**，summary 同期沒有才退用前一期一份。南亞實例：2026Q3 只有 10-13 法說簡報，Q2 財報 PDF 與 Q2 簡報不會進 Q3 報告；Q2 兩份 ir_summary（9-21 細、9-24 只有公告）silver 只留 seq 大的 9-24。

| # | 做什麼 | 說明 |
| --- | --- | --- |
| D2-1 ✅ repo | [c09] 文件改取「最近 N 期」 | 台股法說講 Q3 自結時 Q3 財報還沒公告，最近的財報永遠在前一期。建議：本期全部文件 + 往前一期的 `Financial_Statements`（本期沒有財報時）+ 往前一期的 `Presentation` / `Earnings_Transcript`（本期沒有法說文件時）；prompt 與報告來源節都標期別。`docs_digest` 要連帶入的前期文件一起算，否則前期文件更新不觸發重做 |
| D2-2 ✅ repo | summary 同期多份不要覆蓋 | `consume_batches` [c09] `write_silver` MERGE 鍵 (company_key, period) 以 seq 大的為準，內容少的會蓋掉內容多的（覆蓋度評估 #11）。二選一：(a) MERGE 前比內容（`key_numbers` / `management_views` 長度，少的不覆蓋）；(b) summary 改成 (company_key, period, batch_path) 保留每份，[c09] 讀的時候合併。建議 (a) 改動最小 |
| D2-3 ✅ repo | summary 更新要觸發重做 | [c04] `select_work` 只用文件 sha256 算 `docs_digest`；爬蟲新版補上 `management_views` / `business_segments` 後 gold 不會重做。digest 加入 summary 的 `batch_id`（或 `updated_at`）與 conference `revision` |
| D2-4 ✅ repo | 報告來源節要分「餵了」與「略過」 | [c05] `pack_documents` 因 `max_total_chars` 略過或截尾的文件只寫在 prompt 裡，不回傳；[c07] `render_sources` 列的是 `facts["docs"]` 全部，讀者以為都參考過。把 packed / skipped / truncated 回傳進 facts 與 gold，來源節標「已讀（截尾）」「因長度略過」 |
| D2-5 ✅ repo（以 D1-3 + D2-4 解） | 字元上限重估 | 台股財報 PDF 解析後 10–15 萬字（長興 151,972、奇美 106,871），`max_doc_chars = 40000` 必截；D2-1 跨期取文件後 `max_total_chars = 120000` 更容易爆、財報整份被略過。配合 D1-3 限頁數，或財報只餵四大表那段元素（`s_document_element` 的 table） |
| D2-6 | 同業 / SEMI 的 prompt → **改成「報告視角」擴充**（10-29 骨架已做進 notebook，HANDOFF §0.0a；剩視角專屬節等使用者模板） | 構想見 `docs/20261029_ir_calendar_report_views_peer_semi_proposal.md`（§6-1、6-2 已定案）。重點：爬蟲分類一家一類，報告端自建 view 對應（supplier / peer / semi / customer）、一家可多視角，解決台積電等半導體供應商在 SEMI 視角被跳過的問題；一支 notebook 三個 profile 不拆支；gold 鍵加 `report_kind`（趁 0 列時改）；peer 視角以友達 TPE:2409 財務為對照基準 |

順序：D1-1 → D1-2（先確定解析結果可用）→ D2-2 / D2-3（資料不要丟、不要漏更新）→ D2-1 + D2-4 + D2-5（一起改 [c04] [c05] [c09] [c07] [c10]，gold 多 `source_periods` / `docs_fed` 欄）→ D1-3 → D2-6。
