# ir_calendar 在 Databricks 的分層設計（bronze / silver）

> 2026-09-21。適用 `jobs/ir_calendar_init_tables/`（建表）與 `jobs/ir_calendar_consume_batches/`（消費 job）。
> 分層通則見 `docs/conventions.md` 2.1；本文只講這個領域怎麼套。

## 1. 一句話

爬蟲批次進 Databricks 只做兩件事：**bronze 原樣收下、silver 算成能查的形狀**。bronze 的 schema 永遠不改，silver 隨時可以從 bronze 重算。

## 2. 為什麼不是「一種 record_type 一張表」

第一版把爬蟲的每種 `record_type` 各建一張表、直接 MERGE 進去，8 張。用 lakehouse 的角度看，那是把 bronze 和 silver 揉在一層：

| 問題 | 後果 |
|---|---|
| 攤成型別欄位 | 爬蟲多一個欄位就要改 DDL、schema、row 函式三處；沒改就默默丟掉 |
| MERGE 覆蓋 | `document_file` 新 revision 蓋掉舊 sha、主檔快照只剩最新；歷史只能回 Volume 歸檔翻 |
| 表數隨 record_type 長 | 3 列的分類常數也一張表；工作狀態（docs manifest 的 wanted / missing）也一張表 |
| silver 壞了無法重建 | 因為沒有 bronze，只能從 Volume 的 JSON 重刷 |

## 3. 現在的結構

```
內網目錄 batches/<批次>/           ← 爬蟲 VM 發布，不可變
   │  GET + sha256 核對
   ▼
Volume（實體檔落地 + JSON 歸檔）    ← 給人看、給 PDF 用
   │
   ├─► b_ir_calendar_record         ← bronze：一檔一列，payload = JSON 全文，append-only
   │        │  from_json + select（純函式，本機可測）
   │        ▼
   │   s_ir_calendar_conference / summary / document_file / company   ← silver：MERGE，給查詢
   │
   └─► b_ir_calendar_batch_log      ← bronze：每批處理紀錄 + API 回應（job 遙測）
```

### 3.1 bronze：`b_ir_calendar_record`

- **一列 = 批次裡的一個檔案**。`record_type` 來自 manifest；`payload` 是 JSON 全文（STRING）。實體檔（PDF / HTM）本體在 Volume，bronze 那列的 `payload` 是 manifest 該條目、`volume_path` 是落地位置。manifest 本身也一列（`record_type = batch_manifest`）。
- **所有 record_type 共用一張表**。爬蟲新增 record_type 不用建表，自動進來；`CLUSTER BY (record_type)` 讓 silver 只讀自己那一型。
- **append-only**。重跑同一批：`DELETE WHERE batch_id = X` 再 append。不 MERGE、不去重、不改內容。
- **schema 固定 11 欄**：`batch_id / seq / record_type / batch_path / company_key / period / sha256 / bytes / volume_path / payload / ingested_at`。爬蟲加欄位只會出現在 `payload` 裡。
- 直接查用 Databricks SQL 的路徑運算子：`payload:conference_date`、`payload:summary.guidance`。

### 3.2 bronze：`b_ir_calendar_batch_log`

每批一列：manifest 摘要（seq、kind、producer、counts）、本 job 的處理結果（落地 / 歸檔 / bronze 列數、SUCCESS / FAILED、錯誤）、API 回應（`api_results` 陣列）。這是 job 自己的紀錄不是來源資料，所以允許以 `batch_id` MERGE 覆蓋。

### 3.3 silver：4 張

| 表 | 鍵 | 來源 record_type | 保留 |
|---|---|---|---|
| `s_ir_calendar_conference` | `(company_key, period, revision)` | `ir_conference` | 每個 revision 一列；目前版本取 `max(revision)` |
| `s_ir_calendar_summary` | `(company_key, period)` | `ir_summary` | 同鍵以較新批次為準 |
| `s_ir_calendar_document_file` | `volume_path` | `ir_document_file` | 同名檔以較新批次為準（舊版 sha 仍在 bronze） |
| `s_ir_calendar_company` | `company_key` | `app_company`（rows[] 展開） | 同鍵以較新批次為準 |

