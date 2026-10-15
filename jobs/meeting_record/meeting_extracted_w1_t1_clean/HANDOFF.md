# HANDOFF — 2026-10-15 中斷點（下次 session 先讀這份）

總覽與決定（D1–D21）在 `../meeting_extracted_migration/STATUS.md`；這份只寫「現在停在哪、下一步做什麼」。

## 1. 現在的狀態

| 項目 | 狀態 |
|---|---|
| W1 task 1 `meeting_extracted_w1_t1_mail` | ✅ Databricks 已正式寫表（493 封；mail 表 + participants 表）。使用者沒貼 [c30] 與 STATUS §6.1 的三段診斷 SQL 結果（去重落差 17 vs Phase 0 112 未解，不擋） |
| W1 task 2 `meeting_extracted_w1_t1_clean`（本資料夾） | 🟡 Databricks `dry_run = true` 第 3 輪**關卡全過**，**還沒跑 `dry_run = false`**，清洗表目前是空的 |
| Databricks 上的 notebook | 與 repo 的 `notebook.ipynb` **同步**（最後一次同步：[c02]、[c05] 替換，已跑過 dry_run 確認） |
| 本機測試 | `py -3.10 -m pytest tests/test_meeting_extracted_w1_t1_clean.py` 14 passed；ruff clean；notebook 已 strip |
| git | ✅ 已 commit 並 push：`75f3d97`（含 eda80fb 一起推上 origin/main）。之後的改動再照第 4 節流程 |

最後一輪 dry_run 的 [c12] log（2026-10-15）：

```
mails_in_batch 493（skip none 22 / 整封重複 17 / oversize 0）→ 454 封分段、1,865 段、每封 4.1 段
content_type: thread_reply 981 / inline_minutes 583 / noise 228 / attachment_only 49 / appointment 24
extractable 1,564；dup_of 24.4%（398 段）；clean_len P50 603 / P95 7,636；compress 0.58；over_12k 1
date_inferred 11%；customer_hint 47.7%；app_hint 63.6%；emails_masked 128（56 段）；residual_names 0
seg0_kept 199（三輪分別 214 → 214 → 199；剩下的內容還沒看過）
```

## 2. 下一步（照順序）

1. **使用者在 Databricks**：同一支 notebook，widget `run_mode = backfill`、`date_from = 2026-06-01`、`dry_run = false`，從頭跑全部 → 貼 [c30] 輸出（期望 `stale 0`、`dup_keys 0`、`email_left 0`、`dangling 0`、`batch_segments_in_table` ≈ 1,865）。
2. **寫表後抽查段 0**（SQL 在 STATUS §6.2 第 6 點）：看那 199 段是轉寄人附註（該留）還是殘渣（要加規則）。要改規則就出 `cleaner_version = 0.2`：改 [c05]、升 [c01] 預設值、補 tests、更新 README；incremental 會自動重洗舊版本的 pk。
3. **Agent 開發 task 3（T2 L1 萃取）**：計畫在 STATUS §6.3。**開工前先問使用者**：LLM 走 `ai_query` 還是 Foundation Model API、模型名、每次跑最多幾段 / 費用上限。
4. 之後：golden set 模板、003 migration（Sales Brief 鏡頭表、column mask、分應用 View、`b_meeting_job_run_log`）。

## 3. 掛著的問題（都不擋）

- task 1 `dup_of_pk` 3.4%（17 封）vs Phase 0 整封相同 112 封：口徑不同（初洗後 vs 原文），診斷 SQL 在 STATUS §6.1，使用者還沒跑。
- task 1 有 1 封 `mail_from` 解析失敗（Phase 0 之後新進的 3 封之一）、1 筆 `auo.comhi` 網域（來源資料黏字）。
- task 2 紀要若整封是 md 表格（型號在格子裡不在行首）切不開，整筆一段送 T2（pk 120 那類，3.2k 字）；Phase 1 接受。
- 簡轉繁沒做（D17）；只寫英文名字的稱呼（Hi Quinn）不換 token（D17）。

## 4. Commit 提醒

2026-10-15 已 commit / push 到 `75f3d97`。之後的改動**要先問使用者**，同意後：

```
py -3.10 tools/nb.py strip jobs/meeting_record/meeting_extracted_w1_t1_mail/notebook.ipynb
py -3.10 tools/nb.py strip jobs/meeting_record/meeting_extracted_w1_t1_clean/notebook.ipynb
py -3.10 -m ruff check tests/
py -3.10 -m pytest tests/test_meeting_extracted_w1_t1_mail.py tests/test_meeting_extracted_w1_t1_clean.py -q
git add jobs/meeting_record/meeting_extracted_migration/STATUS.md jobs/meeting_record/meeting_extracted_w1_t1_mail jobs/meeting_record/meeting_extracted_w1_t1_clean tests/test_meeting_extracted_w1_t1_mail.py tests/test_meeting_extracted_w1_t1_clean.py
```

建議 commit 訊息：

```
meeting_extracted: W1 task 1 (mail/participants) + task 2 (clean/segments), STATUS D12–D21

- w1_t1_mail: T1-a/T1-m/T1-c, executed on Databricks (493 mails)
- w1_t1_clean: T1-b segmentation, tokenization, content_type, content_hash/dup_of; dry_run gates pass, not yet written
- STATUS.md: decisions D12–D21, progress, next steps (T2 L1 plan)

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
```

## 5. 使用者的固定要求（別忘）

- 使用者只能**複製貼上**到 Databricks；每次改 notebook 後回覆最後附「Databricks 同步清單」（哪個檔、哪個 cell 替換 / 新增於哪之後 / 刪除 / 整支匯入），不解釋工具指令。
- 跑在 serverless：不 `cache` / `persist`。
- 本機測試用 `py -3.10`，Windows console 要 `PYTHONIOENCODING=utf-8`。
- 不 commit / push，除非使用者要求；commit 前 `nb.py strip`。
- 外部公司人員資訊不進 repo；tests 用假名與 `.example` 網域。
