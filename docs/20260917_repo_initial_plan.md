# Databricks Coding Agent 工作區：需求說明與初始規劃

- 建立日期：2026-09-17
- 狀態：v2（2026-09-17 使用者已回覆六項決定，Phase 0 已建置；見第二部分 E、F 節）

---

## 第一部分：需求整理

### 1. 本 repo 的目的

本 repo 是一個 **Databricks 開發的輔助工作區**。開發者在本機透過 Coding Agent（Claude Code）與 repo 互動，
由 Agent 協助產生、修改、審閱 Databricks 上會用到的程式碼與設定；最終成果部署到 Databricks workspace。

重點不是「在本機跑 Spark」，而是「用 Agent 加速 Databricks 端的開發」。

### 2. 需求範圍

依重要程度排序：

| 優先 | 工作類型 | 說明 | 產出形式 |
|---|---|---|---|
| 主力 | Job 開發 | 撰寫可在 Databricks Job 執行的程式 | Notebook（`.ipynb`）或 Python script（`.py`） |
| 主力 | 開發建議 | 針對需求給設計 / 實作方向建議 | 文字說明、範例片段 |
| 主力 | 修改建議 | 針對既有程式碼提出調整、重構、效能建議 | 修改後的 code + 變更說明 |
| 主力 | SQL query 建議 | 在 Databricks SQL 編輯模式下使用的 query | `.sql` 或可直接貼上的 SQL |
| 非主力 | Genie Space 建構建議 | Genie Space 的資料集選擇、instructions、sample questions 等 | 文字設定草稿 |

### 3. 目標環境

| 項目 | 內容 | 備註 |
|---|---|---|
| Databricks Runtime | **17.3 LTS** | Spark 4.0 系列、Python 3.12（版本細節請以官方 release note 為準） |
| 本機 Python | 3.10.11 | 與 DBR 不同版本，本機僅做靜態檢查，不作為執行驗證依據 |
| Databricks CLI | 尚未安裝 | `~/.databrickscfg` 已存在 `DEFAULT` 與 `1806011` 兩個 profile（目前不使用） |
| 本機 Java / PySpark | Java 17、pyspark 3.5.8 | 可跑 local Spark 測試；建議在 venv 升級為 pyspark 4.0.x 以貼近 DBR 17.3 |

### 4. 互動模式

使用者會以下列兩種方式之一與 Agent 合作：

- **模式 A：貼 code 請求修改**
  使用者貼上一段既有程式碼（或放進 repo），描述想要的調整，Agent 修改後回傳並說明改了什麼、為什麼。
- **模式 B：描述需求請求生成**
  使用者用文字描述要做的事（輸入 / 輸出 / 邏輯），Agent 生成一段可用的程式碼。

兩種模式都可能套用到 Job、SQL、Genie 任一工作類型。

### 5. 原始需求未定義、已於 2026-09-17 確認的事項

以下項目在原始需求中沒有提到，但會影響 Agent 產出的形式與正確性。決定結果見第二部分 E 節：

1. **Job 部署方式**：手動上傳 Workspace、Git folder（Repos）同步，還是 Databricks Asset Bundles（DAB）？
2. **Unity Catalog**：是否啟用？預設 catalog / schema 命名規則？
3. **運算資源**：Serverless、Shared（Standard）、還是 Dedicated（Single-user）cluster？影響可用的 API（例如 RDD、部分 `dbutils` 功能）。
4. **本機是否需要連線 workspace**：是否允許在本機用 CLI / SDK 驗證 table schema、提交 job？
5. **語言偏好**：PySpark DataFrame API、Spark SQL、pandas API on Spark 的優先順序。
6. **Notebook 格式**：`.ipynb` 還是 Databricks 的 `.py` source 格式（含 `# COMMAND ----------` 分隔）？後者對 git diff 較友善。
7. **測試策略**：是否需要本機單元測試（例如 `pytest` + 小型 DataFrame），或只在 Databricks 上驗證？

---

## 第二部分：Claude 的規劃提案

> 以下為 Agent 根據第一部分的需求所做的規劃，供使用者調整。標示「建議」者為 Agent 的預設選擇，可被覆蓋。

### A. 目標目錄結構

```text
databricks_coding/
├── CLAUDE.md                 # Agent 工作準則（runtime、慣例、禁止事項）
├── .gitignore
├── requirements-dev.txt      # 本機 lint / test 工具（ruff、pytest、pyspark）
├── config/
│   └── project.yml           # 預設 catalog / schema / cluster 設定（唯一填寫處）
├── docs/
│   ├── 20260917_repo_initial_plan.md   # 本文件
│   └── conventions.md        # 命名、notebook 結構、SQL 風格
├── jobs/                     # 每個 job 一個資料夾
│   └── <job_name>/
│       ├── notebook.ipynb    # 主要格式；每個 code cell 第一行有 [cNN] 標籤
│       └── README.md         # 輸入 / 輸出 / 參數 / 排程
├── sql/                      # SQL 編輯器用的 query，一檔一題
├── snippets/                 # 可重複使用的片段（讀 UC table、寫 Delta、widgets 等）
├── genie/                    # Genie Space 設定草稿
├── scratch/                  # 使用者貼上待修改的 code 暫存區
├── tools/
│   └── nb.py                 # .ipynb 操作工具（依 cell 標籤 list / show / set / strip）
└── tests/                    # 本機 pytest；只測純 DataFrame 轉換
```

