# ruff: noqa: E501 - 測試資料與斷言逐字對齊比寬度重要
"""ir_calendar_build_ir_report 的純函式 cell 測試（[c02]～[c07]）：facts 換算、工作清單（當季為準 / 只有彙整也產 / 補位預設關 / 來源雜湊 / 視角 supplier · peer · semi）、
prompt（依視角）/ JSON 解析、文件餵入狀態、SVG 標籤不重疊、
新版面（20261021）HTML 章節順序、爬蟲彙整與 LLM 的合併規則、「未取得 / 未提及」呈現；並比對建表 notebook [c19a] / [c19b] 的 DDL 欄位與 [c10] 的 schema。

financials 用假資料（台股仟元；含 2026-10-21 新版欄位 quick_ratio / dso_days / dpo_days / net_margin_parent）、
summary 用新版結構化欄位（management_views 六類 / business_segments / qa_highlights）、LLM 輸出用假 JSON；不呼叫任何端點。
"""

import json
import re

import pytest
from nbload import ROOT, load_cells, nbtool

NB = "jobs/ir_calendar/build_ir_report/notebook.ipynb"
INIT_NB = "jobs/ir_calendar/init_tables/notebook.ipynb"


@pytest.fixture(scope="module")
def mod(spark):  # 依賴 spark：cell 內的 F.* 要有 SparkContext
    return load_cells(NB, ["c02", "c03", "c03a", "c04", "c05", "c05a", "c06", "c06a", "c07", "c07a"], name="irreport")


# ---------- 測試資料 ----------

COMPANY = {"company_key": "TPE:3481", "company_name": "群創光電", "english_name": "Innolux", "stock_code": "3481",
           "market": "TPE", "category": "SUPPLIER", "company_slug": "Innolux", "industry": "光電", "ir_url": None}


def fin(period, ptype, **kw):
    base = {"company_key": "TPE:3481", "period": period, "period_type": ptype, "currency": "TWD", "unit": "thousand",
            "source": "MOPS", "seq": 36, "batch_id": "000040_20261022T090000", "source_urls": ["https://mops.twse.com.tw/x"],
            "revenue": None, "pretax_income": None, "net_income": None, "eps": None, "operating_cash_flow": None,
            "gross_margin": None, "operating_margin": None, "net_margin": None, "debt_ratio": None, "current_ratio": None,
            "operating_income": None, "total_assets": None, "total_liabilities": None, "capex": None, "derived": None,
            # 2026-10-21 新版欄位
            "pretax_margin": None, "net_margin_parent": None, "quick_ratio": None, "dso_days": None, "dpo_days": None,
            "operating_cash_flow_ytd": None}
    base.update(kw)
    return base


# 仟元：2.0e8 仟元 = 2,000 億。2020 年刻意沒有 net_margin_parent（舊批次）→ 退用 net_margin 並標合併口徑
ANNUAL = [fin(f"{y}FY", "annual", revenue=rev * 1e8, pretax_income=pre * 1e8, net_income=net * 1e8, eps=eps,
              operating_cash_flow=ocf * 1e8, gross_margin=gm, operating_margin=opm, net_margin=nm, debt_ratio=dr,
              current_ratio=cr, quick_ratio=qr, dso_days=dso, dpo_days=dpo, net_margin_parent=nmp)
          for y, rev, pre, net, eps, ocf, gm, opm, nm, dr, cr, qr, dso, dpo, nmp in [
              (2020, 2.73, 0.07, 0.03, 0.03, 0.40, 7.1, 0.3, 1.1, 48.2, 1.52, 1.01, 55.0, 60.0, None),
              (2021, 3.68, 0.70, 0.62, 6.44, 0.95, 24.0, 16.9, 16.8, 45.1, 1.70, 1.20, 50.2, 58.1, 16.5),
              (2022, 2.21, -0.33, -0.33, -3.43, 0.12, 2.5, -13.0, -14.9, 49.9, 1.40, 0.95, 61.3, 66.0, -14.5),
              (2023, 2.24, -0.22, -0.20, -2.08, 0.25, 5.4, -8.9, -8.9, 51.7, 1.35, 0.90, 58.8, 63.2, -8.6),
              (2024, 2.21, -0.03, -0.02, -0.25, 0.30, 7.8, -2.5, -1.1, 50.3, 1.44, 0.97, 57.0, 61.9, -1.0),
          ]] + [fin("2019FY", "annual", revenue=2.6e8, gross_margin=6.0, operating_margin=-1.0)]   # 第 6 年，應被切掉

QUARTERLY = [fin(p, "quarterly", revenue=rev * 1e8, gross_margin=gm, operating_margin=opm, net_income=net * 1e8,
                 net_margin=nm, eps=eps, current_ratio=cr, pretax_income=pre * 1e8, quick_ratio=qr,
                 operating_cash_flow=(ocf * 1e8 if ocf is not None else None))
             for p, rev, gm, opm, net, nm, eps, cr, pre, qr, ocf in [
                 ("2025Q1", 0.50, 6.1, -3.5, -0.03, -6.0, -0.30, 1.40, -0.03, 0.88, 0.05),
                 ("2025Q2", 0.55, 7.0, -1.0, -0.01, -1.8, -0.10, 1.42, -0.01, 0.90, 0.06),
                 ("2025Q3", 0.58, 8.2, 0.5, 0.01, 1.7, 0.10, 1.45, 0.01, 0.92, 0.07),
                 ("2025Q4", 0.52, 6.5, None, -0.02, -3.8, -0.20, 1.43, -0.02, 0.91, None),   # 推算列：無 OPM、無單季 OCF
                 ("2026Q1", 0.54, 7.9, 0.2, 0.00, 0.0, 0.00, 1.47, 0.00, 0.93, 0.04),
                 ("2026Q2", 0.60, 9.1, 1.8, 0.02, 3.3, 0.20, 1.50, 0.02, 0.99, 0.09),
             ]]

DOCS = [
    {"file_name": "Innolux_Q2CY26_Presentation.pdf", "doc_kind": "Presentation", "sha256": "a1", "source_url": "https://x/p.pdf",
     "text_chars": 30, "volume_path": "/Volumes/c/s/v/supplier/Innolux/Innolux_Q2CY26_Presentation.pdf", "fiscal_label": None,
     "doc_date": "2026-08-05", "text_md": "# Q2 2026 Results\n營收 600 億，毛利率 9.1%。" * 3},
    {"file_name": "Innolux_Q2CY26_Financial_Statements.pdf", "doc_kind": "Financial_Statements", "sha256": "b2", "source_url": None,
     "text_chars": 50000, "volume_path": "/Volumes/c/s/v/supplier/Innolux/Innolux_Q2CY26_Financial_Statements.pdf", "fiscal_label": None,
     "doc_date": "2026-08-12", "text_md": "合併財務報告 " * 10000},
]

# 爬蟲新版 summary（silver 一列 asDict 後的形狀）：六類只給四類（capacity / auo_topics 缺 → 由 LLM 補位 / 未提及），另有一條舊詞彙
SUMMARY = {
    "period": "2026Q2", "conference_date": "2026-08-05", "reported_period": "2026 Q2 及上半年", "guidance": "下半年審慎",
    "core_points": ["a"], "sources": [{"title": "法說簡報", "url": "https://x/p.pdf", "media": "MOPS"}], "notes": "簡報 PDF 文字抽取",
    "management_views": [
        {"topic": "事業體／產品線重點", "view": "車用顯示器營收年增兩成，占比升至 35%。"},
        {"topic": "獲利能力變化", "view": "Q2 毛利率 9.1%，本業轉正。"},
        {"topic": "未來市場預測", "view": "下半年需求審慎，Q3 出貨持平。"},
        {"topic": "投資／M&A／組織整改", "view": "無新投資案。"},
        {"topic": "本業需求", "view": "舊詞彙的一條"},
    ],
    "business_segments": [
        {"segment": "車用顯示", "revenue": "NT$210 億", "revenue_yoy": "+20%", "operating_margin": "12%", "opm_yoy": "+3 pt", "note": "簡報 p.5"},
        {"segment": "IT 顯示", "revenue": None, "revenue_yoy": None, "operating_margin": "-2%", "opm_yoy": None, "note": None},
    ],
    "qa_highlights": [{"question": "產能利用率？", "answer": "約 80%。"}],
    "positive_signals": ["p1"], "watch_items": ["w1"], "open_questions": [],
}

LLM_OUT = {
    "conclusion": "營收回升但本業僅小幅轉正（財報數據）。負債比 50%。",
    "confirmed_facts": ["2026Q2 營收 600 億（財報數據）"], "management_outlook": ["下半年需求審慎（Innolux_Q2CY26_Presentation.pdf）"],
    "actions": [{"area": "成本與議價", "advice": "議價時留意毛利率回升"}, {"area": "其他", "advice": "x"}],
    "financial_highlights": ["毛利率 9.1%（財報數據）"],
    "segments": [{"segment": "LLM 事業群", "revenue": "NT$1 億", "revenue_yoy": None, "operating_margin": None, "opm_yoy": None, "note": "只在彙整缺時用"}],
    "conference": {"business_lines": ["LLM 的事業體（彙整已有，應不採用）"], "capacity": ["新廠 2027 投產"], "profitability": [],
                   "market_outlook": [], "investment_ma_org": [], "auo_topics": [], "qa": [{"q": "LLM 問", "a": "LLM 答"}]},
    "sources_used": ["Innolux_Q2CY26_Presentation.pdf"],
    "caveats": ["財報本體已截尾"],
}


@pytest.fixture(scope="module")
def facts(mod):
    return mod.build_facts(COMPANY, "2026Q2", ANNUAL + QUARTERLY, SUMMARY, {"conference_date": "2026-08-05"}, DOCS)


@pytest.fixture(scope="module")
def llm(mod):
    return mod.normalize_report(LLM_OUT)


@pytest.fixture(scope="module")
def html_out(mod, facts, llm):
    return mod.render_report(facts, llm, generated_on="2026-10-21", version="template 20261021 / prompt 2.0")


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


