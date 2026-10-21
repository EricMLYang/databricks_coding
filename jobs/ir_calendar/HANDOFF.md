# jobs/ir_calendar HANDOFF — 現況與接續點

給下一次任務或其他 Agent 的接續資訊。靜態說明（用途、參數、表設計）在各 `README.md` 與 `docs/`，這裡只記**動態狀態**：
Databricks 上貼到哪一版、還沒貼什麼、爬蟲端告警現況、下一步。每次改完 Databricks 更新本檔 §0 與 §1。

## §0 接續點（2026-10-21 收工）

### 0.1 這次改了什麼（repo 已 commit；Databricks **全部未貼**）

兩件事同時做：**換報告版面**（`doc/20261021_SCM財報和法說報告html格式v20261007.html` 取代 20261010 版）與**接爬蟲新版欄位**
（MI_Crawler 交代文件 `doc/20261021_給Databricks_notebook開發者_新版SCM報告欄位交代_HANDOFF.md`、規劃 `doc/20261021_爬蟲對齊新版SCM報告版面_規劃與實測.md`）。

| 改動 | 哪裡 | 內容 |
| --- | --- | --- |
| 換爬蟲：silver 加欄 | `init_tables` [c13] [c19] [c21] | `s_financials` 加 21 欄（`cash`、三類流動金融資產、`short_term_investments`、應收／應付（含票據、關係人）、`inventory`、`equity_parent`、`investing_cash_flow_ytd`、`pretax_margin`、`net_margin_parent`、`quick_assets`、`quick_ratio`、`dso_days`、`dpo_days`、`days_basis`）；`s_summary` 加 `reported_period`、`business_segments`、`qa_highlights`；[c21] 對既有表 ADD COLUMNS，另改 5 個既有欄位註解（`management_views.topic` 詞彙換六類） |
| 換爬蟲：silver 轉換 | `consume_batches` [c04] [c06] | `FIN_AMOUNTS/RATIOS` 拆 V1/V2（select 順序照 DDL：V1 → 血緣 → V2）、`days_basis` 字串欄、`SUMMARY_PAYLOAD.summary` 加三鍵；`transform_summary` / `_financial_rows` 的 select 接在最後 |
| 換版面 | `build_supplier_report` [c01] [c02] [c03] [c05] [c06] [c07] [c09] [c10] [c11] [c30] + 第一個 markdown | `TEMPLATE_VERSION = 20261021`、prompt **2.0**（無燈號／分數／War Room／Watchlist；法說六主題用爬蟲固定詞彙、事業群六欄）；`INDICATORS` 11 項全接欄位（速動比／應收付天數／母公司淨利率）；第 02 節本季 vs 去年同季＋同比變動；法說 01–06 先用 `management_views`、07 用 `qa_highlights`、03 事業群先用 `business_segments`，缺的才 LLM；頁首財報公布日取 `document_file.doc_date`、法說報告期間取 `reported_period`；[c09] 同期沒彙整退用最近一期；gold `light`/`score` 一律 NULL（DDL 不動）；新模板檔與 `USER_GUIDE.md` 放 `template/` |
| 檢視 | `inspect_record` [c03] | `summary_report` 多印法說報告期間、事業群表、Q&A |
| 測試 | `tests/test_ir_calendar_{consume,build_supplier_report,inspect_record}.py` | 86 個全綠（consume 45、report 30、inspect 11）：含 DDL ↔ transform 欄位順序、新欄位值、彙整優先於 LLM、十項圖單欄、標籤不重疊 |
| 範例 | `範例財報/` | 五家用新版面 + 爬蟲新版實測資料的純 Python 版（`build_report.py`），黃底數 Corning 2／南亞 5／長興 3／奇美 14／永光 13；`模板覆蓋度評估.md` |

### 0.2 要複製到 Databricks 的檔案與 cell（照順序）

