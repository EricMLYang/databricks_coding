"""meeting_extracted_w2_t3_label 的測試（[c02]～[c04]）。

[c03] 窗口用純日期算：submitted_at（含缺截止點退回 fixed_day、上一期跳月）、calendar、
fixed_day、grace、overrides。
[c04] 規則鏈在本機 Spark 以假表實跑：app 展開、窗口切、品牌（含 D9 samsung）、brand_in_sb、
面向（primary / follow / secondary / unresolved）、相關性四條規則、標註表欄位順序。假資料無人名。
"""

from datetime import date, datetime

import pytest
from nbload import load_cells

NB = "jobs/meeting_record/meeting_extracted_w2_t3_label/notebook.ipynb"
NB_004 = "jobs/meeting_record/meeting_extracted_migration/004_meeting_sb_lens.ipynb"
NB_T3 = "jobs/meeting_record/meeting_extracted_w1_t2_extract/notebook.ipynb"


@pytest.fixture(scope="module")
def mod():
    return load_cells(NB, ["c02", "c03", "c04"], name="w2_t3")


@pytest.fixture(scope="module")
def mod004():
    return load_cells(NB_004, ["c02", "c03", "c04", "c05", "c06"], name="mig004_for_t3")


@pytest.fixture(scope="module")
def facet_rows(mod004):
    rows = mod004.parse_csv_text(mod004.FACET_MAP_SEED, mod004.FACET_MAP_COLS)
    return [{**r, "is_active": True} for r in rows]


# ---------- 常數對齊 ----------
def test_constants_align(mod, mod004):
    assert mod.FACETS == mod004.FACETS and mod.APP_UNRESOLVED == mod004.APP_UNRESOLVED
    assert set(mod.RELEVANCE_RULES) == set(mod004.RELEVANCE_RULES)
    table_cols = [c[0] for c in mod004.TABLES["g_meeting_items_sb_bu"]["columns"]]
    assert mod.LABEL_COLS == table_cols  # 順序也要一樣（MERGE INSERT 用）
    assert isinstance(mod.LABELER_RULE_VERSION_IN_CELL, str) and mod.LABELER_RULE_VERSION_IN_CELL
    t3 = load_cells(NB_T3, ["c02"], name="t3_for_w2")
    assert set(mod.SPEC_STATEMENT_TYPES) <= set(t3.STATEMENT_TYPES)
    assert set(mod.APPS) <= set(t3.APPS)


# ---------- [c03] 窗口 ----------
_P = {  # periods[app][ym] = submitted_end
    "MNT": {
        "2026-07": datetime(2026, 7, 25),
        "2026-08": datetime(2026, 8, 24, 16, 40),
        "2026-09": datetime(2026, 9, 21, 9, 47),
    },
    "TV": {
        "2026-06": datetime(2026, 6, 25),
        "2026-08": datetime(2026, 8, 25, 14, 8),
        "2026-09": datetime(2026, 9, 22, 9, 41),
    },
}
_KW = dict(mode="submitted_at", fixed_day=25, grace_days=0, overrides={})


def test_window_submitted_at(mod):
    w = mod.app_window("MNT", "2026-09", _P["MNT"], **_KW)
    assert (w["start"], w["end"], w["basis"]) == (
        date(2026, 8, 25),
        date(2026, 9, 21),
        "submitted_at",
    )
    assert w["note"] == ""


def test_window_prev_period_skips_month(mod):
    """TV 缺 2026-07：8 月窗口從 6 月截止 + 1 起。"""
    w = mod.app_window("TV", "2026-08", _P["TV"], **_KW)
    assert (w["start"], w["end"]) == (date(2026, 6, 26), date(2026, 8, 25))


def test_window_fallback_when_no_submitted_end(mod):
    """10 月 brief 還沒填：迄退回 fixed_day，起仍用 9 月真實截止 + 1。"""
    w = mod.app_window("MNT", "2026-10", _P["MNT"], **_KW)
    assert (w["start"], w["end"], w["basis"]) == (
        date(2026, 9, 22),
        date(2026, 10, 25),
        "fixed_day",
    )
    assert "fallback" in w["note"]


def test_window_first_period_and_grace(mod):
    """沒有任何上一期：起 = 上個月 fixed_day + 1；grace 兩端一起移。"""
    w = mod.app_window(
        "NB",
        "2026-09",
        {"2026-09": datetime(2026, 9, 22, 10, 41)},
        mode="submitted_at",
        fixed_day=25,
        grace_days=3,
        overrides={},
    )
    assert (w["start"], w["end"]) == (date(2026, 8, 29), date(2026, 9, 25))
    assert "prev period missing" in w["note"]


