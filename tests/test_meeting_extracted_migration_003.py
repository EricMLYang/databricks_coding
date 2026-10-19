"""003_meeting_semantic_lens 的純函式 cell 測試（[c02]～[c05]）。

驗 spec 合法、鏡頭表的鍵與必要欄，以及兩個 View 的 SQL 真的能跑：
用 002 的 spec 在本機 Spark 建中立層假表、用 003 的 spec 建鏡頭假表，把 [c05] 的 SELECT 跑一遍，
檢查 category_rule 四條規則、source / tags / week 的組法、
already_classified 與 rule_disagree。假資料只用假 token 與 entity_id，無人名。
"""

import copy
from datetime import date, datetime

import pytest
from nbload import load_cells

NB = "jobs/meeting_record/meeting_extracted_migration/003_meeting_semantic_lens.ipynb"
NB_002 = "jobs/meeting_record/meeting_extracted_migration/002_meeting_neutral_tables.ipynb"


@pytest.fixture(scope="module")
def mod():
    return load_cells(NB, ["c02", "c03", "c04", "c05"], name="mig003")


@pytest.fixture(scope="module")
def mod002():
    return load_cells(NB_002, ["c02", "c03", "c04"], name="mig002_for_003")


def test_specs_valid(mod):
    assert mod.validate_specs(mod.TABLES, mod.VIEWS) == []
    assert set(mod.TABLES) == {"g_meeting_items_sem_bu", "b_meeting_migration_log"}
    assert set(mod.VIEWS) == {"v_meeting_items_sem_cand", "v_meeting_items_sem_q"}
    assert mod.SLUG == "003_meeting_semantic_lens"


def test_sem_table_key_and_yaml_fields(mod):
    """§8.3：承接鍵是 item_key；YAML items 區的欄位都要在。"""
    spec = mod.TABLES["g_meeting_items_sem_bu"]
    assert spec["key"] == ["item_key"] and spec["cluster_by"] == ["week"]
    names = {c[0] for c in spec["columns"]}
    for yaml_field in [
        "category",
        "app",
        "term",
        "summary",
        "quote",
        "date",
        "source",
        "tags",
        "as_of",
        "dup_of",
        "route_hint",
        "extract_note",
        "verified",
        "review_note",
    ]:
        assert yaml_field in names, yaml_field
    for extra in [
        "item_id",
        "week",
        "category_rule",
        "rule_basis",
        "active",
        "sem_id",
        "stage_a_version",
    ]:
        assert extra in names, extra


def test_validate_catches_missing_required(mod):
    tables = copy.deepcopy(mod.TABLES)
    tables["g_meeting_items_sem_bu"]["columns"] = [
        c for c in tables["g_meeting_items_sem_bu"]["columns"] if c[0] != "review_note"
    ]
    views = copy.deepcopy(mod.VIEWS)
    views["v_meeting_items_sem_q"]["select"].append(("s.name_zh", "name_zh", "洩漏"))
    text = "\n".join(mod.validate_specs(tables, views))
    assert "缺必要欄 review_note" in text and "暴露 S3 欄" in text


def test_create_table_ddl(mod):
    ddl = mod.build_create_table("c.s.g_meeting_items_sem_bu", mod.TABLES["g_meeting_items_sem_bu"])
    assert ddl.startswith("CREATE TABLE IF NOT EXISTS c.s.g_meeting_items_sem_bu (")
    assert "item_key STRING NOT NULL" in ddl and "USING DELTA\nCLUSTER BY (week)" in ddl


def test_candidate_constants_match_spec(mod):
    """候選規則的常數照 §8.3；INTEL_TAGS 必須是 L1 詞表（task 3 [c02] TOPIC_TAGS）的子集。"""
    t3 = load_cells(
        "jobs/meeting_record/meeting_extracted_w1_t2_extract/notebook.ipynb",
        ["c02"],
        name="t3_for_003",
    )
    assert set(mod.INTEL_TAGS) <= set(t3.TOPIC_TAGS)
    assert set(mod.INTEL_STATEMENT_TYPES) == {"opinion", "fact"}
    assert mod.CATEGORIES == ("semantic", "intel", "event")