def test_fmt_delta(mod):
    assert mod.fmt_delta(110.0, 100.0, "money") == "+10.0%"
    assert mod.fmt_delta(1.8, -1.0, "pct") == "+2.80 pt"
    assert mod.fmt_delta(1.5, 1.42, "ratio") == "+0.08x"
    assert mod.fmt_delta(5.0, -2.0, "money") == "轉正（基期為負）"
    assert mod.fmt_delta(None, 1.0, "money") == "未取得"


def test_annual_series_last_five_new_fields_and_fallback(mod, facts):
    annual = facts["annual"]
    assert [s["period"] for s in annual] == ["2020FY", "2021FY", "2022FY", "2023FY", "2024FY"]
    assert annual[1]["values"]["revenue"] == pytest.approx(3680.0)          # 3.68e8 仟元 → 3,680 億
    assert annual[1]["values"]["pretax_margin"] == pytest.approx(0.70 / 3.68 * 100, rel=1e-6)   # 欄位 NULL → 推算
    assert annual[1]["values"]["quick_ratio"] == 1.20 and annual[1]["values"]["ar_days"] == 50.2 and annual[1]["values"]["ap_days"] == 58.1
    assert annual[1]["values"]["net_margin_parent"] == 16.5 and annual[1]["values"]["_fallback"] == []
    assert annual[0]["values"]["net_margin_parent"] == 1.1 and annual[0]["values"]["_fallback"] == ["net_margin_parent"]
    assert facts["net_margin_fallback_years"] == ["2020FY"]


def test_quarter_series_window_and_actuals(mod, facts):
    assert [s["period"] for s in facts["quarterly"]] == ["2025Q2", "2025Q3", "2025Q4", "2026Q1", "2026Q2"]
    cols = facts["actuals"]["columns"]
    assert [c["period"] for c in cols] == ["2026Q2", "2025Q2"] and [c["tag"] for c in cols] == ["本季", "去年同季"]
    assert cols[0]["values"]["revenue"] == pytest.approx(600.0)        # 0.60e8 仟元 = 600 億
    assert cols[0]["values"]["quick_ratio"] == 0.99 and cols[0]["values"]["operating_cash_flow"] == pytest.approx(90.0)
    assert [m["key"] for m in facts["actuals"]["metrics"]] == ["revenue", "operating_margin", "eps", "operating_cash_flow", "current_ratio", "quick_ratio"]
    kpi = facts["kpis"]
    assert kpi[0]["value"] == "NT$ 600.00 億" and kpi[0]["note"].startswith("YoY +9.09%") and kpi[0]["tone"] == "green"
    assert kpi[1]["value"] == "1.80%" and "+2.80 pt" in kpi[1]["note"] and kpi[1]["tone"] == "green"


def test_indicator_availability_all_eleven(mod, facts):
    av = facts["indicator_avail"]
    assert all(av[i["key"]] for i in mod.INDICATORS)
    f2 = mod.build_facts(COMPANY, "2026Q2", [fin("2024FY", "annual", revenue=1e8, gross_margin=5.0)], None, None, [])
    assert not f2["indicator_avail"]["quick_ratio"] and not f2["indicator_avail"]["ar_days"] and f2["indicator_avail"]["revenue"]


def test_facts_dates_and_summary_fields(mod, facts):
    assert facts["conference_date"] == "2026-08-05" and facts["report_date"] == "2026-08-12"
    assert facts["reported_period"] == "2026 Q2 及上半年" and facts["summary_period"] == "2026Q2"
    assert set(facts["summary_views"]) == {"business_lines", "profitability", "market_outlook", "investment_ma_org", "_other"}
    assert facts["summary_views"]["_other"] == ["本業需求：舊詞彙的一條"]
    assert [s["segment"] for s in facts["summary_segments"]] == ["車用顯示", "IT 顯示"] and facts["summary_segments"][1]["revenue"] is None
    assert facts["summary_qa"] == [{"q": "產能利用率？", "a": "約 80%。"}]
    assert facts["financial_batch"] == ["000040_20261022T090000"]


def test_facts_without_financials(mod):
    f = mod.build_facts({"company_key": "TYO:5201", "company_name": "AGC", "market": "TYO", "category": "SUPPLIER"},
                        "2026Q2", [], None, None, DOCS[:1])
    assert not f["has_financials"] and f["annual"] == [] and f["quarterly"] == []
    assert all(k["value"] == "未取得" for k in f["kpis"])
    assert f["conference_date"] is None and f["reported_period"] is None and f["summary_views"] == {}
    txt = mod.facts_to_prompt_text(f)
    assert "未取得" in txt and "必須來自下方文件" in txt


def test_prompt_text_lists_numbers_and_summary(mod, facts):
    txt = mod.facts_to_prompt_text(facts)
    assert "2024FY |" in txt and "2026Q2 |" in txt and "速動比" in txt
    assert "展望：下半年審慎" in txt and "經營層觀點［事業體／產品線重點］" in txt
    assert "事業群［車用顯示］：營收 NT$210 億（YoY +20%）" in txt and "Q&A：產能利用率？" in txt
    assert "法說報告期間（公司口徑）：2026 Q2 及上半年" in txt
    assert "報告會直接採用上列彙整的主題" in txt


# ---------- [c04] work plan ----------

def _doc(ck, period, kind, sha, slug="Innolux", cat="SUPPLIER"):
    return {"company_key": ck, "company_slug": slug, "category": cat, "period": period, "doc_kind": kind, "sha256": sha,
            "volume_path": f"/Volumes/c/s/v/{cat.lower()}/{slug}/{slug}_{period}_{kind}.pdf", "parsed_at": None}


# 南亞實例（2026-10-28 檢討）：Q3 只有 10-13 法說簡報；Q2 有財報 + 簡報；Q1 只有財報
NANYA = [
    _doc("TPE:1303", "2026Q3", "Presentation", "p3", slug="Nan-Ya"),
    _doc("TPE:1303", "2026Q2", "Financial_Statements", "f2", slug="Nan-Ya"),
    _doc("TPE:1303", "2026Q2", "Presentation", "p2", slug="Nan-Ya"),
    _doc("TPE:1303", "2026Q1", "Financial_Statements", "f1", slug="Nan-Ya"),
]


def _by_period(docs):
    out = {}
    for d in docs:
        out.setdefault(d["period"], []).append(d)
    return out


def test_plan_docs_carries_missing_group_from_previous_period(mod):
    by_p = _by_period(NANYA)
    got = mod.plan_docs("2026Q3", by_p, lookback=2)
    assert [(d["period"], d["doc_kind"], d["carried"]) for d in got] == [("2026Q3", "Presentation", False), ("2026Q2", "Financial_Statements", True)]
    q2 = mod.plan_docs("2026Q2", by_p, 2)                                   # 兩類都有 → 不補
    assert len(q2) == 2 and not any(d["carried"] for d in q2)
    assert len(mod.plan_docs("2026Q3", by_p, 0)) == 1                       # lookback 0 → 不補
    q4 = mod.plan_docs("2026Q4", by_p, 2)                                   # 本期沒文件：財報取最近的 Q2、法說取 Q3
    assert sorted((d["period"], d["doc_kind"]) for d in q4) == [("2026Q2", "Financial_Statements"), ("2026Q3", "Presentation")]
    assert [d["doc_kind"] for d in mod.plan_docs("2026Q1", by_p, 1)] == ["Financial_Statements"]   # 往前 1 期沒法說 → 不補
    assert mod.doc_group("Earnings_Transcript") == "conference" and mod.doc_group("Financial_Statements") == "financial" and mod.doc_group("x") is None


def test_pick_summary_period_and_source_digest(mod):
    assert mod.pick_summary_period("2026Q3", ["2026Q2", "2026Q3"]) == "2026Q3"
    assert mod.pick_summary_period("2026Q3", ["2026Q1", "2026Q2", "2026Q4"]) is None       # 2026-10-29：只用同期，不退用前期、不拿後一期
    assert mod.pick_summary_period("2026Q3", ["2026Q4"]) is None and mod.pick_summary_period("2026Q3", []) is None
    docs = [{"sha256": "b"}, {"sha256": "a"}]
    d1 = mod.source_digest(docs, "000010", 1)
    assert d1 == mod.source_digest(list(reversed(docs)), "000010", 1)       # 文件順序無關
    assert d1 != mod.source_digest(docs, "000011", 1)                       # 彙整換批次 → 重做
    assert d1 != mod.source_digest(docs, "000010", 2)                       # 場次改版 → 重做
    assert d1 != mod.source_digest(docs[:1], "000010", 1)                   # 文件增減 → 重做
    assert mod.source_digest(docs, None, None) != d1


