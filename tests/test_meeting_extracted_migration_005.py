"""005_semantic_ledgers 的純函式 cell 測試（[c02]～[c05]）。

驗 spec 合法、三張台帳表的鍵與必要欄，兩個 View 在本機 Spark 以假表實跑：
retire_candidate 以 as_of 距今季數判（用 current_date 相對值造資料）。假資料無人名。
"""

import copy
from datetime import date

import pytest
from nbload import load_cells

NB = "jobs/meeting_record/meeting_extracted_migration/005_semantic_ledgers.ipynb"


@pytest.fixture(scope="module")
def mod():
    return load_cells(NB, ["c02", "c03", "c04", "c05"], name="mig005")


def test_specs_valid(mod):
    assert mod.validate_specs(mod.TABLES, mod.VIEWS) == []
    assert set(mod.TABLES) == {
        "g_semantic_record",
        "g_semantic_record_evidence",
        "g_background_intel",
        "b_meeting_migration_log",
    }
    assert set(mod.VIEWS) == {"v_semantic_record_q", "v_background_intel_q"}
    assert mod.SLUG == "005_semantic_ledgers" and mod.RETIRE_QUARTERS == 2
    assert mod.TABLES["g_semantic_record"]["key"] == ["sem_id"]
    assert mod.TABLES["g_semantic_record_evidence"]["key"] == ["sem_id", "item_key"]
    assert mod.TABLES["g_background_intel"]["key"] == ["intel_id"]


def test_validate_catches(mod):
    tables = copy.deepcopy(mod.TABLES)
    tables["g_background_intel"]["columns"] = [
        c for c in tables["g_background_intel"]["columns"] if c[0] != "term_norm"
    ]
    views = copy.deepcopy(mod.VIEWS)
    views["v_semantic_record_q"]["select"].append(("s.email", "email", "洩漏"))
    text = "\n".join(mod.validate_specs(tables, views))
    assert "缺必要欄 term_norm" in text and "暴露 S3 欄" in text


def test_ddl(mod):
    ddl = mod.build_create_table("c.s.g_background_intel", mod.TABLES["g_background_intel"])
    assert "intel_id STRING NOT NULL" in ddl and "CLUSTER BY (app)" in ddl
    ddl2 = mod.build_create_table("c.s.g_semantic_record", mod.TABLES["g_semantic_record"])
    assert "CLUSTER BY" not in ddl2


def _q_label(d: date, back: int) -> str:
    """今天往回 back 季的 yyyy-Qn。"""
    qi = d.year * 4 + (d.month - 1) // 3 - back
    return f"{qi // 4}-Q{qi % 4 + 1}"


def _m_label(d: date, back: int) -> str:
    """今天往回 back 季的季首月 yyyy-MM。"""
    qi = d.year * 4 + (d.month - 1) // 3 - back
    return f"{qi // 4}-{(qi % 4) * 3 + 1:02d}"


@pytest.fixture(scope="module")
def fake_tables(mod, spark):
    today = date.today()
    rec = mod.TABLES["g_semantic_record"]
    rec_cols = [c[0] for c in rec["columns"]]
    recs = [
        {
            "sem_id": "SEM-001",
            "term": "a",
            "summary": "d",
            "route_hint": "pa:semantics",
            "status": "confirmed",
        },
        {
            "sem_id": "SEM-002",
            "term": "b",
            "summary": "d",
            "route_hint": "pa:semantics",
            "status": "retired",
        },
        {
            "sem_id": "SEM-003",
            "term": "c",
            "summary": "d",
            "route_hint": "pa:semantics",
            "status": None,
        },
    ]
    spark.createDataFrame(
        [tuple(r.get(c) for c in rec_cols) for r in recs], mod.schema_ddl(rec)
    ).createOrReplaceTempView("t_g_semantic_record")
    intel = mod.TABLES["g_background_intel"]
    intel_cols = [c[0] for c in intel["columns"]]
    rows = [
        {"intel_id": "INT-001", "app": "MNT", "as_of": _q_label(today, 0), "status": "active"},
        {"intel_id": "INT-002", "app": "MNT", "as_of": _q_label(today, 3), "status": "active"},
        {"intel_id": "INT-003", "app": "TV", "as_of": _m_label(today, 3), "status": "retired"},
        {"intel_id": "INT-004", "app": "TV", "as_of": _m_label(today, 2), "status": None},
        {"intel_id": "INT-005", "app": "TV", "as_of": "bad", "status": "active"},
        {
            "intel_id": "INT-006",
            "app": "TV",
            "as_of": _q_label(today, 3),
            "status": "unreviewed",
        },  # D32
    ]
    spark.createDataFrame(
        [tuple(r.get(c) for c in intel_cols) for r in rows], mod.schema_ddl(intel)
    ).createOrReplaceTempView("t_g_background_intel")
    return lambda t: f"t_{t}"


def test_views(mod, spark, fake_tables):
    for v, spec in mod.VIEWS.items():
        df = spark.sql(mod.build_select(spec, fake_tables))
        assert df.columns == [a for _, a, _ in spec["select"]], v
    rec = {
        r.sem_id
        for r in spark.sql(
            mod.build_select(mod.VIEWS["v_semantic_record_q"], fake_tables)
        ).collect()
    }
    assert rec == {"SEM-001", "SEM-003"}  # retired 不出現；status NULL 視為 confirmed
    got = {
        r.intel_id: r
        for r in spark.sql(
            mod.build_select(mod.VIEWS["v_background_intel_q"], fake_tables)
        ).collect()
    }
    assert (got["INT-001"].quarters_old, got["INT-001"].retire_candidate) == (0, False)
    assert (got["INT-002"].quarters_old, got["INT-002"].retire_candidate) == (3, True)
    assert (got["INT-003"].quarters_old, got["INT-003"].retire_candidate) == (3, False)  # retired
    assert (got["INT-004"].quarters_old, got["INT-004"].retire_candidate) == (
        2,
        False,
    )  # 剛好兩季不算
    assert got["INT-005"].quarters_old is None and got["INT-005"].retire_candidate is None
    assert got["INT-006"].retire_candidate is True  # unreviewed 也算退場候選
