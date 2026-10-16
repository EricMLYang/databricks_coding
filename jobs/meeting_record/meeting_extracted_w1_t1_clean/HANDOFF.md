# HANDOFF — 2026-10-16 中斷點（下次 session 先讀這份）

總覽與決定（D1–D25）在 `../meeting_extracted_migration/STATUS.md`；這份只寫「現在停在哪、下一步做什麼」。

## 1. 現在的狀態

| 項目 | 狀態 |
|---|---|
| W1 task 1 `meeting_extracted_w1_t1_mail` | ✅ Databricks 已正式寫表（493 封）。STATUS §6.1 三段診斷 SQL 使用者還沒跑（去重落差 17 vs 112 未解，不擋） |
| W1 task 2 `meeting_extracted_w1_t1_clean`（本資料夾） | ✅ 2026-10-16 Databricks `dry_run = false` 寫表完成，[c30]：1,865 段 / stale 0 / dup_keys 0 / email_left 0 / dangling 0。段 0 抽查 SQL（STATUS §6.2 第 6 點）還沒跑 |
| W1 task 3 `meeting_extracted_w1_t2_extract`（T2 L1，LLM） | 🟡 repo 與 Databricks 同步（13 cell；[c11a]、[c12a] 除錯 cell 兩邊都已刪）。dry_run 四輪調完（§3）。**2026-10-16 下午全量 backfill 跑中**：`prompt_version 0.2`、`dry_run false`、`max_segments 0`、`run_mode backfill`、`date_from 2026-06-01`、`concurrency 4`；約 1,180 段、估 70 美元；開跑 2 小時時還在 [c11]，預估 2.5–3.5 小時（[c11] 不印逐段進度，正常）。**使用者還沒貼 [c12] / [c30] 結果**。D22–D25 |
| 本機測試 | `py -3.10 -m pytest tests/test_meeting_extracted_w1_t2_extract.py` 15 passed、ruff clean；task 1 / task 2 的 tests 沒動 |
| git | ✅ 2026-10-16 已 commit（task 3 資料夾、tests、STATUS.md、本檔）；之後若全量結果要求改 cell，再另 commit |

## 2. 下一步（照順序）

1. **接全量結果**：使用者貼 [c12] JSON log 與 [c30] dict。看：`endpoint errors`（有就 `run_mode = incremental`、`retry_failed = false` 再跑一次撿回，D24）、`segments_truncated`、quote / schema 失敗率（硬關卡 15% / 10%）、S3 命中率、`est_cost_usd`；[c30] 的 S3 = 0、dup 0。
2. **出 summary 人名抽查 SQL**（答應過使用者）：對 `g_meeting_items_bu` 的 `summary` / `quote` 找「大寫開頭英文字」樣式（排除詞表裡的產品 / 公司 / 縮寫），只輸出 pk / item_id / 遮罩形狀 / 命中字，不輸出全文。命中多就升 prompt 0.3 或擴大 [c05] 的 S3 掃描。
3. **[c11] 加進度 log**：每 50 段印 `done / total | elapsed s | errors`（ThreadPool 改 `as_completed` 或用 counter + lock），避免 backfill 盲等；順便把 [c12] 的 `latency_p50_s` 旁加 mean / max。改完補 tests、附同步清單（只替換 [c11]、[c12]）。
4. 段 0 抽查（task 2，STATUS §6.2 第 6 點）＋ cleaner 0.2（去 `**` 殘渣、名單段歸 `attachment_only`）；升版後 incremental 自動重洗 + 重萃。
5. W1 三個 task 串成一個 Job 週跑（`run_mode = incremental`）；加規格 §2.4 設定一致性檢查。
6. 之後：golden set 模板（有了才做 llama 比較、§9.2 指標）、003 migration（Sales Brief 鏡頭表、column mask、分應用 View）、W2 T3–T5（STATUS §6.4）。

## 3. 掛著的問題（都不擋）

