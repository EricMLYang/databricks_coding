# meeting_extracted_w2_t5_export

W2 Sales Brief 鏡頭的 T5（規格 §4.5、§4.6）：T4 寫好的對照格 → 關卡彙總 ＋ PM 審核例外清單 md。無 LLM、不改表。決定見 `../meeting_extracted_migration/STATUS.md` D37。

- 輸入：`v_meeting_sb_reconcile_q`（004；本期格，含 `relation_rank / effective_relation / review_pending`）、`v_meeting_items_sb_q`（004；本期 active 且 sb_relevant 的條目，當證據）
- 輸出：印出的 md（使用者整段複製貼給 PM）；`dry_run = false` 時在 `b_meeting_migration_log` 寫一列 `slug = w2_t5_export:<brief_month>`（關卡結果 JSON）
- 參數（widgets）：`catalog`、`schema`、`unit`、`brief_month`（空 = 本月）、`max_evidence`（每格證據條數；other 格每個主標籤幾條）、`max_other_ids`、`include_corroborate`、`dry_run`
- 排程：每月一次，T4 之後。
- 負責人 / 更新日期：（填）/ 2026-10-23

## md 版面（§4.6）

每 app 一節；節內固定順序 **conflict → supplement → meeting_only → ALL 格（跨客戶訊號）→ corroborate**，`sb_only` 只給一行計數。
同節內品牌格依 `n_items` 降冪，`UNKNOWN`（客戶不明）品牌格排該節最後。分節用 `effective_relation`（PM `fix_relation` 後的值），
標題顯示 `原判 → PM 改 X`。

每格：標題（app × 品牌 × 面向｜relation（basis）｜敏感度｜條目數（送 LLM 數）｜窗口）→ 填報原文 → 會議摘要（內部版，含 S2）→
外送版（驗證失敗則提示 PM 自己寫）→ 理由｜數字口徑 → 證據前 N 條（日期｜發言方｜類型/標籤｜敏感度｜摘要｜「原文」｜pk seg）→
其餘 item_id → 審核欄（待審 / verdict → relation｜note｜reviewer）。`other` 格的證據依 `topic_tag_primary` 分組、每組最多 N 條。
ALL 格另列 `cross_customer_note` 與同 facet 被標 `cross_customer_flag` 的品牌。

md 開頭：格數與 relation 分布、待審 / 已審數、軟關卡 WARN、怎麼審（`agree / fix_relation / drop`）、PM 直接 UPDATE 表的 SQL 範例。
人名不出現：條目本來就是 `<Pnn>` token，[c04] 再把 email 樣式換 `<email>`，[c30] 驗 md 無 email。

## 關卡（[c12]）

| 類型 | 條件 | 說明 |
|---|---|---|
| 硬（assert 停） | 本期 0 格 | T4 還沒跑這一期 |
| 硬 | 本期 `prompt_version` 不只一種 | T4 換版後沒整期重跑 |
| 硬 | llm 格沒 `meeting_summary` / `relation` 不合法 | T4 [c30] 應已擋，雙保險 |
| 軟（WARN） | meeting_only 格沒摘要 | T4 摘要批失敗或被 `max_cells` 跳過 |
| 軟 | 外送版驗證失敗 > 20% | T4 [c04] S2 規則要調 |
| 軟 | T3 本期相關條目數 ≠ 品牌格 `n_items` 合計 | T3 在 T4 後又重標，T4 要重跑 |
| 軟 | 本期沒有任何填報文字 | brief 還沒填，預期內 |

## 怎麼跑

1. T4 同一期跑完（[c30] 過）→ T5 `brief_month` 同一期、`dry_run = true` → 看 [c12] 彙總與 WARN、[c21] 的 md。
2. 要留紀錄：`dry_run = false` 再跑一次（只多寫一列 log）。
3. md 整段複製給 PM；PM 審完直接 UPDATE 表（md 開頭有 SQL）。T4 重跑不覆蓋審核欄；T5 重印會把 PM 改過的 relation 分到新的節。

純函式測試：`tests/test_meeting_extracted_w2_t5_export.py`（[c02]～[c05]；篩選在本機 Spark 以假表實跑）。
