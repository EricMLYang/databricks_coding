"""meeting_extracted_pm_pack 的測試（[c02]～[c06]、[c08]）。

[c03] A 節：格子排序、effective_relation 呈現、審核欄、每 app 待審數、文字截斷與 `|` 跳脫、衝突理由、空月份；
[c04] B 節：token → 陣營、分組順序、代表句規則、輪廓、總覽列、md 卡片；
[c06] HTML：總覽卡、A 節只展開衝突 / 補充、B 節摘要卡與折疊全列、跳脫、無 JS；
[c08] LLM：prompt 內容與條目上限、JSON 解析、後處理（token / email 外洩作廢、長度上限）；
[c05] 本機 Spark 假表：attach_months 的兩種月與 dup_key、各 funnel、select_month_items。假資料無人名（<Pnn> token）。
"""

from datetime import date

import pytest
from nbload import load_cells

NB = "jobs/meeting_record/meeting_extracted_pm_pack/notebook.ipynb"


@pytest.fixture(scope="module")
def mod():
    return load_cells(NB, ["c02", "c03", "c04", "c05", "c06", "c08"], name="pm_pack")


# ---------- A 節 ----------
def _cell(**kw):
    base = {"app_name": "MNT", "brand": "dell", "facet": "market_outlook", "brief_month": "2026-09",
            "window_start": date(2026, 8, 25), "window_end": date(2026, 9, 21),
            "sb_text": "Dell 全年 22~23M", "sb_source": "g_sales_brief_brand_summary",
            "meeting_summary": "客戶方 8/27 說全年 24M 不變", "n_items": 4, "relation": "conflict", "relation_basis": "llm",
            "rationale": "數字方向不同", "number_caveat": None, "cross_customer_note": None, "sensitivity_max": "S0",
            "reviewer": None, "review_verdict": None, "review_relation": None, "review_note": None,
            "prompt_version": "0.4", "effective_relation": "conflict", "review_pending": True}
    return {**base, **kw}


def _cells():
    return [
        _cell(),
        _cell(brand="hp", facet="other", relation="supplement", effective_relation="supplement", rationale=None),
        _cell(brand="ALL", facet="price", relation="sb_only", effective_relation="sb_only", meeting_summary=None, n_items=0,
              relation_basis="rule", cross_customer_note=None),
        _cell(brand="UNKNOWN", facet="product_tech", relation="meeting_only", effective_relation="meeting_only", sb_text=None,
              relation_basis="rule"),
        _cell(app_name="TV", brand="tcl", facet="price", relation="conflict", effective_relation="supplement",
              review_verdict="fix_relation", review_relation="supplement", reviewer="pm", review_pending=False,
              sb_text="85 吋 | 報價", meeting_summary="55 吋\n機種"),
        _cell(brief_month="2026-10", brand="dell", relation="corroborate", effective_relation="corroborate",
              review_verdict="agree", review_pending=False, rationale=None),
    ]


def test_cell_sort_key_app_brand_facet(mod):
    keys = [mod.cell_sort_key(c) for c in _cells()]
    order = sorted(range(len(keys)), key=lambda i: keys[i])
    brands = [_cells()[i]["brand"] for i in order]
    assert brands[:4] == ["dell", "hp", "UNKNOWN", "ALL"] or brands[:5] == ["dell", "dell", "hp", "UNKNOWN", "ALL"]
    assert brands[-1] == "tcl"


def test_review_label(mod):
    cs = _cells()
    assert mod.review_label(cs[0]) == "待審"
    assert mod.review_label(cs[2]) == "—"  # sb_only 不審
    assert mod.review_label(cs[4]) == "改判 → 補充"
    assert mod.review_label(cs[5]) == "同意"


def test_summarize_sb_counts(mod):
    s = mod.summarize_sb(_cells())
    m = s["2026-09"]
    assert m["n"] == 5 and m["app_cells"] == 1 and m["brand_cells"] == 4
    assert m["relations"]["conflict"] == 1 and m["relations"]["supplement"] == 2  # TV 格改判後算 supplement
    assert m["pending"] == 3 and m["reviewed"] == 1  # sb_only 不算
    assert m["apps"]["MNT"]["brands"] == {"dell", "hp"}  # UNKNOWN / ALL 不算填報品牌
    assert m["apps"]["MNT"]["window"] == (date(2026, 8, 25), date(2026, 9, 21))
    assert m["apps"]["MNT"]["pending"] == 3 and m["apps"]["TV"]["pending"] == 0


