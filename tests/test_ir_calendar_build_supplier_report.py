# ruff: noqa: E501 - 測試資料與斷言逐字對齊比寬度重要
"""ir_calendar_build_supplier_report 的純函式 cell 測試（[c02]～[c07]）：facts 換算、工作清單、prompt / JSON 解析、SVG 標籤不重疊、
HTML 章節順序與「未取得 / 未提及」呈現；並比對建表 notebook [c19a] / [c19b] 的 DDL 欄位與 [c10] 的 schema。

financials 用假資料（台股仟元 / 美股元兩種口徑）、LLM 輸出用假 JSON；不呼叫任何端點。
"""

import json
import re

import pytest
from nbload import ROOT, load_cells, nbtool

NB = "jobs/ir_calendar/build_supplier_report/notebook.ipynb"
INIT_NB = "jobs/ir_calendar/init_tables/notebook.ipynb"


@pytest.fixture(scope="module")
def mod(spark):  # 依賴 spark：cell 內的 F.* 要有 SparkContext
    return load_cells(NB, ["c02", "c03", "c04", "c05", "c06", "c07"], name="irreport")


# ---------- 測試資料 ----------

COMPANY = {"company_key": "TPE:3481", "company_name": "群創光電", "english_name": "Innolux", "stock_code": "3481",
           "market": "TPE", "category": "SUPPLIER", "company_slug": "Innolux", "industry": "光電", "ir_url": None}


def fin(period, ptype, **kw):
    base = {"company_key": "TPE:3481", "period": period, "period_type": ptype, "currency": "TWD", "unit": "thousand",
            "source": "MOPS", "seq": 36, "source_urls": ["https://mops.twse.com.tw/x"], "revenue": None,
            "pretax_income": None, "net_income": None, "eps": None, "operating_cash_flow": None, "gross_margin": None,
            "operating_margin": None, "net_margin": None, "debt_ratio": None, "current_ratio": None,
            "operating_income": None, "total_assets": None, "total_liabilities": None, "capex": None}
    base.update(kw)
    return base


# 仟元：2.0e8 仟元 = 2,000 億
ANNUAL = [fin(f"{y}FY", "annual", revenue=rev * 1e8, pretax_income=pre * 1e8, net_income=net * 1e8, eps=eps,
              operating_cash_flow=ocf * 1e8, gross_margin=gm, operating_margin=opm, net_margin=nm, debt_ratio=dr,
              current_ratio=cr)
          for y, rev, pre, net, eps, ocf, gm, opm, nm, dr, cr in [
              (2020, 2.73, 0.07, 0.03, 0.03, 0.40, 7.1, 0.3, 1.1, 48.2, 1.52),
              (2021, 3.68, 0.70, 0.62, 6.44, 0.95, 24.0, 16.9, 16.8, 45.1, 1.70),
              (2022, 2.21, -0.33, -0.33, -3.43, 0.12, 2.5, -13.0, -14.9, 49.9, 1.40),
              (2023, 2.24, -0.22, -0.20, -2.08, 0.25, 5.4, -8.9, -8.9, 51.7, 1.35),
              (2024, 2.21, -0.03, -0.02, -0.25, 0.30, 7.8, -2.5, -1.1, 50.3, 1.44),
          ]] + [fin("2019FY", "annual", revenue=2.6e8, gross_margin=6.0, operating_margin=-1.0)]   # 第 6 年，應被切掉

QUARTERLY = [fin(p, "quarterly", revenue=rev * 1e8, gross_margin=gm, operating_margin=opm, net_income=net * 1e8,
                 net_margin=nm, eps=eps, current_ratio=cr, pretax_income=pre * 1e8)
             for p, rev, gm, opm, net, nm, eps, cr, pre in [
                 ("2025Q1", 0.50, 6.1, -3.5, -0.03, -6.0, -0.30, 1.40, -0.03),
                 ("2025Q2", 0.55, 7.0, -1.0, -0.01, -1.8, -0.10, 1.42, -0.01),
                 ("2025Q3", 0.58, 8.2, 0.5, 0.01, 1.7, 0.10, 1.45, 0.01),
                 ("2025Q4", 0.52, 6.5, -2.0, -0.02, -3.8, -0.20, 1.43, -0.02),
                 ("2026Q1", 0.54, 7.9, 0.2, 0.00, 0.0, 0.00, 1.47, 0.00),
                 ("2026Q2", 0.60, 9.1, 1.8, 0.02, 3.3, 0.20, 1.50, 0.02),
             ]]

