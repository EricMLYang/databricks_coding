"""meeting_extracted_w2_t4_reconcile 的測試（[c02]～[c06]）。

[c03] 條目挑選（每格上限 / other 格每標籤上限）、shareable 驗證、numbers 解析；
[c04] 三種模式的 prompt 組裝；
[c05] LLM 回覆後處理（格子 / 摘要 / app 層，含不合法 relation、evidence 過濾、
signals 只留 ≥ 2 品牌）；
[c06] 會議格 / 填報格 / grid 在本機 Spark 以假表實跑。不打 LLM（[c07] 不載入），
回覆用手寫 dict 模擬。假資料無人名。
"""

from datetime import date

import pytest
from nbload import load_cells

NB = "jobs/meeting_record/meeting_extracted_w2_t4_reconcile/notebook.ipynb"
NB_004 = "jobs/meeting_record/meeting_extracted_migration/004_meeting_sb_lens.ipynb"


@pytest.fixture(scope="module")
def mod():
    return load_cells(NB, ["c02", "c03", "c04", "c05", "c06"], name="w2_t4")


@pytest.fixture(scope="module")
def mod004():
    return load_cells(NB_004, ["c02", "c03", "c04", "c05", "c06"], name="mig004_for_t4")


def _item(item_id, **kw):
    base = {
        "item_id": item_id,
        "item_key": f"k-{item_id}",
        "topic_tag_primary": "supply_chain",
        "summary": f"摘要 {item_id}",
        "quote": f"原文 {item_id}",
        "event_date": date(2026, 9, 10),
        "speaker_side": "customer",
        "numbers": "[]",
        "model_nos": ["T850QVN08.LT0"],
        "sensitivity": "S1",
        "confidence": 0.8,
        "statement_type": "fact",
    }
    return {**base, **kw}


def _cell(**kw):
    base = {
        "app_name": "TV",
        "brand": "TCL",
        "facet": "other",
        "brief_month": "2026-09",
        "window_start": date(2026, 8, 26),
        "window_end": date(2026, 9, 22),
        "sb_text": "存儲缺料導致中小尺寸成本增加",
        "sb_source": "g_sales_brief_brand_summary",
        "items": [],
        "n_items": 0,
        "topic_tags_agg": ["supply_chain"],
        "sensitivity_max": "S1",
        "relation_rule": None,
    }
    return {**base, **kw}


# ---------- 常數對齊 ----------
def test_constants_align(mod, mod004):
    assert mod.FACETS == mod004.FACETS and set(mod.RELATIONS) == set(mod004.RELATIONS)
    assert mod.BRAND_ALL == mod004.BRAND_ALL
    table_cols = [c[0] for c in mod004.TABLES["g_meeting_sb_reconcile_bu"]["columns"]]
    assert mod.RECONCILE_COLS == table_cols
    assert set(mod.PROTECTED_COLS) <= set(table_cols)
    assert mod.ROW_SCHEMA.fieldNames() == [
        c for c in mod.WRITE_COLS if c not in ("created_at", "updated_at")
    ]
    view_cols = {a for _, a, _ in mod004.VIEWS["v_meeting_items_sb_q"]["select"]} | {"brand"}
    assert set(mod.ITEM_COLS) <= view_cols
    assert isinstance(mod.PROMPT_VERSION_IN_CELL, str) and mod.PROMPT_VERSION_IN_CELL


# ---------- [c03] ----------
def test_pick_items_cell_and_other(mod):
    items = [
        _item(f"i{n}", confidence=1 - n / 100, topic_tag_primary=t)
        for n, t in enumerate(["quality"] * 10 + ["supply_chain"] * 10 + ["capacity"] * 2)
    ]
    top = mod.pick_items(items, "price", 8, 3)
    assert [x["item_id"] for x in top] == [f"i{n}" for n in range(8)]
    other = mod.pick_items(items, "other", 8, 3)
    tags = [x["topic_tag_primary"] for x in other]
    assert (
        tags.count("quality") == 3
        and tags.count("supply_chain") == 3
        and tags.count("capacity") == 2
    )
    assert [x["confidence"] for x in other] == sorted(
        (x["confidence"] for x in other), reverse=True
    )