def test_render_sb_md_layout(mod):
    md = mod.render_sb_md(_cells(), ["2026-09", "2026-10", "2026-11"], max_text=10)
    assert "## 2026-09" in md and "### MNT" in md and "### TV" in md
    assert md.index("### MNT") < md.index("### TV")
    assert "| app 層（跨品牌） | 價格 | 只有填報 |" in md
    assert "| （品牌不在填報名單） | 產品技術 | 只有會議 |" in md
    assert "衝突理由：" in md and "- dell × 市場展望：數字方向不同" in md
    assert "85 吋 ／ 報價" in md and "55 吋 機種" in md
    assert "Dell 全年 2…" in md
    tv = md[md.index("### TV"):]
    assert "衝突理由" not in tv
    assert "## 2026-11" in md and "沒有對照格" in md.split("## 2026-11")[1]


# ---------- B 節 ----------
def _item(i, **kw):
    base = {"item_id": f"I{i:03d}", "item_key": f"k{i}", "pk_seq": 100 + i % 2, "segment_no": 1, "sub_no": 0,
            "subject_clean": "acer weekly", "statement_type": "fact", "speaker_side": "customer", "speaker_company": "acer",
            "customer": "acer", "app": "MNT", "model_nos_str": None, "topic_tag_primary": "engineering",
            "summary": f"<P01> 說明 {i}", "quote": f"<P01> 原文 {i}", "event_date": date(2026, 9, 1 + i % 5),
            "event_month": "2026-09", "sensitivity": "S0", "confidence": 0.9, "dup_key": None}
    return {**base, **kw}


def _items():
    return [_item(0), _item(1, statement_type="request", topic_tag_primary="demand", summary="<P01> 要求 Q4 加 100K", confidence=0.8),
            _item(2, statement_type="decision", topic_tag_primary="price", summary="雙方同意 10 月降 2%", sensitivity="S2", confidence=0.95),
            _item(3, statement_type="issue", summary="<P02> 回報 EC 延遲", speaker_side="auo", speaker_company="auo"),
            _item(4, statement_type="plan", topic_tag_primary="product_plan", summary="客戶規劃 27 吋新案"),
            _item(5, statement_type="request", topic_tag_primary="demand", summary="<P01> 要求 q4 加 100k"),  # 與 1 同句（大小寫）
            _item(10, customer="dell", app="NB", statement_type="fact", summary="x"),
            _item(11, customer=None, app="MNT", summary="y"),
            _item(12, dup_key="x", summary="dup")]


def test_token_labels_and_resolve(mod):
    labels = mod.token_labels([{"pk_seq": 100, "token": "P01", "side": "customer", "company": "acer"},
                               {"pk_seq": 100, "token": "P02", "side": "auo", "company": "auo"},
                               {"pk_seq": 100, "token": "G01", "side": "customer", "company": "acer"}])
    assert labels[(100, "P01")] == "客戶方（acer）" and labels[(100, "P02")] == "AUO 方" and labels[(100, "G01")] == "群組（acer）"
    assert mod.resolve_tokens("<P01> 要求 <P02> 回覆 <P09>", 100, labels) == "客戶方（acer） 要求 AUO 方 回覆 與會者"
    assert mod.resolve_tokens(None, 100, labels) == "" and mod.resolve_tokens("<P01>", 100, None) == "<P01>"


def test_group_items_order_and_dups(mod):
    groups = mod.group_items(_items())
    assert list(groups) == [("acer", "MNT"), ("dell", "NB"), (None, "MNT")]  # 條目數降冪、客戶不明最後
    assert len(groups[("acer", "MNT")]) == 6  # dup 不列
    assert len(mod.group_items(_items(), include_dups=True)[("acer", "MNT")]) == 7


def test_pick_highlights_rule(mod):
    rows = mod.group_items(_items())[("acer", "MNT")]
    hl = mod.pick_highlights(rows, n=3)
    ids = [it["item_id"] for it in hl]
    # 要求 / 決定 / 問題 優先，再商務主題：決定 × price（S2、conf .95）第一、要求 × demand 第二（I005 conf .9 > I001 .8，同句只留一條）、issue × engineering 第三
    assert ids == ["I002", "I005", "I003"]
    assert "I001" not in [it["item_id"] for it in mod.pick_highlights(rows, n=10)]