def test_build_work_current_period_only_and_done_filter(mod):
    """預設 lookback = 0：南亞 2026Q3 只帶 Q3 簡報；Q2 彙整不退用；Q3 彙整有才用。"""
    sm_q2 = [{"company_key": "TPE:1303", "period": "2026Q2", "batch_id": "000010", "category": "SUPPLIER"}]
    sm_q3 = sm_q2 + [{"company_key": "TPE:1303", "period": "2026Q3", "batch_id": "000011", "category": "SUPPLIER"}]
    conf = [{"company_key": "TPE:1303", "period": "2026Q3", "revision": 1}, {"company_key": "TPE:1303", "period": "2026Q3", "revision": 2}]
    kw = dict(views=["supplier"], periods=[], prompt_versions=mod.PROMPT_VERSIONS, template_version=mod.TEMPLATE_VERSION, force=False, lookback=0)
    work = mod.build_work(NANYA, sm_q2, conf, [], **kw)
    assert len(work) == 1
    w = work[0]
    assert w["period"] == "2026Q3" and w["source_periods"] == ["2026Q3"] and w["doc_count"] == 1 and w["doc_kinds"] == ["Presentation"]
    assert w["summary_period"] is None and w["summary_batch_id"] is None and w["conference_revision"] == 2   # Q2 彙整不混進 Q3
    assert w["company_slug"] == "Nan-Ya" and w["category"] == "SUPPLIER" and w["doc_paths"] == [NANYA[0]["volume_path"]]
    assert w["report_kind"] == "supplier" and w["topics"] == []
    assert set(w) == set(mod.WORK_COLS)
    w3 = mod.build_work(NANYA, sm_q3, conf, [], **kw)[0]
    assert w3["summary_period"] == "2026Q3" and w3["summary_batch_id"] == "000011" and w3["docs_digest"] != w["docs_digest"]   # 同期彙整到了 → 重做
    done = [{"company_key": "TPE:1303", "period": "2026Q3", "report_kind": "supplier", "docs_digest": w3["docs_digest"],
             "prompt_version": mod.PROMPT_VERSIONS["supplier"], "template_version": mod.TEMPLATE_VERSION}]
    assert mod.build_work(NANYA, sm_q3, conf, done, **kw) == []                                       # 來源沒變 → 跳過
    sm_q3b = sm_q2 + [{"company_key": "TPE:1303", "period": "2026Q3", "batch_id": "000012", "category": "SUPPLIER"}]
    assert len(mod.build_work(NANYA, sm_q3b, conf, done, **kw)) == 1                                  # 彙整換批次 → 重做（D2-3）
    new_doc = NANYA + [_doc("TPE:1303", "2026Q3", "Financial_Statements", "f3", slug="Nan-Ya")]
    assert mod.build_work(new_doc, sm_q3, conf, done, **kw)[0]["doc_count"] == 2                      # 新文件進來 → 重做
    assert len(mod.build_work(NANYA, sm_q3, conf, done, **{**kw, "force": True})) == 1
    assert len(mod.build_work(NANYA, sm_q3, conf, done, **{**kw, "template_version": "20261021"})) == 1   # 版型升版 → 重做
    assert len(mod.build_work(NANYA, sm_q3, conf, done, **{**kw, "prompt_versions": {"supplier": "9.9"}})) == 1   # 該視角 prompt 升版 → 重做
    old_done = [{**done[0], "report_kind": None}]                                                        # 10-29 前的 gold 列沒有 report_kind → 視為 supplier
    assert mod.build_work(NANYA, sm_q3, conf, old_done, **kw) == []
    w_all = mod.build_work(NANYA, sm_q2, conf, [], **{**kw, "periods": ["2026Q1", "2026Q2", "2026Q4"]})
    assert [(x["period"], x["doc_count"], x["summary_period"]) for x in w_all] == [("2026Q1", 1, None), ("2026Q2", 2, "2026Q2")]   # Q4 沒來源 → 不做
    assert mod.build_work([], [], conf, [], **kw) == []


def test_company_views_and_multi_view_work(mod):
    """視角（2026-10-29）：分類預設 + override；一家多視角 → 一視角一列、各自 done；友達不產 peer；CUSTOMER 沒有視角。"""
    assert mod.company_views("TPE:1303", "SUPPLIER") == {"supplier": []}
    assert mod.company_views("TPE:2330", "SUPPLIER") == {"supplier": [], "semi": ["A", "C"]}          # 台積電：供應商 + 半導體
    assert mod.company_views("TPE:3481", "PANEL_PEER") == {"peer": [], "semi": ["A"]}                   # 群創：同業 + FOPLP 對標
    assert mod.company_views("TPE:2409", "PANEL_PEER") == {}                                            # 友達自己只當對照基準
    assert mod.company_views("NASDAQ:NVDA", "SEMI") == {"semi": ["A", "C"]} and mod.company_views("SZ:300308", "SEMI") == {"semi": ["B"]}
    assert mod.company_views("HK:992", "CUSTOMER") == {} and mod.company_views("X:1", None) == {}
    assert set(mod.VIEW_OVERRIDES) == {"TPE:2330", "NYSE:GLW", "TPE:3714", "TPE:3481", "TPE:6770", "TPE:2454", "TPE:6854", "TPE:2303"}
    for ck, vs in mod.VIEW_OVERRIDES.items():
        for v, topics in vs.items():
            assert v in mod.REPORT_VIEWS and set(topics) <= set(mod.SEMI_TOPICS), (ck, v)
    assert set(mod.PROFILES) == set(mod.REPORT_VIEWS) == set(mod.PROMPT_VERSIONS)
    for p in mod.PROFILES.values():
        assert len(p["dimensions"]) == 4 and {"report", "conclusion", "actions", "actions_note", "observe"} <= set(p["titles"])

    tsmc = [_doc("TPE:2330", "2026Q3", "Presentation", "t3", slug="TSMC"), _doc("TPE:2330", "2026Q3", "Financial_Statements", "tf3", slug="TSMC")]
    kw = dict(views=list(mod.REPORT_VIEWS), periods=[], prompt_versions=mod.PROMPT_VERSIONS, template_version=mod.TEMPLATE_VERSION, force=False, lookback=0)
    work = mod.build_work(tsmc + NANYA, [], [], [], **kw)
    assert [(w["company_key"], w["report_kind"], w["topics"]) for w in work] == [
        ("TPE:1303", "supplier", []), ("TPE:2330", "supplier", []), ("TPE:2330", "semi", ["A", "C"])]      # 依視角排序；同雜湊兩列
    assert work[1]["docs_digest"] == work[2]["docs_digest"] and work[1]["doc_count"] == 2
    done = [{"company_key": "TPE:2330", "period": "2026Q3", "report_kind": "supplier", "docs_digest": work[1]["docs_digest"],
             "prompt_version": mod.PROMPT_VERSIONS["supplier"], "template_version": mod.TEMPLATE_VERSION}]
    left = mod.build_work(tsmc, [], [], done, **kw)
    assert [w["report_kind"] for w in left] == ["semi"]                                                 # supplier 做過、semi 還沒
    assert [w["report_kind"] for w in mod.build_work(tsmc, [], [], done, **{**kw, "views": ["supplier"]})] == []
    assert [w["report_kind"] for w in mod.build_work(tsmc, [], [], [], **{**kw, "views": ["peer"]})] == []
    auo = [_doc("TPE:2409", "2026Q3", "Presentation", "a3", slug="AUO", cat="PANEL_PEER")]
    innolux = [_doc("TPE:3481", "2026Q3", "Presentation", "i3", slug="Innolux", cat="PANEL_PEER")]
    assert [(w["company_key"], w["report_kind"]) for w in mod.build_work(auo + innolux, [], [], [], **kw)] == [("TPE:3481", "peer"), ("TPE:3481", "semi")]


def test_build_work_summary_only_and_next_period(mod):
    """當季只有爬蟲彙整、沒有任何已解析文件：也要產（0 檔）；下一季任一來源出現就換期。"""
    sm = [{"company_key": "TPE:1763", "period": "2026Q3", "batch_id": "000011", "category": "SUPPLIER"}]
    kw = dict(views=["supplier"], periods=[], prompt_versions=mod.PROMPT_VERSIONS, template_version=mod.TEMPLATE_VERSION, force=False, lookback=0)
    w = mod.build_work([], sm, [], [], **kw)
    assert len(w) == 1 and w[0]["company_key"] == "TPE:1763" and w[0]["period"] == "2026Q3"
    assert w[0]["doc_count"] == 0 and w[0]["doc_paths"] == [] and w[0]["doc_kinds"] == [] and w[0]["source_periods"] == ["2026Q3"]
    assert w[0]["summary_batch_id"] == "000011" and w[0]["company_slug"] is None and w[0]["category"] == "SUPPLIER"
    # 南亞：文件最新 Q3，但 Q4 彙整先到 → 期別前進到 Q4、只用 Q4 彙整（Q3 簡報不帶）
    sm_q4 = [{"company_key": "TPE:1303", "period": "2026Q4", "batch_id": "000020", "category": "SUPPLIER"}]
    w4 = mod.build_work(NANYA, sm_q4, [], [], **kw)
    assert [(x["period"], x["doc_count"], x["summary_period"]) for x in w4] == [("2026Q4", 0, "2026Q4")]
    # 只有場次（日期）沒有內容的期別不觸發
    conf_q4 = [{"company_key": "TPE:1303", "period": "2026Q4", "revision": 1}]
    assert [x["period"] for x in mod.build_work(NANYA, [], conf_q4, [], **kw)] == ["2026Q3"]


def test_build_work_lookback_opt_in(mod):
    """lookback_quarters > 0 時才補前期文件；補位不會讓期別前進。"""
    sm = [{"company_key": "TPE:1303", "period": "2026Q2", "batch_id": "000010", "category": "SUPPLIER"}]
    kw = dict(views=["supplier"], periods=[], prompt_versions=mod.PROMPT_VERSIONS, template_version=mod.TEMPLATE_VERSION, force=False, lookback=2)
    w = mod.build_work(NANYA, sm, [], [], **kw)[0]
    assert w["period"] == "2026Q3" and w["source_periods"] == ["2026Q2", "2026Q3"] and w["doc_count"] == 2
    assert w["doc_kinds"] == ["Financial_Statements", "Presentation"] and w["summary_period"] is None   # 文件可補位，彙整仍只用同期
    w_all = mod.build_work(NANYA, sm, [], [], **{**kw, "periods": ["2026Q4"]})
    assert [(x["period"], x["doc_count"]) for x in w_all] == [("2026Q4", 2)]                           # 指定期別：補得到前期文件就做


def _text_rows(spark, docs_status):
    return spark.createDataFrame([(d["company_key"], d["company_slug"], d["category"], d["period"], d["doc_kind"], d["sha256"],
                                   d["volume_path"], None, st) for d, st in docs_status],
                                 "company_key string, company_slug string, category string, period string, doc_kind string, "
                                 "sha256 string, volume_path string, parsed_at timestamp, parse_status string")