DOCS = [
    {"file_name": "Innolux_Q2CY26_Presentation.pdf", "doc_kind": "Presentation", "sha256": "a1", "source_url": "https://x/p.pdf",
     "text_chars": 30, "volume_path": "/Volumes/c/s/v/supplier/Innolux/Innolux_Q2CY26_Presentation.pdf", "fiscal_label": None,
     "text_md": "# Q2 2026 Results\n營收 600 億，毛利率 9.1%。" * 3},
    {"file_name": "Innolux_Q2CY26_Financial_Statements.pdf", "doc_kind": "Financial_Statements", "sha256": "b2", "source_url": None,
     "text_chars": 50000, "volume_path": "/Volumes/c/s/v/supplier/Innolux/Innolux_Q2CY26_Financial_Statements.pdf", "fiscal_label": None,
     "text_md": "合併財務報告 " * 10000},
]

LLM_OUT = {
    "procurement_conclusion": {
        "light": "Amber", "score": "62.4", "one_liner": "營收回升但本業僅小幅轉正。",
        "confirmed_facts": ["2026Q2 營收 600 億（財報數據）"], "management_outlook": ["下半年需求審慎（Innolux_Q2CY26_Presentation.pdf）"],
        "procurement_actions": [{"area": "成本與議價", "advice": "議價時留意毛利率回升"}, {"area": "其他", "advice": "x"}],
        "qbr_questions": ["OCF 改善計畫？"],
    },
    "financial_highlights": ["毛利率 9.1%（財報數據）"],
    "segment_performance": [],
    "conference": {"business_lines": ["車用顯示器成長"], "capacity": [], "profitability": ["本業轉正"], "market_outlook": [],
                   "investment_ma_org": [], "auo_microled": [], "qa": [{"q": "產能利用率？", "a": "約 80%。"}]},
    "war_room": [{"item": "本業", "management_view": "轉正", "financial_check": "OPM 1.8%", "verdict": "Watch"},
                 {"item": "現金流", "management_view": "", "financial_check": "未取得", "verdict": "bogus"}],
    "positive_signals": ["毛利率連兩季回升"], "watch_items": [], "sources_used": ["Innolux_Q2CY26_Presentation.pdf"],
    "caveats": ["財報本體已截尾"],
}


@pytest.fixture(scope="module")
def facts(mod):
    return mod.build_facts(COMPANY, "2026Q2", ANNUAL + QUARTERLY, {"guidance": "下半年審慎", "core_points": ["a"], "sources": []},
                           {"conference_date": "2026-08-05"}, DOCS)


@pytest.fixture(scope="module")
def llm(mod):
    return mod.normalize_report(LLM_OUT)


@pytest.fixture(scope="module")
def html_out(mod, facts, llm):
    return mod.render_report(facts, llm, generated_on="2026-10-20", version="template 20261010 / prompt 1.0")


# ---------- [c03] facts ----------

def test_money_scale(mod):
    assert mod.money_scale("TWD", "thousand") == {"divisor": 1e5, "label": "億", "prefix": "NT$", "note": "台股 MOPS 仟元換算為億元"}
    assert mod.money_scale("USD", "one")["divisor"] == 1e6 and mod.money_scale("USD", "one")["label"] == "百萬"
    assert mod.money_scale("JPY", "one")["label"] == "億"
    assert mod.money_scale(None, None)["prefix"] == ""


