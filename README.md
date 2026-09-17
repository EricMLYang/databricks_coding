# databricks_coding

Databricks 開發的 Coding Agent 輔助工作區。在本機用 Claude Code 產生、修改、審閱要放到 Databricks 上跑的
Notebook、SQL query 與設定草稿；本機只做 lint 與純邏輯測試，不是執行環境。

- 目標環境：Databricks Runtime 17.3 LTS（Spark 4.0、Python 3.12）、job cluster、Unity Catalog
- Agent 工作準則：[`CLAUDE.md`](CLAUDE.md)
- 需求與規劃：[`docs/20260917_repo_initial_plan.md`](docs/20260917_repo_initial_plan.md)
- 細部慣例：[`docs/conventions.md`](docs/conventions.md)

## 目錄

| 路徑 | 用途 |
|---|---|
| `jobs/<job_name>/` | 每個 Job 一個資料夾：`notebook.ipynb` + `README.md`。新 job 從 `jobs/_template/` 複製 |
| `sql/` | Databricks SQL 編輯器用的 query，一檔一題 |
| `snippets/` | 可重複使用的片段 |
| `genie/` | Genie Space 設定草稿 |
| `scratch/` | 貼上待修改的 code 暫存區（不追蹤於 git） |
| `config/project.yml` | 預設 catalog / schema / env，唯一填寫處 |
| `tools/nb.py` | 依 cell 標籤操作 `.ipynb` |
| `tests/` | 本機 pytest，只測純 DataFrame 轉換 |

## 使用方式

兩種互動模式：

1. **貼 code 請求修改**：把 code 放進 `scratch/` 或直接貼給 Agent，說明想改什麼。
2. **描述需求請求生成**：說明輸入 table、輸出 table、邏輯、排程，Agent 產生 notebook 到 `jobs/<name>/`。

Agent 的局部修改一律以**整個 cell** 為單位回覆，格式固定為：

```markdown
### [c05] transform_orders → 替換整個 cell
說明一兩句。
（完整 cell 的 code block，第一行是標籤 # [c05] transform_orders）
```

每個 code cell 第一行都有標籤 `# [cNN] 名稱`，方便對照、直接貼進 Databricks 對應 cell。

## Notebook 工具

```text
python tools/nb.py list   jobs/<name>/notebook.ipynb            # 列出 cell 與標籤
python tools/nb.py show   jobs/<name>/notebook.ipynb c05        # 看某個 cell
python tools/nb.py set    jobs/<name>/notebook.ipynb c05 new.py # 替換 cell
python tools/nb.py insert jobs/<name>/notebook.ipynb c05 new.py # 在 c05 之後插入
python tools/nb.py strip  jobs/<name>/notebook.ipynb            # commit 前清除 outputs
```

## 本機環境

需要 Java 17。建議用 venv 安裝對齊 DBR 17.3 的 pyspark 4.0：

```text
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
```

檢查與測試：

```text
python -m ruff check .
python -m ruff format .
python -m pytest -q
```

測試只涵蓋純 `DataFrame -> DataFrame` 函式，不讀寫 table、不用 `dbutils`，細節見 `docs/conventions.md` 第 4 節。