# ---------- View SQL 實跑 ----------
_T0 = datetime(2026, 10, 14, 9, 0)  # 2026-W42（ISO）


def _item(item_id, key, **kw):
    base = {
        "item_id": item_id,
        "item_key": key,
        "pk_seq": 1,
        "segment_no": 1,
        "sub_no": 0,
        "unit": "bu",
        "subject_clean": "acer MNT Monthly Meeting",
        "statement_type": "fact",
        "speaker_side": "customer",
        "customer": "acer",
        "customer_raw": "acer",
        "app": "MNT",
        "topic_tags": ["demand", "price"],
        "topic_tag_primary": "demand",
        "free_tags": ["AG25"],
        "terms_mentioned": [],
        "summary": "sum",
        "quote": "quote text",
        "event_date": date(2026, 8, 13),
        "event_month": "2026-08",
        "sensitivity": "S1",
        "confidence": 0.8,
        "extract_status": "ok",
        "superseded": False,
        "prompt_version": "0.2",
        "cleaner_version": "0.1",
        "extracted_at": _T0,
    }
    return {**base, **kw}


@pytest.fixture(scope="module")
def fake_tables(mod, mod002, spark):
    items = [
        _item(
            "BU-MTG-1-1-0-001", "k1", statement_type="definition", topic_tag_primary="terminology"
        ),
        _item(
            "BU-MTG-1-1-0-002",
            "k2",
            statement_type="fact",
            topic_tag_primary="price",
            terms_mentioned=["BP"],
            quote="BP 的口徑是年初版本",
        ),
        _item(
            "BU-MTG-1-1-0-003",
            "k3",
            statement_type="opinion",
            topic_tag_primary="demand",
            quote="INX 產能集中 32 43 50 吋，可能轉 23.8 吋 Monitor 面板消化產能",
        ),
        _item(
            "BU-MTG-1-1-0-004",
            "k4",
            statement_type="request",
            topic_tag_primary="demand",
            app=None,
            customer=None,
            free_tags=None,
            topic_tags=["demand"],
        ),
        _item(
            "BU-MTG-1-1-0-005",
            "k5",
            statement_type="fact",
            topic_tag_primary="demand",
            superseded=True,
        ),
        _item(
            "BU-MTG-1-1-0-006",
            "k6",
            statement_type="fact",
            topic_tag_primary="demand",
            extract_status="failed_quote",
        ),
        _item(
            "BU-MTG-1-1-0-007",
            "k7",
            statement_type="fact",
            topic_tag_primary="supply_chain",
            segment_no=2,
        ),
        _item(  # 與 k3 同文（標點 / 空白 / 大小寫不同），段較晚 → dup_key = k3
            "BU-MTG-1-1-0-008",
            "k8",
            statement_type="fact",
            topic_tag_primary="price",
            segment_no=2,
            quote="inx產能集中32、43、50吋, 可能轉23.8吋monitor面板消化產能!",
        ),
        _item(  # 價格事實（D30 加進 INTEL_TAGS）
            "BU-MTG-1-1-0-009",
            "k9",
            statement_type="fact",
            topic_tag_primary="price",
            quote="短句",
        ),
    ]
    clean = [
        {
            "pk_seq": 1,
            "segment_no": 1,
            "sub_no": 0,
            "content_type": "thread_reply",
            "segment_date": date(2026, 8, 13),
        },
        {
            "pk_seq": 1,
            "segment_no": 2,
            "sub_no": 0,
            "content_type": "inline_minutes",
            "segment_date": date(2026, 8, 14),
        },
    ]
    sem = [
        {
            "item_key": "k3",
            "item_id": "BU-MTG-1-1-0-003",
            "week": "2026-W42",
            "category": "event",
            "category_rule": "intel",
            "app": "MNT",
            "tags": ["demand"],
            "verified": "y",
            "active": True,
            "stage_a_version": "0.1",
        },
        {
            "item_key": "k10",
            "item_id": "old",
            "week": "2026-W40",
            "category": "semantic",
            "category_rule": "semantic",
            "app": "ALL",
            "tags": ["x"],
            "active": False,
        },
    ]
    rows = {"g_meeting_items_bu": items, "s_meeting_record_clean_bu": clean}
    for t in ("g_meeting_items_bu", "s_meeting_record_clean_bu"):
        spec = mod002.TABLES[t]
        cols = [c[0] for c in spec["columns"]]
        spark.createDataFrame(
            [tuple(r.get(c) for c in cols) for r in rows[t]], mod002.schema_ddl(spec)
        ).createOrReplaceTempView(f"t_{t}")
    spec = mod.TABLES["g_meeting_items_sem_bu"]
    cols = [c[0] for c in spec["columns"]]
    spark.createDataFrame(
        [tuple(r.get(c) for c in cols) for r in sem], mod.schema_ddl(spec)
    ).createOrReplaceTempView("t_g_meeting_items_sem_bu")
    return lambda t: f"t_{t}"


