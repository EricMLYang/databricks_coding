"""004_meeting_sb_lens 的純函式 cell 測試（[c02]～[c06]）。

驗 spec 合法、兩張鏡頭表的鍵與必要欄、面向映射種子剛好涵蓋 L1 詞表（task 3 [c02] TOPIC_TAGS），
以及四個 View 的 SQL 真的能跑：用 002 的 spec 建中立層假表、004 的 spec 建鏡頭假表、
Phase 0 探勘到的欄位建 Sales Brief 三張假表，把 [c06] 的 SELECT 跑一遍，
檢查 brief_text 的 unpivot（品牌格 + ALL 格、空白 → NULL、同格多列取最新）、
period 的截止點與上一期、items_sb_q 的 active 過濾與 join、
reconcile_q 的排序 / 有效 relation / 待審旗標。假資料無人名。
"""

import copy
from datetime import date, datetime

import pytest
from nbload import load_cells

NB = "jobs/meeting_record/meeting_extracted_migration/004_meeting_sb_lens.ipynb"
NB_002 = "jobs/meeting_record/meeting_extracted_migration/002_meeting_neutral_tables.ipynb"
NB_T3 = "jobs/meeting_record/meeting_extracted_w1_t2_extract/notebook.ipynb"


@pytest.fixture(scope="module")
def mod():
    return load_cells(NB, ["c02", "c03", "c04", "c05", "c06"], name="mig004")


@pytest.fixture(scope="module")
def mod002():
    return load_cells(NB_002, ["c02", "c03", "c04"], name="mig002_for_004")


@pytest.fixture(scope="module")
def seed_rows(mod):
    return mod.parse_csv_text(mod.FACET_MAP_SEED, mod.FACET_MAP_COLS)


# ---------- spec ----------
def test_specs_valid(mod):
    assert mod.validate_specs(mod.TABLES, mod.VIEWS) == []
    assert set(mod.TABLES) == {
        "g_meeting_items_sb_bu",
        "g_meeting_sb_reconcile_bu",
        "s_meeting_sb_facet_map",
        "b_meeting_migration_log",
    }
    assert set(mod.VIEWS) == {
        "v_meeting_sb_brief_text",
        "v_meeting_sb_period",
        "v_meeting_items_sb_q",
        "v_meeting_sb_reconcile_q",
    }
    assert mod.SLUG == "004_meeting_sb_lens"


def test_table_keys_and_spec_fields(mod):
    """§3.4 / §3.5 的欄位都要在；鍵照 README（標註表改 item_key）。"""
    sb = mod.TABLES["g_meeting_items_sb_bu"]
    assert sb["key"] == ["item_key", "app_name"] and sb["cluster_by"] == ["brief_month"]
    names = {c[0] for c in sb["columns"]}
    for f in [
        "item_id",
        "brief_month",
        "app_name",
        "brand",
        "brand_in_sb",
        "facet",
        "facet_basis",
        "sb_relevant",
        "relevance_basis",
        "labeler_version",
        "labeled_at",
        "window_start",
        "window_end",
    ]:
        assert f in names, f
    rc = mod.TABLES["g_meeting_sb_reconcile_bu"]
    assert rc["key"] == ["app_name", "brand", "facet", "brief_month"]
    names = {c[0] for c in rc["columns"]}
    for f in [
        "sb_text",
        "sb_source",
        "meeting_summary",
        "meeting_summary_shareable",
        "meeting_item_ids",
        "topic_tags_agg",
        "relation",
        "relation_basis",
        "rationale",
        "number_caveat",
        "cross_customer_flag",
        "cross_customer_note",
        "sensitivity_max",
        "reviewer",
        "review_verdict",
        "review_relation",
        "review_note",
        "review_carried_from",
        "prompt_version",
        "model",
        "created_at",
    ]:
        assert f in names, f


def test_validate_catches_missing_required_and_s3(mod):
    tables = copy.deepcopy(mod.TABLES)
    tables["g_meeting_sb_reconcile_bu"]["columns"] = [
        c for c in tables["g_meeting_sb_reconcile_bu"]["columns"] if c[0] != "review_note"
    ]
    views = copy.deepcopy(mod.VIEWS)
    views["v_meeting_sb_reconcile_q"]["select"].append(("r.email", "email", "洩漏"))
    text = "\n".join(mod.validate_specs(tables, views))
    assert "缺必要欄 review_note" in text and "暴露 S3 欄" in text