def test_group_profile_and_overview(mod):
    rows = mod.group_items(_items())[("acer", "MNT")]
    p = mod.group_profile(rows)
    assert p["n"] == 6 and p["mails"] == 2 and p["highlight_n"] == 4 and p["s2"] == 1
    assert {t for t, _ in p["top_topics"][:2]} == {"engineering", "demand"} and p["customer_side"] == 5 and p["auo_side"] == 1
    assert "6 條 / 2 封" in mod.profile_line(p) and "要求 / 決定 / 問題 4 條" in mod.profile_line(p)
    sbs = mod.summarize_sb(_cells())
    profs = {"2026-09": {k: mod.group_profile(v) for k, v in mod.group_items(_items()).items()}}
    ov = mod.build_overview(["2026-09", "2026-10"], sbs, profs)
    by = {(r["month"], r["app"]): r for r in ov}
    assert by[("2026-09", "MNT")] == {"month": "2026-09", "app": "MNT", "items": 7, "customers": 1, "cust_null": 1, "cells": 4,
                                      "conflict": 1, "supplement": 1, "corroborate": 0, "meeting_only": 1, "sb_only": 1, "pending": 3}
    assert by[("2026-09", "NB")]["items"] == 1 and by[("2026-09", "NB")]["cells"] == 0
    assert by[("2026-10", "MNT")]["items"] == 0 and by[("2026-10", "MNT")]["corroborate"] == 1
    md = mod.render_overview_md(ov)
    assert "| 2026-09 | MNT | 7 | 1 | 1 | 4 | 1 | 1 | 0 | 1 | 1 |" in md and "請 PM 回答" in md


def test_render_monthly_md_cards(mod):
    funnel = {"mails": 40, "mails_no_body": 12, "mails_dup": 3, "mails_skipped": 1, "segments": 150, "extractable": 90,
              "items_valid": 800, "items_canonical": 500, "items_cust_null": 100, "items_s2": 20, "items_mails": 25, "items_no_date": 7}
    summaries = {("acer", "MNT"): {"summary": "客戶方要求加量。", "watch": ["追 Q4 100K"], "error": None},
                 ("dell", "NB"): {"summary": None, "watch": [], "error": "HTTP 500"}}
    md = mod.render_monthly_md("2026-09", funnel, _items(), {}, basis="meeting", summaries=summaries, max_per_group=2)
    assert "## 2026-09 會議紀錄彙整（按會議日期）" in md
    assert "| 收進的信 | 40 | 其中 ETL 截斷無正文 12、同信重複 3、隔離（解析不了）1 |" in md
    assert "| 沒有會議日期 | 7 |" in md
    assert "### 客戶 × 應用摘要（3 組）" in md and "**摘要（LLM）**：客戶方要求加量。" in md and "- 追 Q4 100K" in md
    assert "（LLM 摘要失敗：HTTP 500）" in md
    assert "代表句（規則：要求 / 決定 / 問題 優先）：" in md and "〔S2〕雙方同意 10 月降 2%" in md
    assert "### 條目全列（8 條" in md and "另 4 條" in md
    assert "沒有會議日期" not in mod.render_monthly_md("2026-09", funnel, [], {}, basis="mail")


# ---------- [c08] LLM ----------
def test_build_group_prompt(mod):
    rows = mod.group_items(_items())[("acer", "MNT")]
    labels = {(100, "P01"): "客戶方（acer）", (101, "P01"): "客戶方（acer）", (101, "P02"): "AUO 方"}
    p = mod.build_group_prompt("2026-09", "acer", "MNT", rows, labels)
    assert p.startswith("客戶：acer｜應用：MNT｜月份：2026-09（按會議日期）")
    assert "送出 6 條" in p and "<P01>" not in p and "<P02>" not in p
    assert "客戶（acer）：客戶方（acer） 要求 Q4 加 100K" in p and "〔S2〕雙方同意" in p and "AUO：AUO 方 回報 EC 延遲" in p
    many = [_item(i, summary=f"s{i}") for i in range(80)]
    assert "送出 60 條" in mod.build_group_prompt("2026-09", "acer", "MNT", many, {})
    assert "prompt 0.1" in mod.SYSTEM_PROMPT_PM and "watch" in mod.SYSTEM_PROMPT_PM


