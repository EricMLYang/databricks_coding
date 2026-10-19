"""meeting_extracted_sem_stage_a 的測試。

[c02]～[c05] 純 Python（常數與 003 對齊、prompt 組裝、LLM 回覆解析 / 驗證），
[c07] 用本機 Spark 跑待判選取、三路拆分、規則列、同文複製、組鏡頭表列。
測試資料全是虛構（假 item_key、假 token）；不打 LLM（[c06] 不載入），LLM 回覆用手寫 dict 模擬。
"""

from datetime import date

import pytest
from nbload import load_cells

NB = "jobs/meeting_record/meeting_extracted_sem_stage_a/notebook.ipynb"
NB_003 = "jobs/meeting_record/meeting_extracted_migration/003_meeting_semantic_lens.ipynb"


@pytest.fixture(scope="module")
def mod():
    return load_cells(NB, ["c02", "c03", "c04", "c05", "c07"], name="sem_stage_a")


@pytest.fixture(scope="module")
def mod003():
    return load_cells(NB_003, ["c02", "c03", "c04", "c05"], name="mig003_for_sa")


# ---------- 常數與 003 對齊 ----------
def test_constants_align_with_003(mod, mod003):
    assert mod.CATEGORIES == mod003.CATEGORIES
    # 先驗值全覆蓋：交 LLM 的 ＋ 直接寫的 = 003 view 會產生的四種 rule_basis
    assert set(mod.LLM_RULE_BASIS) | set(mod.RULE_CATEGORY) == {
        "definition",
        "term_hint",
        "intel_tag",
        "default",
    }
    assert set(mod.RULE_CATEGORY.values()) <= set(mod.CATEGORIES)
    view_cols = {a for _, a, _ in mod003.VIEWS["v_meeting_items_sem_cand"]["select"]}
    assert set(mod.CAND_COLS) <= view_cols, set(mod.CAND_COLS) - view_cols
    table_cols = {c[0] for c in mod003.TABLES["g_meeting_items_sem_bu"]["columns"]}
    assert set(mod.COPY_COLS) <= table_cols and set(mod.PROTECTED_COLS) <= table_cols
    assert "confidence" not in mod.COPY_COLS  # view 的 confidence 是 L1 自評，不複製
    assert isinstance(mod.STAGE_A_VERSION_IN_CELL, str) and mod.STAGE_A_VERSION_IN_CELL


# ---------- prompt ----------
def _cand(key, **kw):
    base = {
        "item_id": f"BU-MTG-1-1-0-{key}",
        "item_key": key,
        "pk_seq": 1,
        "segment_no": 1,
        "sub_no": 0,
        "unit": "bu",
        "week": "2026-W42",
        "category_rule": "event",
        "rule_basis": "default",
        "app": "MNT",
        "customer": "acer",
        "customer_raw": "acer",
        "statement_type": "fact",
        "topic_tag_primary": "schedule",
        "topic_tags_str": "schedule",
        "free_tags_str": "AG25",
        "terms_str": "",
        "summary": f"摘要 {key}",
        "quote": f"原文 {key} 逐字",
        "date": date(2026, 9, 3),
        "event_month": "2026-09",
        "source": "acer MNT Monthly 2026-09-03 — customer",
        "tags": ["schedule", "AG25", "acer"],
        "speaker_side": "customer",
        "content_type": "inline_minutes",
        "weight_hint": "low",
        "sensitivity": "S1",
        "confidence": 0.8,
        "already_classified": False,
        "sem_active": None,
        "sem_stage_a_version": None,
        "dup_key": None,
    }
    return {**base, **kw}


def test_build_user_prompt(mod):
    items = [
        _cand("k1", category_rule="semantic", rule_basis="definition", terms_str="JND"),
        _cand("k2", customer=None, customer_raw="VD"),
    ]
    p = mod.build_user_prompt(items)
    assert "本批 2 條" in p and "### n=1 | 先驗 semantic/definition" in p and "### n=2" in p
    assert "命中術語: JND" in p and "客戶 VD" in p and "quote: 原文 k1 逐字" in p
    assert "@" not in p
    assert "pa:semantics" in mod.SYSTEM_PROMPT_SA and "一年後還成立" in mod.SYSTEM_PROMPT_SA


# ---------- 解析 / 驗證 ----------
def test_parse_llm_json(mod):
    obj, err = mod.parse_llm_json('```json\n{"items": [{"n": 1, "category": "event"}]}\n```')
    assert err is None and obj["items"][0]["n"] == 1
    assert mod.parse_llm_json("")[1] == "empty response"
    assert mod.parse_llm_json("not json")[1] == "no JSON object found"
    assert "top-level" in mod.parse_llm_json('{"x": 1}')[1]


