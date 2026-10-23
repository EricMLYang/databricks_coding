"""meeting_extracted_w2_t5_export 的測試（[c02]～[c05]）。

[c03] 關卡彙總與硬 / 軟關卡；[c04] 例外清單 md 的節順序、other 格依標籤分組、證據上限、
sb_only 計數、PM 修正後 effective_relation 的分節、email 遮罩；[c05] 篩選在本機 Spark 以假表實跑。
假資料無人名（<Pnn> token）。
"""

from datetime import date, datetime

import pytest
from nbload import load_cells

NB = "jobs/meeting_record/meeting_extracted_w2_t5_export/notebook.ipynb"
FQ = "c.s.g_meeting_sb_reconcile_bu"


@pytest.fixture(scope="module")
def mod():
    return load_cells(NB, ["c02", "c03", "c04", "c05"], name="w2_t5")


def _cell(**kw):
    base = {
        "app_name": "MNT", "brand": "Dell", "facet": "market_outlook", "brief_month": "2026-09",
        "window_start": date(2026, 8, 25), "window_end": date(2026, 9, 21),
        "sb_text": "Dell 對 2H 悲觀，全年 22~23M", "sb_source": "g_sales_brief_brand_summary",
        "meeting_summary": "會議端 8/27 說全年目標 24M 不變",
        "meeting_summary_shareable": "會議端說全年目標維持", "shareable_failed": False,
        "meeting_item_ids": ["I-1", "I-2", "I-3", "I-4"], "n_items": 4, "n_items_sent": 4,
        "topic_tags_agg": ["demand"],
        "relation": "conflict", "relation_basis": "llm", "rationale": "方向不一致",
        "number_caveat": None,
        "cross_customer_flag": False, "cross_customer_note": None, "sensitivity_max": "S0",
        "reviewer": None, "review_verdict": None, "review_relation": None, "review_note": None,
        "prompt_version": "0.3", "model": "claude-sonnet-5",
        "updated_at": datetime(2026, 10, 23, 18, 0),
        "relation_rank": 1, "effective_relation": "conflict", "review_pending": True,
    }
    return {**base, **kw}


def _item(item_id, **kw):
    base = {"item_id": item_id, "item_key": f"k-{item_id}", "app_name": "MNT", "brand": "Dell",
            "facet": "market_outlook", "pk_seq": 100, "segment_no": 2, "sub_no": 0,
            "event_date": date(2026, 8, 27), "speaker_side": "customer", "statement_type": "fact",
            "topic_tag_primary": "demand", "summary": f"摘要 {item_id}",
            "quote": f"<P02> 說 {item_id}",
            "sensitivity": "S0", "subject_clean": "Dell Monthly"}
    return {**base, **kw}


def _rule(**kw):
    """單邊格（rule 判）的共同欄。"""
    base = {"relation_basis": "rule", "sb_text": None, "sb_source": "none", "rationale": None,
            "model": "claude-sonnet-5"}
    return _cell(**{**base, **kw})


def _grid():
    cells = [
        _cell(),
        _cell(brand="HP", facet="other", relation="supplement", effective_relation="supplement",
              relation_rank=2, n_items=5, n_items_sent=5,
              meeting_item_ids=["O-1", "O-2", "O-3", "O-4", "O-5"],
              topic_tags_agg=["supply_chain", "quality"], sensitivity_max="S2",
              meeting_summary="HP 庫存 8.8K", meeting_summary_shareable=None,
              shareable_failed=True),
        _rule(brand="Acer", facet="price", relation="meeting_only",
              effective_relation="meeting_only", relation_rank=3,
              meeting_summary="Acer 價格談判", meeting_summary_shareable="Acer 價格談判",
              meeting_item_ids=["A-1"], n_items=1, n_items_sent=1),
        _rule(brand="UNKNOWN", facet="price", relation="meeting_only",
              effective_relation="meeting_only",
              relation_rank=3, meeting_summary=None, meeting_summary_shareable=None,
              meeting_item_ids=["U-1"], n_items=1, n_items_sent=0, model="rule"),
        _cell(brand="Lenovo", facet="product_tech", relation="corroborate",
              effective_relation="supplement", relation_rank=4, review_verdict="fix_relation",
              review_relation="supplement", review_note="其實是補充", reviewer="pm1",
              review_pending=False, meeting_item_ids=["L-1"], n_items=1, n_items_sent=1),
        _rule(brand="TPV", facet="price", relation="sb_only", effective_relation="sb_only",
              relation_rank=5, sb_text="TPV 報價", meeting_summary=None,
              meeting_summary_shareable=None,
              meeting_item_ids=None, n_items=0, n_items_sent=0, model="rule", review_pending=False),
        _cell(brand="ALL", facet="market_outlook", relation="supplement",
              effective_relation="supplement", relation_rank=2,
              cross_customer_note="Dell 與 HP 同時提到 Q3 需求下修",
              meeting_item_ids=["I-1", "H-1"], n_items=2, n_items_sent=2,
              sb_text="MNT 整體需求轉弱"),
        _cell(brand="Dell", facet="other", relation="supplement", effective_relation="supplement",
              relation_rank=2, cross_customer_flag=True, meeting_item_ids=["D-9"], n_items=1,
              n_items_sent=1, sb_text="越南產線"),
    ]
    items = {
        "I-1": _item("I-1"), "I-2": _item("I-2", quote="mail me at someone@example.com"),
        "I-3": _item("I-3"), "I-4": _item("I-4"),
        "O-1": _item("O-1", topic_tag_primary="supply_chain", sensitivity="S2"),
        "O-2": _item("O-2", topic_tag_primary="supply_chain"),
        "O-3": _item("O-3", topic_tag_primary="supply_chain"),
        "O-4": _item("O-4", topic_tag_primary="quality", speaker_side="auo",
                     quote="外包管理 | <P07> | pass"),
        "A-1": _item("A-1", brand="Acer", facet="price"), "L-1": _item("L-1", brand="Lenovo"),
        "D-9": _item("D-9", facet="other"),
    }
    return cells, items