def test_select_work_spark_end_to_end(mod, spark):
    df_text = _text_rows(spark, [(d, "success") for d in NANYA] + [
        (_doc("NYSE:GLW", "2026Q2", "Press_Release", "e", slug="Corning"), "partial"),
        (_doc("TPE:1303", "2026Q3", "Earnings_Transcript", "bad", slug="Nan-Ya"), "failed"),     # 失敗不算
        (_doc("HK:1070", "2026Q2", "Presentation", "f", slug="TCL", cat="CUSTOMER"), "success"),
    ])
    df_report = spark.createDataFrame([], "company_key string, period string, docs_digest string, prompt_version string, template_version string")
    df_sm = spark.createDataFrame([
        ("TPE:1303", "SUPPLIER", "2026Q2", "000010", None),
        ("TPE:1303", "SUPPLIER", "2026Q3", "000011", None),
        ("TPE:1763", "SUPPLIER", "2026Q3", "000011", None),          # 只有彙整、沒有文件 → 也要產
        ("HK:1070", "CUSTOMER", "2026Q3", "000011", None),           # 分類外
        ("TPE:1303", "SUPPLIER", "bad", "000011", None),             # 期別不合法
    ], "company_key string, category string, period string, batch_id string, updated_at timestamp")
    df_conf = spark.createDataFrame([("TPE:1303", "2026Q3", 1)], "company_key string, period string, revision int")
    kw = dict(periods=[], prompt_versions=mod.PROMPT_VERSIONS, template_version=mod.TEMPLATE_VERSION, force=False, lookback=0)
    work = mod.select_work(df_text, df_report, df_sm, df_conf, views=["supplier"], company_keys=[], **kw)
    assert [(w["company_key"], w["period"], w["doc_count"], w["summary_period"]) for w in work] == [
        ("NYSE:GLW", "2026Q2", 1, None), ("TPE:1303", "2026Q3", 1, "2026Q3"), ("TPE:1763", "2026Q3", 0, "2026Q3")]
    assert work[1]["summary_batch_id"] == "000011" and work[1]["conference_revision"] == 1 and work[2]["company_slug"] is None
    assert mod.select_work(df_text, df_report, df_sm, df_conf, views=["peer"], company_keys=["TPE:1303"], **kw) == []      # 南亞沒有 peer 視角
    assert [w["company_key"] for w in mod.select_work(df_text, df_report, df_sm, df_conf, views=["supplier"], company_keys=["TPE:1763"], **kw)] == ["TPE:1763"]
    allv = mod.select_work(df_text, df_report, df_sm, df_conf, views=list(mod.REPORT_VIEWS), company_keys=[], **kw)
    assert [(w["company_key"], w["report_kind"]) for w in allv] == [
        ("NYSE:GLW", "supplier"), ("TPE:1303", "supplier"), ("TPE:1763", "supplier"), ("NYSE:GLW", "semi")]   # 康寧另掛 semi；HK:1070 CUSTOMER 沒視角
    assert allv[3]["topics"] == ["A", "B"]
    # gold 已有 report_kind 欄且 supplier 做過 → 只剩 semi
    df_report2 = spark.createDataFrame([("NYSE:GLW", "2026Q2", allv[0]["docs_digest"], mod.PROMPT_VERSIONS["supplier"], mod.TEMPLATE_VERSION, "supplier")],
                                       "company_key string, period string, docs_digest string, prompt_version string, template_version string, report_kind string")
    assert [w["report_kind"] for w in mod.select_work(df_text, df_report2, df_sm, df_conf, views=list(mod.REPORT_VIEWS), company_keys=["NYSE:GLW"], **kw)] == ["semi"]


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
    assert mod.PROMPT_VERSIONS["supplier"] == "2.2" and "AUO 相關議題" in mod.SYSTEM_PROMPT and "燈號" not in mod.SYSTEM_PROMPT
    assert "前期文件" in mod.SYSTEM_PROMPT and "期別 2026Q2" in p and "前期文件" not in p      # DOCS 沒標 carried
    assert mod.SYSTEM_PROMPT == mod.build_system_prompt("supplier") and "採購部門" in mod.SYSTEM_PROMPT and '"actions"' in mod.SYSTEM_PROMPT
    assert "procurement_actions" not in mod.SYSTEM_PROMPT and "題目標籤" not in p                  # supplier 沒有題目標籤


def test_system_prompt_per_view_and_semi_topics(mod, facts):
    """視角 prompt：角色 / 四面向 / 第六主題提示依 PROFILES；semi 的題目標籤進 user prompt。"""
    peer, semi = mod.build_system_prompt("peer"), mod.build_system_prompt("semi")
    assert "策略與競爭情報分析師" in peer and "威脅、機會、技術與產能須跟進項、客戶與價格面的應對" in peer and "同業競爭對照" in peer
    assert "新事業與策略分析師" in semi and "市場窗口、技術門檻與對標、潛在客戶或夥伴、競爭威脅" in semi and "新事業產業雷達" in semi
    for sp in (peer, semi):                                                                           # v2：各自的 JSON，不是供應商的 conference 結構
        assert "## 輸出 JSON 結構" in sp and "## 共同規則" in sp and '"implications"' in sp and '"conference"' not in sp and "{{" not in sp and "}}" not in sp
        assert "採購" not in sp
    f = {**facts, "report_kind": "semi", "topics": ["A", "C"]}
    p = mod.build_user_prompt(f, [], [])
    assert "本公司對友達的題目標籤：A＝封裝／載板" in p and "C＝景氣風向" in p and "（本期沒有可用的文件全文）" in p
    assert mod.topics_prompt_text({**facts, "topics": ["Z"]}) == "" and mod.topics_prompt_text(facts) == ""


def test_pack_documents_period_carried_and_feed_status(mod, facts):
    docs = [{**DOCS[0], "period": "2026Q3", "carried": False},
            {**DOCS[1], "period": "2026Q2", "carried": True},
            {**DOCS[0], "file_name": "Old_Pres.pdf", "period": "2026Q2", "carried": True}]
    packed, skipped = mod.pack_documents(docs, max_doc_chars=5000, max_total_chars=20000)
    # 同一優先序內本期先於前期補位；財報本體最後
    assert [(p["file_name"], p["period"], p["carried"]) for p in packed] == [
        (DOCS[0]["file_name"], "2026Q3", False), ("Old_Pres.pdf", "2026Q2", True), (DOCS[1]["file_name"], "2026Q2", True)]
    prompt = mod.build_user_prompt(facts, packed, skipped)
    assert f"## 文件：{DOCS[1]['file_name']}（Financial_Statements；期別 2026Q2；前期文件；已截尾）" in prompt
    assert f"## 文件：{DOCS[0]['file_name']}（Presentation；期別 2026Q3）" in prompt
    fed = mod.doc_feed_status(docs, packed, skipped)
    assert [(x["file_name"], x["fed"]) for x in fed] == [(DOCS[0]["file_name"], "full"), (DOCS[1]["file_name"], "truncated"), ("Old_Pres.pdf", "full")]
    assert fed[0]["chars_fed"] == len(DOCS[0]["text_md"]) and fed[1]["chars_fed"] == 5000 and fed[1]["period"] == "2026Q2"
    packed2, skipped2 = mod.pack_documents(docs, max_doc_chars=5000, max_total_chars=200)
    fed2 = {x["file_name"]: x for x in mod.doc_feed_status(docs, packed2, skipped2)}
    assert fed2[DOCS[1]["file_name"]] == {"file_name": DOCS[1]["file_name"], "period": "2026Q2", "doc_kind": "Financial_Statements", "fed": "skipped", "chars_fed": 0}


def test_facts_and_render_with_carried_docs(mod, llm):
    """南亞型：本期 2026Q3 只有簡報，財報是 2026Q2 的前期補位；彙整也是 Q2 的。"""
    docs = [{**DOCS[0], "period": "2026Q3", "carried": False}, {**DOCS[1], "period": "2026Q2", "carried": True}]
    f = mod.build_facts(COMPANY, "2026Q3", ANNUAL + QUARTERLY, {**SUMMARY, "period": "2026Q2"}, None, docs)
    assert f["source_periods"] == ["2026Q2", "2026Q3"] and f["carried_docs"] == [DOCS[1]["file_name"]]
    assert f["report_date"] == "2026-08-12" and f["report_date_period"] == "2026Q2"
    assert f["conference_date"] is None                                     # 前期彙整的法說日不是本期的
    assert [d["carried"] for d in f["docs"]] == [False, True]
    txt = mod.facts_to_prompt_text(f)
    assert "前期補位" in txt and DOCS[1]["file_name"] in txt and "必須標明期別" in txt
    f["docs_fed"] = [{"file_name": DOCS[0]["file_name"], "period": "2026Q3", "doc_kind": "Presentation", "fed": "full", "chars_fed": 90},
                     {"file_name": DOCS[1]["file_name"], "period": "2026Q2", "doc_kind": "Financial_Statements", "fed": "skipped", "chars_fed": 0}]
    out = mod.render_report(f, llm, generated_on="2026-10-28", version="v")
    assert "財報公布：2026-08-12（2026 Q2 財報；本期財報尚未公布）" in out
    assert "前期補位 2026 Q2" in out and "LLM 已讀全文" in out and "因長度上限未餵給 LLM</b>" in out
    assert f"因長度上限未餵給 LLM 的文件：{DOCS[1]['file_name']}" in out and "前期補位：本期尚無部分類型的文件" in out
    assert '法說會：<span class="na">未取得' in out and "彙整期別與本報告期別不同" in out
    f["docs_fed"][1] = {**f["docs_fed"][1], "fed": "truncated", "chars_fed": 40000}
    out2 = mod.render_report(f, llm, generated_on="2026-10-28", version="v")
    assert "LLM 已讀前 40,000 字" in out2 and "因長度上限未餵給 LLM 的文件" not in out2
    # 沒標期別的舊呼叫端：一律視為本期，不會標前期
    f3 = mod.build_facts(COMPANY, "2026Q2", ANNUAL + QUARTERLY, SUMMARY, None, DOCS)
    assert f3["carried_docs"] == [] and f3["source_periods"] == ["2026Q2"] and "period" not in DOCS[0]


