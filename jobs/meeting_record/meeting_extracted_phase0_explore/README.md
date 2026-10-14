# meeting_extracted_phase0_explore

- 用途：會議紀錄萃取（PM_Head `metting_record/01_meeting_to_sales_brief_進階規劃.md` v0.4.1）Phase 0 探勘。回答 §11 Phase 0 的統計題：正文欄可用性、`mail_from` 格式、部門代碼、md 標頭與 `Sent:` 日期、三正文一致性、content_type 粗估、email 網域、客戶頻率、跨信重複量級、Sales Brief 文字表欄位與填報時間、`entity_alias` 是否存在。**只讀，不寫任何表**；一次性，用完封存，不升級成 Job（§2.3）。
- 輸入：`b_internal_meeting_record`（不讀 `mail_body_html`）、`g_sales_brief_brand_summary` / `g_sales_brief_app_summary` / `g_sales_brief_market_intelligence`、`mi3_semantic.entity_alias` / `dim_entity`、`information_schema.tables`
- 輸出：stdout；[c30] 印一段 JSON（只有統計、網域、AUO 部門代碼，不含姓名與 email），整段貼回給 Agent
- 參數（widgets）：`catalog`、`schema`、`source_table`、`date_from` / `date_to`（對 `mail_date`，預設 2026-06-01 ~ 2026-09-30）、`sb_periods`
- 排程：無，人工 Run All（serverless / all-purpose / job cluster 皆可；不用 cache）
- 負責人 / 更新日期：（填）/ 2026-10-14

content_type 與重複率是 mail 層粗估（尚未分段、token 化），只用來定門檻量級。

純函式測試：`tests/test_meeting_extracted_phase0_explore.py`（[c02]～[c06]，本機 pyspark 3.5）。
