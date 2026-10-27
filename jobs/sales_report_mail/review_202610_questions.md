# Sales Brief 202610 產出 Review — 待 Databricks Agent 確認的問題

- Review 日期：2026-10-27
- 對象程式：`job_sales_brief_report.ipynb`（10/6 commit 版；`job_sales_brief_report_v2.ipynb` 目前為空檔）

## 比對資料夾（絕對路徑）

| 月份 | 路徑 | 備註 |
|------|------|------|
| 202609_2（上月，基準） | `C:\Users\1806011\Projects\PM_Head\projects\ForwardDeployedEngineer\15_experiments\MI\mi_datahub_table\ai_function_and_job_info\sales_brief\sales_brief_result\202609_2` | 貼上後只手動改過一次（commit `1e90a02`）：三檔 `chart_data` CHART1 的 `"Sep"` → `"Sep(F)"`、`forecast_from_index` 13 → 12 |
| 202610（本月，review 對象） | `C:\Users\1806011\Projects\PM_Head\projects\ForwardDeployedEngineer\15_experiments\MI\mi_datahub_table\ai_function_and_job_info\sales_brief\sales_brief_result\202610` | job 原始輸出，未修改（NB 檔名 `2026_NB.md` 為手動複製筆誤，應為 `202610_NB.md`） |

每個檔案含三段：`【1/3 html_content】`、`【2/3 mail_body】`、`【3/3 chart_data】`。

## 最終版面主要缺失（摘要）

1. **NB 少了 Dell、Acer**：各表、訊息矩陣、庫存燈號、圖表都消失，「Major 6」變「Major 4」，總量 128.9 → 94.3。
2. **MNT Samsung 自相矛盾**：年度表整列「-」，但季度、MoM 有數字；26 4Q 只加兩個月（1.4，QoQ -42%），Dec Major MoM -52% 失真；AI 季度分析把假衰退當真；訊息矩陣全是「（無填寫）」，庫存燈號表沒有 Samsung，圖表的線停在 Nov。
3. **三品類 CHART1 當月沒標 `Oct(F)`**（上月是手動修的）。
4. **品牌配色會換**：TV 的 TCL 和 Samsung 互換顏色，NB 的 Asus 換色。
5. **AI 文字瑕疵**：MNT 出現 `**…**`；「趨勢判讀：月度採購趨勢（分析）摘要：」標題重複；NB 把 Y26 寫成「明年度」。

## 問題

**Q1【完整度】** [c02] 以「任一品牌已 submitted」就把該月當成最新完整月份。202610 NB 的 Dell、Acer、MNT 的 Samsung 都還沒填，報告卻照常產出，而且沒有任何警告。產出前是否應該檢查各品牌的填報完整度？少了品牌時，要警告、暫停產出，還是沿用上期資料？

**Q2【缺填品牌處理不一致】** MNT 的 Samsung 10 月沒填，但各區塊的處理方式不同：
- 1a 年度表：只抓當月送出的資料，所以整列是「-」，Major 加總也不含 Samsung。
- 1b 季度、2a 月度、2b MoM：抓各月份最新一筆，所以用了 9 月的舊值，Major 加總含 Samsung。

結果是 26 4Q 只加兩個月（1.4，QoQ -42%），Dec 的 Major MoM 失真（-52%），標籤又寫「Major 4」。為什麼各區塊的取數邏輯不同？缺填品牌應該統一怎麼呈現？

**Q3【NB 品牌消失】** NB 沒有固定的 `brand_order`，`get_brand_order` / `get_yearly_data` 只抓當月有送出的品牌，Dell、Acer 因此整個消失，「Major 6」變成「Major 4」。這是預期行為嗎？

**Q4【當月預測標記】** `extract_chart_intermediate` 用 `is_forecast = period > fill_period` 判斷，當月不會被標成 (F)。202609_2 是手動改成 `Sep(F)`、`forecast_from_index` 13→12，202610 又出現同樣的問題。但 YTD 的定義是「不含當月，當月尚未結算」。當月到底該算實際值還是預測值？附件 SVG 目前沒有畫出預測段，要不要一致？

**Q5【品牌配色】** `CHART_COLORS` / `COLORS` 是照排名位置 `bi` 給色，排名一變顏色就換（TV 的 Samsung 和 TCL 互換、NB 的 Asus 因 Dell 消失而換色）。能不能讓每個品牌的顏色固定？

**Q6【LLM 輸出清理】** `generate_insight` 的 prompt 要求不要 markdown，但 MNT 季度分析還是出現了 `**…**`。另外月度判讀的開頭變成「趨勢判讀：月度採購趨勢摘要：」，跟固定標題重複。有沒有做輸出後處理？

**Q7【LLM 上下文】**
- `yearly_summary` 沒告訴 LLM 現在是哪一年，NB 年度分析因此把 Y26 寫成「明年度」。
- `mom_summary` 用 `monthly_series[-3:]` 取各品牌序列的最後 3 筆，沒有帶月份標籤。MNT 的 Samsung 序列只到 Nov，它的「近三月」是 Sep–Nov，其他品牌是 Oct–Dec，LLM 卻拿來直接比較。

prompt 的資料要怎麼補？

**Q8【Y26 (Pre) 定義】** TV Samsung 的 Y26 (Pre) 是 36.0，但 202609 報告的 Y26 (Cur) 是 32.7。其他品牌和 NB/MNT 的 Pre 都等於上期的 Cur。Pre 取的是 `target_month = fill_month-1` 的「最新一筆送出」，會不會被後來的重新送出或 10 月填報蓋掉？Pre 應該代表「上期報告當時的值」還是「目前最新值」？請查 Samsung 的 target 2026/9 `yearly_bp_current` 有幾筆送出紀錄。

**Q9【年度和季度沒對齊】** TV TCL 的 Y26 年度是 33.0（`yearly_bp_current`），但 2026 四季 monthly 加總是 30.6。其他品牌兩者一致。要不要在 [c07] 加一道年度值 vs 月度加總的差異檢查？

**Q10【品質關卡範圍】** [c07] 目前只檢查格式（佔位符、長度、JSON、HTML 結構）。上面這些內容面的問題（品牌數比上期少、series 裡有 null、季度只加到部分月份、AI 文字含 markdown）都沒被擋下。要擴充哪些內容檢查？