def test_facts_prompt_and_render_summary_only(mod, llm):
    """當季只有爬蟲彙整、沒有任何已解析文件（2026-10-29 定案）：facts / prompt / HTML 都走得完，來源節與限制註明。"""
    f = mod.build_facts(COMPANY, "2026Q2", ANNUAL + QUARTERLY, SUMMARY, None, [])
    assert f["docs"] == [] and f["carried_docs"] == [] and f["report_date"] is None and f["report_date_period"] is None
    assert f["source_periods"] == ["2026Q2"] and f["summary_period"] == "2026Q2" and f["conference_date"] == "2026-08-05"
    packed, skipped = mod.pack_documents([], max_doc_chars=5000, max_total_chars=6000)
    assert (packed, skipped) == ([], [])
    p = mod.build_user_prompt(f, packed, skipped)
    assert "（本期沒有可用的文件全文）" in p and "前期補位" not in p and "2026Q2 |" in p
    f["docs_fed"] = mod.doc_feed_status([], packed, skipped)
    assert f["docs_fed"] == []
    out = mod.render_report(f, llm, generated_on="2026-10-29", version="v")
    assert "本期尚無已解析的財報 / 法說文件" in out and "本期尚無已解析文件：LLM 沒有讀到任何本期文件原文" in out
    assert "前期補位" not in out and "彙整期別與本報告期別不同" not in out and "因長度上限未餵給 LLM 的文件" not in out
    # 有文件時不會出現「尚無文件」字樣
    f2 = mod.build_facts(COMPANY, "2026Q2", ANNUAL + QUARTERLY, SUMMARY, None, DOCS)
    f2["docs_fed"] = mod.doc_feed_status(DOCS, *mod.pack_documents(DOCS, max_doc_chars=5000, max_total_chars=6000))
    assert "本期尚無已解析" not in mod.render_report(f2, llm, generated_on="2026-10-29", version="v")


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
    assert llm["conclusion"].startswith("營收回升")
    assert [a["area"] for a in llm["actions"]][:4] == mod.ACTION_AREAS == mod.PROFILES["supplier"]["dimensions"]
    assert llm["actions"][1]["advice"] == "議價時留意毛利率回升" and llm["actions"][0]["advice"] == ""
    assert llm["actions"][-1] == {"area": "其他", "advice": "x"}
    legacy = mod.normalize_report({"procurement_actions": [{"area": "付款條件", "advice": "舊鍵"}]})      # prompt 2.1 以前的 gold llm_json
    assert legacy["actions"][2] == {"area": "付款條件", "advice": "舊鍵"} and "procurement_actions" not in legacy
    peer = mod.normalize_report({"implications": [{"area": "機會", "judgement": "對手退出 LCD"}]}, "peer")     # v2：actions 由 implications 映射
    assert [a["area"] for a in peer["actions"]] == mod.PROFILES["peer"]["dimensions"] and peer["actions"][1]["advice"] == "對手退出 LCD"
    assert llm["segments"] == [{"segment": "LLM 事業群", "revenue": "NT$1 億", "revenue_yoy": None, "operating_margin": None, "opm_yoy": None, "note": "只在彙整缺時用"}]
    assert llm["conference"]["capacity"] == ["新廠 2027 投產"] and llm["conference"]["auo_topics"] == []
    assert llm["conference"]["qa"] == [{"q": "LLM 問", "a": "LLM 答"}]
    assert set(llm["conference"]) == set(mod.CONF_KEYS)
    empty = mod.normalize_report(None)
    assert empty["conclusion"] == "" and empty["segments"] == [] and len(empty["actions"]) == 4
    assert mod.normalize_report({"financial_highlights": "單一字串"})["financial_highlights"] == ["單一字串"]


# ---------- [c06] charts ----------

def test_chart_layout_labels_do_not_overlap(mod, facts):
    for series in (facts["annual"], facts["quarterly"]):
        layout = mod.chart_layout([s["label"] for s in series], [s["values"]["revenue"] for s in series],
                                  [s["values"]["operating_margin"] for s in series], bar_kind="money", line_kind="pct")
        assert mod.overlapping_labels(layout) == []
        assert len(layout["bar_labels"]) == len(series)
        for b in layout["bar_labels"] + layout["line_labels"]:          # 全部在圖面內、不進圖例列
            assert b["y"] >= layout["plot"]["y"] - 2 and b["y"] + b["h"] <= layout["h"]
    q = mod.chart_layout([s["label"] for s in facts["quarterly"]], [s["values"]["revenue"] for s in facts["quarterly"]],
                         [s["values"]["operating_margin"] for s in facts["quarterly"]], bar_kind="money", line_kind="pct")
    assert q["points"][2] is None and len(q["line_labels"]) == 4        # 2025Q4 推算列無 OPM → 折線斷點


def test_chart_layout_adversarial_collisions(mod):
    labels = ["2020", "2021", "2022", "2023", "2024"]
    bars = [100.0, 100.0, 100.0, 100.0, 100.0]
    line = [95.0, 96.0, 97.0, 98.0, 99.0]
    layout = mod.chart_layout(labels, bars, line, bar_kind="money", line_kind="pct", shared_axis=True)
    assert mod.overlapping_labels(layout) == []
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
    assert mod.BAR_FILL == "#cfeafa" and mod.LINE_COLOR == "#7752A8" and mod.MARK_FILL == "#F5C400"
    assert mod.BAR_FILL in svg and mod.LINE_COLOR in svg and mod.MARK_FILL in svg and "營業利益率 OPM" in svg
    ind = mod.svg_indicator(facts["annual"], "eps", facts["scale"])
    assert "EPS（元）" in ind and ind.count("<circle") == 5 + 1      # 5 個資料點 + 圖例的一個圓點
    days = mod.svg_indicator(facts["annual"], "ar_days", facts["scale"])
    assert "應收天數（天）" in days and "50.2" in days


# ---------- [c07] render ----------

def test_sections_order_and_no_placeholder(mod, html_out):
    pos = [html_out.index(f'id="{k}"') for k in ("conclusion", "financial", "conference", "sources")]
    assert pos == sorted(pos)
    assert re.search(r"\{\{[^}]+\}\}", html_out) is None
    assert html_out.startswith("<!doctype html>") and "</html>" in html_out
    assert "群創光電（3481）2026 Q2 財報＋法說整合報告" in html_out
    for t in ("01　財報重點", "02　財報實績", "03　事業群財務表現", "04　五年趨勢｜營收 × OPM", "05　五季趨勢｜營收 × OPM",
              "06　近五年財務指標｜2020–2024", "01　事業體／產品線重點", "06　友達4支箭與 Micro LED 相關議題", "07　Q&A 重點",
              "08　採購觀察"):
        assert t in html_out, t
    assert "財報公布：2026-08-12" in html_out and "法說會：2026-08-05" in html_out and "法說報告期間：2026 Q2 及上半年" in html_out
    assert "燈號" not in html_out and "War Room" not in html_out


def test_revenue_chart_once_and_ten_indicator_rows(mod, html_out):
    assert html_out.count('data-indicator="') == 10 and 'data-indicator="revenue"' not in html_out
    assert html_out.count("<svg") == 2 + 10      # 五年 + 五季 + 十項全部有資料
    assert "速動比（x）" in html_out and "應收天數（days）" in html_out and "應付天數（days）" in html_out
    assert "稅後淨利率（%）" in html_out and "2020 為合併口徑" in html_out


def test_indicators_missing_rendered_as_not_available(mod, llm):
    old_rows = [fin(f"{y}FY", "annual", revenue=1e8 * (i + 1), gross_margin=5.0, net_margin=1.0, current_ratio=1.1) for i, y in enumerate(range(2020, 2025))]
    f = mod.build_facts(COMPANY, "2026Q2", old_rows, None, None, DOCS)
    out = mod.render_report(f, llm, generated_on="2026-10-21", version="v")
    for key in ("quick_ratio", "ar_days", "ap_days"):
        block = out.split(f'data-indicator="{key}"', 1)[1].split("</div>", 1)[0]
        assert "未取得" in block and "<svg" not in block
    assert out.count("<svg") == 1 + 3          # 五年 + 毛利率 / 稅後淨利率（退用合併）/ 流動比；五季無列
    assert "未取得：淨利率（稅前）、EPS" in out
    assert "本期沒有爬蟲法說彙整" in out and out.count("未提及") >= 4   # 無 summary：profitability / market_outlook / investment / auo


def test_actuals_table_and_segments_prefer_summary(mod, html_out):
    assert "<td>速動比（倍）</td><td>0.99x</td><td>0.90x</td>" in html_out and "+0.09x" in html_out
    assert "<td>營業利益率</td><td>1.80%</td><td>-1.00%</td>" in html_out and "+2.80 pt" in html_out
    assert "車用顯示</td>" in html_out and "NT$210 億" in html_out and "LLM 事業群" not in html_out      # 彙整優先
    assert "車用顯示 營收<b>NT$210 億</b>" in html_out and "IT 顯示 營益率<b>-2%</b>" in html_out     # KPI 後兩格
    assert "毛利率 9.1%（財報數據）" in html_out                                                         # LLM 財報重點


def test_conference_merge_rules(mod, html_out, facts, llm):
    merged = mod.merged_conference(facts, llm)
    assert merged["business_lines"]["text"].startswith("車用顯示器") and merged["business_lines"]["source"].startswith("爬蟲")
    assert merged["capacity"]["items"] == ["新廠 2027 投產"] and merged["capacity"]["source"].startswith("報告 LLM")
    assert merged["auo_topics"] == {"text": None, "items": [], "source": None}
    assert merged["qa"]["items"] == [{"q": "產能利用率？", "a": "約 80%。"}]
    assert "LLM 的事業體" not in html_out and "新廠 2027 投產" in html_out and "Q：</b>產能利用率？" in html_out and "LLM 問" not in html_out
    assert "財報對照（財報數據）" in html_out and "本業需求：舊詞彙的一條" in html_out
    assert "彙整期別與本報告期別不同" not in html_out


def test_segments_fall_back_to_llm_and_period_mismatch(mod, llm):
    sm = {**SUMMARY, "period": "2026Q1", "business_segments": [], "qa_highlights": []}
    f = mod.build_facts(COMPANY, "2026Q2", ANNUAL + QUARTERLY, sm, None, DOCS)
    out = mod.render_report(f, llm, generated_on="2026-10-21", version="v")
    assert "LLM 事業群" in out and "報告 LLM 自本期文件抽取" in out
    assert "Q：</b>LLM 問" in out and "彙整期別與本報告期別不同" in out and "法說彙整來自 2026Q1 場次" in out
    f2 = mod.build_facts(COMPANY, "2026Q2", ANNUAL + QUARTERLY, None, None, DOCS)
    out2 = mod.render_report(f2, mod.normalize_report({}), generated_on="2026-10-21", version="v")
    assert "未提及（財報數據無部門別" in out2 and out2.count("未提及") >= 8


