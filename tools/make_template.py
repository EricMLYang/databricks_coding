"""產生 jobs/_template/notebook.ipynb。修改範本請改這個檔再重跑：python tools/make_template.py"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def code(text: str) -> dict:
    return {
        "cell_type": "code",
        "metadata": {},
        "execution_count": None,
        "outputs": [],
        "source": text.splitlines(keepends=True),
    }


def md(text: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": text.splitlines(keepends=True)}


CELLS = [
    md(
        """# <job_name>

- 用途：
- 輸入 table：`{catalog}.{schema}.<source>`
- 輸出 table：`{catalog}.{schema}.<target>`
- 排程：
- 負責人 / 更新日期：

Cell 標籤規則見 `docs/conventions.md`。
"""
    ),
    code(
        """# [c01] params
# 預設值請對照 config/project.yml；job 執行時由 job parameters 覆蓋。
dbutils.widgets.text("catalog", "")
dbutils.widgets.text("schema", "")
dbutils.widgets.text("env", "dev")
dbutils.widgets.text("run_date", "")

catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")
env = dbutils.widgets.get("env")
run_date = dbutils.widgets.get("run_date")
assert catalog and schema, "catalog / schema 不可為空"
"""
    ),
    code(
        """# [c02] imports
from pyspark.sql import DataFrame
from pyspark.sql import functions as F
"""
    ),
    code(
        """# [c03] load_source
src_table = f"{catalog}.{schema}.<source>"
df_src = spark.table(src_table)
print(src_table, df_src.count())
"""
    ),
    code(
        '''# [c04] transform_example
def transform_example(df: DataFrame) -> DataFrame:
    """範例純函式：清理 customer_id、轉日期、彙總金額。可被 tests/ 載入測試。"""
    return (
        df.withColumn("customer_id", F.upper(F.trim("customer_id")))
        .withColumn("order_date", F.to_date("order_date"))
        .withColumn("amount", F.coalesce("amount", F.lit(0)))
        .groupBy("customer_id")
        .agg(F.max("order_date").alias("order_date"), F.sum("amount").alias("amount"))
    )
'''
    ),
    code(
        """# [c10] run
df_out = transform_example(df_src)
"""
    ),
    code(
        """# [c20] write_target
# 寫入策略：overwrite（每日全量重算）。若改為增量請換 MERGE 並註明鍵值。
tgt_table = f"{catalog}.{schema}.<target>"
df_out.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(tgt_table)
"""
    ),
    code(
        """# [c30] check_target
df_chk = spark.table(tgt_table)
n_rows = df_chk.count()
n_dup = df_chk.groupBy("customer_id").count().filter("count > 1").count()
print(f"rows={n_rows} dup_keys={n_dup}")
assert n_dup == 0, "customer_id 重複"
"""
    ),
]

NB = {
    "cells": CELLS,
    "metadata": {
        "application/vnd.databricks.v1+notebook": {
            "notebookName": "notebook",
            "language": "python",
            "dashboards": [],
            "widgets": {},
            "notebookMetadata": {"pythonIndentUnit": 4},
        },
        "language_info": {"name": "python"},
    },
    "nbformat": 4,
    "nbformat_minor": 0,
}

if __name__ == "__main__":
    out = ROOT / "jobs" / "_template" / "notebook.ipynb"
    out.write_text(
        json.dumps(NB, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n"
    )
    print("written", out)
