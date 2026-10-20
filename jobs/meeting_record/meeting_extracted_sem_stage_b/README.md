# meeting_extracted_sem_stage_b

方向 C Stage B（規格 §8.3、`_prompt_weekly_extract.md` v1.1 Stage B）的 Databricks 版：把 PM 審過（`verified = 'y'`）的 semantic / intel 條目併進三張台帳表（005），印兩份 md 的 diff、變更摘要、未審清單、退場候選。**純規則、無 LLM。** 決定見 `../meeting_extracted_migration/STATUS.md` D31。

- 輸入：`g_meeting_items_sem_{unit}`（003 / Stage A）、`g_semantic_record`、`g_semantic_record_evidence`、`g_background_intel`、`v_background_intel_q`（005）
- 輸出：同三張台帳表（append / MERGE）＋ 鏡頭表 `sem_id` 回填（semantic → SEM-xxx、intel → INT-xxx）
- 參數（widgets）：`catalog`、`schema`、`unit`、`stage_b_version`（= [c04] `STAGE_B_VERSION_IN_CELL`，現 0.3）、`intel_auto`（預設 true）、`semantic_auto`（預設 true，D33）、`dry_run`
- 排程：每週，PM 審完之後；沒新條目就印「本次無變更」。
- 負責人 / 更新日期：（填）/ 2026-10-20

## 規則（[c04]）

| 條目 | 做法 |
|---|---|
| semantic，`dup_of` = 既有 SEM id | 該 SEM 加一筆證據（`g_semantic_record_evidence`），`n_evidence + 1`、`last_evidence_date` 更新；不新增 |
| semantic，`dup_of` 空或不存在 | 發下一個 SEM id（接表中最大號）＋ 第一筆證據；投影代號 = `review_note` 裡的代號（`pa:` / `skill:` / `de:` / `genie:` / `brief:` / `mv:`）> `route_hint` > `pa:semantics`；`pm_note` = review_note |
| intel，同 app ＋ 同主題（term 正規化相同）已存在 | 更新 summary / as_of（取較新，不倒退）/ date / source / item_key，`n_updates + 1`；`status` / `pm_note` 不動 |
| intel，新主題 | 發 INT id；`as_of` 用鏡頭表值，不合格式就由 date 推 yyyy-MM |
| intel，verified 空白且 `intel_auto = true`（預設，D32） | 照樣併入，`status = unreviewed`、md 標〔未審〕；PM 之後在鏡頭表標 y → [c21] 改 active，該主題條目全部 n → retired |
| semantic，verified 空白且 `semantic_auto = true`（預設，D33） | 照樣發 SEM id，`status = unreviewed`、md 標〔未審〕；PM 標 y（本條或之後補證據的條目）→ [c21] 改 confirmed，全部 n → retired。unreviewed 的 SEM 沒有 `synced_to`，不會被編進 prompt |
| 同文重複（`dup_key` 非空）、verified 空白，正本 y 或已併（D32） | 跟著正本：semantic 補證據到正本的 SEM、intel 更新同主題；不用逐條標 |
| event、verified = n、semantic 空白 | 不併；空白的列成未審清單 |
| 退場 | `v_background_intel_q.retire_candidate`（as_of 超過兩季）只列不改；PM 把 `status` 改 `retired` |

PM 每週實際要做的（D33）：只看 [c12] 的「關鍵審核清單」——口徑候選（semantic）、Stage A 判定與先驗不同、信心 < 0.6；每週約 5–10 條，標 y / n。其餘 intel 自動併入不用看，看到不對的標 n。`n_updates` 只算正本，同文重複的轉寄副本不計次。

PM 維護的欄（Stage B 永不覆蓋，只有 unreviewed → active / retired 這一種同步）：`g_semantic_record.status / synced_to / pm_note`、`g_background_intel.status / pm_note`。

## 怎麼跑

1. 前置：005 已建表、Stage A 已寫鏡頭表、PM 已在鏡頭表填 `verified`。
2. `dry_run = true`：看 [c12] 的變更摘要與兩份 md diff。
3. `dry_run = false`：寫表；[c30] 驗主鍵、回填、證據數。
4. 換版後先 `dbutils.widgets.removeAll()` 再跑 [c01]，否則舊 widget 的 `stage_b_version` 會擋在 [c11]。
5. 要產整份 md 貼回 PM_Head：跑完後 `md_sem_after` / `md_int_after` 兩個變數就是全文，`print()` 出來複製。

純函式測試：`tests/test_meeting_extracted_sem_stage_b.py`（[c02]～[c05]、[c07]）。