def test_parse_and_postprocess(mod):
    obj, err = mod.parse_llm_json('```json\n{"summary": "客戶方要求加量。", "watch": ["追 100K", 5, "", "第三條", "第四條"]}\n```')
    assert err is None
    r = mod.postprocess_summary(obj, None)
    assert r == {"summary": "客戶方要求加量。", "watch": ["追 100K", "第三條", "第四條"], "error": None}
    assert mod.parse_llm_json("not json")[0] is None and mod.parse_llm_json("")[1] == "empty response"
    assert mod.postprocess_summary(None, "HTTP 500")["error"] == "HTTP 500"
    assert mod.postprocess_summary({"summary": "", "watch": []}, None)["error"] == "empty summary"
    assert mod.postprocess_summary({"summary": "<P03> 說要加量"}, None)["error"] == "token / email leaked"
    assert mod.postprocess_summary({"summary": "寫信給 a@b.com"}, None)["error"] == "token / email leaked"
    long = mod.postprocess_summary({"summary": "x" * 900, "watch": ["y" * 300]}, None)
    assert len(long["summary"]) == mod.MAX_SUMMARY_CHARS and len(long["watch"][0]) == mod.MAX_WATCH_CHARS
    assert mod.est_cost_usd({"input": 1_000_000, "output": 0, "cache_read": 0, "cache_write": 0}) == 2.0


# ---------- [c06] HTML ----------
def test_render_overview_html(mod):
    rows = [{"month": "2026-09", "app": "MNT", "items": 7, "customers": 1, "cust_null": 1, "cells": 4, "conflict": 1, "supplement": 1,
             "corroborate": 0, "meeting_only": 1, "sb_only": 1, "pending": 3}]
    html = mod.render_overview_html(rows, badge=1)
    assert 'id="overview"' in html and "<th>衝突</th>" in html and "請 PM 回答三題" in html and "<script" not in html
    assert "<th>會議條目</th>" not in mod.render_overview_html(rows, has_b=False)


def test_render_sb_html_focus_and_collapse(mod):
    cards, nxt = mod.render_sb_html(_cells(), ["2026-09", "2026-10", "2026-11"], max_text=10, badge_start=2)
    assert len(cards) == 3 and nxt == 5
    html = cards[0]
    mnt = html[html.index("MNT｜"):html.index("TV｜")]
    # MNT：展開 dell（衝突）、hp（補充）；sb_only 與 meeting_only 折進 details
    assert mnt.count("<tr>") == 2 + 1 + 2 + 1  # 展開表 2 列 ＋ thead；折疊表 2 列 ＋ thead
    assert "<details><summary>其餘 2 格（只有會議 1、只有填報 1）</summary>" in mnt
    assert mnt.index("dell") < mnt.index("<details>")
    assert "改判 → 補充" in html and 'class="tag-grey">待審' in html
    assert "<input" not in html and "<script" not in html
    assert "85 吋 ／ 報價" in html
    assert "沒有對照格" in cards[2]


def test_render_monthly_html_cards(mod):
    summaries = {("acer", "MNT"): {"summary": "客戶方要求加量 <b>。", "watch": ["追 Q4 100K"], "error": None},
                 ("dell", "NB"): {"skipped": "條目少於 3，只列代表句"}}
    funnel = {"mails": 4, "items_valid": 9, "items_canonical": 8}
    html = mod.render_monthly_html("2026-09", funnel, _items(), {}, basis="meeting", badge=3, max_per_group=2, summaries=summaries)
    assert '<div class="section-badge">3</div>' in html and "會議紀錄彙整（按會議日期）" in html
    assert html.count('<div class="gcard">') == 3
    assert "客戶方要求加量 &lt;b&gt;。" in html and "<li>追 Q4 100K</li>" in html
    assert "條目少於 3，只列代表句" in html
    assert 'class="tag-s2">S2</span> 雙方同意 10 月降 2%' in html
    assert "逐條全列（8 條" in html and html.count("<details>") == 1 + 3  # 外層一個 ＋ 每組一個
    assert "另 4 條" in html and "<th>原文</th>" not in html and "<script" not in html
    assert "<th>原文</th>" in mod.render_monthly_html("2026-09", funnel, _items(), {}, include_quote=True)


def test_render_page_html_shell(mod):
    page = mod.render_page_html("T <x>", ["m1"], ["<div>c</div>"], warn="w", nav=[("a-1", "A")])
    assert page.startswith("<!DOCTYPE html>") and "<title>T &lt;x&gt;</title>" in page
    assert 'href="#a-1"' in page and '<div class="warn-box">w</div>' in page and page.endswith("</body></html>")
    assert "<script" not in page