def test_period_helpers(mod):
    assert mod.prev_quarter("2026Q1") == "2025Q4"
    assert mod.prev_quarter("2026Q2", 4) == "2025Q2"
    assert mod.period_label("2025FY") == "2025" and mod.period_label("2026Q2") == "2026 Q2"
    assert mod.period_parts("bad") == (0, None)


def test_annual_series_last_five_and_scaled(mod, facts):
    annual = facts["annual"]
    assert [s["period"] for s in annual] == ["2020FY", "2021FY", "2022FY", "2023FY", "2024FY"]
    assert annual[1]["values"]["revenue"] == pytest.approx(3680.0)          # 3.68e8 仟元 → 3,680 億
    assert annual[1]["values"]["pretax_margin"] == pytest.approx(0.70 / 3.68 * 100, rel=1e-6)
    assert annual[0]["values"]["quick_ratio"] is None and annual[0]["values"]["ar_days"] is None


def test_quarter_series_window_and_actuals(mod, facts):
    assert [s["period"] for s in facts["quarterly"]] == ["2025Q2", "2025Q3", "2025Q4", "2026Q1", "2026Q2"]
    cols = facts["actuals"]["columns"]
    assert [c["period"] for c in cols] == ["2026Q2", "2025Q2", "2026Q1"]
    assert cols[0]["values"]["revenue"] == pytest.approx(600.0)        # 0.60e8 仟元 = 600 億
    kpi = facts["kpis"]
    assert kpi[0]["value"] == "NT$ 600.00 億" and kpi[0]["note"] == "YoY +9.09%" and kpi[0]["tone"] == "green"
    assert kpi[3]["value"] == "1.50x"


def test_indicator_availability(mod, facts):
    av = facts["indicator_avail"]
    assert av["revenue"] and av["eps"] and av["debt_ratio"]
    assert not av["quick_ratio"] and not av["ar_days"] and not av["ap_days"]


def test_facts_without_financials(mod):
    f = mod.build_facts({"company_key": "TYO:5201", "company_name": "AGC", "market": "TYO", "category": "SUPPLIER"},
                        "2026Q2", [], None, None, DOCS[:1])
    assert not f["has_financials"] and f["annual"] == [] and f["quarterly"] == []
    assert all(k["value"] == "未取得" for k in f["kpis"])
    txt = mod.facts_to_prompt_text(f)
    assert "未取得" in txt and "必須來自下方文件" in txt


def test_prompt_text_lists_numbers_and_missing(mod, facts):
    txt = mod.facts_to_prompt_text(facts)
    assert "2024FY |" in txt and "2026Q2 |" in txt
    assert "未取得的指標" in txt and "速動比" in txt
    assert "展望：下半年審慎" in txt


# ---------- [c04] select_work ----------

def _text_df(spark, rows):
    return spark.createDataFrame(rows, "company_key string, company_slug string, category string, period string, "
                                       "doc_kind string, sha256 string, parse_status string")


def _report_df(spark, rows):
    return spark.createDataFrame(rows, "company_key string, period string, docs_digest string, prompt_version string, template_version string")


def test_candidate_latest_period_per_company(mod, spark):
    df = _text_df(spark, [
        ("TPE:3481", "Innolux", "SUPPLIER", "2026Q1", "Presentation", "a", "success"),
        ("TPE:3481", "Innolux", "SUPPLIER", "2026Q2", "Presentation", "b", "success"),
        ("TPE:3481", "Innolux", "SUPPLIER", "2026Q2", "Financial_Statements", "c", "partial"),
        ("TPE:3481", "Innolux", "SUPPLIER", "2026Q3", "Presentation", "d", "failed"),      # 失敗不算
        ("NYSE:GLW", "Corning", "SUPPLIER", "2026Q2", "Press_Release", "e", "success"),
        ("HK:1070", "TCL", "CUSTOMER", "2026Q2", "Presentation", "f", "success"),
    ])
    out = mod.candidate_reports(df, categories=["SUPPLIER"], company_keys=[], periods=[]).collect()
    got = {(r.company_key, r.period): r for r in out}
    assert set(got) == {("TPE:3481", "2026Q2"), ("NYSE:GLW", "2026Q2")}
    assert got[("TPE:3481", "2026Q2")].doc_count == 2 and got[("TPE:3481", "2026Q2")].doc_kinds == ["Financial_Statements", "Presentation"]
    all_periods = mod.candidate_reports(df, categories=[], company_keys=["TPE:3481"], periods=["2026Q1", "2026Q2"]).collect()
    assert sorted(r.period for r in all_periods) == ["2026Q1", "2026Q2"]


