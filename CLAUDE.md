# CLAUDE.md

## 這個 repo

Databricks 開發的 Agent 輔助工作區。使用者貼 code 請求修改，或用描述請求生成；產出是要放到 Databricks 上跑的
Notebook（`.ipynb`）、SQL query、開發 / 修改建議，偶爾是 Genie Space 設定草稿。
本機不是執行環境，只做 lint 與純邏輯測試。規劃：`docs/20260917_repo_initial_plan.md`；細部規則：`docs/conventions.md`。

## 固定環境

- DBR **17.3 LTS**（Spark 4.0、Python 3.12）、**job cluster**、Unity Catalog。
- 預設 catalog / schema 只在 `config/project.yml` 填；code 一律用參數帶入，不寫死。
- 目前**不連線 workspace、不部署**。查不到 schema 就問，不猜欄位。

## 產出規則

- 主要格式 `.ipynb`；每個 code cell 第一行是標籤 `# [cNN] 名稱`（SQL cell 用 `-- [cNN]`）。
- 局部修改**以整個 cell 為單位**輸出：`### [c05] 名稱 → 替換整個 cell` + 完整 code block，讓使用者直接貼上。
  動作只有：替換整個 cell、新增於 [cNN] 之後、刪除、不變。新增用字母尾碼 `[c05a]`，不重新編號。
- 回覆順序：變更點摘要 → 逐 cell 完整內容 → 假設與需確認事項。
- 改 `.ipynb` 檔用 `python tools/nb.py`，不手改 JSON。新 notebook 從 `jobs/_template/` 複製。
- 轉換邏輯寫成 `DataFrame -> DataFrame` 純函式放獨立 cell，不含 I/O，才能被 `tests/` 載入測試。

## Databricks 開發原則

**資料量與費用**
- 大表一律先過濾再處理：日期 / partition 條件放最前面，用 `run_date` 做增量，不全表重算。
- 不把大表拉回 driver：禁止無 limit 的 `collect()` / `toPandas()` / `display()` 全表；取樣用 `limit`。
- 不為了 log 對大表 `count()`；需要筆數用寫入後的 Delta metrics 或一次算完。
- 避免小檔案：不用 `repartition(1)` / `coalesce(1)` 寫大表；partition 欄位選低基數、常用於過濾的欄位。
- 開發期用抽樣或 `limit` 驗證邏輯，不反覆對全表跑。

**效能**
- 內建函式 > pandas UDF > Python UDF；能用 `F.*` 就不寫 UDF。
- join 前先 `select` 需要的欄位與 `filter`；小表明確 `broadcast`；留意 skew 鍵。
- 同一 DataFrame 要多次 action 才 `cache`，用完 `unpersist`；不預設 cache。
- Window 一定有 `partitionBy`；`collect_list` / `collect_set` 要確認上限。
- 避免 `withColumn` 迴圈幾十次；改用一次 `select` 或 `withColumns`。

**Catalog 與資料**
- 三段式 `catalog.schema.table`；不用 `hive_metastore`、不用 mount、不用 `dbfs:/` 路徑；檔案走 UC Volume。
- 讀寫都是 Delta。每次寫入明示 append / overwrite / MERGE；MERGE 必須有明確、唯一的鍵值。
- Schema 變更用 `mergeSchema` / `overwriteSchema` 時要在 cell 註明原因。
- 憑證只走 `dbutils.secrets` 或 job parameters，不出現在 code。

**Spark 4.0 / DBR 17.3**
- ANSI mode 預設開啟：溢位、非法 cast、除以零會拋錯。需要寬鬆行為用 `try_cast` / `try_divide` 並註明。
- DataFrame API > Spark SQL > pandas API on Spark；不用 RDD、`sc`、`spark.sparkContext`。
- 日期 / 字串轉型一律指定格式；不依賴隱式轉型。

**Databricks 特有**
- 參數用 `dbutils.widgets`，由 job parameters 覆蓋；notebook 不能有互動式依賴。
- 套件安裝放 cluster library；不得已才在第一個 cell `%pip install` 並註明。
- `display()` 只用於開發 cell；job 流程用 `print` 精簡 log，不印大量資料。
- SQL 用 Databricks SQL 語法，大 query 拆 CTE。Genie 建議以 table / 欄位語意與 sample questions 為主。

## 不要做

- 不建立部署檔、不嘗試連線 Databricks。
- 不 commit / push，除非使用者要求；commit 前先 `python tools/nb.py strip <nb>`。
- 不直接覆蓋使用者貼上的 code；以 cell 為單位回覆，或另存到 `jobs/`。
