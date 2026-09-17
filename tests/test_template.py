"""範例：載入 jobs/_template/notebook.ipynb 的純函式 cell 並測試。"""

from nbload import load_cells


def test_transform_example(spark):
    mod = load_cells("jobs/_template/notebook.ipynb", ["c02", "c04"])
    df = spark.createDataFrame(
        [("A", "2026-09-01", 10), ("a ", "2026-09-02", 5), ("B", "2026-09-03", None)],
        ["customer_id", "order_date", "amount"],
    )
    out = mod.transform_example(df)
    rows = {r["customer_id"]: r for r in out.collect()}
    assert set(rows) == {"A", "B"}
    assert rows["A"]["amount"] == 15
    assert rows["B"]["amount"] == 0
    assert str(out.schema["order_date"].dataType) == "DateType()"