def test_create_table_ddl(mod):
    ddl = mod.build_create_table(
        "c.s.g_meeting_sb_reconcile_bu", mod.TABLES["g_meeting_sb_reconcile_bu"]
    )
    assert ddl.startswith("CREATE TABLE IF NOT EXISTS c.s.g_meeting_sb_reconcile_bu (")
    assert "brand STRING NOT NULL" in ddl and "USING DELTA\nCLUSTER BY (brief_month)" in ddl


def test_facet_constants_match_sales_brief(mod):
    """四面向 ↔ 填報表欄名（Phase 0 待決 #10）。"""
    assert mod.FACETS == ("market_outlook", "product_tech", "price", "other")
    assert mod.SB_FACET_COLS == {
        "market_outlook": "summary_futureOutlook",
        "product_tech": "summary_techProduct",
        "price": "summary_pricing",
        "other": "summary_otherInfo",
    }
    assert mod.SB_FIELD_KEYS["market_outlook"] == "futureOutlook"
    assert set(mod.RELATION_RANK) == set(mod.RELATIONS)


# ---------- 種子 ----------
def test_seed_valid_and_covers_topic_tags(mod, seed_rows):
    t3 = load_cells(NB_T3, ["c02"], name="t3_for_004")
    assert mod.validate_facet_seed(seed_rows, set(t3.TOPIC_TAGS)) == []
    look = mod.facet_lookup(seed_rows)
    # §7.1 表
    assert (
        look["demand"]["facet"] == "market_outlook"
        and look["commercial_relation"]["facet"] == "market_outlook"
    )
    assert (
        look["product_plan"]["facet"] == "product_tech" and look["spec"]["facet"] == "product_tech"
    )
    assert look["price"]["facet"] == "price" and look["cost"]["facet"] == "price"
    for t in ("supply_chain", "capacity", "allocation", "quality"):
        assert look[t]["facet"] == "other", t
    for t in ("schedule", "engineering", "terminology", "admin"):
        assert look[t]["facet"] is None and look[t]["relevance_rule"] == "never", t
    assert look["schedule"]["follow_tag"] == "product_plan"
    # §7.2 規則
    assert look["spec"]["relevance_rule"] == "spec_statement"
    assert look["capacity"]["relevance_rule"] == "capacity_timeref"
    assert look["quality"]["relevance_rule"] == "quality_request_or_customer"
    assert all(
        look[t]["relevance_rule"] == "always"
        for t in (
            "demand",
            "allocation",
            "price",
            "cost",
            "product_plan",
            "supply_chain",
            "commercial_relation",
        )
    )


def test_seed_validation_catches_errors(mod, seed_rows):
    rows = copy.deepcopy(seed_rows)
    rows[0]["facet"] = "pricing"  # 不在 FACETS
    rows[1]["relevance_rule"] = "never"  # 有映射卻 never
    rows.append(
        {
            "topic_tag": "schedule",
            "facet": None,
            "relevance_rule": "never",
            "follow_tag": "admin",
            "note": None,
        }
    )
    text = "\n".join(mod.validate_facet_seed(rows, {r["topic_tag"] for r in seed_rows} | {"zzz"}))
    assert "facet 不在" in text and "不能是 never" in text and "topic_tag 重複" in text
    assert "follow_tag 'admin' 不是有映射的 tag" in text and "少了 L1 詞表的 tag：['zzz']" in text


# ---------- View SQL 實跑 ----------
_T = datetime(2026, 9, 23, 2, 5)


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
        "topic_tags": ["demand"],
        "topic_tag_primary": "demand",
        "summary": "sum",
        "quote": "quote text",
        "numbers": "[]",
        "time_refs": "[]",
        "model_nos": ["M270QAN06.A"],
        "event_date": date(2026, 9, 10),
        "event_month": "2026-09",
        "sensitivity": "S1",
        "confidence": 0.8,
        "extract_status": "ok",
        "superseded": False,
        "prompt_version": "0.3",
        "cleaner_version": "0.2",
        "extracted_at": _T,
    }
    return {**base, **kw}