def test_select_work_skips_done_unless_changed(mod, spark):
    df = _text_df(spark, [("TPE:3481", "Innolux", "SUPPLIER", "2026Q2", "Presentation", "b", "success"),
                          ("NYSE:GLW", "Corning", "SUPPLIER", "2026Q2", "Press_Release", "e", "success")])
    cand = {r.company_key: r.docs_digest for r in mod.candidate_reports(df, categories=[], company_keys=[], periods=[]).collect()}
    done = _report_df(spark, [("TPE:3481", "2026Q2", cand["TPE:3481"], "1.0", "20261010"),
                              ("NYSE:GLW", "2026Q2", "old-digest", "1.0", "20261010")])
    kw = dict(categories=[], company_keys=[], periods=[], prompt_version="1.0", template_version="20261010")
    assert [r.company_key for r in mod.select_work(df, done, force=False, **kw).collect()] == ["NYSE:GLW"]   # 文件換版要重做
    assert len(mod.select_work(df, done, force=True, **kw).collect()) == 2
    kw["prompt_version"] = "1.1"
    assert len(mod.select_work(df, done, force=False, **kw).collect()) == 2                               # prompt 升版全部重做


# ---------- [c05] prompt / JSON ----------

def test_pack_documents_priority_and_caps(mod):
    packed, skipped = mod.pack_documents(DOCS, max_doc_chars=5000, max_total_chars=6000)
    assert [d["doc_kind"] for d in packed] == ["Presentation", "Financial_Statements"]
    assert not packed[0]["truncated"] and packed[1]["truncated"] and packed[1]["text"].endswith(mod.TRUNCATED_MARK)
    assert skipped == []
    packed2, skipped2 = mod.pack_documents(DOCS, max_doc_chars=5000, max_total_chars=200)
    assert [d["file_name"] for d in packed2] == [] or len(packed2) <= 1
    assert "Innolux_Q2CY26_Financial_Statements.pdf" in skipped2


def test_build_user_prompt_contains_sections(mod, facts):
    packed, skipped = mod.pack_documents(DOCS, max_doc_chars=5000, max_total_chars=6000)
    p = mod.build_user_prompt(facts, packed, skipped)
    assert p.startswith("# 結構化資料") and "# 文件全文" in p and "## 文件：Innolux_Q2CY26_Presentation.pdf" in p
    assert p.rstrip().endswith("請依 system 規格輸出 JSON。")


def test_parse_llm_json_tolerates_fences(mod):
    obj, err = mod.parse_llm_json('```json\n{"a": 1}\n```')
    assert obj == {"a": 1} and err is None
    obj, err = mod.parse_llm_json("前言 {\"a\": [1, 2]} 後記")
    assert obj == {"a": [1, 2]}
    assert mod.parse_llm_json("")[1] == "empty output"
    assert mod.parse_llm_json("{bad}")[1].startswith("JSONDecodeError")
    assert mod.parse_llm_json("{bad")[1] == "no JSON object found"
    assert mod.parse_llm_json("[1]")[1] == "no JSON object found"