def test_window_calendar_fixed_day_override(mod):
    cal = mod.app_window(
        "MNT", "2026-09", _P["MNT"], mode="calendar", fixed_day=25, grace_days=5, overrides={}
    )
    assert (cal["start"], cal["end"], cal["basis"]) == (
        date(2026, 9, 1),
        date(2026, 9, 30),
        "calendar",
    )
    fx = mod.app_window(
        "MNT", "2026-02", {}, mode="fixed_day", fixed_day=28, grace_days=0, overrides={}
    )
    assert (fx["start"], fx["end"]) == (date(2026, 1, 29), date(2026, 2, 28))
    ov = mod.app_window(
        "TV",
        "2026-08",
        _P["TV"],
        mode="submitted_at",
        fixed_day=25,
        grace_days=0,
        overrides={"TV:2026-08": {"start": "2026-07-26", "end": "2026-08-25"}},
    )
    assert (ov["start"], ov["end"], ov["basis"]) == (
        date(2026, 7, 26),
        date(2026, 8, 25),
        "override",
    )


def test_compute_windows_span(mod):
    ws = mod.compute_windows("2026-09", _P, **_KW)
    assert set(ws) == {"TV", "NB", "MNT", mod.APP_UNRESOLVED}
    assert ws["NB"]["basis"] == "fixed_day"  # NB 沒期別資料 → fallback
    u = ws[mod.APP_UNRESOLVED]
    assert u["start"] == min(ws[a]["start"] for a in mod.APPS) and u["end"] == max(
        ws[a]["end"] for a in mod.APPS
    )
    rows = mod.windows_to_rows(ws)
    assert len(rows) == 4 and rows[0][0] in ws


# ---------- [c04] 規則鏈 ----------
def _item(key, **kw):
    base = {
        "item_id": f"BU-MTG-1-1-0-{key}",
        "item_key": key,
        "pk_seq": 1,
        "segment_no": 1,
        "sub_no": 0,
        "unit": "bu",
        "customer": "acer",
        "app": "MNT",
        "statement_type": "fact",
        "topic_tag_primary": "demand",
        "topic_tags": ["demand"],
        "speaker_side": "customer",
        "event_date": date(2026, 9, 10),
        "summary": "s",
        "sensitivity": "S1",
        "confidence": 0.8,
        "time_refs": "[]",
        "extract_status": "ok",
        "superseded": False,
    }
    return {**base, **kw}


_ITEM_SCHEMA = (
    "item_id string, item_key string, pk_seq bigint, segment_no int, sub_no int, unit string, "
    "customer string, app string, statement_type string, topic_tag_primary string, "
    "topic_tags array<string>, speaker_side string, "
    "event_date date, summary string, sensitivity string, confidence double, time_refs string, "
    "extract_status string, superseded boolean"
)
_ITEM_COLS = [c.split()[0] for c in _ITEM_SCHEMA.split(", ")]