def test_number_values_and_shareable(mod):
    assert mod.number_values(
        '[{"value": "400", "unit": "dppm"}, {"value": 7, "unit": "US$"}, {"value": "1,000"}]'
    ) == ["400", "1000"]
    assert mod.number_values("bad json") == [] and mod.number_values(None) == []
    items = [
        _item("a", sensitivity="S2", numbers='[{"value": "400", "unit": "dppm"}]'),
        _item("b", sensitivity="S1", numbers='[{"value": "10K"}]'),
    ]
    assert mod.validate_shareable("TCL 要求 VLRR 降到 400 dppm", items) == (None, True)
    ok, failed = mod.validate_shareable("TCL 對 VLRR 提出更嚴的要求；備料 10K", items)
    assert failed is False and ok.startswith("TCL")  # S1 的數字可以出現
    assert mod.validate_shareable("", items) == (None, False)
    assert mod.sens_max(["S1", None, "S2", "S0"]) == "S2" and mod.sens_max([None]) is None


def test_parse_llm_json(mod):
    assert mod.parse_llm_json('```json\n{"relation": "conflict"}\n```')[0] == {
        "relation": "conflict"
    }
    assert mod.parse_llm_json("沒有 json")[0] is None and mod.parse_llm_json("[1]")[0] is None


# ---------- [c04] ----------
def test_prompts(mod):
    cell = _cell(items=[_item("a", sensitivity="S2", numbers='[{"value": "400"}]'), _item("b")])
    p = mod.build_cell_prompt(cell, cell["items"])
    assert p.startswith("mode=cell") and "TV × 品牌 TCL × 面向 other" in p and "存儲缺料" in p
    assert "[a]〔S2〕" in p and "[b] 2026-09-10" in p and "numbers: [" in p and "T850QVN08.LT0" in p
    s = mod.build_summary_prompt(
        [(cell, cell["items"]), (_cell(brand="UNKNOWN", facet="price"), [_item("c")])]
    )
    assert s.startswith("mode=summary") and "key=TV|TCL|other" in s and "key=TV|UNKNOWN|price" in s
    a = mod.build_app_prompt(
        "MNT",
        "product_tech",
        "2026-09",
        [{"brand": "Acer", "meeting_summary": "x", "item_ids": ["i1"]}],
        None,
    )
    assert a.startswith("mode=app") and "（空白）" in a and "品牌 Acer：x（item_ids: i1）" in a
    assert (
        "mode=cell" in mod.SYSTEM_PROMPT_T4
        and "mode=app" in mod.SYSTEM_PROMPT_T4
        and "〔S2〕" in mod.SYSTEM_PROMPT_T4
    )
    assert "<email>" not in mod.SYSTEM_PROMPT_T4 and "@" not in mod.SYSTEM_PROMPT_T4


# ---------- [c05] ----------
def test_postprocess_cell(mod):
    items = [_item("a", sensitivity="S2", numbers='[{"value": "400"}]'), _item("b"), _item("c")]
    cell = _cell(items=items, n_items=3)
    sent = items[:2]
    obj = {
        "relation": "Supplement",
        "meeting_summary": "要求 400 dppm",
        "meeting_summary_shareable": "提出更嚴要求",
        "rationale": "r",
        "evidence_item_ids": ["b", "zzz"],
        "number_caveat": None,
    }
    row, st = mod.postprocess_cell(obj, None, cell, sent, "0.1", "m")
    assert (row["relation"], row["relation_basis"], row["model"]) == ("supplement", "llm", "m")
    assert (
        row["meeting_item_ids"] == ["b", "a", "c"]
        and row["n_items"] == 3
        and row["n_items_sent"] == 2
    )
    assert row["meeting_summary_shareable"] == "提出更嚴要求" and row["shareable_failed"] is False
    assert st["supplement"] == 1 and "rationale" in row
    bad = {"relation": "maybe", "meeting_summary": "x"}
    row2, st2 = mod.postprocess_cell(bad, None, cell, sent, "0.1", "m")
    assert row2 is None and st2["bad_relation"] == 1 and st2["cell_failed"] == 1
    row3, st3 = mod.postprocess_cell(None, "HTTP 500", cell, sent, "0.1", "m")
    assert row3 is None and st3["errors"][0].startswith("TV|TCL|other")
    leak = {
        "relation": "conflict",
        "meeting_summary": "x",
        "meeting_summary_shareable": "降到 400 dppm",
        "rationale": "r",
    }
    row4, st4 = mod.postprocess_cell(leak, None, cell, sent, "0.1", "m")
    assert (
        row4["meeting_summary_shareable"] is None
        and row4["shareable_failed"] is True
        and st4["shareable_failed"] == 1
    )