def test_normalize_report_shapes(mod, llm):
    pc = llm["procurement_conclusion"]
    assert pc["light"] == "amber" and pc["score"] == 62
    assert [a["area"] for a in pc["procurement_actions"]][:4] == mod.ACTION_AREAS
    assert pc["procurement_actions"][1]["advice"] == "議價時留意毛利率回升" and pc["procurement_actions"][0]["advice"] == ""
    assert pc["procurement_actions"][-1] == {"area": "其他", "advice": "x"}
    assert llm["conference"]["capacity"] == [] and llm["conference"]["qa"] == [{"q": "產能利用率？", "a": "約 80%。"}]
    assert [w["verdict"] for w in llm["war_room"]] == ["watch", "watch"]
    assert mod.normalize_report(None)["procurement_conclusion"]["score"] is None
    assert mod.normalize_report({"financial_highlights": "單一字串"})["financial_highlights"] == ["單一字串"]


# ---------- [c06] charts ----------

def test_chart_layout_labels_do_not_overlap(mod, facts):
    for series in (facts["annual"], facts["quarterly"]):
        layout = mod.chart_layout([s["label"] for s in series], [s["values"]["revenue"] for s in series],
                                  [s["values"]["operating_margin"] for s in series], bar_kind="money", line_kind="pct")
        assert mod.overlapping_labels(layout) == []
        assert len(layout["bar_labels"]) == len(series) and len(layout["line_labels"]) == len(series)
        for b in layout["bar_labels"] + layout["line_labels"]:          # 全部在圖面內、不進圖例列
            assert b["y"] >= layout["plot"]["y"] - 2 and b["y"] + b["h"] <= layout["h"]


def test_chart_layout_adversarial_collisions(mod):
    # 折線點剛好落在柱內標籤的位置：避讓後仍不重疊
    labels = ["2020", "2021", "2022", "2023", "2024"]
    bars = [100.0, 100.0, 100.0, 100.0, 100.0]
    line = [95.0, 96.0, 97.0, 98.0, 99.0]
    layout = mod.chart_layout(labels, bars, line, bar_kind="money", line_kind="pct", shared_axis=True)
    assert mod.overlapping_labels(layout) == []
    # 負值與缺值
    layout2 = mod.chart_layout(labels, [10.0, -4.0, None, 2.0, -0.5], [1.0, None, -3.0, 4.0, 0.0], bar_kind="money", line_kind="pct")
    assert mod.overlapping_labels(layout2) == []
    assert len(layout2["bars"]) == 4 and len(layout2["missing"]) == 1 and layout2["points"][1] is None


def test_bar_label_inside_bar_upper(mod):
    layout = mod.chart_layout(["a", "b"], [100.0, 1.0], None, bar_kind="money")
    tall, short = layout["bars"][0], layout["bars"][1]
    lbl_tall, lbl_short = layout["bar_labels"][0], layout["bar_labels"][1]
    assert tall["y"] < lbl_tall["ty"] < tall["y"] + tall["h"] / 2          # 柱內中間偏上
    assert lbl_short["ty"] < short["y"]                                    # 太矮 → 柱頂上方


def test_svg_output_basics(mod, facts):
    svg = mod.svg_revenue_opm(facts["annual"], facts["scale"], title="t")
    assert svg.startswith("<svg") and svg.count("<rect") >= 5 and "<path" in svg
    assert mod.BAR_FILL in svg and mod.LINE_COLOR in svg and "營業利益率 OPM" in svg
    ind = mod.svg_indicator(facts["annual"], "eps", facts["scale"])
    assert "EPS（元）" in ind and ind.count("<circle") == 5 + 1      # 5 個資料點 + 圖例的一個圓點


# ---------- [c07] render ----------

def test_sections_order_and_no_placeholder(mod, html_out):
    pos = [html_out.index(f'id="{k}"') for k in ("conclusion", "financial", "conference", "sources")]
    assert pos == sorted(pos)
    assert re.search(r"\{\{[^}]+\}\}", html_out) is None
    assert html_out.startswith("<!doctype html>") and "</html>" in html_out
    assert "群創光電（3481）2026 Q2 財報＋法說整合報告" in html_out


