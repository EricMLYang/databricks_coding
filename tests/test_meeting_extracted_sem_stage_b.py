"""meeting_extracted_sem_stage_b 的測試。

[c02]～[c05] 純 Python（id、as_of、投影代號、semantic / intel 併入計畫、md 與 diff），
[c07] 用本機 Spark 跑待併列與未審清單。假資料虛構、已 token 化，無 LLM。
"""

from datetime import date, datetime

import pytest
from nbload import load_cells

NB = "jobs/meeting_record/meeting_extracted_sem_stage_b/notebook.ipynb"
NB_003 = "jobs/meeting_record/meeting_extracted_migration/003_meeting_semantic_lens.ipynb"
NB_005 = "jobs/meeting_record/meeting_extracted_migration/005_semantic_ledgers.ipynb"
NOW = datetime(2026, 10, 20, 9, 0)
TODAY = date(2026, 10, 20)


@pytest.fixture(scope="module")
def mod():
    return load_cells(NB, ["c02", "c03", "c04", "c05", "c07"], name="sem_stage_b")


@pytest.fixture(scope="module")
def mod005():
    return load_cells(NB_005, ["c02", "c03", "c04", "c05"], name="mig005_for_sb")


def _item(key, category="semantic", **kw):
    base = {
        "item_key": key,
        "item_id": f"id-{key}",
        "week": "2026-W42",
        "category": category,
        "app": "MNT",
        "customer": "acer",
        "term": f"主題 {key}",
        "summary": f"內容 {key}",
        "quote": f"原文 {key}",
        "date": date(2026, 9, 3),
        "source": "acer MNT Monthly 2026-09-03 — customer",
        "as_of": None,
        "dup_of": None,
        "dup_key": None,
        "route_hint": "pa:semantics",
        "review_note": None,
        "verified": "y",
        "sem_id": None,
    }
    return {**base, **kw}


# ---------- 常數對齊 ----------
def test_columns_align(mod, mod005):
    t3 = load_cells(NB_003, ["c02", "c03", "c04"], name="mig003_for_sb")
    assert set(mod.LENS_COLS) <= {c[0] for c in t3.TABLES["g_meeting_items_sem_bu"]["columns"]}
    rec = {c[0] for c in mod005.TABLES["g_semantic_record"]["columns"]}
    intel = {c[0] for c in mod005.TABLES["g_background_intel"]["columns"]}
    assert set(mod.RECORD_UPDATE_COLS) <= rec and set(mod.INTEL_UPDATE_COLS) <= intel
    assert mod.RETIRE_QUARTERS == mod005.RETIRE_QUARTERS
    assert isinstance(mod.STAGE_B_VERSION_IN_CELL, str)


# ---------- 小函式 ----------
def test_ids_and_as_of(mod):
    assert mod.parse_id("SEM-012", "SEM-") == 12 and mod.parse_id("INT-1", "SEM-") is None
    assert mod.fmt_id("SEM-", 7) == "SEM-007" and mod.fmt_id("INT-", 1234) == "INT-1234"
    assert mod.next_n([], "SEM-") == 1 and mod.next_n(["SEM-003", "SEM-010", "bad"], "SEM-") == 11
    assert mod.as_of_key("2026-Q3") == mod.as_of_key("2026-08") == 2026 * 4 + 2
    assert mod.as_of_key("bad") is None
    assert mod.newer_as_of("2026-Q2", "2026-09") == "2026-09"
    assert mod.newer_as_of("2026-Q4", "2026-09") == "2026-Q4"
    assert (
        mod.newer_as_of(None, "2026-09") == "2026-09"
        and mod.newer_as_of("2026-09", "x") == "2026-09"
    )
    assert mod.as_of_of({"as_of": "2026-Q3"}) == "2026-Q3"
    assert mod.as_of_of({"as_of": "bad", "date": date(2026, 9, 3)}) == "2026-09"
    assert mod.as_of_of({"as_of": None, "date": None}) is None
    assert mod.route_from_note("改投影到 skill:multi_genie，口徑紅旗") == "skill:multi_genie"
    assert mod.route_from_note("de:主控 比較適合") == "de:主控"
    assert mod.route_from_note("措辭改一下") is None
    assert mod.quarters_old("2026-Q1", TODAY) == 3 and mod.quarters_old("2025-12", TODAY) == 4
    assert mod.quarters_old(None, TODAY) is None and mod.quarters_old("2026-Q2", TODAY) == 2