def test_postprocess_summary_and_rule_row(mod):
    c1, c2 = (
        _cell(items=[_item("a")], n_items=1, sb_text=None, relation_rule="meeting_only"),
        _cell(brand="UNKNOWN", items=[_item("b")], n_items=1),
    )
    obj = {
        "cells": [
            {"key": "TV|TCL|other", "meeting_summary": "s1", "meeting_summary_shareable": "p1"}
        ]
    }
    out, st = mod.postprocess_summary(obj, None, [(c1, c1["items"]), (c2, c2["items"])])
    assert (
        out == {"TV|TCL|other": ("s1", "p1", False)}
        and st["summary_missing"] == 1
        and st["summary_filled"] == 1
    )
    row = mod.rule_row(c1, "meeting_only", "0.1")
    assert (row["relation"], row["relation_basis"], row["model"], row["sb_source"]) == (
        "meeting_only",
        "rule",
        "rule",
        "g_sales_brief_brand_summary",
    )
    assert row["meeting_item_ids"] == ["a"] and row["n_items"] == 1 and row["n_items_sent"] == 0
    row_sb = mod.rule_row(_cell(items=None, n_items=0), "sb_only", "0.1")
    assert row_sb["meeting_item_ids"] is None and row_sb["relation"] == "sb_only"


def test_postprocess_app(mod):
    bcs = [
        {
            "brand": "Acer",
            "meeting_summary": "a",
            "item_ids": ["i1"],
            "item_keys": ["k1"],
            "topic_tags_agg": ["product_plan"],
            "sensitivity_max": "S1",
            "items": [_item("i1")],
        },
        {
            "brand": "Dell",
            "meeting_summary": "d",
            "item_ids": ["i2"],
            "item_keys": ["k2"],
            "topic_tags_agg": ["spec"],
            "sensitivity_max": "S2",
            "items": [_item("i2", sensitivity="S2", numbers='[{"value": "299"}]')],
        },
    ]
    all_cell = _cell(
        app_name="MNT",
        brand="ALL",
        facet="product_tech",
        sb_text="整體摘要",
        sb_source="g_sales_brief_app_summary",
        items=None,
    )
    obj = {
        "relation": "supplement",
        "meeting_summary": "m",
        "meeting_summary_shareable": "p",
        "signals": [
            {"note": "同關注 4ch LVDS", "brands": ["Acer", "Dell"], "item_ids": []},
            {"note": "只有一家", "brands": ["Acer"]},
            {"note": "不認識的", "brands": ["HP", "Asus"]},
        ],
        "rationale": "r",
    }
    row, flagged, st = mod.postprocess_app(obj, None, all_cell, bcs, "0.1", "m")
    assert (row["relation"], row["relation_basis"], row["brand"]) == ("supplement", "llm", "ALL")
    assert (
        flagged == {"Acer", "Dell"}
        and row["cross_customer_flag"] is True
        and "4ch LVDS（Acer / Dell）" in row["cross_customer_note"]
    )
    assert (
        row["meeting_item_ids"] == ["i1", "i2"]
        and row["sensitivity_max"] == "S2"
        and row["topic_tags_agg"] == ["product_plan", "spec"]
    )
    assert st["signals"] == 1
    # 填報空 → meeting_only / rule，不管 LLM 給什麼
    row2, _, _ = mod.postprocess_app(
        {**obj, "relation": "conflict"}, None, {**all_cell, "sb_text": None}, bcs, "0.1", "m"
    )
    assert (row2["relation"], row2["relation_basis"]) == ("meeting_only", "rule")
    # 填報有但 relation 不合法 → 作廢
    row3, flagged3, st3 = mod.postprocess_app(
        {**obj, "relation": "meeting_only"}, None, all_cell, bcs, "0.1", "m"
    )
    assert row3 is None and flagged3 == set() and st3["app_failed"] == 1


# ---------- [c06] Spark ----------
_Q_SCHEMA = (
    "item_id string, item_key string, app_name string, brand string, facet string, "
    "brief_month string, window_start date, window_end date, topic_tag_primary string, "
    "summary string, quote string, event_date date, "
    "speaker_side string, customer string, numbers string, model_nos array<string>, "
    "sensitivity string, confidence double, statement_type string, sb_relevant boolean"
)
_Q_COLS = [c.split()[0] for c in _Q_SCHEMA.split(", ")]