| 步驟 | notebook（repo 路徑 `jobs/ir_calendar/<資料夾>/notebook.ipynb`） | cell | 動作 | 貼完做什麼 |
| --- | --- | --- | --- | --- |
| 1 | `init_tables` | [c13] ddl_s_summary | 替換整個 cell | — |
| 1 | `init_tables` | [c19] ddl_s_financials | 替換整個 cell | — |
| 1 | `init_tables` | [c21] add_columns | 替換整個 cell | 整支跑一次：輸出應有 `add …s_ir_calendar_financials：[21 欄]`、`add …s_ir_calendar_summary：[reported_period, business_segments, qa_highlights]`、`comment …`；再跑一次全部 `ok 欄位已齊` |
| 2 | `consume_batches` | [c04] table_schemas | 替換整個 cell | — |
| 2 | `consume_batches` | [c06] transform_silver | 替換整個 cell | 先 `dry_run = true` 跑一次；再 `rebuild_silver = true` 跑一次（舊批次新欄多為 NULL，正常；爬蟲新版整檔重發後再 rebuild 一次就有值） |
| 3 | `build_supplier_report` | 整支（第一個 markdown + [c01] [c02] [c03] [c05] [c06] [c07] [c09] [c10] [c11] [c30]；[c04] [c08] [c20] 沒變） | 整支重新匯入最省事（Databricks 上原本就**未貼**） | job parameter `prompt_version = 2.0`；依 notebook 第一格「首次上線順序」：`dry_run` → `max_reports = 1`（`TPE:1303`）→ 無彙整的 `TPE:1763` → 無 financials 的 TYO |
| 4 | `inspect_record` | [c03] pure_helpers | 替換整個 cell | 只讀，隨時可貼 |
| — | `check_landing` / `check_api_status` / `parse_documents` | — | 不用動 | — |

比對方法：本機 `python tools/nb.py show <notebook> <tag>` 與 Databricks 上同標籤 cell 逐字對；`python tools/nb.py export <nb> <tag>` 可直接複製。

### 0.3 相依與先後

- 爬蟲端新版（MI_Crawler `main` 工作目錄）**尚未 commit、尚未 rsync 上 VM**（交代文件開頭）。bronze 全文照收，不改 silver 也不會壞；步驟 1–2 貼了之後舊批次新欄是 NULL，等 VM 下一班 `fetch_financials` 整檔重發 193 家、`consume_batches` 正常消費即有值（或再 `rebuild_silver`）。
- `s_summary.management_views.topic` 在 10-21 前的批次是舊七類詞彙，報告會把它們收在「爬蟲彙整的其他主題」摺疊區，法說七節走 LLM 補位；新批次才會直接填。
- `build_supplier_report` 的 gold `light` / `score` 欄位保留但寫 NULL；[c30] 不再印這兩欄。
- 五家範例（`範例財報/`）用的是沙箱 dev 批次 `dev_20261021T103341`，**不在 Databricks**；真正上線後拿 Databricks 的 bundle 重跑 `build_report.py` 即可對照。

### 0.4 之前的接續點（仍有效）

- Databricks `ir_calendar_consume_batches` 游標 `_cursor.json` 在 seq = 36（2026-10-20）。告警分級那組 cell 已貼、`dry_run = true` 跑過；正式跑後驗 `batch_log.crawler_alerts`（§4-1）。
- `parse_documents` 2026-10-20 手動跑過 10 份供應商文件；還沒排程（建議接成 `consume_batches` job 的下一個 task，`max_files = 50`）。
- 爬蟲端 2 筆實體檔案放棄待人工補（§2）。

## §1 Databricks 上各 notebook 的版本狀態

「已貼」= 使用者確認或從輸出推得；「未知」= repo 查不到、要到 Databricks 比對；「未貼」= 確定還是舊版。