def _label(key, app, **kw):
    base = {
        "item_key": key,
        "app_name": app,
        "item_id": f"id-{key}",
        "pk_seq": 1,
        "segment_no": 1,
        "sub_no": 0,
        "unit": "bu",
        "brief_month": "2026-09",
        "brief_month_basis": "submitted_at",
        "window_start": date(2026, 8, 25),
        "window_end": date(2026, 9, 22),
        "app_basis_sb": "neutral",
        "customer": "acer",
        "brand": "Acer",
        "brand_basis": "sb_brand",
        "brand_in_sb": True,
        "facet": "product_tech",
        "facet_basis": "rule_primary",
        "sb_relevant": True,
        "relevance_basis": "always:product_plan",
        "statement_type": "plan",
        "topic_tag_primary": "product_plan",
        "topic_tags": ["product_plan"],
        "speaker_side": "customer",
        "event_date": date(2026, 9, 10),
        "summary": "sum",
        "sensitivity": "S1",
        "confidence": 0.9,
        "active": True,
        "labeler_version": "0.1+map0.1",
        "labeled_at": _T,
        "updated_at": _T,
    }
    return {**base, **kw}


def _cell(app, brand, facet, relation, **kw):
    base = {
        "app_name": app,
        "brand": brand,
        "facet": facet,
        "brief_month": "2026-09",
        "window_start": date(2026, 8, 25),
        "window_end": date(2026, 9, 22),
        "sb_text": "sb",
        "sb_source": "g_sales_brief_brand_summary",
        "meeting_summary": "ms",
        "meeting_summary_shareable": "ms",
        "shareable_failed": False,
        "meeting_item_ids": ["id-k1"],
        "meeting_item_keys": ["k1"],
        "n_items": 1,
        "n_items_sent": 1,
        "topic_tags_agg": ["product_plan"],
        "relation": relation,
        "relation_basis": "llm",
        "sensitivity_max": "S1",
        "prompt_version": "0.1",
        "model": "m",
        "created_at": _T,
        "updated_at": _T,
    }
    return {**base, **kw}


_SB_SUMMARY_COLS = (
    "app_code string, brand_code string, fill_year smallint, fill_month smallint, "
    "summary_futureOutlook string, summary_techProduct string, summary_pricing string, "
    "summary_otherInfo string, create_time timestamp"
)
_SB_APP_COLS = (
    "app_code string, fill_year smallint, fill_month smallint, create_time timestamp, "
    "summary_futureOutlook string, summary_techProduct string, summary_pricing string, "
    "summary_otherInfo string"
)
_SB_MI_COLS = (
    "submission_id bigint, app_code string, brand_master_id int, brand_code string, "
    "brand_name string, module_code string, product_line_type string, emp_no string, "
    "fill_year smallint, fill_month smallint, status string, submitted_at timestamp, "
    "field_key string, content string"
)


