# meeting_record_weekly_report

- 用途：每週看 meeting record 兩張表進了幾筆、寄件人（`mail_from`，誰記的）與信件標題（`mail_subject`）。前身是 `jobs/MeetingRecord_Weekly_Ingestion_Report.py`（只算筆數）。**只讀，不寫任何東西。**
- 輸入：`b_internal_meeting_record`、`b_internal_meeting_record_scm`（欄位：`create_date`、`mail_from`、`mail_subject`）
- 輸出：stdout 文字報告 + `display` 表格 / 圖
- 參數（widgets）：`catalog`、`schema`、`tables`（逗號分隔）、`run_date`（空 = 今天）、`weeks_back`、`detail_weeks`、`detail_limit`、`top_senders`
- 排程：每週人工 Run All（all-purpose 或 job cluster 都可以）
- 負責人 / 更新日期：（填）/ 2026-09-25

純函式測試：`tests/test_meeting_record_weekly_report.py`（[c02]～[c03]）。
