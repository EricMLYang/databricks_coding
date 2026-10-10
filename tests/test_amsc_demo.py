"""amsc_demo 的純函式 cell 測試（[c02]～[c03]）。測資是合成的，不放 Omdia 授權內容。"""

import pytest
from nbload import load_cells

NB = "jobs/amsc_demo/notebook.ipynb"

VIEWS_SQL = """-- 檔頭註解；含「;」不是結尾
-- 第二行註解

-- V1 說明
CREATE OR REPLACE VIEW micenter.mi3_datahub_dev.amsc_v_a
COMMENT 'x'
AS
SELECT 1 AS a;

-- F1 說明
CREATE OR REPLACE FUNCTION micenter.mi3_datahub_dev.amsc_fn_b(p STRING)
RETURNS TABLE (a INT)
RETURN SELECT a FROM micenter.mi3_datahub_dev.amsc_v_a ORDER BY a;
"""


@pytest.fixture(scope="module")
def mod():
    return load_cells(NB, ["c02", "c03"], name="amscdemo")


def test_sql_str_escapes(mod):
    assert mod.sql_str("AUO's") == "'AUO\\'s'"
    assert mod.sql_str("a\\b") == "'a\\\\b'"
    assert mod.sql_str(2026) == "'2026'"


def test_spark_schema(mod):
    cols = [
        {"name": "a", "type": "STRING"},
        {"name": "b", "type": "INT"},
        {"name": "c", "type": "DATE"},
    ]
    st = mod.spark_schema(cols)
    assert [f.name for f in st.fields] == ["a", "b", "c"]
    assert st.simpleString() == "struct<a:string,b:int,c:date>"
    with pytest.raises(ValueError, match="DECIMAL"):
        mod.spark_schema([{"name": "x", "type": "DECIMAL"}])


def test_ddl_columns_and_props(mod):
    cols = [{"name": "a", "type": "STRING", "comment": "面板廠's"}, {"name": "b", "type": "DOUBLE"}]
    assert mod.ddl_columns(cols) == "`a` STRING COMMENT '面板廠\\'s',\n  `b` DOUBLE"
    assert (
        mod.tblproperties({"demo": "amsc", "expires": "2026-12-31"})
        == "'demo' = 'amsc', 'expires' = '2026-12-31'"
    )


def test_split_sql(mod):
    stmts = mod.split_sql(VIEWS_SQL)
    assert len(stmts) == 2
    assert [mod.created_object(s) for s in stmts] == [
        "VIEW micenter.mi3_datahub_dev.amsc_v_a",
        "FUNCTION micenter.mi3_datahub_dev.amsc_fn_b",
    ]
    assert stmts[1].endswith("ORDER BY a")  # 結尾分號被切掉
    assert mod.split_sql("-- only comment;\n\n  \n") == []


def test_retarget_sql(mod):
    sql = "SELECT * FROM micenter.mi3_datahub_dev.amsc_v_a JOIN micenter.mi3_datahub_dev.amsc_dim b"
    assert mod.retarget_sql(sql, "micenter.mi3_datahub_dev", "micenter.mi3_datahub_dev") == sql
    got = mod.retarget_sql(sql, "micenter.mi3_datahub_dev", "dev_cat.sandbox")
    assert got == "SELECT * FROM dev_cat.sandbox.amsc_v_a JOIN dev_cat.sandbox.amsc_dim b"


def test_check_ok(mod):
    from decimal import Decimal

    assert mod.check_ok(264, 264)
    assert mod.check_ok(Decimal("77043"), 77043)
    assert mod.check_ok(77043.0, 77043)
    assert not mod.check_ok(77042.0, 77043)
    assert not mod.check_ok(None, 0)


def test_drop_statements(mod):
    objs = [
        ("amsc_fact_x", "TABLE"),
        ("amsc_v_y", "VIEW"),
        ("amsc_fn_z", "FUNCTION"),
        ("amsc_dim_w", "TABLE"),
    ]
    assert mod.drop_statements(objs, "c.s") == [
        "DROP FUNCTION IF EXISTS c.s.amsc_fn_z",
        "DROP VIEW IF EXISTS c.s.amsc_v_y",
        "DROP TABLE IF EXISTS c.s.amsc_dim_w",
        "DROP TABLE IF EXISTS c.s.amsc_fact_x",
    ]
    assert mod.drop_statements([], "c.s") == []
    with pytest.raises(ValueError, match="other_table"):
        mod.drop_statements([("amsc_a", "TABLE"), ("other_table", "TABLE")], "c.s")