# ---------- semantic 計畫 ----------
def test_plan_semantic(mod):
    records = {
        "SEM-001": {
            "sem_id": "SEM-001",
            "term": "既有",
            "n_evidence": 1,
            "last_evidence_date": date(2026, 8, 1),
        },
        "SEM-003": {
            "sem_id": "SEM-003",
            "term": "跳號",
            "n_evidence": 2,
            "last_evidence_date": None,
        },
    }
    evidence_keys = {("SEM-001", "old")}
    items = [
        _item("n1", review_note="投影改 skill:multi_genie"),  # 新 SEM-004，投影以 review_note 為準
        _item(
            "n2", route_hint=None, date=date(2026, 9, 1)
        ),  # 新 SEM（較早日期 → 先編號）、預設投影
        _item("e1", dup_of="SEM-001", date=date(2026, 9, 10)),  # 補證據
        _item("e2", dup_of="SEM-001", date=date(2026, 9, 12)),  # 同 SEM 再補
        _item("old", dup_of="SEM-001"),  # 證據已存在 → 只回填
        _item("m1", dup_of="SEM-999"),  # dup_of 不存在 → 新 SEM
        _item(
            "d1", dup_key="n2", date=date(2026, 8, 1)
        ),  # 同文重複、正本 n2 本次新發 → 跟著（雖然日期更早）
        _item("d2", dup_key="zz", primary_sem_id="SEM-003"),  # 正本已併 SEM-003 → 補證據
    ]
    p = mod.plan_semantic(items, records, evidence_keys, "0.1", NOW)
    new = {r["sem_id"]: r for r in p["new_records"]}
    assert list(new) == [
        "SEM-004",
        "SEM-005",
        "SEM-006",
    ]  # 接最大號；依 (date, item_key)：n2, m1, n1
    assert (
        new["SEM-004"]["first_item_key"] == "n2" and new["SEM-004"]["route_hint"] == "pa:semantics"
    )
    assert (
        new["SEM-006"]["first_item_key"] == "n1"
        and new["SEM-006"]["route_hint"] == "skill:multi_genie"
    )
    assert (
        new["SEM-006"]["pm_note"] == "投影改 skill:multi_genie"
        and new["SEM-006"]["status"] == "confirmed"
    )
    assert new["SEM-005"]["first_item_key"] == "m1" and new["SEM-005"]["n_evidence"] == 1
    assert p["updates"] == [
        {
            "sem_id": "SEM-001",
            "n_evidence": 3,
            "last_evidence_date": date(2026, 9, 12),
            "updated_at": NOW,
        },
        {
            "sem_id": "SEM-003",
            "n_evidence": 3,
            "last_evidence_date": date(2026, 9, 3),
            "updated_at": NOW,
        },
    ]
    assert new["SEM-004"]["n_evidence"] == 2  # d1 跟著 n2
    assert [(e["sem_id"], e["item_key"]) for e in p["evidence"]] == [
        ("SEM-004", "n2"),
        ("SEM-005", "m1"),
        ("SEM-006", "n1"),
        ("SEM-001", "e1"),
        ("SEM-001", "e2"),
        ("SEM-004", "d1"),
        ("SEM-003", "d2"),
    ]
    assert dict(p["lens"]) == {
        "n1": "SEM-006",
        "n2": "SEM-004",
        "e1": "SEM-001",
        "e2": "SEM-001",
        "old": "SEM-001",
        "m1": "SEM-005",
        "d1": "SEM-004",
        "d2": "SEM-003",
    }
    acts = {(a["item_key"], a["action"]) for a in p["actions"]}
    assert (
        ("old", "evidence_exists") in acts
        and ("m1", "dup_of_missing") in acts
        and ("m1", "new_sem") in acts
    )