def test_summarize_and_gates_ok(mod):
    cells, _ = _grid()
    s = mod.summarize_cells(cells, {"label_rows": 20, "relevant_items": 13})
    assert s["cells"] == 8 and s["brand_cells"] == 7 and s["app_cells"] == 1
    assert s["relation_dist"]["supplement"] == 3 and s["relation_dist"]["meeting_only"] == 2
    assert s["llm_cells"] == 5 and s["llm_without_summary"] == 0
    assert s["meeting_only_without_summary"] == 1          # UNKNOWN 格沒摘要
    assert s["shareable_failed"] == 1 and s["unknown_brand_cells"] == 1
    assert s["review_pending"] == 6 and s["reviewed"] == 1
    assert s["n_items_brand_cells"] == 13 and s["prompt_versions"] == ["0.3"]
    hard, soft = mod.run_gates(s)
    assert hard == []
    assert any("meeting_only 格沒摘要" in w for w in soft)
    assert not any("≠" in w for w in soft)                  # 13 = 13，條目都進格


def test_gates_hard_and_soft(mod):
    cells, _ = _grid()
    assert mod.run_gates(mod.summarize_cells([]))[0]       # 0 格 → 硬關卡
    cells[0]["prompt_version"] = "0.2"
    cells[1]["meeting_summary"] = None                       # llm 格沒摘要
    cells[2]["relation"] = "weird"
    s = mod.summarize_cells(cells, {"label_rows": 20, "relevant_items": 99})
    hard, soft = mod.run_gates(s)
    assert len(hard) == 3
    assert any("T3 相關 99 vs 格內 13" in w for w in soft)
    for c in cells:
        c["sb_text"] = None
    assert any("brief 還沒填" in w for w in mod.run_gates(mod.summarize_cells(cells))[1])


def _block(md: str, start: str, end: str) -> str:
    return md[md.index(start):md.index(end)]


def test_render_sections_and_order(mod):
    cells, items = _grid()
    s = mod.summarize_cells(cells)
    md = mod.render_review_md(cells, items, s, ["測試 WARN"], max_evidence=2, max_other_ids=2,
                              fq_table=FQ, generated_at="2026-10-23 18:00")
    assert md.startswith("# Sales Brief 對照例外清單 — 2026-09")
    assert "> ⚠ 測試 WARN" in md and f"UPDATE {FQ}" in md
    assert "## MNT" in md
    heads = ["### 1. 衝突", "### 2. 補充", "### 3. 只有會議", "### 4. app 層", "### 5. 一致"]
    idx = [md.index(h) for h in heads]
    assert idx == sorted(idx)
    # conflict 格：證據最多 2 條，其餘 id 最多 2 個；email 遮罩、token 保留
    conf = _block(md, heads[0], heads[1])
    assert "MNT × Dell × 市場展望 ｜ conflict（llm）｜ S0 ｜ 條目 4（送 LLM 4）" in conf
    assert conf.count("｜客戶方｜") == 2 and "- 其餘條目：I-3, I-4" in conf
    assert "- 審核：待審" in conf
    assert "@example.com" not in md and "<email>" in conf and "<P02>" in conf
    # PM 改過的格：顯示 corroborate → PM 改 supplement，分到 supplement 節、不在 corroborate 節
    sup = _block(md, heads[1], heads[2])
    assert "corroborate → PM 改 supplement" in sup
    assert "- 審核：fix_relation → supplement｜其實是補充｜pm1" in sup
    assert "Lenovo" not in md[idx[4]:]
    # other 格依標籤分組、每標籤最多 2 條、shareable 失敗提示、AUO 方標籤；n_items 大的排前面
    hp = _block(sup, "#### MNT × HP × 其他", "#### MNT × Dell × 其他")
    assert "- 證據（依主標籤分組）：" in hp and "  - supply_chain：" in hp and "  - quality：" in hp
    assert hp.count("    - ") == 3                           # supply_chain 2 ＋ quality 1
    assert "（驗證失敗：含 S2 數字，未產" in hp and "AUO 方" in hp
    assert "外包管理 ／ <P07> ／ pass" in hp and "\\|" not in md       # | 換 ／，不跳脫
    # meeting_only：Acer 在 UNKNOWN 前；UNKNOWN 標示客戶不明、無摘要
    mo = _block(md, heads[2], heads[3])
    assert mo.index("Acer") < mo.index("UNKNOWN（客戶不明）") and "（無摘要）" in mo
    # app 層：訊號；H-1 不在標註表 → 提示
    app = _block(md, heads[3], heads[4])
    assert "ALL（app 層）" in app and "- 跨客戶訊號：Dell 與 HP 同時提到 Q3 需求下修" in app
    assert "（1 條證據 id 已不在本期標註表" in app
    # sb_only 一行計數
    assert "- sb_only（只有填報、本期沒有相關會議條目）：1 格（TPV）" in md


