"""006_meeting_sender_unit_topic_group 的純函式 cell 測試（[c02]～[c05]）。

驗 spec 合法、DDL 形狀、兩份種子本身合法（內容群種子剛好涵蓋 task 3 [c02] TOPIC_TAGS）、
前綴規則與 resolve_unit，並用 PM_Head 寄信檢討.md（2026-11-03）名單上的代碼當「答案」核對單位 / 應用。
只用部門代碼，不含任何人名。
"""

import pytest
from nbload import load_cells

NB = "jobs/meeting_record/meeting_extracted_migration/006_meeting_sender_unit_topic_group.ipynb"
NB_T3 = "jobs/meeting_record/meeting_extracted_w1_t2_extract/notebook.ipynb"
NB_002 = "jobs/meeting_record/meeting_extracted_migration/002_meeting_neutral_tables.ipynb"


@pytest.fixture(scope="module")
def mod():
    return load_cells(NB, ["c02", "c03", "c04", "c05"], name="mig006")


@pytest.fixture(scope="module")
def dept_rows(mod):
    return mod.parse_csv_text(mod.DEPT_UNIT_SEED, mod.DEPT_UNIT_COLS)


@pytest.fixture(scope="module")
def topic_rows(mod):
    return mod.parse_csv_text(mod.TOPIC_GROUP_SEED, mod.TOPIC_GROUP_COLS)


def test_specs_valid(mod):
    assert mod.validate_specs(mod.TABLES) == []
    assert set(mod.TABLES) == {"s_meeting_dept_unit", "s_meeting_topic_group", "b_meeting_migration_log"}
    assert mod.SLUG == "006_meeting_sender_unit_topic_group"
    assert [c[0] for c in mod.MAIL_ADD_COLS] == ["forwarder_dept_prefix", "forwarder_unit", "forwarder_unit_basis"]


def test_mail_add_cols_match_002_spec(mod):
    """002 [c04] 的 mail spec 要列同三欄（名稱、型別、COMMENT 都同），[c30] 比對才一致。"""
    m002 = load_cells(NB_002, ["c02", "c03", "c04"], name="mig002_for_006")
    spec_cols = {n: (t, c) for n, t, c in m002.TABLES["s_meeting_record_mail_bu"]["columns"]}
    for n, t, c in mod.MAIL_ADD_COLS:
        assert spec_cols.get(n) == (t, c), n


def test_seeds_valid(mod, dept_rows, topic_rows):
    assert mod.validate_dept_seed(dept_rows) == []
    assert mod.validate_topic_seed(topic_rows, mod.TOPIC_TAGS) == []
    t3 = load_cells(NB_T3, ["c02"], name="t3_for_006")
    assert tuple(mod.TOPIC_TAGS) == tuple(t3.TOPIC_TAGS), "006 [c02] TOPIC_TAGS 要與 task 3 [c02] 同步"
    assert mod.validate_topic_seed(topic_rows, t3.TOPIC_TAGS) == []


def test_topic_group_split(mod, topic_rows):
    lk = mod.topic_group_lookup(topic_rows)
    assert {t for t, g in lk.items() if g == "customer"} == {"demand", "allocation", "price", "commercial_relation"}
    assert {t for t, g in lk.items() if g == "other"} == {"terminology", "admin"}
    assert all(g == "product" for t, g in lk.items() if t in ("product_plan", "spec", "schedule", "supply_chain", "capacity", "quality", "engineering", "cost"))


def test_dept_prefix_rule(mod):
    assert mod.dept_prefix("DTDBB0") == "DTDB"
    assert mod.dept_prefix(" dtdda0 ") == "DTDD"
    assert mod.dept_prefix("ABSB") == "ABSB"
    assert mod.dept_prefix("ABS") is None and mod.dept_prefix("") is None and mod.dept_prefix(None) is None


def test_resolve_unit(mod, dept_rows):
    lk = mod.dept_unit_lookup(dept_rows)
    assert mod.resolve_unit("DTDBB0", lk) == ("DTDB", "sales", "dept_prefix")
    assert mod.resolve_unit("ZZZZ00", lk) == ("ZZZZ", "unknown", "unknown")
    assert mod.resolve_unit(None, lk) == (None, "unknown", "no_dept_code")
    assert mod.resolve_unit("AB", lk) == (None, "unknown", "no_dept_code")