@pytest.fixture(scope="module")
def fake_tables(mod, mod002, spark):
    items = [
        _item("id-k1", "k1"),
        _item("id-k2", "k2", superseded=True),  # 已被重萃取代
        _item("id-k9", "k9", app=None, customer=None),
    ]
    labels = [
        _label("k1", "MNT"),
        _label("k2", "MNT", item_id="id-k2"),
        _label("k3", "NB", item_id="id-k3", active=False),  # 不在 q
    ]
    cells = [
        _cell("MNT", "Acer", "product_tech", "meeting_only", sb_text=None, sb_source="none"),
        _cell(
            "MNT", "Asus", "product_tech", "sb_only", meeting_item_ids=[], n_items=0, n_items_sent=0
        ),
        _cell(
            "MNT",
            "ALL",
            "product_tech",
            "supplement",
            sb_source="g_sales_brief_app_summary",
            cross_customer_note="acer 與 ASUS 同時關注 4ch LVDS",
        ),
        _cell(
            "TV",
            "TCL",
            "other",
            "corroborate",
            review_verdict="fix_relation",
            review_relation="supplement",
        ),
        _cell("TV", "TCL", "price", "conflict"),
    ]
    t1, t2 = datetime(2026, 9, 15, 17, 23), datetime(2026, 9, 22, 10, 41)
    brand_summary = [
        ("MNT", "Asus", 2026, 9, "fo", "tp", "pr", "", datetime(2026, 9, 23, 2, 5)),
        ("MNT", "Dell", 2026, 9, None, None, None, None, datetime(2026, 9, 23, 2, 5)),
        ("MNT", "Asus", 2026, 8, "old-fo", "old-tp", None, None, datetime(2026, 8, 24, 14, 44)),
        (
            "MNT",
            "Asus",
            2026,
            8,
            "new-fo",
            "new-tp",
            None,
            None,
            datetime(2026, 9, 4, 0, 32),
        ),  # 重填取最新
        ("TV", "TCL", 2026, 9, "tv-fo", "tv-tp", "tv-pr", "tv-ot", datetime(2026, 9, 23, 2, 5)),
    ]
    app_summary = [
        ("MNT", 2026, 9, datetime(2026, 9, 23, 2, 2), "app-fo", "app-tp", "app-pr", "app-ot"),
        ("MNT", 2026, 8, datetime(2026, 8, 24, 14, 41), "a8", None, None, None),
    ]
    mi = [
        (1, "MNT", 1, "Asus", "ASUS", "m", "p", "e", 2026, 9, "submitted", t1, "pricing", "c"),
        (2, "MNT", 2, "Dell", "Dell", "m", "p", "e", 2026, 9, "submitted", t2, "pricing", "c"),
        (
            3,
            "MNT",
            1,
            "Asus",
            "ASUS",
            "m",
            "p",
            "e",
            2026,
            8,
            "submitted",
            datetime(2026, 8, 24, 16, 40),
            "pricing",
            "c",
        ),
        (
            4,
            "TV",
            3,
            "TCL",
            "TCL",
            "m",
            "p",
            "e",
            2026,
            9,
            "submitted",
            datetime(2026, 9, 22, 9, 41),
            "pricing",
            "c",
        ),
        (
            5,
            "NB",
            4,
            "HP",
            "HP",
            "m",
            "p",
            "e",
            2026,
            9,
            "submitted",
            datetime(2026, 9, 22, 8, 39),
            "pricing",
            "c",
        ),  # NB 沒 brand_summary
    ]
    spec = mod002.TABLES["g_meeting_items_bu"]
    cols = [c[0] for c in spec["columns"]]
    spark.createDataFrame(
        [tuple(r.get(c) for c in cols) for r in items], mod002.schema_ddl(spec)
    ).createOrReplaceTempView("t_g_meeting_items_bu")
    for t, rows in (("g_meeting_items_sb_bu", labels), ("g_meeting_sb_reconcile_bu", cells)):
        spec = mod.TABLES[t]
        cols = [c[0] for c in spec["columns"]]
        spark.createDataFrame(
            [tuple(r.get(c) for c in cols) for r in rows], mod.schema_ddl(spec)
        ).createOrReplaceTempView(f"t_{t}")
    spark.createDataFrame(brand_summary, _SB_SUMMARY_COLS).createOrReplaceTempView(
        "t_g_sales_brief_brand_summary"
    )
    spark.createDataFrame(app_summary, _SB_APP_COLS).createOrReplaceTempView(
        "t_g_sales_brief_app_summary"
    )
    spark.createDataFrame(mi, _SB_MI_COLS).createOrReplaceTempView(
        "t_g_sales_brief_market_intelligence"
    )
    return lambda t: f"t_{t}"


def _run(mod, spark, fq, view):
    return spark.sql(mod.build_select(mod.VIEWS[view], fq))


def test_views_columns_and_no_s3(mod, spark, fake_tables):
    for v, spec in mod.VIEWS.items():
        df = _run(mod, spark, fake_tables, v)
        assert df.columns == [a for _, a, _ in spec["select"]], v
        assert not (set(df.columns) & mod.S3_COLS), v


