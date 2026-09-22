# jobs/

每個 Databricks Job 一個資料夾：`jobs/<job_name>/notebook.ipynb` + `README.md`（輸入、輸出、參數、排程）。
同一個資料來源 / 流程的多個 job 收在一個系列資料夾下：`jobs/<系列>/<job>/`，系列資料夾自己放一份 `README.md` 說明彼此順序（例：`jobs/ir_calendar/`）。
新 job 從 `_template/` 複製。Cell 標籤與回覆格式見 `docs/conventions.md`。