不建 silver 的：`app_company_category`（3 列常數，`category_name` 已在 company 表）、`ir_document`（docs manifest，是爬蟲的工作狀態）、`api_payload`（送出去的 body，回應在 batch_log）。都在 bronze，要查就查 `payload`。

### 3.4 bronze → silver 的轉換

- 純函式 `transform_<短名>(df_bronze) -> DataFrame`，只用 `F.from_json` + `select`，本機 pyspark 可測（`tests/test_ir_calendar_consume.py`）。
- payload schema 只列 silver 要的欄位：爬蟲多的欄位自動忽略、少的補 NULL。
- `latest_per_key`：同鍵多列時取 `seq` 最大的（批次越新越大），再 MERGE。**逐批增量與整表重算用同一套函式**，所以 `rebuild_silver` 的結果等於逐批累積的結果。
- 時間：`ts_col` 把帶時區的字串照用、不帶時區的補 `+08:00`（爬蟲在台北），存 UTC 瞬間。日期：`date_col` 只解析、不換算，`conference_date` 是台北曆日（爬蟲端已統一，Databricks 不碰）。

## 4. 一次執行的順序與失敗語意

```
下載 + sha256 → 落 Volume / 歸檔 → bronze（刪後 append）→ silver（MERGE）→ POST API → batch_log SUCCESS → 推游標
```

任一步例外：batch_log 寫 FAILED、游標不動、job 失敗。下次從同一批重來：Volume 同名覆蓋、bronze 刪後重寫、silver MERGE、API 有 `Idempotency-Key`，重來不會多寫。

游標留在 Volume 的 `_cursor.json`（不在 Delta）：不依賴表已建好，補批次後人工改 `last_seq` 就能重處理。

## 5. 為什麼 payload 用 STRING 不用 VARIANT

DBR 17.3（Spark 4.0）有 `VARIANT`，查詢與儲存效率較好。這裡選 STRING 的理由：

1. 本機 pyspark 3.5 沒有 VARIANT，silver 的 transform 用 `from_json` 才能在 `tests/` 跑。
2. Databricks SQL 的 `payload:欄位` 路徑運算子對 STRING 一樣可用，日常查詢體驗相同。
3. 資料量小（每天數十列），VARIANT 的效能差異看不出來。

要換：bronze 加一欄 `payload_v VARIANT GENERATED ALWAYS AS (parse_json(payload))` 或直接改型別，silver 的 transform 改用 `variant_get`。屬於之後的優化，不影響現在的設計。

## 6. 維護對照表

| 情境 | bronze | silver |
|---|---|---|
| 爬蟲多一個欄位 | 不用改 | 要用才改：DDL `ADD COLUMNS` → payload schema → transform 的 select |
| 爬蟲多一種 record_type | 不用改 | 要查才建：DDL → `TABLE_KEYS` → `transform_<短名>` → 登記 `SILVER_TRANSFORMS` |
| silver 邏輯改了 / 資料壞了 | 不動 | 消費 job `rebuild_silver = true` 整表重算 |
| 要看某批當時送了什麼 | `WHERE batch_id = X`（含 `batch_manifest` 那列） | 看 `batch_id` / `seq` 血緣欄位 |
| 要看 API 有沒有失敗 | `batch_log.api_results`（`explode` 後看 `failed` / `failures_json`） | 無 |

## 7. 下一層（gold）什麼時候建

目前沒有 gold。當出現「月份 × 分類的場次數」、「某公司歷年法說清單」這種固定報表或 Genie Space 需求時，從 silver 建 `g_ir_calendar_*`；不從 bronze 直接建，也不回頭改 silver 的鍵。