@pytest.fixture(scope="module")
def fake(mod, spark):
    items = [
        _item("k1"),  # MNT acer demand fact → relevant（always:demand），Acer 不在 MNT brief
        _item("k1", item_id="BU-MTG-1-1-0-k1b"),  # 同 key 第二列 → 去重
        _item("k2", customer="dell", app=None),  # ALL → Dell MNT|NB 展開 2 列
        _item("k3", customer=None, app=None),  # 客戶 NULL → app_unresolved
        _item(
            "k4", customer="samsung", app="TV", topic_tags=["price"], topic_tag_primary="price"
        ),  # D9 → Samsung
        _item("k5", customer="sony", app="TV"),  # 無 sb_brand → customer_fallback
        _item(
            "k6",
            app="NB",
            topic_tag_primary="schedule",
            topic_tags=["schedule", "product_plan"],
            statement_type="plan",
        ),  # follow_tag → product_tech / rule_secondary；always:product_plan
        _item(
            "k7", topic_tag_primary="engineering", topic_tags=["engineering", "cost"]
        ),  # secondary → price
        _item(
            "k8", topic_tag_primary="admin", topic_tags=["admin", "terminology"]
        ),  # unresolved / never
        _item(
            "k9", topic_tag_primary="spec", topic_tags=["spec"], statement_type="fact"
        ),  # 規則 2 不符 → no_rule
        _item(
            "k10", topic_tag_primary="spec", topic_tags=["spec"], statement_type="request"
        ),  # 規則 2 符合
        _item(
            "k11", topic_tag_primary="capacity", topic_tags=["capacity"], time_refs="[]"
        ),  # 規則 3 不符
        _item(
            "k12",
            topic_tag_primary="capacity",
            topic_tags=["capacity"],
            time_refs='[{"when": "2026-11", "what": "x"}]',
        ),  # 規則 3 符合
        _item(
            "k13", topic_tag_primary="quality", topic_tags=["quality"], speaker_side="auo"
        ),  # 規則 4 不符
        _item(
            "k14",
            topic_tag_primary="quality",
            topic_tags=["quality"],
            speaker_side="auo",
            statement_type="request",
        ),  # 規則 4 符合
        _item("k15", event_date=date(2026, 8, 20)),  # MNT 窗口外（8-25 起）
        _item(
            "k16", app="TV", event_date=date(2026, 8, 24), customer="tcl"
        ),  # TV 窗口內（8-23 起）
        _item("k17", superseded=True),
        _item("k18", extract_status="failed_quote"),
        _item("k19", unit="xx"),
        _item("k20", event_date=None),
    ]
    entity = [
        ("acer", ["MNT", "NB"], True),
        ("dell", ["MNT", "NB"], True),
        ("samsung", [], True),
        ("samsung_vd", ["TV", "MNT"], True),
        ("sony", ["TV"], True),
        ("tcl", ["TV"], True),
        ("old", ["TV"], False),
    ]
    alias = [
        ("sb_brand", "Acer", "acer", True),
        ("sb_brand", "Dell", "dell", True),
        ("sb_brand", "Samsung", "samsung_vd", True),
        ("sb_brand", "TCL", "tcl", True),
        ("name", "Sony", "sony", True),
        ("sb_brand", "Old", "old", False),
    ]
    period = [
        ("MNT", "2026-09", ["Asus", "Dell", "HP", "Samsung"]),
        ("NB", "2026-09", ["Acer", "Dell"]),
        ("TV", "2026-09", ["Samsung", "TCL"]),
        ("MNT", "2026-08", ["Asus"]),
    ]
    spark.createDataFrame(
        [tuple(r[c] for c in _ITEM_COLS) for r in items], _ITEM_SCHEMA
    ).createOrReplaceTempView("t_items")
    df_items = spark.table("t_items")
    df_entity = spark.createDataFrame(
        entity, "entity_id string, app_default array<string>, is_active boolean"
    )
    df_alias = spark.createDataFrame(
        alias, "alias_type string, alias string, entity_id string, is_active boolean"
    )
    df_period = spark.createDataFrame(
        period, "app_name string, brief_month string, brands array<string>"
    )
    windows = {
        "MNT": {"start": date(2026, 8, 25), "end": date(2026, 9, 21), "basis": "submitted_at"},
        "NB": {"start": date(2026, 8, 27), "end": date(2026, 9, 22), "basis": "submitted_at"},
        "TV": {"start": date(2026, 8, 23), "end": date(2026, 9, 22), "basis": "submitted_at"},
        mod.APP_UNRESOLVED: {
            "start": date(2026, 8, 23),
            "end": date(2026, 9, 22),
            "basis": "unresolved_span",
        },
    }
    df_windows = spark.createDataFrame(
        mod.windows_to_rows(windows),
        "app_name string, window_start date, window_end date, brief_month_basis string",
    )
    return dict(
        items=df_items,
        entity=df_entity,
        alias=df_alias,
        period=df_period,
        windows=df_windows,
        span=(date(2026, 8, 23), date(2026, 9, 22)),
    )


@pytest.fixture(scope="module")
def labeled(mod, fake, facet_rows):
    df = mod.label_pipeline(
        fake["items"],
        fake["entity"],
        fake["alias"],
        fake["period"],
        fake["windows"],
        facet_rows,
        unit="bu",
        brief_month="2026-09",
        span=fake["span"],
        labeler_version="0.1+map0.1",
    )
    rows = df.collect()
    return df, {(r.item_key, r.app_name): r for r in rows}


def test_label_columns_and_filters(mod, labeled):
    df, got = labeled
    assert df.columns == mod.LABEL_COLS
    keys = {k for k, _ in got}
    assert {"k15", "k17", "k18", "k19", "k20"}.isdisjoint(
        keys
    )  # 窗口外 / superseded / failed / 別的 unit / 無日期
    assert sum(1 for k, _ in got if k == "k1") == 1  # 同 key 去重
    assert {a for k, a in got if k == "k2"} == {"MNT", "NB"}  # ALL 展開
    assert all(
        r.brief_month == "2026-09" and r.active and r.labeler_version == "0.1+map0.1"
        for r in got.values()
    )