- task 1 `dup_of_pk` 3.4%（17 封）vs Phase 0 整封相同 112 封：口徑不同，診斷 SQL 在 STATUS §6.1，使用者還沒跑。
- task 1 有 1 封 `mail_from` 解析失敗、1 筆 `auo.comhi` 網域。
- task 2 紀要若整封是 md 表格切不開，整筆一段送 T2（3.2k 字那類）；Phase 1 接受。簡轉繁沒做（D17）。
- task 3 第一次 dry_run（2026-10-16，10 段）：端點與 cache 正常（system 約 5.7k token 全走 cache_read）；pk 112 五段是「附件轉寄 ＋ 與會名單」被 task 2 當 `thread_reply`（名單撐過 300 字）→ LLM 回 `empty`，可接受，cleaner 0.2 考慮「只有名單的段」歸 `attachment_only`；4 段紀要輸出超過 4,000 token 截斷 → 已把 `L1_MAX_TOKENS` 提到 16,000、截斷時改用 COMPACT_HINT 重打。
- task 3 第二次 dry_run（10 段，改完 max_tokens 後）：90 條全 ok、quote 失敗 0、S3 0、customer 全對上、截斷 1 次後精簡重打成功；費用 0.64 美元（八成是輸出 token，約 5.2 萬），全量估 80–100 美元，比 §10.1 高一倍多。樣本品質可接受（pk 120 整封紀要拆 22 條，事實 / 要求有分開，S2 判定合理）。**發現 clean_text 有 md 粗體殘渣**（`** **`、`1****月`）會進 quote，不影響驗證但難看 → cleaner 0.2 待辦：去掉落單的 `**`。thread 段（有 `<Pnn>` 發言人）還沒出現在樣本，等 50 段那輪看 speaker_token。
- task 3 第三次 dry_run（50 段）：482 條、schema 失敗 1、quote 失敗 104 → [c05] 比對改三層（去空白 / NFKC / 去標點符號）＋「…」串接片段後剩 5（1%）；thread 段 speaker_token 正確（P09 → customer）；**summary 抄進未 token 化的英文名（Luke, Juno）** → prompt 升 0.2 加人名規則、S3 掃描加英文名首字整字比對、關卡改 D25。費用 3 美元 / 50 段 → 全量估 70 美元。
- **thread 近似段**：同一 thread 的兩段（152-7、152-8）內容近似但不完全相同，`content_hash` 抓不到，各萃出一組相同的事 → 條目重複。Phase 1 接受；之後可考慮段層近似去重或 T3 以 `item_key` 外的相似度合併。
- task 3 詞彙表壓縮版實測 system ≈ 5.7k token；`terms_mentioned` 只收 LLM 給的、不回查詞表。`sensitivity` 關鍵字「數字＋K」可能把「10K 片」以外的也抓成 S2，看樣本再收。

## 4. Commit 提醒

2026-10-16 的改動已 commit（使用者要求）。之後改 notebook 的固定流程：

```
py -3.10 tools/nb.py strip jobs/meeting_record/meeting_extracted_w1_t2_extract/notebook.ipynb
py -3.10 -m ruff check tests/test_meeting_extracted_w1_t2_extract.py
py -3.10 -m pytest tests/test_meeting_extracted_w1_t2_extract.py -q
```

不 commit / push，除非使用者要求。

## 5. 使用者的固定要求（別忘）

- 使用者只能**複製貼上**到 Databricks；每次改 notebook 後回覆最後附「Databricks 同步清單」（哪個檔、哪個 cell 替換 / 新增於哪之後 / 刪除 / 整支匯入），不解釋工具指令。
- 跑在 serverless：不 `cache` / `persist`。
- 本機測試用 `py -3.10`，Windows console 要 `PYTHONIOENCODING=utf-8`。`tests/` 整包 ruff 有 ir_calendar 舊檔的 E501，與本案無關。
- 不 commit / push，除非使用者要求；commit 前 `nb.py strip`。
- 外部公司人員資訊不進 repo；tests 用假名與 `.example` 網域。prompt 不帶姓名 / email。