def test_render_include_corroborate_false(mod):
    cells, items = _grid()
    s = mod.summarize_cells(cells)
    md = mod.render_review_md(cells, items, s, [], include_corroborate=False)
    assert "### 5. 一致" not in md and "### 4. app 層" in md


def test_pick_evidence_other_per_tag(mod):
    cells, items = _grid()
    shown, rest, missing = mod.pick_evidence(cells[1], items, 1)
    assert [i for _, i, _ in shown] == ["O-1", "O-4"]
    assert rest == ["O-2", "O-3", "O-5"] and missing == ["O-5"]
    # 交錯的標籤要集中：q, s, q, s → q, q, s, s（標籤照首次出現排）
    items2 = {"a": _item("a", topic_tag_primary="quality"),
              "b": _item("b", topic_tag_primary="supply_chain"),
              "c": _item("c", topic_tag_primary="quality"),
              "d": _item("d", topic_tag_primary="supply_chain")}
    cell = _cell(facet="other", meeting_item_ids=["a", "b", "c", "d"])
    shown2, _, _ = mod.pick_evidence(cell, items2, 3)
    assert [(tg, i) for tg, i, _ in shown2] == [("quality", "a"), ("quality", "c"),
                                                ("supply_chain", "b"), ("supply_chain", "d")]


def _schema(cols, typemap, default="string"):
    return ", ".join(f"{c} {typemap.get(c, default)}" for c in cols)


def test_select_month_spark(mod):
    from pyspark.sql import SparkSession

    spark = SparkSession.builder.master("local[1]").appName("t5").getOrCreate()
    rec_cols = mod.CELL_COLS
    rec_types = {"window_start": "date", "window_end": "date", "updated_at": "timestamp",
                 "meeting_item_ids": "array<string>", "topic_tags_agg": "array<string>",
                 "shareable_failed": "boolean", "cross_customer_flag": "boolean",
                 "review_pending": "boolean",
                 "n_items": "int", "n_items_sent": "int", "relation_rank": "int"}
    rows = [tuple(_cell(brief_month=bm, brand=b).get(c) for c in rec_cols)
            for bm, b in (("2026-09", "Dell"), ("2026-10", "Dell"), ("2026-09", "HP"))]
    df_rec = spark.createDataFrame(rows, _schema(rec_cols, rec_types))
    got = mod.select_month_cells(df_rec, "2026-09").collect()
    assert len(got) == 2 and set(got[0].asDict()) == set(rec_cols)

    item_cols = mod.ITEM_COLS + ["brief_month", "active", "sb_relevant"]
    item_types = {"event_date": "date", "pk_seq": "bigint", "segment_no": "int", "sub_no": "int",
                  "active": "boolean", "sb_relevant": "boolean"}

    def irow(it, active, relevant):
        d = {**it, "brief_month": "2026-09", "active": active, "sb_relevant": relevant}
        return tuple(d.get(c) for c in item_cols)

    irows = [irow(_item("I-1"), True, True), irow(_item("I-1", app_name="NB"), True, True),
             irow(_item("I-2"), True, False), irow(_item("I-3"), False, True)]
    df_items = spark.createDataFrame(irows, _schema(item_cols, item_types))
    assert [r["item_id"] for r in mod.select_month_items(df_items, "2026-09").collect()] == ["I-1"]
    st = mod.label_stats_df(df_items, "2026-09").first()
    assert (st["label_rows"], st["relevant_items"]) == (3, 2)