def test_table_and_chart_use_same_numbers(mod, facts, html_out):
    rev_2021 = mod.fmt_value(facts["annual"][1]["values"]["revenue"], "money")
    assert html_out.count(rev_2021) >= 2            # 指標表 + 五年圖標籤


def test_render_without_financials(mod):
    f = mod.build_facts({"company_key": "TYO:5201", "company_name": "AGC", "market": "TYO", "category": "SUPPLIER",
                         "company_slug": "AGC"}, "2026Q2", [], None, None, DOCS[:1])
    out = mod.render_report(f, mod.normalize_report(LLM_OUT), generated_on="2026-10-21", version="v")
    assert "<svg" not in out and out.count("未取得") > 10
    assert "此公司目前沒有結構化財報來源" in out
    assert mod.report_file_name(f) == "AGC_2026Q2_supplier_report.html"


def test_actuals_fall_back_to_latest_published_quarter(mod, llm):
    """本期季報未公告（10 月法說講 Q3、Q3 財報 11 月才出）：第 01 / 02 節與財報對照退用最新已公告季並標示；頁首寫「本期財報尚未公布」。"""
    f = mod.build_facts(COMPANY, "2026Q3", ANNUAL + QUARTERLY, None, None, [])
    a = f["actuals"]
    assert a["fallback"] is True and a["base_period"] == "2026Q2" and [c["period"] for c in a["columns"]] == ["2026Q2", "2025Q2"]
    assert f["kpis"][0]["label"] == "2026 Q2 營收" and f["kpis"][0]["value"] != mod.NOT_AVAILABLE
    f["docs_fed"] = []
    out = mod.render_report(f, llm, generated_on="2026-10-29", version="v")
    assert "最新已公告季：</b>2026 Q2" in out and "02　財報實績（最新已公告季 2026 Q2）" in out
    assert "財報對照（財報數據，最新已公告季 2026 Q2）" in out and "本期 2026Q3 財報尚未公布：第 01／02 節" in out
    assert "本期財報尚未公布（無財報檔案）" in out and "財報檔案無 doc_date" not in out
    # 本期有季報 → 不退用；有財報檔但缺 doc_date → 原措辭
    f2 = mod.build_facts(COMPANY, "2026Q2", ANNUAL + QUARTERLY, SUMMARY, None, [{**DOCS[1], "doc_date": None}])
    assert f2["actuals"]["fallback"] is False and f2["actuals"]["base_period"] == "2026Q2"
    f2["docs_fed"] = []
    out2 = mod.render_report(f2, llm, generated_on="2026-10-29", version="v")
    assert "財報檔案無 doc_date" in out2 and "最新已公告季" not in out2 and "02　財報實績</h2>" in out2
    # 完全沒有財報數據 → 維持 period、不標退用
    f3 = mod.build_facts(COMPANY, "2026Q3", [], None, None, [])
    assert f3["actuals"]["fallback"] is False and f3["actuals"]["base_period"] == "2026Q3"


def test_render_dispatch_by_view_and_file_names(mod, facts, llm):
    """supplier 走 v1 版面；peer / semi 走 [c07a] v2，且 facts 沒跑 enrich_view_facts（沒有 peer / semi 鍵）也不崩；檔名帶視角。"""
    sup = mod.render_report(facts, llm, generated_on="2026-10-29", version="v")
    assert "給 AUO 採購主管的結論" in sup and "<h3>採購建議</h3>" in sup and "02　財報實績" in sup
    f_peer = {**facts, "report_kind": "peer", "topics": []}
    peer = mod.render_report(f_peer, mod.normalize_report({"positioning": "p", "implications": [{"area": "威脅", "judgement": "j", "evidence": "e", "confidence": "高"}]}, "peer"),
                             generated_on="2026-10-29", version="v")
    assert "群創光電（3481）2026 Q2 同業競爭對照" in peer and '<header class="peer">' in peer and "威脅等級：低" in peer and "02　財報實績" not in peer
    assert "同業當季無足夠數據" in peer and "無結構化財報數據" in peer and "<td>威脅</td><td>j</td>" in peer
    f_semi = {**facts, "report_kind": "semi", "topics": ["A"]}
    semi = mod.render_report(f_semi, mod.normalize_report({"thesis": "t"}, "semi"), generated_on="2026-10-29", version="v")
    assert "群創光電（3481）2026 Q2 新事業產業雷達" in semi and "雷達環：暫緩" in semi and "無結構化財報數據" in semi and "01　財報重點" not in semi
    assert mod.report_file_name(f_peer) == "Innolux_2026Q2_peer_report.html" and mod.report_file_name(f_semi) == "Innolux_2026Q2_semi_report.html"
    assert mod.report_file_name(facts) == "Innolux_2026Q2_supplier_report.html"


# ---------- 視角 v2（[c03a] [c05a] [c06a] [c07a]）----------

V2_Q = ["2025Q1", "2025Q2", "2025Q3", "2025Q4", "2026Q1", "2026Q2"]


def _vfin(ck, period, rev, *, gm, opm, nmp, inv, cogs, capex, ocf, dr, cur="TWD", unit="thousand"):
    return {"company_key": ck, "period": period, "period_type": "quarterly", "currency": cur, "unit": unit, "seq": 1, "source": "MOPS", "source_urls": [],
            "revenue": rev, "gross_margin": gm, "operating_margin": opm, "net_margin_parent": nmp, "net_margin": nmp, "inventory": inv,
            "cost_of_revenue": cogs, "capex": capex, "operating_cash_flow": ocf, "debt_ratio": dr, "pretax_income": rev * 0.05, "net_income": rev * 0.04,
            "eps": 0.5, "current_ratio": 1.4, "total_assets": rev * 4, "total_liabilities": rev * 2, "quick_ratio": None, "dso_days": None, "dpo_days": None,
            "operating_cash_flow_ytd": None}


def _vrows(ck, base, growth, opm0, *, cur="TWD", capex_pct=0.08, ocf_pct=0.10, gm_step=1.0, dr0=50):
    rows = []
    for i, p in enumerate(V2_Q):
        rev = base * (1 + growth) ** i
        rows.append(_vfin(ck, p, rev, gm=12 + i * gm_step, opm=opm0 + i * 0.5, nmp=1 + i * 0.2, inv=rev * 0.5, cogs=rev * 0.85,
                          capex=-rev * capex_pct, ocf=rev * ocf_pct, dr=dr0 - i, cur=cur))
    return rows


RIVAL = _vrows("TPE:3481", 600e8, 0.02, 1.0)
AUO = _vrows("TPE:2409", 700e8, 0.01, 1.5)
PEERS = {"SZ:000725": _vrows("SZ:000725", 5000e8, 0.03, 3.0, cur="CNY"), "KRX:034220": _vrows("KRX:034220", 6e12, 0.04, 2.0, cur="KRW")}
PEER_SUMMARY = {**SUMMARY, "period": "2026Q3", "conference_date": "2026-10-20", "guidance": "Q4 持平",
                "business_segments": [{"segment": "IT 面板", "revenue": "NT$ 200 億", "revenue_yoy": "+5%", "operating_margin": "3%", "opm_yoy": None, "note": "n"},
                                      {"segment": "車用顯示", "revenue": None, "revenue_yoy": None, "operating_margin": "6%", "opm_yoy": None, "note": None},
                                      {"segment": "手機", "revenue": "NT$ 50 億", "revenue_yoy": "-3%", "operating_margin": None, "opm_yoy": None, "note": None}]}
PEER_LLM = {"positioning": "群創營益率落後友達 0.5 pt、低於同業中位數（財報數據）", "watch_next": ["8.6 代線良率", "車用客戶", "LCD 處置", "多的第四條"],
            "confirmed_facts": ["f1"], "management_outlook": ["o1"],
            "overlap_actions": [{"application": "IT 面板", "action": "IT OLED 量產", "auo_impact": "高階 IT 壓力"}, {"application": "穿戴", "action": "新案", "auo_impact": "—"}],
            "tech_routes": [{"tech": "FOPLP", "rival": "2027H2 量產", "auo": "未公開", "gap": "對手領先"}, {"tech": "Micro LED", "rival": "穿戴", "auo": "光通訊", "gap": "亂填"}],
            "moves": [{"when": "2026-09", "what": "出售廠房（文件）"}], "outlook_rival": ["Q4 持平（彙整）"],
            "implications": [{"area": "機會", "judgement": "LCD 外溢", "evidence": "第 6 節", "confidence": "中"}, {"area": "威脅", "judgement": "IT 重疊", "evidence": "第 5 節", "confidence": "高"}],
            "watchlist": [{"event": "良率揭露", "trigger": "法說給數字", "when": "2027Q1", "impact": "重估時間窗"}], "qa": [{"q": "q", "a": "a"}],
            "sources_used": ["Innolux_Q2CY26_Presentation.pdf"], "caveats": ["c"]}
SEMI_LLM = {"thesis": "題目 A 需求加速（財報數據）", "next_steps": ["追夥伴", "比規格", "看交期"],
            "topic_segments": [{"segment": "先進封裝與測試", "topic": "A", "revenue": "NT$ 212 億", "share_pct": "19", "yoy": "+48%", "growth_contribution_pct": 41, "note": "AI（文件）"}],
            "signals": [{"category": "需求", "signal": "能見度到 2027H2", "direction": "up", "specificity": "有訂單／時程", "source": "逐字稿", "confidence": "高"},
                        {"category": "價格", "signal": "成熟封裝年減", "direction": "down", "specificity": "有數字／規格", "source": "逐字稿", "confidence": "中"},
                        {"category": "怪類別", "signal": "x", "direction": "sideways", "specificity": "??", "source": "", "confidence": "很高"}],
            "readiness": [{"item": "FOPLP", "topic": "A", "tech_level": 3, "market_level": "2", "timing": "2027H2", "auo_item": "玻璃核心基板", "gap": "落後約 1 年"},
                          {"item": "玻璃載板", "topic": "A", "tech_level": 9, "market_level": 0, "timing": "", "auo_item": "", "gap": ""}],
            "ecosystem": [{"layer": "封裝／測試", "name": "Amkor", "relation": "競爭", "note": "也做 FOPLP"}, {"layer": "亂層", "name": "未點名 AI 客戶", "relation": "客戶", "note": ""}],
            "risks": [{"claim": "c", "disconfirm": "d", "evidence": "e", "when": "w"}],
            "implications": [{"area": "市場窗口", "judgement": "2027–2028", "evidence": "第 3 節", "confidence": "高"}],
            "qa": [{"q": "q", "a": "a", "topic_related": True}, {"q": "q2", "a": "a2", "topic_related": False}], "sources_used": [], "caveats": []}