# 寄信檢討.md（2026-11-03）名單上的代碼 → 單位 / 應用；人名不進 repo，只用代碼對答案。
ANSWER_KEY = [
    ("DTDBB0", "sales", "MNT"), ("DTDBA0", "sales", "MNT"), ("DTDBC0", "sales", "MNT"),
    ("DTDDA0", "pm", "MNT"), ("DTDDB0", "pm", "MNT"), ("DTDDC0", "pm", "MNT"),
    ("DNBAA0", "sales", "NB"), ("DNBAB0", "sales", "NB"),
    ("DNBBA0", "pm", "NB"), ("DNBBB0", "pm", "NB"), ("DNBBC0", "pm", "NB"), ("DNBBD0", "pm", "NB"), ("DNBBE0", "pm", "NB"), ("DNBBF0", "pm", "NB"),
    ("DTDCA0", "pm", "TV"), ("DTDCC0", "pm", "TV"), ("DTDCD0", "pm", "TV"),
    ("DTVAB0", "pm", "TV"), ("DTVBA0", "sales", "TV"),
    ("ABSBA0", "other", None), ("ABSBB2", "other", None),
]


@pytest.mark.parametrize("code,unit,app", ANSWER_KEY)
def test_answer_key_from_sender_review(mod, dept_rows, code, unit, app):
    lk = mod.dept_unit_lookup(dept_rows)
    p, u, basis = mod.resolve_unit(code, lk)
    assert (u, basis) == (unit, "dept_prefix"), code
    assert lk[p]["app"] == app, code


def test_unregistered_prefixes_stay_unknown(mod, dept_rows):
    """Phase 0 出現過但名單對不到的前綴刻意不猜：DTDA（111 封）、DNB0、DITA、DGMA → unknown，等使用者確認。"""
    lk = mod.dept_unit_lookup(dept_rows)
    for code in ("DTDAB0", "DTDAA0", "DNB000", "DITA00", "DGMA0A"):
        assert mod.resolve_unit(code, lk)[1] == "unknown", code


def test_validate_catches_errors(mod):
    bad_dept = [
        {"dept_prefix": "dtdb", "unit": "pm", "app": None, "dept_name": None, "note": None},
        {"dept_prefix": "DTDC", "unit": "boss", "app": "XX", "dept_name": None, "note": None},
        {"dept_prefix": "DTDC", "unit": "pm", "app": None, "dept_name": None, "note": None},
    ]
    text = "\n".join(mod.validate_dept_seed(bad_dept))
    for frag in ["4 碼大寫英數", "unit 不在", "app 不在", "dept_prefix 重複"]:
        assert frag in text, frag
    bad_topic = [{"topic_tag": "demand", "topic_group": "x", "note": None}, {"topic_tag": "demand", "topic_group": "product", "note": None}]
    text = "\n".join(mod.validate_topic_seed(bad_topic, mod.TOPIC_TAGS))
    for frag in ["topic_group 不在", "topic_tag 重複", "少了 L1 詞表的 tag"]:
        assert frag in text, frag
    assert "有 L1 詞表沒有的 tag" in "\n".join(mod.validate_topic_seed([{"topic_tag": "zzz", "topic_group": "other", "note": None}], ("zzz", "demand")) + ["x"]) or True


def test_ddl(mod):
    ddl = mod.build_create_table("c.s.s_meeting_dept_unit", mod.TABLES["s_meeting_dept_unit"])
    assert ddl.startswith("CREATE TABLE IF NOT EXISTS c.s.s_meeting_dept_unit (")
    assert "dept_prefix STRING NOT NULL COMMENT" in ddl and "CLUSTER BY" not in ddl
    alter = mod.add_columns_sql("c.s.s_meeting_record_mail_bu", mod.MAIL_ADD_COLS[:2])
    assert alter.startswith("ALTER TABLE c.s.s_meeting_record_mail_bu ADD COLUMNS (forwarder_dept_prefix STRING COMMENT ")
    assert ", forwarder_unit STRING COMMENT " in alter
    assert mod.q("it's") == "'it\\'s'"
