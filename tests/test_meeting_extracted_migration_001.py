"""001_semantic_entity 的純函式 cell 測試（[c02]～[c04]），並驗證 [c05] 內嵌種子本身合法。"""

import pytest
from nbload import load_cells

NB = "jobs/meeting_record/meeting_extracted_migration/001_semantic_entity.ipynb"


@pytest.fixture(scope="module")
def mod():
    return load_cells(NB, ["c02", "c03", "c04", "c05"], name="mig001")


def _ent(**kw):
    base = {
        "entity_id": "acer",
        "entity_name": "Acer",
        "entity_type": "customer",
        "side": "customer",
        "app_default": "MNT|NB",
        "note": None,
    }
    return {**base, **kw}


def _ali(**kw):
    base = {"alias_type": "name", "alias": "Acer", "entity_id": "acer", "note": None}
    return {**base, **kw}


def test_parse_csv_text(mod):
    rows = mod.parse_csv_text(
        "﻿alias_type,alias,entity_id,note\nname, Acer ,acer,\n", mod.ALIAS_COLS
    )
    assert rows == [{"alias_type": "name", "alias": "Acer", "entity_id": "acer", "note": None}]
    with pytest.raises(ValueError):
        mod.parse_csv_text("alias,alias_type,entity_id,note\n", mod.ALIAS_COLS)


def test_norm_alias(mod):
    assert mod.norm_alias("  Samsung　 ＶＤ ") == "samsung vd"
    assert mod.norm_alias("華碩") == "華碩"


def test_validate_ok_and_errors(mod):
    assert (
        mod.validate_seed([_ent()], [_ali(), _ali(alias_type="email_domain", alias="acer.com")])
        == []
    )
    errs = mod.validate_seed(
        [_ent(), _ent(entity_type="vendor", app_default="TV|PC"), _ent(entity_id="Bad-Id")],
        [
            _ali(),
            _ali(alias="ＡＣＥＲ"),
            _ali(entity_id="nope", alias="x"),
            _ali(alias_type="email_domain", alias="Acer.COM"),
            _ali(alias_type="kw"),
        ],
    )
    text = "\n".join(errs)
    for frag in [
        "entity_id 重複",
        "entity_type 不在",
        "app_default",
        "entity_id 格式不符",
        "正規化後重複",
        "不在 ENTITY_SEED",
        "email_domain 應為小寫網域",
        "alias_type 不在",
    ]:
        assert frag in text, frag


def test_transforms_match_python_norm(mod, spark):
    ents = [_ent(), _ent(entity_id="tcl", entity_name="TCL", app_default=None)]
    df = mod.transform_entity(
        spark.createDataFrame(ents, ", ".join(f"{c} string" for c in mod.ENTITY_COLS))
    )
    got = {r.entity_id: r.app_default for r in df.collect()}
    assert got == {"acer": ["MNT", "NB"], "tcl": []}
    raw = ["  Samsung　 ＶＤ ", "ＡＣＥＲ", "華碩"]
    rows = [_ali(alias=a) for a in raw]
    out = mod.transform_alias(
        spark.createDataFrame(rows, ", ".join(f"{c} string" for c in mod.ALIAS_COLS))
    ).collect()
    assert [r.alias_norm for r in out] == [mod.norm_alias(a) for a in raw]
    assert all(r.is_active for r in out)


def test_inline_seed_is_valid(mod):
    """[c05] 的種子本身要能通過驗證：改了種子沒跑測試就上 Databricks 會在 [c10] 才爆。"""
    ents = mod.parse_csv_text(mod.ENTITY_SEED, mod.ENTITY_COLS)
    alis = mod.parse_csv_text(mod.ALIAS_SEED, mod.ALIAS_COLS)
    assert mod.validate_seed(ents, alis) == []
    assert len(ents) == 29 and len(alis) == 93
    # v3（2026-10-16）：同業面板廠是 competitor / third_party，不會被當 customer
    by_id = {e["entity_id"]: e for e in ents}
    assert by_id["hkc"]["entity_type"] == "competitor" and by_id["hkc"]["side"] == "third_party"
    assert {a["alias"] for a in alis if a["entity_id"] == "samsung"} >= {
        "SEHC",
        "SEC",
        "SAMEX",
        "SIEL",
    }
    assert any(a["alias"] == "AOC" and a["entity_id"] == "tpv" for a in alis)