@pytest.fixture(scope="module")
def peer_facts(mod):
    f = mod.build_facts(COMPANY, "2026Q3", RIVAL, PEER_SUMMARY, {"conference_date": "2026-10-20"}, DOCS)
    f["report_kind"], f["topics"] = "peer", []
    bundle = {"fin_rows": RIVAL, "bench_rows": AUO, "peer_rows": PEERS, "docs": DOCS,
              "bench_summary": {**PEER_SUMMARY, "company_key": "TPE:2409", "guidance": "友達 Q4 低個位數下滑"},
              "peer_summaries": {"SZ:000725": {"guidance": "京東方 Q4 持平"}, "KRX:034220": {}}}
    mod.enrich_view_facts(f, bundle)
    f["docs_fed"] = mod.doc_feed_status(DOCS, *mod.pack_documents(DOCS, max_doc_chars=5000, max_total_chars=6000))
    return f


@pytest.fixture(scope="module")
def semi_facts(mod):
    rows = _vrows("TPE:3711", 1500e8, 0.03, 6.0, capex_pct=0.20, gm_step=0.0)
    company = {**COMPANY, "company_key": "TPE:3711", "company_name": "日月光投控", "stock_code": "3711", "category": "SEMI", "company_slug": "ASE-Holding", "industry": "半導體業"}
    sm = {**PEER_SUMMARY, "business_segments": [{"segment": "先進封裝與測試", "revenue": "NT$ 212 億", "revenue_yoy": "+48%", "operating_margin": None, "opm_yoy": None, "note": "AI"},
                                                 {"segment": "EMS", "revenue": "NT$ 562 億", "revenue_yoy": "+6%", "operating_margin": None, "opm_yoy": None, "note": None}]}
    f = mod.build_facts(company, "2026Q3", rows, sm, None, [])
    f["report_kind"], f["topics"] = "semi", ["A"]
    mod.enrich_view_facts(f, {"fin_rows": rows, "docs": []})
    f["docs_fed"] = []
    return f


def test_v2_derived_metrics_and_series(mod):
    row, prev = RIVAL[4], RIVAL[0]
    m = mod.derived_metrics(row, prev, mod.money_scale("TWD", "thousand"))
    assert abs(m["revenue_yoy"] - ((1.02 ** 4) - 1) * 100) < 1e-6 and m["gross_margin"] == 16 and m["debt_ratio"] == 46
    assert abs(m["inventory_days"] - 0.5 / 0.85 * 91.25) < 1e-6 and abs(m["capex_to_revenue"] - 8.0) < 1e-9 and abs(m["ocf_to_capex"] - 1.25) < 1e-9
    assert abs(m["fcf"] - (row["revenue"] * 0.02 / 1e5)) < 1e-6                      # 仟元 → 億
    assert mod.derived_metrics(None, None, mod.money_scale("TWD", "thousand"))["revenue_yoy"] is None
    s = mod.quarter_metric_series(RIVAL, mod.money_scale("TWD", "thousand"), "2026Q3")
    assert [x["period"] for x in s] == ["2025Q2", "2025Q3", "2025Q4", "2026Q1", "2026Q2"]        # Q3 沒有 → 退用 Q2 往前五季
    assert s[0]["metrics"]["revenue_yoy"] is None and s[-1]["metrics"]["revenue_yoy"] is not None  # 2025Q2 沒有 2024Q2 可比
    assert mod.trend_arrow([1, 2, 3]) == "↑" and mod.trend_arrow([3, 2, 1]) == "↓" and mod.trend_arrow([1, 3, 2]) == "→" and mod.trend_arrow([None, 1, 2]) == "—"
    assert mod.position_vs_median(5, 3, True, 1.0) == "優" and mod.position_vs_median(5, 3, False, 1.0) == "劣"
    assert mod.position_vs_median(3.5, 3, True, 1.0) == "接近" and mod.position_vs_median(5, 3, None, 1.0) is None
    assert mod.quadrant_of(5, 2, 3, 3) == "高成長・低獲利" and mod.quadrant_of(None, 2, 3, 3) is None
    assert mod.app_bucket("IT 面板") == "IT" and mod.app_bucket("Automotive") == "車用" and mod.app_bucket("電視") == "TV" and mod.app_bucket("其它") == "其他"


def test_v2_peer_facts(mod, peer_facts):
    p = peer_facts["peer"]
    assert p["base_period"] == "2026Q2" and p["auo_period"] == "2026Q2" and p["fallback"] is True and p["n_median"] == 4
    sc = {r["key"]: r for r in p["scorecard"]}
    assert [r["key"] for r in p["scorecard"]] == [k for k, *_ in mod.PEER_METRICS]
    assert abs(sc["operating_margin"]["gap"] - (-0.5)) < 1e-9 and sc["operating_margin"]["gap_good"] is False and sc["operating_margin"]["rival_trend"] == "↑"
    assert sc["capex_to_revenue"]["rival_pos"] is None and sc["capex_to_revenue"]["gap_good"] is None           # 無方向
    assert sc["debt_ratio"]["rival_trend"] == "↓" and sc["revenue_yoy"]["rival_pos"] == "劣"                     # 2% 成長低於中位數
    assert sc["gross_margin"]["median"] == 17.0 and sc["gross_margin"]["rival_pos"] == "接近"
    q = {x["name"]: (x["quadrant"], x["role"]) for x in p["quadrants"]}
    assert q["群創"][1] == "rival" and q["友達"][1] == "auo" and q["京東方"][1] == "peer" and q["LGD"][0] == "高成長・高獲利"
    assert [o["bucket"] for o in p["overlap"]] == ["IT", "車用", "手機"] and [o["overlap"] for o in p["overlap"]] == ["高", "高", "低"]
    assert p["overlap"][0]["rival_share"] == "NT$ 200 億" and p["overlap"][0]["auo_share"] == "NT$ 200 億"       # 友達彙整同桶分部
    t = p["trends"]["operating_margin"]
    assert t["labels"][-1] == "2026 Q2" and len(t["rival"]) == len(t["auo"]) == len(t["median"]) == 5 and t["median"][-1] == 4.25
    assert abs(p["gaps"]["operating_margin"] - (-0.5)) < 1e-9 and p["gaps"]["operating_margin_prev_year"] is not None
    assert peer_facts["auo_guidance"]["guidance"] == "友達 Q4 低個位數下滑" and peer_facts["peer_guidance"] == [{"name": "京東方", "guidance": "京東方 Q4 持平"}]
    txt = mod.view_facts_prompt_text(peer_facts)
    assert "【同業對照" in txt and "營業利益率：對手 3.50%｜友達 4.00%｜中位數 4.25%" in txt and "友達同季法說指引" in txt and "同業指引［京東方］" in txt
    # 對手無財報：計分卡空值、不崩
    f0 = mod.build_peer_facts([], AUO, PEERS, "2026Q3", company_key="KRX:005930")
    assert f0["base_period"] is None and f0["fallback"] is False and all(r["rival"] is None for r in f0["scorecard"]) and f0["n_median"] == 3


def test_v2_semi_facts(mod, semi_facts):
    s = semi_facts["semi"]
    assert s["industry_type"] == "OSAT" and s["base_period"] == "2026Q2" and s["fallback"] is True
    rows = {r["key"]: r for r in s["rows"]}
    assert [r["key"] for r in s["rows"]] == [k for k, *_ in mod.DURABILITY_METRICS]
    assert rows["growth_streak"]["value"] == 2 and rows["growth_streak"]["grade"] == "w"                         # 只有 2026Q1/Q2 有去年同季可比
    assert abs(rows["capex_to_revenue"]["value"] - 20.0) < 1e-9 and rows["capex_to_revenue"]["grade"] == "w" and "高於帶" in rows["capex_to_revenue"]["grade_text"]
    assert abs(rows["ocf_to_capex"]["value"] - 0.5) < 1e-9 and rows["ocf_to_capex"]["grade"] == "b"
    assert rows["fcf"]["value"] < 0 and rows["fcf"]["grade"] == "b" and rows["gross_margin"]["grade"] == "b"        # 12% 低於 OSAT 帶 15
    assert rows["inventory_days"]["grade"] == "g" and rows["debt_ratio"]["grade"] == "g" and len(rows["debt_ratio"]["path"]) == 5
    assert s["grade_counts"] == {"g": 2, "w": 2, "b": 3}
    assert [(x["segment"], x["topic"]) for x in s["topic_segments"]] == [("先進封裝與測試", "A"), ("EMS", None)]
    assert mod.growth_streak(_vrows("X:1", 100, 0.05, 1.0), "2026Q2") == 2 and mod.growth_streak([], "2026Q2") is None
    txt = mod.view_facts_prompt_text(semi_facts)
    assert "【行業持續性" in txt and "產業類型 OSAT" in txt and "題目相關分部（關鍵字對到）：先進封裝與測試［A］" in txt
    assert mod.grade_durability("growth_streak", 5, None, [])[0] == "g" and mod.grade_durability("fcf", None, None, [])[0] is None


