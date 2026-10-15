"""002_meeting_neutral_tables 的純函式 cell 測試（[c02]～[c05]）。

驗 spec 合法、DDL 形狀，以及 View SQL 真的能跑：依 [c04] spec 在本機 Spark 建同名 temp view、
塞幾列假資料，把 [c05] 的 SELECT 跑一遍，檢查輸出欄 = spec、沒有 S3 欄、
join / mode / explode 行為正確。
假資料只用假 token 與 entity_id，無人名。
"""

import copy

import pytest
from nbload import load_cells

NB = "jobs/meeting_record/meeting_extracted_migration/002_meeting_neutral_tables.ipynb"
EXPECT_TABLES = {
    "s_meeting_record_mail_bu",
    "s_meeting_record_clean_bu",
    "s_meeting_participants_bu",
    "g_meeting_items_bu",
    "b_meeting_migration_log",
}
EXPECT_VIEWS = {"v_meeting_items_q", "v_meeting_item_models", "v_meeting_mail_index"}


@pytest.fixture(scope="module")
def mod():
    return load_cells(NB, ["c02", "c03", "c04", "c05"], name="mig002")


def test_specs_valid(mod):
    assert mod.validate_specs(mod.TABLES, mod.VIEWS) == []
    assert set(mod.TABLES) == EXPECT_TABLES
    assert set(mod.VIEWS) == EXPECT_VIEWS


def test_spec_keys_match_plan(mod):
    """MERGE key 照規格 §3.0b / §3.1 / §3.2 / §3.3。"""
    assert mod.TABLES["s_meeting_record_mail_bu"]["key"] == ["pk_seq"]
    assert mod.TABLES["s_meeting_record_clean_bu"]["key"] == ["pk_seq", "segment_no", "sub_no"]
    assert mod.TABLES["s_meeting_participants_bu"]["key"] == [
        "pk_seq",
        "segment_no",
        "token",
        "role",
    ]
    assert mod.TABLES["g_meeting_items_bu"]["key"] == ["item_id"]


def test_validate_catches_errors(mod):
    tables = copy.deepcopy(mod.TABLES)
    views = copy.deepcopy(mod.VIEWS)
    t = tables["g_meeting_items_bu"]
    t["columns"].append(("item_id", "STRING", "重複欄"))
    t["columns"] = [c for c in t["columns"] if c[0] != "item_key"]  # 拿掉必要欄
    t["columns"].append(("Bad Col", "MAP<STRING,STRING>", ""))
    t["cluster_by"] = ["nope"]
    views["v_meeting_items_q"]["select"].append(("p.email", "email", "洩漏"))
    text = "\n".join(mod.validate_specs(tables, views))
    for frag in [
        "欄位重複",
        "缺必要欄 item_key",
        "欄名格式不符",
        "型別不在允許清單",
        "沒有 COMMENT",
        "cluster_by 欄 nope 不存在",
        "暴露 S3 欄",
    ]:
        assert frag in text, frag


def test_build_create_table(mod):
    ddl = mod.build_create_table(
        "c.s.s_meeting_record_clean_bu", mod.TABLES["s_meeting_record_clean_bu"]
    )
    assert ddl.startswith("CREATE TABLE IF NOT EXISTS c.s.s_meeting_record_clean_bu (")
    assert (
        "pk_seq BIGINT NOT NULL" in ddl
        and "segment_no INT NOT NULL" in ddl
        and "sub_no INT NOT NULL" in ddl
    )
    assert (
        "clean_text STRING COMMENT" in ddl
        and "NOT NULL COMMENT" not in ddl.split("clean_text")[1].split("\n")[0]
    )
    assert "USING DELTA\nCLUSTER BY (pk_seq)" in ddl
    log = mod.build_create_table(
        "c.s.b_meeting_migration_log", mod.TABLES["b_meeting_migration_log"]
    )
    assert "CLUSTER BY" not in log


def test_q_escapes(mod):
    assert mod.q("it's") == "'it\\'s'"
    assert mod.q(None) == "''"


def test_add_columns_sql(mod):
    sql = mod.add_columns_sql(
        "c.s.g_meeting_items_bu", mod.TABLES["g_meeting_items_bu"], ["item_key", "model"]
    )
    assert sql.startswith(
        "ALTER TABLE c.s.g_meeting_items_bu ADD COLUMNS (item_key STRING COMMENT "
    )
    assert ", model STRING COMMENT " in sql


def test_create_view_has_column_comments(mod):
    ddl = mod.build_create_view(
        "c.s.v_meeting_item_models", mod.VIEWS["v_meeting_item_models"], lambda t: f"c.s.{t}"
    )
    assert ddl.startswith(
        "CREATE OR REPLACE VIEW c.s.v_meeting_item_models (\n    item_id COMMENT "
    )
    assert "\nAS\nSELECT\n" in ddl and "FROM c.s.g_meeting_items_bu i" in ddl