def test_build_cls_rows_rules(mod):
    items = [
        _cand("s1", category_rule="semantic", rule_basis="definition", app="MNT"),
        _cand("i1", category_rule="intel", rule_basis="intel_tag", app=None, event_month="2026-09"),
        _cand("e1", category_rule="intel", rule_basis="intel_tag"),
        _cand("m1", category_rule="intel", rule_basis="intel_tag"),
        _cand("b1", category_rule="semantic", rule_basis="definition"),
    ]
    resp = {
        "items": [
            # semantic：route 不在投影代號表 → 預設；term 含 email → 遮罩；
            # confidence 超過 1 → 夾到 1
            {
                "n": 1,
                "category": "Semantic",
                "term": "口徑 a@b.com",
                "route_hint": "somewhere",
                "as_of": "2026-09",
                "extract_note": "通用口徑",
                "confidence": 1.7,
            },
            # intel：as_of 格式錯 → event_month；route 由程式依 app 組（app NULL → ALL）
            {
                "n": 2,
                "category": "intel",
                "term": "",
                "route_hint": "pa:semantics",
                "as_of": "Q3 2026",
                "extract_note": "",
                "confidence": "0.6",
            },
            # event：route / as_of 一律 NULL；先驗 intel → disagree
            {
                "n": 3,
                "category": "event",
                "term": "料號變更",
                "route_hint": "pa:semantics",
                "as_of": "2026-09",
                "confidence": None,
            },
            # n=4 漏掉；n=5 category 不合法；n=9 多出來
            {"n": 5, "category": "other", "term": "x"},
            {"n": 9, "category": "event", "term": "x"},
        ]
    }
    rows, st = mod.build_cls_rows(resp, None, items, "claude-x")
    got = {r["item_key"]: r for r in rows}
    assert set(got) == {"s1", "i1", "e1"}
    s1, i1, e1 = got["s1"], got["i1"], got["e1"]
    assert (s1["category"], s1["route_hint"], s1["as_of"]) == ("semantic", "pa:semantics", None)
    assert s1["term"] == "口徑 <email>" and s1["sa_confidence"] == 1.0 and s1["model"] == "claude-x"
    assert (i1["category"], i1["route_hint"], i1["as_of"]) == (
        "intel",
        "background_intel:ALL",
        "2026-09",
    )
    assert i1["term"] == "摘要 i1" and i1["sa_confidence"] == 0.6
    assert (e1["route_hint"], e1["as_of"], e1["sa_confidence"]) == (None, None, None)
    assert (
        st["sent"] == 5 and st["classified"] == 3 and st["missing"] == 1 and st["bad_category"] == 1
    )
    assert (
        st["extra"] == 1
        and st["route_fixed"] == 1
        and st["as_of_fixed"] == 1
        and st["term_filled"] == 1
    )
    assert st["disagree"] == 1 and st["semantic"] == 1 and st["intel"] == 1 and st["event"] == 1


def test_build_cls_rows_batch_failed(mod):
    items = [_cand("a"), _cand("b")]
    rows, st = mod.build_cls_rows(None, "HTTP 500", items, "m")
    assert (
        rows == []
        and st["batch_failed"] == 1
        and st["failed_items"] == 2
        and st["errors"] == ["HTTP 500"]
    )
    too_many = {
        "items": [{"n": i, "category": "event"} for i in range(1, mod.MAX_ITEMS_PER_CALL + 2)]
    }
    rows, st = mod.build_cls_rows(too_many, None, items, "m")
    assert rows == [] and st["batch_failed"] == 1


def test_route_for(mod):
    assert mod.route_for("intel", "TV", None) == ("background_intel:TV", False)
    assert mod.route_for("intel", "bogus", None) == ("background_intel:ALL", False)
    assert mod.route_for("semantic", "TV", "skill:multi_genie") == ("skill:multi_genie", False)
    assert mod.route_for("semantic", "TV", None) == ("pa:semantics", True)
    assert mod.route_for("event", "TV", "pa:semantics") == (None, False)


# ---------- [c07] Spark ----------
CAND_DDL = (
    "item_id string, item_key string, pk_seq bigint, segment_no int, sub_no int, unit string, "
    "week string, "
    "category_rule string, rule_basis string, app string, customer string, customer_raw string, "
    "statement_type string, topic_tag_primary string, topic_tags_str string, free_tags_str string, "
    "terms_str string, summary string, quote string, date date, event_month string, source string, "
    "tags array<string>, speaker_side string, content_type string, weight_hint string, "
    "sensitivity string, "
    "confidence double, already_classified boolean, sem_active boolean, "
    "sem_stage_a_version string, "
    "dup_key string"
)