| notebook | cell | repo 版本來源 | Databricks 狀態 | 備註 |
| --- | --- | --- | --- | --- |
| `init_tables` | [c13] ddl_s_summary、[c19] ddl_s_financials、[c21] add_columns | **2026-10-21 新版欄位** | **未貼** | 貼完整支跑一次（§0.2 步驟 1） |
| `init_tables` | [c02] / [c11] / [c15] / [c19a] / [c19b] | 10-11 / 10-20 | 已貼、已跑 | 12 張表齊；[c19a]/[c19b] 兩張表存在、0 列 |
| `consume_batches` | [c04] table_schemas、[c06] transform_silver | **2026-10-21 新版欄位** | **未貼** | 貼完 `rebuild_silver = true`（§0.2 步驟 2） |
| `consume_batches` | [c02] [c03] [c05] [c11] [c20] | SEMI / 10-11 §3.1 | 已貼（2026-10-20） | 告警分級；只有 FATAL 才 raise |
| `check_landing` | [c02] imports、[c13] check_silver | SEMI + 10-11 §2.2 | 已貼（2026-10-20） | 不受這次影響（[c13] 只查鍵與列數） |
| `inspect_record` | [c03] pure_helpers | **2026-10-21** | **未貼**（10-20 版已貼） | 只讀，隨時可貼 |
| `parse_documents` | [c02] [c03] [c03a] [c05] [c07] [c08] [c10] | 10-11 §3.2 | 未知 | `.htm` 改純 Python 抽文字不計費；貼完先 `dry_run = true` |
| `check_api_status` | — | — | 不用動 | |
| `build_supplier_report` | 整支 | **2026-10-21 新版面（template 20261021 / prompt 2.0）** | **未貼**（10-20 的舊版面也沒貼過） | 整支匯入；job parameter `prompt_version = 2.0` |

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

- 實際：2026-10-16/17 的 batch_log `processed_at` 落在台北 09:19 / 12:18 / 20:18，`consume_batches` 有在跟 VM 班次跑；`parse_documents` **尚未排程**（2026-10-20 手動跑第一次）；`build_supplier_report` 未上線。
- 設計：`consume_batches` 跟 VM 班次（掃描 08:10 / 17:10、抓檔 09:40 / 18:40 之後各一次）或每小時；`parse_documents` → `build_supplier_report` 接在其後。
- **實際 Databricks job 的 trigger 設定 repo 沒有紀錄**，要到 Workflows 看，或查 `b_ir_calendar_batch_log.processed_at` 的時間分布。
- 手動跑的注意事項：參數要與 job 相同（尤其 `api_base_url` / `api_key_secret`，留空會略過 API 但游標照推，之後不補送）；避開排程時段；只驗邏輯用 `dry_run = true`。

## §4 下一步

1. **貼 §0.2 的四步**（init_tables → consume_batches + rebuild_silver → build_supplier_report 整支 → inspect_record）。
2. **驗 `crawler_alerts` 落表**：下一批 SUCCESS 後
   ```sql
   SELECT batch_id, processed_at, explode(crawler_alerts) AS alert
   FROM micenter.mi3_datahub_prod.b_ir_calendar_batch_log
   ORDER BY processed_at DESC LIMIT 20
   ```
   有 `[WARN] 實體檔案放棄…` 與 `[INFO] …` 列即完成。若 MERGE 報缺欄位，回頭跑 `init_tables` [c21]。
3. 爬蟲新版上 VM 後，用 `inspect_record` 讀最新一批 `ir_financials` / `ir_summary`，確認 `quick_ratio`、`dso_days`、`reported_period`、`business_segments` 存在；再 `rebuild_silver` 一次，`build_supplier_report` 對 `TPE:1303` 產一份看第 06 節 11 項是否全有值。
4. 到 Databricks 比對 §1 標「未知」的 cell（`parse_documents`），把狀態改成已貼 / 未貼。
5. 確認 Workflows 上實際 trigger，記進 §3；`parse_documents` → `build_supplier_report` 排進 `consume_batches` job 後面兩個 task。
6. 跟爬蟲端追 TYO:5201 / TYO:5214 的 2026Q2 財報補檔，以及 269 筆待抓是否下降。
7. `backlog.md` §B1（法說漏抓 alert）等爬蟲端做；B3 選做。待決（交代文件 §6）：`auo_topics` 四支箭定義、`positive_signals / watch_items / open_questions` 續留 silver（目前續留，報告第 08 節有用）。

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
`=====BUNDLE_BEGIN=====` 到 `=====BUNDLE_END=====` 之間整段貼給 Agent。程式碼：`build_supplier_report/dev/export_bundle.py`（整檔貼進一個 Python cell，改 `COMPANY_KEY, PERIOD`）；形狀 = `build_supplier_report` [c09] `load_company_bundle` 的回傳。
貼回 repo 時存成 `範例財報/<公司>/<公司>.md`，爬蟲 payload（`inspect_record` 印出）存成 `<公司>_爬蟲_<期別>.md`，`python3 build_report.py` 重產。