def test_brief_text_unpivot(mod, spark, fake_tables):
    rows = _run(mod, spark, fake_tables, "v_meeting_sb_brief_text").collect()
    got = {(r.app_name, r.brand, r.facet, r.brief_month): r for r in rows}
    # 品牌格：5 列 brand_summary 去掉重填的 1 列 = 4 格組 × 4 面向；ALL 格：2 期 × 4
    assert len(rows) == 4 * 4 + 2 * 4
    assert got[("MNT", "Asus", "market_outlook", "2026-09")].sb_text == "fo"
    assert got[("MNT", "Asus", "price", "2026-09")].sb_source == "g_sales_brief_brand_summary"
    empty = got[("MNT", "Asus", "other", "2026-09")]  # '' → NULL / none
    assert empty.sb_text is None and empty.sb_source == "none"
    dell = got[("MNT", "Dell", "product_tech", "2026-09")]  # 有列但全空：仍出現，sb_text NULL
    assert dell.sb_text is None and dell.sb_source == "none"
    assert (
        got[("MNT", "Asus", "market_outlook", "2026-08")].sb_text == "new-fo"
    )  # 同格多列取 create_time 最新
    assert got[("MNT", "ALL", "product_tech", "2026-09")].sb_text == "app-tp"
    assert got[("MNT", "ALL", "product_tech", "2026-09")].sb_source == "g_sales_brief_app_summary"
    assert ("NB", "ALL", "price", "2026-09") not in got  # NB 沒 app_summary


def test_period_cutoffs(mod, spark, fake_tables):
    got = {
        (r.app_name, r.brief_month): r
        for r in _run(mod, spark, fake_tables, "v_meeting_sb_period").collect()
    }
    assert set(got) == {
        ("MNT", "2026-09"),
        ("MNT", "2026-08"),
        ("TV", "2026-09"),
        ("NB", "2026-09"),
    }
    m9 = got[("MNT", "2026-09")]
    assert m9.brands == ["Asus", "Dell"] and m9.n_brands == 2
    assert m9.submitted_end == datetime(2026, 9, 22, 10, 41) and m9.submitted_start == datetime(
        2026, 9, 15, 17, 23
    )
    assert m9.prev_submitted_end == datetime(2026, 8, 24, 16, 40) and m9.has_app_summary is True
    m8 = got[("MNT", "2026-08")]
    assert m8.prev_submitted_end is None and m8.brands == ["Asus"]
    nb = got[("NB", "2026-09")]  # 只有 market_intelligence：品牌空、無 app 摘要，但截止點在
    assert nb.brands == [] and nb.n_brands == 0 and nb.has_app_summary is False
    assert nb.submitted_end == datetime(2026, 9, 22, 8, 39)


def test_items_sb_q_active_and_join(mod, spark, fake_tables):
    got = {r.item_key: r for r in _run(mod, spark, fake_tables, "v_meeting_items_sb_q").collect()}
    assert set(got) == {"k1", "k2"}  # active = false 不出現
    assert got["k1"].quote == "quote text" and got["k1"].model_nos == ["M270QAN06.A"]
    assert got["k1"].item_still_valid is True and got["k2"].item_still_valid is False
    assert got["k1"].app_neutral == "MNT" and got["k1"].brand == "Acer"


def test_reconcile_q_rank_and_review(mod, spark, fake_tables):
    rows = _run(mod, spark, fake_tables, "v_meeting_sb_reconcile_q").collect()
    got = {(r.app_name, r.brand, r.facet): r for r in rows}
    order = [r.relation for r in sorted(rows, key=lambda r: (r.relation_rank, r.app_name, r.brand))]
    assert order == ["conflict", "supplement", "meeting_only", "corroborate", "sb_only"]
    tcl = got[("TV", "TCL", "other")]
    assert tcl.effective_relation == "supplement" and tcl.review_pending is False
    assert got[("TV", "TCL", "price")].effective_relation == "conflict"
    assert got[("TV", "TCL", "price")].review_pending is True
    assert got[("MNT", "Asus", "product_tech")].review_pending is False  # sb_only 不審
    assert got[("MNT", "ALL", "product_tech")].is_app_level is True
    assert got[("MNT", "Acer", "product_tech")].is_app_level is False