@pytest.fixture(scope="module")
def fake(mod, mod003, spark):
    cands = [
        _cand("a"),  # 規則列
        _cand("b", category_rule="semantic", rule_basis="definition"),  # LLM
        _cand(
            "c", rule_basis="intel_tag", category_rule="intel", dup_key="b"
        ),  # 同文，複製本次判的 b
        _cand("d", dup_key="zzz"),  # 同文，但最早那條不存在 → 等
        _cand(
            "e", already_classified=True, sem_active=True, sem_stage_a_version="0.0"
        ),  # 只在 reclassify
        _cand(
            "f",
            rule_basis="intel_tag",
            category_rule="intel",
            already_classified=True,
            sem_active=False,
        ),
        _cand("g", week="2026-W43"),  # 週過濾
        _cand(
            "h",
            rule_basis="intel_tag",
            category_rule="intel",
            dup_key="x",
            app="TV",
            event_month="2026-09",
        ),
        _cand(
            "a", item_id="BU-MTG-1-1-0-a2"
        ),  # 同 item_key 第二列（同段同 quote）→ 只留 item_id 小的
    ]
    cols = CAND_DDL.replace(" string", "").replace(" bigint", "").replace(" int", "")
    names = [c.strip().split(" ")[0] for c in cols.replace("array<>", "").split(",")]
    df_cand = spark.createDataFrame([tuple(r[n] for n in names) for r in cands], CAND_DDL)
    spec = mod003.TABLES["g_meeting_items_sem_bu"]
    lens_names = [c[0] for c in spec["columns"]]
    lens_rows = [
        {
            "item_key": "x",
            "item_id": "old-x",
            "category": "intel",
            "term": "VD 第二來源",
            "route_hint": "background_intel:MNT",
            "as_of": "2026-07",
            "confidence": 0.8,
            "model": "claude-x",
            "active": True,
            "verified": "y",
        },
        {"item_key": "e", "item_id": "old-e", "category": "event", "active": True},
    ]
    df_lens = spark.createDataFrame(
        [tuple(r.get(n) for n in lens_names) for r in lens_rows], mod003.schema_ddl(spec)
    )
    return df_cand, df_lens, lens_names


def test_select_and_split(mod, fake):
    df_cand, _, _ = fake
    keys = lambda df: {r.item_key for r in df.select("item_key").collect()}  # noqa: E731
    assert keys(mod.select_pending(df_cand, "0.1", False, "")) == {
        "a",
        "b",
        "c",
        "d",
        "f",
        "g",
        "h",
    }
    assert keys(mod.select_pending(df_cand, "0.1", False, "2026-W42")) == {
        "a",
        "b",
        "c",
        "d",
        "f",
        "h",
    }
    assert "e" in keys(mod.select_pending(df_cand, "0.1", True, ""))
    rule, llm, dup = mod.split_pending(mod.select_pending(df_cand, "0.1", False, ""))
    assert (keys(rule), keys(llm), keys(dup)) == ({"a", "g"}, {"b", "f"}, {"c", "d", "h"})
    pend = mod.select_pending(df_cand, "0.1", False, "")
    assert pend.count() == 7 and pend.where("item_key = 'a'").first().item_id == "BU-MTG-1-1-0-a"


def test_rule_dup_and_lens_rows(mod, mod003, spark, fake):
    df_cand, df_lens, lens_names = fake
    pending = mod.select_pending(df_cand, "0.1", False, "")
    rule, llm, dup = mod.split_pending(pending)
    r = {x.item_key: x for x in mod.rule_cls(rule).collect()}
    assert (r["a"].category, r["a"].extract_note, r["a"].model) == ("event", "rule:default", "rule")
    assert r["a"].term is None and r["a"].route_hint is None and r["a"].sa_confidence is None
    llm_cls = spark.createDataFrame(
        [
            ("b", "semantic", "分貨 code", "pa:semantics", None, "通用", 0.9, "claude-x"),
            ("f", "intel", "需求", "background_intel:MNT", "2026-09", "框架", 0.7, "claude-x"),
        ],
        mod.CLS_SCHEMA,
    )
    primary = mod.rule_cls(rule).unionByName(llm_cls)
    d = {
        x.item_key: x
        for x in mod.dup_cls(dup, primary.unionByName(mod.lens_cls_existing(df_lens))).collect()
    }
    assert set(d) == {"c", "h"}  # d 的最早那條不存在 → 等
    assert (d["c"].category, d["c"].term, d["c"].route_hint, d["c"].extract_note) == (
        "semantic",
        "分貨 code",
        "pa:semantics",
        "dup of b",
    )
    # h 複製鏡頭表既有的 x（intel）：as_of 用自己的月、route 依自己的 app
    assert (d["h"].category, d["h"].as_of, d["h"].route_hint, d["h"].model) == (
        "intel",
        "2026-09",
        "background_intel:TV",
        "claude-x",
    )
    all_cls = primary.unionByName(
        mod.dup_cls(dup, primary.unionByName(mod.lens_cls_existing(df_lens)))
    )
    out = mod.to_lens_rows(pending, all_cls, "0.1")
    expected_cols = [c for c in lens_names if c not in mod.PROTECTED_COLS]
    assert set(out.columns) == set(expected_cols)
    rows = {x.item_key: x for x in out.collect()}
    assert set(rows) == {"a", "g", "b", "f", "c", "h"}
    assert rows["b"].confidence == 0.9 and rows["b"].active is True
    assert rows["b"].stage_a_version == "0.1" and rows["b"].quote == "原文 b 逐字"
    assert rows["c"].dup_key == "b" and rows["c"].category_rule == "intel"