# ---------- intel 計畫 ----------
def test_plan_intel(mod):
    existing = [
        {
            "intel_id": "INT-002",
            "app": "MNT",
            "term": "INX 產能",
            "term_norm": mod.normalize_text("INX 產能"),
            "summary": "舊",
            "as_of": "2026-Q2",
            "date": date(2026, 6, 1),
            "n_updates": 1,
            "status": "active",
            "pm_note": "PM 寫的",
        }
    ]
    items = [
        _item(
            "i1", "intel", term="inx產能", summary="新", as_of="2026-09", date=date(2026, 9, 3)
        ),  # 同主題 → 更新
        _item(
            "i2", "intel", term="VD 第二來源", app=None, as_of="bad", date=date(2026, 6, 22)
        ),  # 新；as_of 由 date 推
        _item(
            "i3", "intel", term="VD 第二來源", app="TV", as_of="2026-Q3", date=date(2026, 9, 9)
        ),  # 不同 app → 另一列
        _item(
            "i4", "intel", term="VD 第二來源", app="TV", as_of="2026-Q1", date=date(2026, 9, 30)
        ),  # 同主題，as_of 較舊不倒退
        _item(
            "u1", "intel", term="未審主題", verified=None, date=date(2026, 9, 1)
        ),  # intel_auto → unreviewed
        _item(
            "u2", "intel", term="未審主題", verified=None, eff_verified="y", date=date(2026, 9, 2)
        ),  # 正本 y → active
    ]
    p = mod.plan_intel(items, existing, "0.1", NOW)
    upd = {u["intel_id"]: u for u in p["updates"]}
    assert set(upd) == {"INT-002"}
    assert (upd["INT-002"]["summary"], upd["INT-002"]["as_of"], upd["INT-002"]["n_updates"]) == (
        "新",
        "2026-09",
        2,
    )
    assert upd["INT-002"]["pm_note"] == "PM 寫的"  # 更新不動 PM 欄
    new = {r["intel_id"]: r for r in p["new"]}
    assert list(new) == ["INT-003", "INT-004", "INT-005"]
    assert (new["INT-004"]["status"], new["INT-004"]["n_updates"]) == (
        "active",
        2,
    )  # u1 unreviewed → u2 轉 active
    assert upd["INT-002"]["status"] == "active"  # 本來 active 不動
    assert (new["INT-003"]["app"], new["INT-003"]["as_of"], new["INT-003"]["first_item_key"]) == (
        "ALL",
        "2026-06",
        "i2",
    )
    assert (new["INT-005"]["as_of"], new["INT-005"]["n_updates"], new["INT-005"]["item_key"]) == (
        "2026-Q3",
        2,
        "i4",
    )
    assert dict(p["lens"]) == {
        "i1": "INT-002",
        "i2": "INT-003",
        "i3": "INT-005",
        "i4": "INT-005",
        "u1": "INT-004",
        "u2": "INT-004",
    }
    assert [a["action"] for a in p["actions"]] == [
        "new_intel",
        "new_intel",
        "update_intel",
        "update_intel",
        "new_intel",
        "update_intel",
    ]


# ---------- md 與 diff ----------
def test_render_and_diff(mod):
    records = [
        {
            "sem_id": "SEM-002",
            "app": "MNT",
            "term": "b|b",
            "summary": "d",
            "route_hint": "pa:semantics",
            "n_evidence": 1,
            "last_evidence_date": date(2026, 9, 1),
            "status": "confirmed",
            "synced_to": None,
        },
        {
            "sem_id": "SEM-001",
            "app": "ALL",
            "term": "a",
            "summary": "d",
            "route_hint": "de:主控",
            "n_evidence": 2,
            "last_evidence_date": date(2026, 9, 3),
            "status": "retired",
            "pm_note": "併入 SEM-002",
        },
    ]
    evi = {"SEM-002": [{"date": date(2026, 9, 1), "source": "s", "quote": "q", "item_key": "k"}]}
    md = mod.render_semantic_md(records, evi)
    assert "| SEM-002 | MNT | b\\|b | d | pa:semantics | 1 | 2026-09-01 | 未投影 |" in md
    assert "- **SEM-002** b\\|b\n  - 2026-09-01｜s｜「q」" in md
    assert "## 退場區\n\n- SEM-001 a（併入 SEM-002）" in md and "| SEM-001 |" not in md
    intel = [
        {
            "intel_id": "INT-001",
            "app": "TV",
            "term": "t1",
            "summary": "s1",
            "as_of": "2026-Q2",
            "source": "src",
            "status": "active",
        },
        {
            "intel_id": "INT-002",
            "app": "TV",
            "term": "t2",
            "summary": "s2",
            "as_of": "2026-09",
            "source": "src",
            "status": "active",
        },
        {
            "intel_id": "INT-003",
            "app": "MNT",
            "term": "t3",
            "summary": "s3",
            "as_of": "2025-12",
            "source": "src",
            "status": "retired",
        },
    ]
    md2 = mod.render_intel_md(intel, TODAY)
    assert (
        md2.index("## TV") < md2.index("| 2026-09 | t2 |") < md2.index("| 2026-Q2 | t1 |")
    )  # 新的在前
    assert "⚠" not in md2 and "## MNT" not in md2  # 剛好兩季不標；retired 不列
    md3 = mod.render_intel_md([{**intel[0], "as_of": "2026-Q1"}], TODAY)
    assert "| ⚠ 2026-Q1 | t1 |" in md3
    md4 = mod.render_intel_md([{**intel[1], "status": "unreviewed"}], TODAY)
    assert "| 2026-09 | 〔未審〕t2 |" in md4
    assert mod.md_diff(md, md, "x") == ""
    d = mod.md_diff(md2, md3, "background_intel.md")
    assert d.startswith("--- background_intel.md（現況）") and "+| ⚠ 2026-Q1 | t1 |" in d
    assert mod.render_intel_md([], TODAY).endswith("（無）\n")