def test_app_expand_and_window(mod, labeled):
    _, got = labeled
    k1, k2, k3 = got[("k1", "MNT")], got[("k2", "NB")], got[("k3", mod.APP_UNRESOLVED)]
    assert (k1.app_basis_sb, k1.window_start, k1.window_end, k1.brief_month_basis) == (
        "neutral",
        date(2026, 8, 25),
        date(2026, 9, 21),
        "submitted_at",
    )
    assert k2.app_basis_sb == "customer_default" and k2.window_start == date(2026, 8, 27)
    assert (k3.app_basis_sb, k3.brand, k3.brand_basis, k3.sb_relevant) == (
        "unresolved",
        None,
        "none",
        False,
    )
    assert k3.brief_month_basis == "unresolved_span"
    assert ("k16", "TV") in got  # TV 窗口比 MNT 早開


def test_brand_rules(mod, labeled):
    _, got = labeled
    assert (
        got[("k1", "MNT")].brand,
        got[("k1", "MNT")].brand_basis,
        got[("k1", "MNT")].brand_in_sb,
    ) == ("Acer", "sb_brand", False)
    assert (
        got[("k1", "NB")].brand_in_sb is True if ("k1", "NB") in got else True
    )  # k1 app 固定 MNT，不展開
    assert (got[("k2", "MNT")].brand, got[("k2", "MNT")].brand_in_sb) == ("Dell", True)
    assert (
        got[("k4", "TV")].brand,
        got[("k4", "TV")].brand_basis,
        got[("k4", "TV")].brand_in_sb,
    ) == ("Samsung", "samsung_vd_rule", True)
    assert (
        got[("k5", "TV")].brand,
        got[("k5", "TV")].brand_basis,
        got[("k5", "TV")].brand_in_sb,
    ) == ("sony", "customer_fallback", False)
    assert (got[("k16", "TV")].brand, got[("k16", "TV")].brand_in_sb) == ("TCL", True)


def test_facet_rules(mod, labeled):
    _, got = labeled
    assert (got[("k1", "MNT")].facet, got[("k1", "MNT")].facet_basis) == (
        "market_outlook",
        "rule_primary",
    )
    assert (got[("k6", "NB")].facet, got[("k6", "NB")].facet_basis) == (
        "product_tech",
        "rule_secondary",
    )  # follow_tag
    assert (got[("k7", "MNT")].facet, got[("k7", "MNT")].facet_basis) == (
        "price",
        "rule_secondary",
    )  # 其餘 tag
    assert (got[("k8", "MNT")].facet, got[("k8", "MNT")].facet_basis) == (None, "unresolved")
    assert got[("k4", "TV")].facet == "price"


def test_relevance_rules(mod, labeled):
    _, got = labeled
    r = {k: got[(k, "MNT")] for k in ("k1", "k7", "k8", "k9", "k10", "k11", "k12", "k13", "k14")}
    assert (r["k1"].sb_relevant, r["k1"].relevance_basis) == (True, "always:demand")
    assert (r["k7"].sb_relevant, r["k7"].relevance_basis) == (
        True,
        "always:cost",
    )  # engineering 不算，cost 算
    assert (r["k8"].sb_relevant, r["k8"].relevance_basis) == (False, "never")
    assert (r["k9"].sb_relevant, r["k9"].relevance_basis) == (False, "no_rule")  # spec + fact
    assert (r["k10"].sb_relevant, r["k10"].relevance_basis) == (True, "spec_statement:spec")
    assert (r["k11"].sb_relevant, r["k11"].relevance_basis) == (
        False,
        "no_rule",
    )  # capacity 無 time_refs
    assert (r["k12"].sb_relevant, r["k12"].relevance_basis) == (True, "capacity_timeref:capacity")
    assert (r["k13"].sb_relevant, r["k13"].relevance_basis) == (
        False,
        "no_rule",
    )  # quality + auo + fact
    assert (r["k14"].sb_relevant, r["k14"].relevance_basis) == (
        True,
        "quality_request_or_customer:quality",
    )
    assert (
        got[("k6", "NB")].relevance_basis == "always:product_plan"
    )  # schedule 本身 never，product_plan 命中
    assert (
        got[("k3", mod.APP_UNRESOLVED)].relevance_basis == "always:demand"
    )  # 規則有命中，但 app 未解 → 不相關