@pytest.fixture(scope="module")
def fake_tables(mod, spark):
    """依 spec 建 temp view：t_<table>，塞少量假資料。"""
    rows = {
        "s_meeting_record_mail_bu": [
            {
                "pk_seq": 1,
                "subject_clean": "acer weekly",
                "forwarder_dept_code": "DTDBB0",
                "display_len": 100,
            },
            {"pk_seq": 2, "subject_clean": "dup mail", "dup_of_pk": 1},
        ],
        "s_meeting_record_clean_bu": [
            {"pk_seq": 1, "segment_no": 1, "sub_no": 0, "content_type": "inline_minutes"},
            {
                "pk_seq": 1,
                "segment_no": 2,
                "sub_no": 0,
                "content_type": "inline_minutes",
                "dup_of": "9-1-0",
            },
            {"pk_seq": 1, "segment_no": 3, "sub_no": 0, "content_type": "noise"},
        ],
        "s_meeting_participants_bu": [
            {
                "pk_seq": 1,
                "segment_no": 0,
                "token": "P01",
                "role": "forwarder",
                "kind": "person",
                "side": "auo",
                "company": "auo",
                "dept_code": "DTDBB0",
                "name_zh": "假名",
                "email": "x@auo.com",
            },
            {
                "pk_seq": 1,
                "segment_no": 1,
                "token": "P02",
                "role": "from",
                "kind": "person",
                "side": "customer",
                "company": "acer",
                "email": "y@acer.com",
            },
            {
                "pk_seq": 1,
                "segment_no": 2,
                "token": "P02",
                "role": "cc",
                "kind": "person",
                "side": "customer",
                "company": "acer",
            },
            {
                "pk_seq": 1,
                "segment_no": 1,
                "token": "P03",
                "role": "to",
                "kind": "person",
                "side": "third_party",
                "company": "sumika",
            },
        ],
        "g_meeting_items_bu": [
            {
                "item_id": "BU-MTG-1-1-0-001",
                "pk_seq": 1,
                "segment_no": 1,
                "sub_no": 0,
                "speaker_token": "P02",
                "customer": "acer",
                "app": "NB",
                "model_nos": ["M1", "M2"],
                "topic_tags": ["price", "supply"],
                "sensitivity": "S1",
                "extract_status": "ok",
                "superseded": False,
            },
            {
                "item_id": "BU-MTG-1-1-0-002",
                "pk_seq": 1,
                "segment_no": 1,
                "sub_no": 0,
                "speaker_token": None,
                "speaker_side": "auo",
                "customer": "acer",
                "app": "MNT",
                "sensitivity": "S2",
                "extract_status": "ok",
                "superseded": False,
            },
            {
                "item_id": "BU-MTG-1-1-0-003",
                "pk_seq": 1,
                "segment_no": 1,
                "sub_no": 0,
                "customer": "dell",
                "app": "NB",
                "model_nos": ["M9"],
                "sensitivity": "S0",
                "extract_status": "ok",
                "superseded": True,
            },
            {
                "item_id": "BU-MTG-1-1-0-004",
                "pk_seq": 1,
                "segment_no": 1,
                "sub_no": 0,
                "customer": "dell",
                "extract_status": "failed_quote",
                "superseded": False,
            },
        ],
        "b_meeting_migration_log": [],
    }
    for t, spec in mod.TABLES.items():
        cols = [c[0] for c in spec["columns"]]
        data = [tuple(r.get(c) for c in cols) for r in rows[t]]
        spark.createDataFrame(data, mod.schema_ddl(spec)).createOrReplaceTempView(f"t_{t}")
    return lambda t: f"t_{t}"


def _run(mod, spark, fq, view):
    return spark.sql(mod.build_select(mod.VIEWS[view], fq))


def test_views_columns_and_no_s3(mod, spark, fake_tables):
    for v, spec in mod.VIEWS.items():
        df = _run(mod, spark, fake_tables, v)
        assert df.columns == [a for _, a, _ in spec["select"]], v
        assert not (set(df.columns) & mod.S3_COLS), v


def test_items_q_filters_and_speaker_join(mod, spark, fake_tables):
    got = {r.item_id: r for r in _run(mod, spark, fake_tables, "v_meeting_items_q").collect()}
    assert set(got) == {"BU-MTG-1-1-0-001", "BU-MTG-1-1-0-002"}  # superseded / failed 不出現
    a, b = got["BU-MTG-1-1-0-001"], got["BU-MTG-1-1-0-002"]
    assert (a.speaker_company, a.speaker_side, a.speaker_dept_code) == ("acer", "customer", None)
    assert a.model_nos_str == "M1, M2" and a.topic_tags_str == "price, supply"
    assert (b.speaker_company, b.speaker_side) == (
        None,
        "auo",
    )  # token NULL → 採條目自己的 speaker_side


def test_item_models_explode(mod, spark, fake_tables):
    rows = _run(mod, spark, fake_tables, "v_meeting_item_models").collect()
    assert sorted((r.item_id, r.model_no) for r in rows) == [
        ("BU-MTG-1-1-0-001", "M1"),
        ("BU-MTG-1-1-0-001", "M2"),
    ]


def test_mail_index_aggregates(mod, spark, fake_tables):
    got = {r.pk_seq: r for r in _run(mod, spark, fake_tables, "v_meeting_mail_index").collect()}
    assert set(got) == {1, 2}
    m = got[1]
    assert (m.segment_count, m.dup_segment_count) == (3, 1)
    assert m.content_types == "inline_minutes:2,noise:1"
    assert (m.item_count, m.customer, m.sensitivity_max) == (2, "acer", "S2")
    assert m.participant_companies == ["acer", "sumika"]  # 不含 auo
    e = got[2]
    assert (e.segment_count, e.item_count, e.customer, e.participant_companies, e.dup_of_pk) == (
        0,
        0,
        None,
        None,
        1,
    )