# ---------- [c07] Spark ----------
def test_select_pending_and_unreviewed(mod, spark):
    load_cells(NB_003, ["c02", "c03", "c04"], name="mig003_for_sb_spark")
    t3 = load_cells(NB_003, ["c02", "c03", "c04"], name="mig003_for_sb_spark2")
    spec = t3.TABLES["g_meeting_items_sem_bu"]
    names = [c[0] for c in spec["columns"]]
    rows = [
        {"item_key": "a", "category": "semantic", "verified": "y", "active": True},
        {
            "item_key": "b",
            "category": "intel",
            "verified": "y",
            "active": True,
            "sem_id": "INT-001",
        },  # 已併
        {"item_key": "c", "category": "event", "verified": "y", "active": True},  # event 不併
        {
            "item_key": "d",
            "category": "intel",
            "verified": None,
            "active": True,
            "date": date(2026, 9, 1),
        },  # 未審
        {"item_key": "e", "category": "semantic", "verified": "n", "active": True},  # n 不算未審
        {"item_key": "f", "category": "intel", "verified": "y", "active": False},  # 停用
        {
            "item_key": "g",
            "category": "semantic",
            "verified": None,
            "active": True,
            "dup_key": "a",
        },  # 正本 a 是 y → 跟著
        {
            "item_key": "h",
            "category": "intel",
            "verified": None,
            "active": True,
            "dup_key": "b",
        },  # 正本 b 已併 → 跟著
        {
            "item_key": "i",
            "category": "semantic",
            "verified": None,
            "active": True,
            "dup_key": "e",
        },  # 正本 e 是 n → 不併
    ]
    df = spark.createDataFrame([tuple(r.get(n) for n in names) for r in rows], t3.schema_ddl(spec))
    got = {r.item_key: r for r in mod.select_pending(df, False).collect()}
    assert set(got) == {"a", "g", "h"}
    assert (got["g"].pending_reason, got["g"].eff_verified, got["g"].primary_sem_id) == (
        "dup_of_primary",
        "y",
        None,
    )
    assert (got["h"].pending_reason, got["h"].eff_verified, got["h"].primary_sem_id) == (
        "dup_of_primary",
        "y",
        "INT-001",
    )
    assert mod.select_pending(df, False).columns == mod.LENS_COLS + [
        "pending_reason",
        "eff_verified",
        "primary_sem_id",
    ]
    auto = {r.item_key: r for r in mod.select_pending(df, True).collect()}
    assert set(auto) == {"a", "g", "h", "d"} and auto["d"].pending_reason == "intel_auto"
    assert (
        auto["d"].eff_verified is None and auto["h"].pending_reason == "dup_of_primary"
    )  # dup 優先於 intel_auto
    assert sorted(r.item_key for r in mod.unreviewed(df).collect()) == ["d", "g", "h", "i"]
