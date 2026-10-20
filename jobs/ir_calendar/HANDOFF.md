# jobs/ir_calendar HANDOFF — 現況與接續點

給下一次任務或其他 Agent 的接續資訊。靜態說明（用途、參數、表設計）在各 `README.md` 與 `docs/`，這裡只記**動態狀態**：
Databricks 上貼到哪一版、還沒貼什麼、爬蟲端告警現況、下一步。每次改完 Databricks 更新本檔 §0 與 §1。

## §0 接續點（2026-10-20）

- repo 最後一個動到 ir_calendar 的 commit：`da6e895`（SEMI 分類）。本檔建立時 repo 沒有未 commit 的 notebook 變更。
- Databricks `ir_calendar_consume_batches` 游標 `_cursor.json` 在 seq = 36，VM 最新批次也是 36（2026-10-20 09:56 health.json）。
- 2026-10-20 已把**告警分級**那組 cell 貼上 Databricks（§1 表），`dry_run = true` 跑過一次，輸出正確（§2）。
  正式跑（`dry_run = false`）或下一班排程還沒驗證 `batch_log.crawler_alerts` 有落表 → **下一步 §4-1**。
- 爬蟲端 2 筆實體檔案放棄待人工補（§2），Databricks 端沒事可做。
- **下次第一步**（2026-10-20 收工時）：`parse_documents` 正在解析 10 份供應商文件（categories=SUPPLIER、max_files=10）。
  到 Databricks 看那次 run 的「本次結果」有無 failed → 用本檔 §5 的 Cell B 匯出 `TPE:1303`（南亞塑膠）`2026Q2` 的 bundle 貼給 Agent → Agent 套模板出 HTML 給使用者看版面。
  `parse_documents` 還沒排程：建議加成 `consume_batches` job 的下一個 task，`max_files = 50`、`categories` 留空。
- 2026-10-20 新增 job `build_supplier_report/`（供應商財報＋法說整合報告 HTML）：repo 完成、24 個本機測試全綠、**尚未貼到 Databricks、未 commit**。
  要貼的是 `init_tables` [c02]/[c19a]/[c19b] + 整支新 notebook（§1 最後兩列）；模板與使用者說明在 `build_supplier_report/template/`。

## §1 Databricks 上各 notebook 的版本狀態

「已貼」= 使用者確認或從輸出推得；「未知」= repo 查不到、要到 Databricks 比對；「未貼」= 確定還是舊版。
比對方法：本機 `python tools/nb.py show <notebook> <tag>` 與 Databricks 上同標籤 cell 逐字對。

| notebook | cell | repo 版本來源 | Databricks 狀態 | 備註 |
| --- | --- | --- | --- | --- |
| `init_tables` | [c21] add_columns | 10-11 §3.1 / §2.1 | 已貼、已跑（2026-10-20，summary 五欄已在） | 補 `batch_log.crawler_alerts` 與 summary 五欄。dry run 不寫表，欄位是否真的存在要用 §4-1 驗 |
| `init_tables` | [c02] / [c11] / [c13] / [c19] | 10-11 §2.2 / §3.1 / §2.1 | 已貼、已跑（2026-10-20，12 張表齊；summary 28 欄） | [c19] 建 `s_ir_calendar_financials`；表不存在時 `consume_batches` 新版 [c06] 會失敗 |
| `consume_batches` | [c02] imports | SEMI（`da6e895`） | 已貼 | 使用者確認半導體分類已落 `semiconductor/` |
| `consume_batches` | [c03] [c04] [c05] [c11] [c20] | 10-11 §3.1 | 已貼（2026-10-20） | 只有 FATAL 才 raise；WARN / INFO 印在告警區塊並寫 batch_log |
| `consume_batches` | [c06] transform_silver | 10-11 §2.1 / §2.2 | 已貼（2026-10-20）；`rebuild_silver` 已重跑，`s_ir_calendar_financials` 261 列 / 24 家 | 含 summary 五欄與 `transform_financials`。先貼 `init_tables` [c19]，貼完跑一次 `rebuild_silver = true` |
| `check_landing` | [c02] imports | SEMI + 10-11 §2.2 | 已貼（2026-10-20） | SEMI 的 `semiconductor` 目錄應已貼（否則 [c16] 會 FAIL）；financials 常數是否同一版未知 |
| `check_landing` | [c13] check_silver | 10-11 §2.2 | 已貼（2026-10-20） | |
| `inspect_record` | [c03] pure_helpers | 10-11 §2.1 | 已貼（2026-10-20） | 只讀，隨時可貼 |
| `parse_documents` | [c02] [c03] [c03a] [c05] [c07] [c08] [c10] | 10-11 §3.2 | 未知 | `.htm` 改純 Python 抽文字不計費；貼完先 `dry_run = true` |
| `check_api_status` | — | — | 不用動 | |
| `init_tables` | [c02] imports、[c19a] ddl_b_supplier_report_llm、[c19b] ddl_g_supplier_report | 2026-10-20 新 job | 已貼、已跑（兩張表存在、0 列） | [c02] 加 gold 前綴與兩張表；[c19a]/[c19b] 新增於 [c19] 之後；貼完整份跑一次（只建新表） |
| `build_supplier_report` | 整支（13 個 code cell + markdown） | 2026-10-20 新 job | **未貼** | 整支匯入；依 notebook 第一格「首次上線順序」先 `dry_run`、再 `max_reports = 1` |

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

- 實際：2026-10-16/17 的 batch_log `processed_at` 落在台北 09:19 / 12:18 / 20:18，`consume_batches` 有在跟 VM 班次跑；`parse_documents` **尚未排程**（2026-10-20 手動跑第一次）。
- 設計：`consume_batches` 跟 VM 班次（掃描 08:10 / 17:10、抓檔 09:40 / 18:40 之後各一次）或每小時；`parse_documents` 接在其後。
- **實際 Databricks job 的 trigger 設定 repo 沒有紀錄**，要到 Workflows 看，或查 `b_ir_calendar_batch_log.processed_at` 的時間分布。
- 手動跑的注意事項：參數要與 job 相同（尤其 `api_base_url` / `api_key_secret`，留空會略過 API 但游標照推，之後不補送）；避開排程時段；只驗邏輯用 `dry_run = true`。

## §4 下一步

1. **驗 `crawler_alerts` 落表**：下一批 SUCCESS 後
   ```sql
   SELECT batch_id, processed_at, explode(crawler_alerts) AS alert
   FROM micenter.mi3_datahub_prod.b_ir_calendar_batch_log
   ORDER BY processed_at DESC LIMIT 20
   ```
   有 `[WARN] 實體檔案放棄…` 與 `[INFO] …` 列即完成。若 MERGE 報缺欄位，回頭跑 `init_tables` [c21]。
2. 到 Databricks 比對 §1 標「未知」的 cell，把狀態改成已貼 / 未貼；未貼的照 10-11 文件順序補（`init_tables` → `consume_batches` + `rebuild_silver` → `check_landing` / `inspect_record` → `parse_documents`）。
3. 確認 Workflows 上實際 trigger，記進 §3。
4. 跟爬蟲端追 TYO:5201 / TYO:5214 的 2026Q2 財報補檔，以及 269 筆待抓是否下降。
5. `backlog.md` §B1（法說漏抓 alert）等爬蟲端做；B3 選做。

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