### B. 分階段執行計畫

**Phase 0：基礎建置**（可立即執行，不依賴任何待確認事項）

- [x] 建立 `CLAUDE.md`，寫入 Agent 工作準則（見 C 節）
- [x] 建立 `.gitignore`（Python、Jupyter checkpoint、`.databricks/`、憑證檔）
- [x] 建立上述目錄骨架，每個目錄放 `README.md` 說明用途
- [x] 建立 `docs/conventions.md` 初稿
- [x] 建立 `tools/nb.py`、`tests/` 框架、`jobs/_template/notebook.ipynb`（因決定 5、6 提前到 Phase 0）
- [ ] 第一次 commit

**Phase 1：本機工具鏈**（決定 4 為「暫時不用」，CLI / SDK 項目延後）

- [ ] （延後）安裝 Databricks CLI，用既有 profile 驗證 `databricks current-user me`
- [ ] 設定 `ruff`（Python lint / format）與 `sqlfluff`（dialect = databricks）
- [ ] （延後）視需要安裝 `databricks-sdk`，讓 Agent 能查詢 table schema 以減少猜測
- [ ] 建立 venv 並安裝 `requirements-dev.txt`（pyspark 4.0.x）

**Phase 2：工作流程範本**（需確認事項 1、5、6）

- [ ] Job 範本：含 widgets / 參數、logging、Delta 寫入策略（append / overwrite / MERGE）
- [ ] SQL 範本：含 header 註解（用途、資料來源、作者、日期）
- [ ] Genie Space 建議範本：資料集、instructions、sample questions、已知限制
- [ ] `snippets/` 放入常用片段

**Phase 3：部署自動化**（決定 1：原則 DAB，暫不進行）

- [ ] 若採 DAB：建立 `databricks.yml`，每個 job 對應一個 resource
- [ ] 若採 Git folder：定義 branch 與 workspace 同步規則

### C. `CLAUDE.md` 應包含的工作準則（建議）

1. **目標 runtime 固定為 DBR 17.3 LTS**。產生的 code 不使用已被移除或在 Spark 4.0 行為改變的 API。
2. **Spark 4.0 注意事項**：ANSI mode 預設開啟（整數溢位、非法 cast 會拋錯而非回傳 null）；優先使用 DataFrame API，避免 RDD；VARIANT 型別可用。
3. **優先順序**：PySpark DataFrame API > Spark SQL > pandas API on Spark；除非使用者指定。
4. **命名**：一律使用 Unity Catalog 三段式名稱 `catalog.schema.table`，不寫死環境相關值，改用 widgets / job parameters。
5. **寫入策略明示**：每次寫 Delta 都要在 code 或註解中說明是 append、overwrite 還是 MERGE，以及 partition / clustering 選擇。
6. **安全**：不在 code 內放憑證、token、連線字串；一律用 secret scope 或 job parameters。
7. **修改模式的回覆格式**：先列「變更點摘要」，再給完整 code，最後列「需要使用者確認的假設」。
8. **生成模式的前置確認**：若需求缺少輸入 table、輸出 table、schema、排程頻率任一項，先問再寫。
9. **SQL**：使用 Databricks SQL 語法；避免資料庫特有函式；大 query 拆 CTE 並加註解。
10. **Genie Space**：產出以文字設定為主，說明每個 table 的用途與欄位語意，不假設 Genie 的 UI 細節。

### D. 各互動模式的對應流程

| 模式 | 使用者動作 | Agent 動作 | 產出位置 |
|---|---|---|---|
| 貼 code 修改 | 貼上 code 或放進 `scratch/` | 修改、說明變更點與假設 | 原位置或 `jobs/<name>/` |
| 描述生成 Job | 說明輸入 / 輸出 / 邏輯 / 排程 | 缺項先問；生成 code + README | `jobs/<name>/` |
| SQL 建議 | 描述要查什麼、來源 table | 產出 `.sql`，附說明 | `sql/` |
| 開發 / 修改建議 | 描述情境或貼 code | 文字建議，必要時附片段 | 回覆或 `docs/` |
| Genie Space | 描述使用情境與資料集 | 產出設定草稿 | `genie/` |

### E. 使用者決定（2026-09-17）

