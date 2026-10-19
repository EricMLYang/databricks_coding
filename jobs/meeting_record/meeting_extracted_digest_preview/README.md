# meeting_extracted_digest_preview

月報版面草稿（會議紀錄 × Sales Brief）的**預覽工具**，拿去跟 user 討論版面用；不是正式產出、不寫表。

- 輸入：`g_meeting_items_sem_bu`（003 建、`meeting_extracted_sem_stage_a` 寫；已 token 化，無人名）
- 輸出：`displayHTML` 預覽 ＋ 印出 markdown 全文（可貼到文件）
- 參數（widgets）：`catalog`、`schema`、`unit`、`customer`（entity_id；空 = 不限）、`app`（TV / NB / MNT；空 = 不限，`ALL` 條目一律納入）、`month`（yyyy-MM；空 = 條目最多的月）、`max_per_topic`、`include_dups`
- 排程：無，手動。
- 負責人 / 更新日期：（填）/ 2026-10-19

## 版面（[c03] `build_sections`）

| 節 | 內容 | 資料來源 |
|---|---|---|
| 1 資料範圍 | 月份、信件數、場合數、條目數（原始 / 去重）、S2 數 | 鏡頭表 |
| 2 本月重點（示意） | 前三大主題的條數與陳述類型；正式版由 LLM 產摘要 | 鏡頭表 |
| 3 主題對照 | 主題｜會議說了什麼（每條：日期 摘要（場合））｜Sales Brief 說了什麼｜狀態 | 會議欄來自鏡頭表；**後兩欄是示意文字**，W2 對照（§4.3–§4.5）做完才接 `g_meeting_sb_reconcile_bu` |
| 4 事件時間軸 | 日期、類型、內容、發言方、場合 | 鏡頭表 |
| 5 背景情報與口徑 | 同客戶 / 應用跨月的 intel / semantic 候選 ＋ PM 審核狀態 | 鏡頭表 |
| 6 待確認 | 分類與先驗不同、信心 < 0.6、S2 | 鏡頭表 |
| 7 資料缺口 | 固定文字：ETL 截斷、客戶欄空值、附件不讀、同文合併、人名代號 | — |

主題中文名與順序在 [c02] `TOPIC_ZH`（商務在前、工程在後）。改版面只動 [c03]。

## 跟 user 討論時要問的

1. 月報的單位：客戶 × 應用（現在這樣）、會議系列、還是主題跨客戶？
2. 第 3 節的「狀態」要幾種（一致 / 只有會議 / 只有簡報 / 矛盾）？誰處理矛盾？
3. 事件要不要全列，還是只列要求 / 決定 / 問題？
4. 第 5 節的情報與口徑要不要放進月報，還是另一份文件？
5. 對外版（給客戶端 / 業務以外）要遮哪些：S2、金額、對手報價？

純函式測試：`tests/test_meeting_extracted_digest_preview.py`（[c02]、[c03]）。