def _run(mod, spark, fq, view):
    return spark.sql(mod.build_select(mod.VIEWS[view], fq))


def test_views_columns_and_no_s3(mod, spark, fake_tables):
    for v, spec in mod.VIEWS.items():
        df = _run(mod, spark, fake_tables, v)
        assert df.columns == [a for _, a, _ in spec["select"]], v
        assert not (set(df.columns) & mod.S3_COLS), v


def test_candidate_rules(mod, spark, fake_tables):
    got = {
        r.item_key: r for r in _run(mod, spark, fake_tables, "v_meeting_items_sem_cand").collect()
    }
    assert set(got) == {"k1", "k2", "k3", "k4", "k7", "k8", "k9"}  # superseded / failed 不出現
    assert (got["k1"].category_rule, got["k1"].rule_basis) == ("semantic", "definition")
    assert (got["k2"].category_rule, got["k2"].rule_basis) == ("semantic", "term_hint")
    assert (got["k3"].category_rule, got["k3"].rule_basis) == ("intel", "intel_tag")
    assert (got["k4"].category_rule, got["k4"].rule_basis) == (
        "event",
        "default",
    )  # request 不算 intel
    assert (got["k7"].category_rule, got["k7"].weight_hint) == ("intel", "low")  # 紀要段降權
    assert (got["k9"].category_rule, got["k9"].rule_basis) == ("intel", "intel_tag")  # D30 price


def test_candidate_derived_fields(mod, spark, fake_tables):
    got = {
        r.item_key: r for r in _run(mod, spark, fake_tables, "v_meeting_items_sem_cand").collect()
    }
    k1, k3, k4 = got["k1"], got["k3"], got["k4"]
    assert k1.week == "2026-W42"
    assert k1.source == "acer MNT Monthly Meeting 2026-08-13 — customer"
    assert sorted(k1.tags) == ["AG25", "acer", "demand", "price"]
    assert k1.date == date(2026, 8, 13) and k1.event_month == "2026-08"
    assert (k1.already_classified, k1.sem_category) == (False, None)
    assert (k3.already_classified, k3.sem_category, k3.sem_verified) == (True, "event", "y")
    assert (k3.sem_active, k3.sem_stage_a_version) == (True, "0.1")
    assert (k1.sem_active, k1.sem_stage_a_version) == (None, None)
    assert k4.app == "ALL" and k4.tags == [
        "demand"
    ]  # NULL app → ALL；NULL customer / free_tags 不進 tags


def test_candidate_dup_key(mod, spark, fake_tables):
    """D30：quote 正規化後相同 → 指向最早那條；自己最早 / 短句 / 無重複 → NULL。"""
    got = {
        r.item_key: r for r in _run(mod, spark, fake_tables, "v_meeting_items_sem_cand").collect()
    }
    assert got["k8"].dup_key == "k3" and got["k3"].dup_key is None
    assert got["k9"].dup_key is None and got["k1"].dup_key is None  # 短句不比；無重複


def test_sem_q_active_only_and_disagree(mod, spark, fake_tables):
    rows = {r.item_key: r for r in _run(mod, spark, fake_tables, "v_meeting_items_sem_q").collect()}
    assert set(rows) == {"k3"}  # active = false 不出現
    assert rows["k3"].rule_disagree is True and rows["k3"].tags_str == "demand"
