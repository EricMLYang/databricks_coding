# meeting_record_explore

- 用途：探索用，依時間範圍、BU / SCM、寄件人、標題關鍵字、第幾封到第幾封，把 meeting record 信件內容 print 出來。只讀；唯一例外是 [c20] 人工刪除單封信（cell 內填值、先 DRY_RUN）。
- 輸入：`b_internal_meeting_record`（BU）、`b_internal_meeting_record_scm`（SCM）；固定用到 `create_date`、`mail_from`、`mail_subject`，其他欄位都當成「內容」印出
- 輸出：stdout（目錄 + 逐封內容）
- 參數（widgets）：`source`（ALL / BU / SCM）、`start_date`、`end_date`、`sender`、`from_no`、`to_no`；其他（catalog、schema、標題關鍵字、排序、要印的欄位、截斷字數）是 [c01] 內的常數
- 排程：無，人工互動使用（serverless / all-purpose 皆可；不用 cache）
- 負責人 / 更新日期：（填）/ 2026-10-07

純函式測試：`tests/test_meeting_record_explore.py`（[c02]～[c03]）。