# ---------- [c05] Spark ----------
@pytest.fixture(scope="module")
def frames(spark, mod):
    items = spark.createDataFrame(
        [("I1", "k1", 1, 1, 0, "s", "fact", "customer", "acer", "acer", "MNT", None, "demand", "a", "q", date(2026, 9, 3), "2026-09", "S0", 0.9),
         ("I2", "k2", 2, 1, 0, "s", "fact", "customer", "acer", "acer", "MNT", None, "demand", "a", "q", date(2026, 9, 3), "2026-09", "S2", 0.9),
         ("I3", "k3", 2, 2, 0, "s", "plan", "auo", None, None, "TV", None, "schedule", "b", "q", date(2026, 8, 30), "2026-08", "S0", 0.9),
         ("I4", "k4", 3, 1, 0, "s", "plan", "auo", None, "tcl", "TV", None, "schedule", "c", "q", None, None, "S0", 0.9)],
        "item_id string, item_key string, pk_seq int, segment_no int, sub_no int, subject_clean string, statement_type string, "
        "speaker_side string, speaker_company string, customer string, app string, model_nos_str string, topic_tag_primary string, "
        "summary string, quote string, event_date date, event_month string, sensitivity string, confidence double")
    mail = spark.createDataFrame(
        [(1, date(2026, 9, 10), "mail_body_md", None), (2, date(2026, 10, 2), "mail_body_md", None),
         (3, date(2026, 10, 5), "none", 2), (4, date(2026, 10, 6), "none", None)],
        "pk_seq int, mail_date date, body_source_field string, dup_of_pk int")
    lens = spark.createDataFrame([("k1", None, True), ("k2", "k1", True), ("k3", "zzz", False)], "item_key string, dup_key string, active boolean")
    clean = spark.createDataFrame(
        [(1, date(2026, 9, 10), "inline_minutes", None), (2, date(2026, 10, 2), "inline_minutes", None),
         (2, date(2026, 10, 2), "thread_reply", "dup"), (3, date(2026, 10, 5), "noise", None)],
        "pk_seq int, mail_date date, content_type string, dup_of string")
    skipped = spark.createDataFrame([(9, date(2026, 10, 7))], "pk_seq int, mail_date date")
    return {"items_m": mod.attach_months(items, mail, lens), "mail": mail, "clean": clean, "skipped": skipped}


def test_attach_months(mod, frames):
    rows = {r["item_id"]: r.asDict() for r in frames["items_m"].collect()}
    assert rows["I1"]["mail_month"] == "2026-09" and rows["I1"]["meeting_month"] == "2026-09" and rows["I1"]["dup_key"] is None
    assert rows["I2"]["dup_key"] == "k1" and rows["I2"]["mail_month"] == "2026-10"
    assert rows["I3"]["dup_key"] is None  # 鏡頭表 inactive → 不算 dup
    assert rows["I4"]["meeting_month"] is None and rows["I4"]["mail_month"] == "2026-10"


def test_funnels(mod, frames):
    months = ["2026-09", "2026-10"]
    mf = {r["month"]: r.asDict() for r in mod.mail_funnel(frames["mail"], months).collect()}
    assert mf["2026-10"] == {"month": "2026-10", "mails": 3, "mails_no_body": 2, "mails_dup": 1}
    assert mod.skipped_funnel(frames["skipped"], months).first()["mails_skipped"] == 1
    cf = {r["month"]: r.asDict() for r in mod.clean_funnel(frames["clean"], months).collect()}
    assert cf["2026-10"]["segments"] == 3 and cf["2026-10"]["extractable"] == 1
    fi = {r["month"]: r.asDict() for r in mod.items_funnel(frames["items_m"], months, basis="meeting").collect()}
    assert fi["2026-09"] == {"month": "2026-09", "items_valid": 2, "items_canonical": 1, "items_cust_null": 0, "items_s2": 0, "items_mails": 2}
    fm = {r["month"]: r.asDict() for r in mod.items_funnel(frames["items_m"], months, basis="mail").collect()}
    assert fm["2026-10"]["items_valid"] == 3 and fm["2026-10"]["items_canonical"] == 2 and fm["2026-10"]["items_cust_null"] == 1
    assert mod.items_no_date(frames["items_m"]).first()["items_no_date"] == 1


def test_select_month_items_and_counts(mod, frames):
    ids = sorted(r["item_id"] for r in mod.select_month_items(frames["items_m"], "2026-09", basis="meeting").collect())
    assert ids == ["I1"]
    ids = sorted(r["item_id"] for r in mod.select_month_items(frames["items_m"], "2026-09", basis="meeting", include_dups=True).collect())
    assert ids == ["I1", "I2"]
    cnt = [(r["customer"], r["app"], r["n"]) for r in mod.cust_app_counts(frames["items_m"], "2026-10", basis="mail").collect()]
    assert cnt == [(None, "TV", 1), ("tcl", "TV", 1)]
    cols = set(mod.select_month_items(frames["items_m"], "2026-09").columns)
    assert {"dup_key", "mail_month", "meeting_month", "summary"} <= cols