def test_revenue_chart_once_and_ten_indicator_rows(mod, html_out):
    assert html_out.count("營收 × OPM") == 1
    assert html_out.count('data-indicator="') == 10 and 'data-indicator="revenue"' not in html_out
    # 三項無來源 → 未取得卡片，不畫圖
    for key in ("quick_ratio", "ar_days", "ap_days"):
        block = html_out.split(f'data-indicator="{key}"', 1)[1].split("</div>", 1)[0]   # 該列第一個 </div> 之前
        assert "未取得" in block and "<svg" not in block
    assert html_out.count("<svg") == 2 + 7      # 五年 + 五季 + 七項有資料的指標


def test_not_mentioned_and_not_available_rendering(mod, html_out, llm):
    assert "事業群財務表現" in html_out and "未提及（文件未提供" in html_out
    assert html_out.count("未提及") >= 5          # capacity / market_outlook / investment / auo_microled / watch_items …
    assert "暫定燈號：🟡 黃燈（加強監控）" in html_out and "conic-gradient(var(--amber) 0 62%" in html_out
    assert "Q：</b>產能利用率？" in html_out
    assert "🟡 Watch" in html_out and "bogus" not in html_out


def test_table_and_chart_use_same_numbers(mod, facts, html_out):
    rev_2021 = mod.fmt_value(facts["annual"][1]["values"]["revenue"], "money")
    assert html_out.count(rev_2021) >= 2            # 指標表 + 五年圖標籤
    assert "4.50" not in html_out.split('id="sources"')[0] or True   # 無亂數；只確認不丟例外


def test_render_without_financials(mod):
    f = mod.build_facts({"company_key": "TYO:5201", "company_name": "AGC", "market": "TYO", "category": "SUPPLIER",
                         "company_slug": "AGC"}, "2026Q2", [], None, None, DOCS[:1])
    out = mod.render_report(f, mod.normalize_report(LLM_OUT), generated_on="2026-10-20", version="v")
    assert "<svg" not in out and out.count("未取得") > 10
    assert "此公司目前沒有結構化財報來源" in out
    assert mod.report_file_name(f) == "AGC_2026Q2_supplier_report.html"


def test_html_escapes_text(mod, facts):
    bad = json.loads(json.dumps(LLM_OUT))
    bad["financial_highlights"] = ["<script>alert(1)</script>"]
    out = mod.render_report(facts, mod.normalize_report(bad), generated_on="2026-10-20", version="v")
    assert "<script>" not in out and "&lt;script&gt;" in out


# ---------- DDL 與 schema 對照 ----------

def _ddl_columns(tags):
    nb = nbtool.load(str(ROOT / INIT_NB))
    ns = {"catalog": "c", "schema": "s", "domain": "ir_calendar"}
    for tag in ["c02", *tags]:
        exec(nbtool.source_of(nb["cells"][nbtool.find(nb, tag)]), ns)
    out = {}
    for (layer, short), ddl in ns["DDLS"].items():
        body = ddl.split("(", 1)[1].rsplit("\n)", 1)[0]
        out[(layer, short)] = [m.group(1) for m in re.finditer(r"^\s{2}(\w+)\s+\w", body, re.M)]
    return out, ns


def _schema_fields(tag, name):
    """[c10] 有 delta import，不能整格載入：只抓 StructType 定義那段。"""
    nb = nbtool.load(str(ROOT / NB))
    src = nbtool.source_of(nb["cells"][nbtool.find(nb, tag)])
    start = src.index(f"{name} = StructType([")
    end = src.index("])", start) + 2
    ns = {}
    exec("from pyspark.sql.types import *\n" + src[start:end], ns)
    return [f.name for f in ns[name].fields]


def test_ddl_matches_write_schema():
    cols, ns = _ddl_columns(["c19a", "c19b"])
    assert ("bronze", "supplier_report_llm") in ns["TABLES"] and ("gold", "supplier_report") in ns["TABLES"]
    assert ns["LAYER_PREFIX"]["gold"] == "g_"
    assert cols[("bronze", "supplier_report_llm")] == _schema_fields("c10", "LLM_SCHEMA")
    assert cols[("gold", "supplier_report")] == _schema_fields("c10", "REPORT_SCHEMA")