def _q(item_id, **kw):
    base = {
        "item_id": item_id,
        "item_key": f"k-{item_id}",
        "app_name": "TV",
        "brand": "TCL",
        "facet": "other",
        "brief_month": "2026-09",
        "window_start": date(2026, 8, 26),
        "window_end": date(2026, 9, 22),
        "topic_tag_primary": "supply_chain",
        "summary": "s",
        "quote": "q",
        "event_date": date(2026, 9, 10),
        "speaker_side": "customer",
        "customer": "tcl",
        "numbers": "[]",
        "model_nos": [],
        "sensitivity": "S1",
        "confidence": 0.8,
        "statement_type": "fact",
        "sb_relevant": True,
    }
    return {**base, **kw}


@pytest.fixture(scope="module")
def grid(mod, spark):
    q = [
        _q("a"),
        _q("b", topic_tag_primary="quality", sensitivity="S2", confidence=0.9),
        _q("c", facet="price"),
        _q("d", brand=None, customer=None, app_name="MNT", facet="other"),  # UNKNOWN
        _q("e", sb_relevant=False),
        _q("f", brief_month="2026-08"),
        _q(
            "g",
            app_name="MNT",
            brand="Acer",
            facet="market_outlook",
            window_start=date(2026, 8, 25),
            window_end=date(2026, 9, 21),
        ),
    ]
    brief = [
        ("TV", "TCL", "other", "2026-09", "存儲缺料", "g_sales_brief_brand_summary"),
        ("TV", "TCL", "product_tech", "2026-09", "轉向 AG25", "g_sales_brief_brand_summary"),
        ("TV", "TCL", "price", "2026-09", None, "none"),
        ("TV", "ALL", "other", "2026-09", "整體", "g_sales_brief_app_summary"),
        ("MNT", "Asus", "other", "2026-09", "x", "g_sales_brief_brand_summary"),
        ("TV", "TCL", "other", "2026-08", "舊", "g_sales_brief_brand_summary"),
    ]
    df_q = spark.createDataFrame([tuple(r[c] for c in _Q_COLS) for r in q], _Q_SCHEMA)
    df_brief = spark.createDataFrame(
        brief,
        "app_name string, brand string, facet string, brief_month string, "
        "sb_text string, sb_source string",
    )
    df_items = mod.select_relevant(df_q, "2026-09")
    df_grid = mod.build_grid(mod.meeting_cells(df_items), mod.sb_cells(df_brief, "2026-09"))
    return mod.grid_to_dicts(df_grid.collect())


def test_select_and_meeting_cells(mod, grid):
    g = {(x["app_name"], x["brand"], x["facet"]): x for x in grid}
    tcl = g[("TV", "TCL", "other")]
    assert tcl["n_items"] == 2 and {it["item_id"] for it in tcl["items"]} == {"a", "b"}
    assert tcl["topic_tags_agg"] == ["quality", "supply_chain"] and tcl["sensitivity_max"] == "S2"
    assert (
        tcl["relation_rule"] is None
        and tcl["has_meeting"]
        and tcl["has_sb"]
        and tcl["sb_text"] == "存儲缺料"
    )
    assert set(tcl["items"][0]) == set(mod.CELL_ITEM_FIELDS)
    assert ("TV", "UNKNOWN", "other") not in g and g[("MNT", "UNKNOWN", "other")][
        "relation_rule"
    ] == "meeting_only"
    assert all(x["brief_month"] == "2026-09" for x in grid)
    assert not any(it["item_id"] in ("e", "f") for x in grid for it in (x["items"] or []))


def test_grid_sides(mod, grid):
    g = {(x["app_name"], x["brand"], x["facet"]): x for x in grid}
    assert (
        g[("TV", "TCL", "price")]["relation_rule"] == "meeting_only"
    )  # 填報格存在但空白 → 不算填報端
    assert (
        g[("TV", "TCL", "product_tech")]["relation_rule"] == "sb_only"
        and g[("TV", "TCL", "product_tech")]["n_items"] == 0
    )
    assert g[("TV", "TCL", "product_tech")]["window_start"] == date(2026, 8, 26)  # 補同 app 窗口
    assert (
        g[("TV", "ALL", "other")]["relation_rule"] == "sb_only"
        and g[("TV", "ALL", "other")]["sb_source"] == "g_sales_brief_app_summary"
    )
    assert g[("MNT", "Asus", "other")]["relation_rule"] == "sb_only" and g[
        ("MNT", "Asus", "other")
    ]["window_start"] == date(2026, 8, 25)
    assert (
        g[("MNT", "Acer", "market_outlook")]["relation_rule"] == "meeting_only"
        and g[("MNT", "Acer", "market_outlook")]["sb_source"] == "none"
    )
    assert len(grid) == 7