def test_v2_prompts_and_normalize(mod):
    assert mod.PROFILES["peer"]["template"] == "v2" and mod.PROFILES["semi"]["template"] == "v2" and mod.PROFILES["supplier"]["template"] == "v1"
    assert mod.PROMPT_VERSIONS == {"supplier": "2.2", "peer": "2.0", "semi": "2.0"} and mod.TEMPLATE_VERSION == "20261029c"
    sp = mod.build_system_prompt("peer")
    assert sp == mod.build_v2_system_prompt("peer") and '"positioning"' in sp and '"watchlist"' in sp and "威脅 / 機會" in sp and "{{" not in sp
    ss = mod.build_system_prompt("semi")
    assert '"readiness"' in ss and '"ecosystem"' in ss and "需求端（AI／網通）" in ss and "市場窗口 / 技術門檻與對標" in ss
    assert "procurement" not in sp and mod.build_system_prompt("supplier") == mod.SYSTEM_PROMPT
    p = mod.normalize_report(PEER_LLM, "peer")
    assert p["positioning"].startswith("群創") and p["conclusion"] == p["positioning"] and len(p["watch_next"]) == 3
    assert [x["area"] for x in p["implications"]] == mod.PROFILES["peer"]["dimensions"] and p["implications"][0]["judgement"] == "IT 重疊"
    assert p["actions"][1] == {"area": "機會", "advice": "LCD 外溢"} and p["tech_routes"][1]["gap"] == "亂填" and p["tech_routes"][0]["gap"] == "對手領先"
    assert p["moves"] == [{"when": "2026-09", "what": "出售廠房（文件）"}] and p["watchlist"][0]["impact"] == "重估時間窗"
    s = mod.normalize_report(SEMI_LLM, "semi")
    assert s["topic_segments"][0]["share_pct"] == 19.0 and s["topic_segments"][0]["growth_contribution_pct"] == 41.0
    assert [x["direction"] for x in s["signals"]] == ["up", "down", "flat"] and s["signals"][2]["category"] == "需求" and s["signals"][2]["specificity"] == "定性"
    assert s["signals"][2]["confidence"] == "" and s["readiness"][0]["market_level"] == 2 and s["readiness"][1]["tech_level"] == 4 and s["readiness"][1]["market_level"] == 1
    assert s["ecosystem"][1]["layer"] == mod.ECO_LAYERS[0] and s["ecosystem"][0]["relation"] == "競爭"
    assert [x["topic_related"] for x in s["qa"]] == [True, False] and s["conclusion"] == s["thesis"]
    empty = mod.normalize_report(None, "semi")
    assert empty["thesis"] == "" and empty["signals"] == [] and len(empty["implications"]) == 4 and mod.exposure_pct(empty) is None


def test_v2_charts(mod):
    labels = ["2025 Q2", "2025 Q3", "2025 Q4", "2026 Q1", "2026 Q2"]
    svg = mod.svg_lines(labels, [{"name": "對手", "values": [1, 2, None, 4, 5], "color": mod.C_RIVAL}, {"name": "友達", "values": [2, 2, 2, 2, 2], "color": mod.C_AUO},
                                 {"name": "中位數", "values": [1.5] * 5, "color": mod.C_MEDIAN, "dashed": True}], kind="pct", title="t")
    assert svg.startswith("<svg") and svg.count("<path") == 4 and "stroke-dasharray" in svg and "對手 5%" in svg and "友達 2%" in svg and "2026 Q2" in svg
    assert "chart-missing" in mod.svg_lines([], [], kind="pct", title="t") and "chart-missing" in mod.svg_lines(labels, [{"name": "x", "values": [None] * 5, "color": "#000"}], kind="pct", title="t")
    sc = mod.svg_scatter([{"name": "A", "x": 1, "y": 2, "role": "rival"}, {"name": "友達", "x": 3, "y": 4, "role": "auo"}, {"name": "P", "x": 2, "y": 3, "role": "peer"}],
                         x_label="x", y_label="y", x_ref=2, y_ref=3, title="s")
    assert sc.count("<circle") == 3 and sc.count("stroke-dasharray") >= 2 and ">A<" in sc and ">友達<" in sc
    assert "chart-missing" in mod.svg_scatter([{"name": "A", "x": None, "y": 1, "role": "rival"}], x_label="x", y_label="y", x_ref=None, y_ref=None, title="s")
    b = mod.svg_bars(labels, [1.2, -0.5, None, 2.0, 1.0], kind="ratio", title="b", ref=1.0, ref_label="1.0x")
    assert b.count("<rect") == 4 and "未取得" in b and "1.0x" in b
    assert 'class="on"' in mod.svg_steps(3, mod.MATURITY_TECH) and mod.svg_steps(3, mod.MATURITY_TECH).count('class="on"') == 3 and "試產" in mod.svg_steps(3, mod.MATURITY_TECH)


def test_v2_render_peer(mod, peer_facts):
    llm = mod.normalize_report(PEER_LLM, "peer")
    lvl, why = mod.threat_level(peer_facts, llm)
    assert lvl == "中" and "FOPLP" in why and "IT" in why                       # 高重疊有動作 1 桶 + 對手領先 1 項 → 中
    out = mod.render_report(peer_facts, llm, generated_on="2026-10-29", version="v")
    for sid in ("summary", "position", "scorecard", "trend", "overlap", "moves", "outlook", "implication", "watch", "sources"):
        assert f'id="{sid}"' in out, sid
    assert "群創光電（3481）2026 Q3 同業競爭對照" in out and "威脅等級：中" in out and '<header class="peer">' in out and "8　對友達的意涵" in out
    assert "最新已公告季：</b>對手 2026 Q2、友達 2026 Q2" in out and out.count("<svg") == 4 and "同業中位數（n=4）" in out
    assert "IT OLED 量產" in out and "穿戴" in out and "對手領先" in out and "出售廠房" in out and "友達 Q4 低個位數下滑" in out and "京東方：京東方 Q4 持平" in out
    assert "低成長・低獲利" in out and "群創（對手）" in out and "友達（友達）" in out
    assert re.search(r"\{\{[^}]+\}\}", out) is None and "採購" not in out.split('id="sources"')[0] and "供應穩定性" not in out
    assert "高" in out and "良率揭露" in out and "Innolux_Q2CY26_Presentation.pdf" in out
    low = mod.render_report(peer_facts, mod.normalize_report({}, "peer"), generated_on="2026-10-29", version="v")
    assert "威脅等級：低" in low and "LLM 未產出定位" in low and "未提及" in low


def test_v2_render_semi(mod, semi_facts):
    llm = mod.normalize_report(SEMI_LLM, "semi")
    assert mod.exposure_pct(llm) == 19.0 and mod.radar_ring(semi_facts, llm) == ("立即跟進", "曝險 19%、時程落後")
    out = mod.render_report(semi_facts, llm, generated_on="2026-10-29", version="v")
    for sid in ("thesis", "exposure", "signals", "readiness", "durability", "ecosystem", "risks", "implication", "sources"):
        assert f'id="{sid}"' in out, sid
    assert "日月光投控（3711）2026 Q3 新事業產業雷達" in out and "雷達環：立即跟進" in out and '<header class="semi">' in out and "A 封裝／載板" in out
    assert "題目曝險（題目事業體占營收）</span><b>19%</b>" in out and "▲ 1" in out and "▼ 1" in out and "● 1" in out
    assert "綠 2</span>・<span class=\"grade w\">黃 2</span>・<span class=\"grade b\">紅 3" in out and "參考帶（OSAT）" in out and "高於帶（擴張期）" in out
    assert "非題目事業體 1 項（摺疊）" in out and "EMS" in out and "落後約 1 年" in out and 'class="on"' in out and out.count("<svg") == 4
    assert "友達（封裝／載板）" in out and "Amkor（競爭）" in out and "未點名 AI 客戶（客戶）" in out and "其他 Q&A 1 題（摺疊）" in out
    assert "最新已公告季：</b>2026 Q2" in out and "8　對友達新事業的意涵" in out and re.search(r"\{\{[^}]+\}\}", out) is None
    assert "採購" not in out.split('id="sources"')[0]
    # 無分部占比、無訊號 → 曝險未取得、雷達環暫緩、不崩
    llm0 = mod.normalize_report({"readiness": [{"item": "x", "topic": "A", "tech_level": 1, "market_level": 1, "gap": "同階段"}]}, "semi")
    out0 = mod.render_report(semi_facts, llm0, generated_on="2026-10-29", version="v")
    assert mod.radar_ring(semi_facts, llm0)[0] == "暫緩" and "題目曝險（題目事業體占營收）</span><b>未取得</b>" in out0 and "先進封裝與測試" in out0   # 退用規則對到的分部


def test_html_escapes_text(mod, facts):
    bad = json.loads(json.dumps(LLM_OUT))
    bad["financial_highlights"] = ["<script>alert(1)</script>"]
    out = mod.render_report(facts, mod.normalize_report(bad), generated_on="2026-10-21", version="v")
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
    end = src.index("\n])", start) + 3          # 行首的 ])；docs_fed 的巢狀 StructType 行內也有 ])
    ns = {}
    exec("from pyspark.sql.types import *\n" + src[start:end], ns)
    return [f.name for f in ns[name].fields]


def test_ddl_matches_write_schema():
    cols, ns = _ddl_columns(["c19a", "c19b"])
    assert ("bronze", "ir_report_llm") in ns["TABLES"] and ("gold", "ir_report") in ns["TABLES"]
    assert ns["LAYER_PREFIX"]["gold"] == "g_"
    assert cols[("bronze", "ir_report_llm")] == _schema_fields("c10", "LLM_SCHEMA")
    assert cols[("gold", "ir_report")] == _schema_fields("c10", "REPORT_SCHEMA")


def test_indicator_sources_exist_in_financials_ddl(mod):
    """[c02] INDICATORS 的 source / fallback 都要是 s_ir_calendar_financials 的欄位（含 2026-10-21 新欄）。"""
    cols, _ = _ddl_columns(["c19"])
    fin_cols = set(cols[("silver", "financials")])
    for ind in mod.INDICATORS:
        assert ind["source"] in fin_cols, ind
        if ind.get("fallback"):
            assert ind["fallback"] in fin_cols, ind
    assert {"quick_ratio", "dso_days", "dpo_days", "net_margin_parent", "days_basis"} <= fin_cols