| # | 題目 | 決定 | 對規劃的影響 |
|---|---|---|---|
| 1 | 部署方式 | **原則 DAB，但暫時不碰部署** | Phase 3 延後；目錄結構先相容 DAB（每個 job 一個資料夾），不建立 `databricks.yml` |
| 2 | Unity Catalog | **提供地方填預設 catalog / schema** | 建立 `config/project.yml` 作為唯一填寫處；Agent 產出一律從此讀取，不寫死 |
| 3 | 運算資源 | **原則 job cluster** | 範本與建議以 job cluster 為前提；不假設 Serverless 限制 |
| 4 | 本機連 workspace | **暫時不用** | Agent 無法查 schema，缺資料時必須先問，不可猜 |
| 5 | Notebook 格式 | **原則 `.ipynb`** | 重點需求：局部建議必須清楚標示是哪個 cell，方便比對、修改、直接貼上。見 F 節 |
| 6 | 本機單元測試 | **可以，但限制在本機 Spark 可測的純邏輯** | 不碰實際資料、UC、`dbutils`、Delta 寫入；只測 DataFrame 轉換函式。見 G 節 |

### F. `.ipynb` 工作流程（核心設計）

**問題**：`.ipynb` 是 JSON，直接看 diff 不易讀；局部修改若只給片段，使用者難以定位要貼到哪個 cell。

**做法：cell 標籤 + 整 cell 產出 + 工具腳本**

1. **每個 code cell 第一行加標籤**，格式 `# [cNN] 名稱`，例如 `# [c03] load_source`。
   SQL magic cell 的標籤放在 `%sql` 下一行，用 `-- [c07] 名稱`。
   標籤是 cell 的穩定 ID；插入新 cell 時用字母尾碼（`[c03a]`），不重新編號既有 cell。
2. **Agent 的局部建議一律以「整個 cell」為單位輸出**，格式固定：

   ```markdown
   ### [c05] clean_orders → 替換整個 cell
   一兩句說明改了什麼。
   （接著一個 code block，內容是完整的 cell，含第一行標籤）
   ```

   動作只有四種：`替換整個 cell`、`新增於 [cNN] 之後`、`刪除`、`不變`。
   不輸出 partial snippet、不輸出 diff 當作主要產出（diff 可附在後面當參考）。
3. **`tools/nb.py`** 提供 `list / show / set / insert / delete / strip / export` 子命令，
   讓 Agent 與使用者都能用標籤直接操作 `.ipynb`，不必手動改 JSON。
   `strip` 會清掉 outputs 與 execution_count，建議 commit 前執行以保持 diff 乾淨。
4. **範本**：`jobs/_template/notebook.ipynb` 定義標準 cell 順序（標題、參數、import、讀取、轉換、寫入、驗證）。

### G. 本機單元測試的邊界

**可測**：純 DataFrame 轉換函式（`DataFrame -> DataFrame`）、schema 檢查、簡單 UDF、日期 / 字串處理邏輯。

**不測**：讀寫 UC table、Delta MERGE、`dbutils`、secret、`%sql` cell、任何需要 workspace 的東西。

**做法**：
- 轉換邏輯寫在獨立的 code cell（例如 `[c05] transform_xxx`），cell 內只有 `def` 與必要 import，不含 I/O。
- `tests/nbload.py` 會用標籤把指定 cell 的原始碼載入成 Python module，測試直接呼叫其中的函式。
- `tests/conftest.py` 提供 `local[2]` 的 SparkSession fixture。
- 因此 notebook 仍是單一檔案可直接上傳，不需要拆出 `.py` 模組。

### H. Phase 0 執行紀錄（2026-09-17）

已建立：`CLAUDE.md`、`.gitignore`、`pyproject.toml`、`requirements-dev.txt`、`config/project.yml`、`docs/conventions.md`、
`tools/nb.py`、`tools/make_template.py`、`tests/conftest.py`、`tests/nbload.py`、`tests/test_template.py`、
`jobs/_template/notebook.ipynb`、各目錄 `README.md`。

驗證：`nb.py` 的 list / insert / delete / strip / export / 標籤檢查皆通過；`pytest` 以本機 pyspark 3.5.8 + ANSI mode 跑過範例測試；`ruff check` 與 `ruff format` 通過。尚未 commit。

---

## 附錄：原始需求描述（2026-09-17，保留原文以供追溯）

> 本 repo. 將進行 Databricks 的程式輔助撰寫，
> 主要是希望透過電腦端 Coding Agent 能力來協助開發，
> 開發內容有可能是 Job ( jypyter or *py), 或是請你提供開發建議, 或是修改建議, 或是在 SQL 編輯模式 的 query 建議,
> 非主力的話甚至會有 Genie Space 建構的建議...等，
> 目前 runtime 是 17.3，
> 作業模式有可能是我放上一段 code 做調整修改，或是我用描述去生出一段 code
