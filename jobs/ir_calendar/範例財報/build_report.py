#!/usr/bin/env python3
"""把每家公司資料夾的 <公司>.md（實為 JSON）依《SCM 財報和法說報告 v20261007》版型產出 HTML。

模板：PM_Head/projects/MI_Crawler/ir_calendar/doc/20261021_SCM財報和法說報告html格式v20261007.html（3M 範例、AUO 配色）
版型：給採購主管的結論 → 財報六節（重點 KPI／實績表／事業群／五年圖／五季圖／五年指標表＋10 小圖）→ 法說七節 → 資料來源與限制。
- 數字欄位全部由 fin_rows 算；模板的 12 張靜態 PNG 改成純 Python 產的 inline SVG（無套件依賴，可 hover 看值）。
- 敘事欄位（結論、事業群、法說七節、限制）在 NARRATIVE 逐家撰寫，數字一律從 k dict 帶入，不手抄。
- 資料給不出的欄位保留 <mark>資料缺：…</mark>（黃底），對照 模板覆蓋度評估.md。
- 同資料夾的 <公司>_爬蟲*.md（bronze payload）用於頁首法說時間軸與附錄「資料履歷」。
- <公司>_爬蟲*_新版實測.md（2026-10-21 爬蟲新版 dev 批次）若存在：financials 取代 bundle fin_rows 當財報六節資料源
  （共同欄位逐值比對，差異印在 console 與附錄），補速動比／應收付天數／母公司淨利率；summary 的 management_views
  五類直接填法說 01–05、qa_highlights 填 07、notes 的 AUO 判讀句填 06、business_segments 填 03 與 01 兩格，另加 08 採購觀察。

資料夾：<公司>/<公司>.md、<公司>_爬蟲*.md → <公司>.html（報告）、<公司>_原始資料.html、<公司>_爬蟲資料*.html（build_sources.py）
用法：python3 build_report.py            # 在本資料夾執行，另產 index.html
"""
from __future__ import annotations

import html
import json
import pathlib
import re

from build_sources import (
    COMPANIES,
    RECORD_LABEL,
    build_all,
    is_new_fin,
    is_new_summary,
    record_brief,
    record_date,
    record_source_url,
)

HERE = pathlib.Path(__file__).resolve().parent
TODAY = "2026-10-21"
VERSION = "v4"
TEMPLATE_REF = "doc/20261021_SCM財報和法說報告html格式v20261007.html"

MISSING = '<mark>資料缺</mark>'

# 模板配色（AUO）
C_BLUE, C_LBLUE, C_PURPLE, C_YELLOW, C_GREEN, C_INK = "#0066B3", "#26A9E0", "#7752A8", "#F5C400", "#40A86B", "#111111"
C_BARFILL, C_GRID = "#cfeafa", "#e3eef5"


# ---------------------------------------------------------------- 數字工具
def load(p: pathlib.Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"), strict=False)


def yi(v, unit: str):
    """原始值 → 億（TW 千元 /1e5；美元 one /1e8）。"""
    if v is None:
        return None
    factor = {"one": 1.0, "thousand": 1e3, "million": 1e6}[unit]
    return v * factor / 1e8


def f2(v, d=2):
    return "—" if v is None else f"{v:,.{d}f}"


def pct(v, d=2, sign=False):
    if v is None:
        return "—"
    return f"{v:+.{d}f}%" if sign else f"{v:.{d}f}%"


def m(v, d=2):
    return MISSING if v is None else f2(v, d)


def mp(v, d=2, sign=False):
    return MISSING if v is None else pct(v, d, sign)


def esc(s) -> str:
    return html.escape(str(s), quote=True)


def q_label(period: str) -> str:  # 2026Q2 → 2026 Q2
    return period.replace("Q", " Q")


def q_short(period: str) -> str:  # 2026Q2 → 26 Q2
    return period[2:4] + " Q" + period[-1]


def ratio_pct(a, b):
    return (a / b * 100) if (a is not None and b) else None


def delta_cell(cur, prev, kind="pct", d=1):
    """同比變動欄：kind=pct 以百分比、pt 以百分點、x 以倍數差；None 給黃底。"""
    if cur is None or prev is None:
        return MISSING
    if kind == "pct":
        if prev == 0:
            return "—"
        v = (cur / prev - 1) * 100
        if prev < 0:  # 基期為負，百分比無意義
            return f'<span class="{"delta-positive" if cur > prev else "delta-negative"}">{"轉正" if cur >= 0 else "仍為負"}（基期為負）</span>'
        txt = f"{v:+.{d}f}%"
    elif kind == "pt":
        v = cur - prev
        txt = f"{v:+.{d}f} pt"
    else:
        v = cur - prev
        txt = f"{v:+.2f}x"
    cls = "delta-positive" if v > 0 else "delta-negative" if v < 0 else ""
    return f'<span class="{cls}">{txt}</span>'


# ---------------------------------------------------------------- 指標整理
def build_k(d: dict, fin_new_rows: list | None = None) -> dict:
    co = d["company"]
    rows = fin_new_rows or d["fin_rows"]          # 新版爬蟲實測 financials 優先（共同欄位與 bundle 相同，見 compare_fin）
    unit = rows[0]["unit"]
    cur = rows[0]["currency"]
    cur_label = "NT$" if cur == "TWD" else ("US$" if cur == "USD" else cur)

    annual = sorted([r for r in rows if r["period_type"] == "annual"], key=lambda r: r["fiscal_year"])[-5:]
    quarters = sorted([r for r in rows if r["period_type"] == "quarterly"], key=lambda r: r["period_end"])
    q = quarters[-1]
    year, qn = q["period"][:4], q["period"][4:]
    q_ly = next((r for r in quarters if r["period"] == f"{int(year) - 1}{qn}"), None)
    q5 = quarters[-5:]                                   # 五季圖：最近 5 季（含推算列）

    rev_q, rev_ly = yi(q["revenue"], unit), (yi(q_ly["revenue"], unit) if q_ly else None)
    yoy = (rev_q / rev_ly - 1) * 100 if (rev_q and rev_ly) else None
    oi, pt, ni = yi(q["operating_income"], unit), yi(q["pretax_income"], unit), yi(q["net_income"], unit)
    nonop = (pt - oi) if (pt is not None and oi is not None) else None
    ocf_ytd, ocf_ytd_ly = yi(q.get("operating_cash_flow_ytd"), unit), (yi(q_ly.get("operating_cash_flow_ytd"), unit) if q_ly else None)
    ni_ytd = yi(q.get("net_income_ytd"), unit)
    if ni_ytd is None:
        vals = [r["net_income"] for r in quarters if r["period"].startswith(year)]
        ni_ytd = yi(sum(vals), unit) if vals and all(v is not None for v in vals) else None

    k = dict(
        name=co["company_name"], code=co["stock_code"], key=co["company_key"], market=co["market"],
        industry=co.get("industry"), ir_url=co.get("ir_url"), english=co.get("english_name"),
        cur=cur, cur_label=cur_label, unit=unit, unit_note=("千元" if unit == "thousand" else "元"),
        period=d["period"], q=q, q_ly=q_ly, year=year, annual=annual, quarters=quarters, q5=q5,
        q_label=q_label(q["period"]), q_ly_label=q_label(q_ly["period"]) if q_ly else "去年同季",
        rev_q=rev_q, rev_ly=rev_ly, yoy=yoy,
        gm=q["gross_margin"], gm_ly=q_ly["gross_margin"] if q_ly else None,
        opm=q["operating_margin"], opm_ly=q_ly["operating_margin"] if q_ly else None,
        nm=q["net_margin"], nm_ly=q_ly["net_margin"] if q_ly else None,
        eps=q["eps"], eps_ly=q_ly["eps"] if q_ly else None,
        oi=oi, pt=pt, ni=ni, nonop=nonop, nonop_pct=ratio_pct(nonop, pt),
        ocf_ytd=ocf_ytd, ocf_ytd_ly=ocf_ytd_ly, ni_ytd=ni_ytd, capex_ytd=yi(q.get("capex_ytd"), unit),
        cr=q["current_ratio"], cr_ly=q_ly["current_ratio"] if q_ly else None,
        qr=q.get("quick_ratio"), qr_ly=q_ly.get("quick_ratio") if q_ly else None,          # 新版爬蟲才有
        nmp=q.get("net_margin_parent"),
        dr=q["debt_ratio"], ta=yi(q["total_assets"], unit), tl=yi(q["total_liabilities"], unit),
        summary=d.get("summary"), conference=d.get("conference"), docs=d.get("docs") or [],
        fin_version="新版實測" if fin_new_rows else "bundle", fin_batch=rows[0].get("batch_id"), fin_path=rows[0].get("batch_path"),
        nmp_all=all(r.get("net_margin_parent") is not None for r in annual),   # 五年都有母公司淨利率 → 第 06 節用模板口徑
    )
    k.update(  # 敘事用字串
        REV_Q=f2(rev_q), REV_LY=f2(rev_ly), YOY=pct(yoy, 1, True), GM=pct(k["gm"]), GM_LY=pct(k["gm_ly"]),
        OPM=pct(k["opm"]), OPM_LY=pct(k["opm_ly"]), NM=pct(k["nm"]), OI=f2(oi), PT=f2(pt), NI=f2(ni),
        NONOP=f2(nonop), NONOP_PCT=pct(k["nonop_pct"], 0), OCF=f2(ocf_ytd), NI_YTD=f2(ni_ytd), CAPEX=f2(k["capex_ytd"]),
        DR=pct(k["dr"]), CR=f2(k["cr"]), TA=f2(k["ta"]), EPS=f2(k["eps"]),
        OPM_D=(f"{k['opm'] - k['opm_ly']:+.1f} pt" if k["opm"] is not None and k["opm_ly"] is not None else "—"),
        QR=m(k["qr"]), QR_LY=m(k["qr_ly"]),
    )
    return k


# ---------------------------------------------------------------- 新版爬蟲實測（2026-10-21 dev 批次）
TOPIC_KEYS = {"事業體／產品線重點": "business", "擴產／產能變化": "capacity", "獲利能力變化": "profit", "未來市場預測": "outlook", "投資／M&A／組織整改": "invest"}
IR_TITLES = {"business": "01　事業體／產品線重點", "capacity": "02　擴產／產能變化", "profit": "03　獲利能力變化", "outlook": "04　未來市場預測", "invest": "05　投資／M&amp;A／組織整改"}


def pick_new(crawler: dict | None) -> dict:
    """從合併後的爬蟲紀錄挑出新版（version=新版實測）的 financials / summary / conference / manifest。"""
    out = dict(fin=None, fin_rec=None, summaries=[], conferences=[], manifests=[], batch=None)
    for r in (crawler or {}).get("records", []):
        if r.get("version") != "新版實測" or r["payload"] is None:
            continue
        p, t = r["payload"], r["record_type"]
        out["batch"] = r["batch_id"]
        if t == "ir_financials" and is_new_fin(p):
            out["fin"], out["fin_rec"] = p, r
        elif t == "ir_summary" and is_new_summary(p):
            out["summaries"].append(ir_from_summary(p))
        elif t == "ir_conference":
            out["conferences"].append(p)
        elif t == "ir_document":
            out["manifests"].append(p)
    out["summaries"].sort(key=lambda s: (s["date"] or "", s["period"] or ""))
    return out


def rows_from_new_fin(p: dict, rec: dict) -> list[dict]:
    """新版 financials payload → 與 bundle fin_rows 同形狀的列（period_type / period / fiscal_year / currency / unit / source / batch_*）。"""
    base = dict(currency=p.get("currency"), unit=p.get("unit"), source=p.get("source"), batch_id=rec["batch_id"], batch_path=rec["batch_path"])
    rows = [dict(base, period_type="annual", period=f"{a['fiscal_year']}FY", **a) for a in p.get("annual") or []]
    rows += [dict(base, period_type="quarterly", fiscal_year=int(q["period"][:4]), **q) for q in p.get("quarterly") or []]
    return rows


def compare_fin(old_rows: list[dict], new_rows: list[dict]) -> dict:
    """bundle fin_rows 與新版列共同欄位逐值比對 → {same, filled（bundle 為 null、新版有值）, diff:[(期別, 欄, 舊, 新)], new_keys}。"""
    idx = {(r["period_type"], r["period"]): r for r in old_rows}
    skip = {"source_urls", "derived", "_derived", "batch_id", "batch_path", "seq", "updated_at", "generated_at"}
    res = dict(same=0, filled=0, diff=[], missing_periods=[])
    old_keys = set().union(*[set(r) for r in old_rows])
    res["new_keys"] = sorted(set().union(*[set(r) for r in new_rows]) - old_keys)
    for n in new_rows:
        o = idx.get((n["period_type"], n["period"]))
        if not o:
            res["missing_periods"].append(n["period"])
            continue
        for kk, v in n.items():
            if kk in skip or kk not in o:
                continue
            if o[kk] == v:
                res["same"] += 1
            elif o[kk] is None:
                res["filled"] += 1
            else:
                res["diff"].append((n["period"], kk, o[kk], v))
    return res


def ir_from_summary(p: dict) -> dict:
    """新版 summary → 法說七節用的 dict：views 依固定五類、qa、notes 裡的 AUO 判讀句、headline、事業群、三清單。"""
    s = p.get("summary") or {}
    views = {}
    for v in s.get("management_views") or []:
        key = TOPIC_KEYS.get(v.get("topic"))
        if key and v.get("view"):
            views[key] = v["view"]
    notes = s.get("notes") or ""
    sents = re.split(r"(?<=[。；])", notes)
    auo = "".join(x for x in sents if ("AUO" in x or "友達" in x)).strip()
    qa_note = "".join(x for x in sents if ("Q&A" in x or "逐字稿" in x)).strip()
    return dict(date=p.get("conference_date"), period=p.get("period"), reported=s.get("reported_period"), views=views,
                qa=s.get("qa_highlights") or [], auo=auo, qa_note=qa_note, headline=s.get("headline_metrics") or [],
                segments=s.get("business_segments") or [], positive=s.get("positive_signals") or [],
                watch=s.get("watch_items") or [], open_q=s.get("open_questions") or [], sources=s.get("sources") or [],
                guidance=s.get("guidance"), crawled=(p.get("crawled_at") or "")[:10], batch=None)


def segments_for(n: dict, latest: dict | None):
    """第 03 節的列：優先新版 summary 的 business_segments（有任一數字才算完整），否則 NARRATIVE 手抄。回傳 (segs, 利潤率欄名, 註, 來源說明)。"""
    if latest and latest["segments"]:
        segs = [dict(name=x.get("segment"), revenue=x.get("revenue"), revenue_yoy=x.get("revenue_yoy"), margin=x.get("operating_margin"),
                     margin_yoy=x.get("opm_yoy"), note=x.get("note")) for x in latest["segments"]]
        has_num = any(x["revenue"] or x["margin"] for x in segs)
        src = f"新版爬蟲實測 ir_summary {latest['date']}（{latest['period']}）的 business_segments，LLM 自簡報／新聞稿抽取；欄位為原文字串"
        return segs, "營益率（法說口徑）", (None if has_num else "法說未揭露各事業群金額與利潤率，只有文字描述。"), src
    return n.get("segments"), n.get("seg_margin_label") or "OPM", n.get("seg_note"), None


# ---------------------------------------------------------------- SVG 圖（取代模板的 12 張 PNG）
def _nice_max(v: float) -> float:
    if v <= 0:
        return 1.0
    import math
    mag = 10 ** math.floor(math.log10(v))
    for s in (1, 2, 2.5, 5, 10):
        if v <= s * mag:
            return s * mag
    return 10 * mag


def _fmt(v, d):
    return "—" if v is None else f"{v:,.{d}f}"


def svg_bars(labels, vals, *, d=1, unit="", line=True, h=260, w=1000, note_missing="推算列無此值"):
    """單指標：淺藍柱 + 紫色折線連柱頂（模板第 06 節小圖的樣子）；支援負值（基線在 0）、缺值留空。"""
    n = len(labels)
    pl, pr, pt_, pb = 56, 20, 34, 34
    pw, ph = w - pl - pr, h - pt_ - pb
    present = [v for v in vals if v is not None]
    if not present:
        return f'<div class="chart-missing">{MISSING}：此指標 fin_rows 沒有</div>'
    vmax, vmin = max(0, max(present)), min(0, min(present))
    top = _nice_max(vmax) if vmax > 0 else 0
    bot = -_nice_max(-vmin) if vmin < 0 else 0
    if top == bot:
        top = 1
    Y = lambda v: pt_ + (top - v) / (top - bot) * ph
    slot = pw / n
    bw = slot * 0.56
    X = lambda i: pl + slot * i + slot / 2
    g = [f'<svg viewBox="0 0 {w} {h}" class="svgchart" role="img" aria-label="{esc(unit)}">']
    # 格線 + 軸標
    for t in range(5):
        v = bot + (top - bot) * t / 4
        y = Y(v)
        g.append(f'<line x1="{pl}" y1="{y:.1f}" x2="{w - pr}" y2="{y:.1f}" stroke="{C_GRID}"/>'
                 f'<text x="{pl - 8}" y="{y + 4:.1f}" text-anchor="end" class="ax">{_fmt(v, 0 if abs(top - bot) >= 20 else 1)}</text>')
    if bot < 0 < top:
        g.append(f'<line x1="{pl}" y1="{Y(0):.1f}" x2="{w - pr}" y2="{Y(0):.1f}" stroke="#8aa0b5"/>')
    pts = []
    for i, (lab, v) in enumerate(zip(labels, vals, strict=True)):
        x = X(i)
        g.append(f'<text x="{x:.1f}" y="{h - 10}" text-anchor="middle" class="ax">{esc(lab)}</text>')
        if v is None:
            g.append(f'<text x="{x:.1f}" y="{Y(0) - 8:.1f}" text-anchor="middle" class="miss">{esc(note_missing)}</text>')
            pts.append(None)
            continue
        y0, y1 = Y(0), Y(v)
        g.append(f'<rect x="{x - bw / 2:.1f}" y="{min(y0, y1):.1f}" width="{bw:.1f}" height="{abs(y0 - y1):.1f}" fill="{C_BARFILL}" stroke="{C_INK}" stroke-width="1">'
                 f'<title>{esc(lab)}：{_fmt(v, d)}{esc(unit)}</title></rect>')
        ly = y1 - 10 if v >= 0 else y1 + 16
        g.append(f'<text x="{x:.1f}" y="{ly:.1f}" text-anchor="middle" class="val">{_fmt(v, d)}{esc(unit) if unit == "%" else ""}</text>')
        pts.append((x, y1))
    if line:
        seg, path = [], []
        for p in pts + [None]:
            if p is None:
                if len(seg) > 1:
                    path.append("M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in seg))
                seg = []
            else:
                seg.append(p)
        if path:
            g.append(f'<path d="{" ".join(path)}" fill="none" stroke="{C_PURPLE}" stroke-width="2.5"/>')
        for p in pts:
            if p:
                g.append(f'<circle cx="{p[0]:.1f}" cy="{p[1]:.1f}" r="5" fill="{C_YELLOW}" stroke="{C_PURPLE}" stroke-width="2"/>')
    g.append("</svg>")
    return "".join(g)


def svg_rev_opm(labels, rev, opm, cur_label, h=400, w=1000):
    """營收柱（上格）＋ OPM 折線（下格），共用 x 軸。模板把 OPM 疊在金額軸上（雙軸），這裡拆成兩格避免誤讀。"""
    n = len(labels)
    pl, pr = 56, 20
    pw = w - pl - pr
    slot = pw / n
    bw = slot * 0.56
    X = lambda i: pl + slot * i + slot / 2
    # 上格：營收
    t1, h1 = 30, 200
    rmax = max([v for v in rev if v is not None] + [0])
    top = _nice_max(rmax)
    Y1 = lambda v: t1 + (top - v) / top * h1
    # 下格：OPM
    t2, h2 = t1 + h1 + 40, 110
    o = [v for v in opm if v is not None]
    omax, omin = (max(o + [0]), min(o + [0])) if o else (1, 0)
    otop = _nice_max(omax) if omax > 0 else 0
    obot = -_nice_max(-omin) if omin < 0 else 0
    if otop == obot:
        otop = 1
    Y2 = lambda v: t2 + (otop - v) / (otop - obot) * h2
    g = [f'<svg viewBox="0 0 {w} {h}" class="svgchart" role="img" aria-label="營收與營業利益率">']
    g.append(f'<text x="{pl}" y="{t1 - 12}" class="ttl"><tspan fill="{C_BLUE}">■</tspan> 營收（{esc(cur_label)} 億）</text>')
    g.append(f'<text x="{pl}" y="{t2 - 12}" class="ttl"><tspan fill="{C_PURPLE}">●</tspan> 營業利益率（%）</text>')
    for t in range(5):
        v = top * t / 4
        y = Y1(v)
        g.append(f'<line x1="{pl}" y1="{y:.1f}" x2="{w - pr}" y2="{y:.1f}" stroke="{C_GRID}"/><text x="{pl - 8}" y="{y + 4:.1f}" text-anchor="end" class="ax">{_fmt(v, 0)}</text>')
    od = 0 if (otop - obot) >= 5 else 1
    for v in (sorted({obot, 0.0, otop}) if obot < 0 else (0.0, otop / 2, otop)):   # 有負值時刻度放 下界／0／上界
        y = Y2(v)
        g.append(f'<line x1="{pl}" y1="{y:.1f}" x2="{w - pr}" y2="{y:.1f}" stroke="{C_GRID}"/><text x="{pl - 8}" y="{y + 4:.1f}" text-anchor="end" class="ax">{_fmt(v, od)}%</text>')
    if obot < 0 < otop:
        g.append(f'<line x1="{pl}" y1="{Y2(0):.1f}" x2="{w - pr}" y2="{Y2(0):.1f}" stroke="#8aa0b5"/>')
    pts = []
    for i, lab in enumerate(labels):
        x = X(i)
        g.append(f'<text x="{x:.1f}" y="{h - 8}" text-anchor="middle" class="ax">{esc(lab)}</text>')
        r = rev[i]
        if r is not None:
            ly = Y1(r) - 8 if Y1(r) - 8 > t1 + 6 else Y1(r) + 18      # 柱頂貼到格頂時標籤改放柱內
            g.append(f'<rect x="{x - bw / 2:.1f}" y="{Y1(r):.1f}" width="{bw:.1f}" height="{Y1(0) - Y1(r):.1f}" fill="{C_BARFILL}" stroke="{C_INK}"><title>{esc(lab)} 營收 {_fmt(r, 2)}</title></rect>'
                     f'<text x="{x:.1f}" y="{ly:.1f}" text-anchor="middle" class="val">{_fmt(r, 1 if r >= 100 else 2)}</text>')
        v = opm[i]
        if v is None:
            g.append(f'<text x="{x:.1f}" y="{Y2(obot) - 6:.1f}" text-anchor="middle" class="miss">推算列無 OPM</text>')
            pts.append(None)
        else:
            pts.append((x, Y2(v), v))
    seg, path = [], []
    for p in pts + [None]:
        if p is None:
            if len(seg) > 1:
                path.append("M" + " L".join(f"{x:.1f},{y:.1f}" for x, y, _ in seg))
            seg = []
        else:
            seg.append(p)
    if path:
        g.append(f'<path d="{" ".join(path)}" fill="none" stroke="{C_PURPLE}" stroke-width="2.5"/>')
    for p in pts:
        if p:
            x, y, v = p
            ly = y - 11 if y - 11 > t2 + 8 else y + 22                   # 點貼到格頂時標籤改放點下方，避免壓到標題
            g.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5.5" fill="{C_YELLOW}" stroke="{C_PURPLE}" stroke-width="2"><title>OPM {v:.2f}%</title></circle>'
                     f'<text x="{x:.1f}" y="{ly:.1f}" text-anchor="middle" class="val" fill="{C_PURPLE}">{v:.1f}%</text>')
    g.append("</svg>")
    return "".join(g)


# ---------------------------------------------------------------- 各節 HTML
def kpi_cards(k, segs):
    segs = [s for s in (segs or []) if s.get("revenue") or s.get("margin")]
    cards = [
        f'<div class="kpi">{k["q_label"]} 營收<b>{k["cur_label"]} {m(k["rev_q"])} 億</b><small>YoY {mp(k["yoy"], 1, True)}（{k["q_ly_label"]}：{m(k["rev_ly"])} 億）</small></div>',
        f'<div class="kpi">營業利益率<b>{mp(k["opm"])}</b><small>YoY {esc(k["OPM_D"])}（{k["q_ly_label"]}：{mp(k["opm_ly"])}）</small></div>',
    ]
    for s in segs[:2]:
        if s.get("revenue"):
            cards.append(f'<div class="kpi">{esc(s["name"])} 營收<b>{esc(s["revenue"])}</b><small>YoY {esc(s.get("revenue_yoy") or "—")}</small></div>')
        else:
            cards.append(f'<div class="kpi">{esc(s["name"])} 營益率<b>{esc(s["margin"])}</b><small>YoY {esc(s.get("margin_yoy") or "—")}；法說未給營收金額</small></div>')
    while len(cards) < 4:
        cards.append('<div class="kpi">事業群營收<b><mark>資料缺</mark></b><small>fin_rows 無部門別；法說／財報未提供</small></div>')
    return "\n".join(cards)


def actual_table(k):
    cl = k["cur_label"]
    rows = [
        (f"營收（{cl} 億）", m(k["rev_q"]), m(k["rev_ly"]), delta_cell(k["rev_q"], k["rev_ly"], "pct")),
        ("營業利益率", mp(k["opm"]), mp(k["opm_ly"]), delta_cell(k["opm"], k["opm_ly"], "pt")),
        (f"每股盈餘（{esc(k['cur'])}）", m(k["eps"]), m(k["eps_ly"]), delta_cell(k["eps"], k["eps_ly"], "pct", 0)),
        (f"營業現金流（{cl} 億，{k['year']} 年初累計）", m(k["ocf_ytd"]), m(k["ocf_ytd_ly"]) + ("（去年同期累計）" if k["ocf_ytd_ly"] is not None else ""), delta_cell(k["ocf_ytd"], k["ocf_ytd_ly"], "pct", 0)),
        ("流動比（倍）", m(k["cr"]), m(k["cr_ly"]), delta_cell(k["cr"], k["cr_ly"], "x")),
        ("速動比（倍）", (m(k["qr"]) if k["fin_version"] == "新版實測" else "<mark>資料缺：bundle 無現金／有價證券／應收帳款欄位</mark>"),
         m(k["qr_ly"]) if k["fin_version"] == "新版實測" else MISSING, delta_cell(k["qr"], k["qr_ly"], "x") if k["fin_version"] == "新版實測" else "—"),
    ]
    return "".join(f"<tr><td>{a}</td><td>{b}</td><td>{c}</td><td>{d}</td></tr>" for a, b, c, d in rows)


def segment_table(segs, margin_label, seg_note, src):
    if not segs:
        return f'<p><mark>資料缺：fin_rows 無部門別，法說摘要／財報文字也沒有可用的事業群數字</mark>{("　" + esc(seg_note)) if seg_note else ""}</p>'
    def cell(v):
        if v is None:
            return "—"
        s = esc(v)
        if s.startswith("+"):
            return f'<span class="delta-positive">{s}</span>'
        if s.startswith("−") or s.startswith("-"):
            return f'<span class="delta-negative">{s}</span>'
        return s
    has_note = any(s.get("note") for s in segs)
    body = "".join(f"<tr><td>{esc(s['name'])}</td><td>{cell(s.get('revenue'))}</td><td>{cell(s.get('revenue_yoy'))}</td><td>{cell(s.get('margin'))}</td><td>{cell(s.get('margin_yoy'))}</td>"
                   + (f"<td class=\"mini\">{esc(s.get('note') or '')}</td>" if has_note else "") + "</tr>" for s in segs)
    return (f'<div class="scroll"><table><tr><th>事業群</th><th>營收</th><th>營收 YoY</th><th>{esc(margin_label)}</th><th>YoY</th>{"<th>法說說明</th>" if has_note else ""}</tr>{body}</table></div>'
            + (f'<p class="mini">{esc(seg_note)}</p>' if seg_note else "") + (f'<p class="mini">來源：{esc(src)}</p>' if src else ""))


def five_year_rows(k):
    u, cl = k["unit"], k["cur_label"]
    A = k["annual"]
    def row(label, fn, d=2, suffix=""):
        return f"<tr><td>{label}</td>" + "".join(f"<td>{m(fn(r), d)}{suffix if fn(r) is not None else ''}</td>" for r in A) + "</tr>"
    nm_label, nm_fn = ("稅後淨利率（%，歸屬母公司）", lambda r: r.get("net_margin_parent")) if k["nmp_all"] else ("稅後淨利率（%，合併口徑）", lambda r: r["net_margin"])
    rows = [
        row(f"營收（{cl} 億）", lambda r: yi(r["revenue"], u), 1),
        row("毛利率（%）", lambda r: r["gross_margin"]),
        row("淨利率（稅前）（%）", lambda r: ratio_pct(r["pretax_income"], r["revenue"])),
        row(nm_label, nm_fn),
        row(f"EPS（{esc(k['cur'])}）", lambda r: r["eps"]),
        row(f"營業現金流（{cl} 億）", lambda r: yi(r["operating_cash_flow"], u), 1),
        row("負債比（%）", lambda r: r["debt_ratio"]),
        row("流動比（x）", lambda r: r["current_ratio"]),
    ]
    if k["fin_version"] == "新版實測":
        rows += [row("速動比（x）", lambda r: r.get("quick_ratio")), row("應收天數（days）", lambda r: r.get("dso_days"), 1), row("應付天數（days）", lambda r: r.get("dpo_days"), 1)]
    else:
        missing = '<td colspan="5"><mark>資料缺：bundle fin_rows 無現金／有價證券／應收／應付欄位（新版爬蟲已有）</mark></td>'
        rows += [f"<tr><td>速動比（x）</td>{missing}</tr>", f"<tr><td>應收天數（days）</td>{missing}</tr>", f"<tr><td>應付天數（days）</td>{missing}</tr>"]
    return "".join(rows)


def trend_cards(k):
    u, cl = k["unit"], k["cur_label"]
    A = k["annual"]
    labels = [str(r["fiscal_year"]) for r in A]
    nm_spec = ("稅後淨利率", "(%，歸屬母公司)", [r.get("net_margin_parent") for r in A], 1, "%") if k["nmp_all"] else ("稅後淨利率", "(%，合併口徑)", [r["net_margin"] for r in A], 1, "%")
    specs = [
        ("毛利率", "(%)", [r["gross_margin"] for r in A], 1, "%"),
        ("淨利率（稅前）", "(%)", [ratio_pct(r["pretax_income"], r["revenue"]) for r in A], 1, "%"),
        nm_spec,
        ("EPS", f"({esc(k['cur'])})", [r["eps"] for r in A], 2, ""),
        ("營業現金流", f"({cl} 億)", [yi(r["operating_cash_flow"], u) for r in A], 1, ""),
        ("負債比", "(%)", [r["debt_ratio"] for r in A], 1, "%"),
        ("流動比", "(x)", [r["current_ratio"] for r in A], 2, ""),
    ]
    if k["fin_version"] == "新版實測":
        specs += [("速動比", "(x)", [r.get("quick_ratio") for r in A], 2, ""),
                  ("應收天數", "(days)", [r.get("dso_days") for r in A], 1, ""),
                  ("應付天數", "(days)", [r.get("dpo_days") for r in A], 1, "")]
    out = [f'<div class="trend-card"><h3>{t} <small>{s}</small></h3>{svg_bars(labels, vals, d=d, unit=unit, note_missing="該年來源無值")}</div>' for t, s, vals, d, unit in specs]
    if k["fin_version"] != "新版實測":
        for t, s in (("速動比", "(x)"), ("應收天數", "(days)"), ("應付天數", "(days)")):
            out.append(f'<div class="trend-card"><h3>{t} <small>{s}</small></h3><div class="chart-missing"><mark>資料缺</mark>：需要現金及約當現金／有價證券／應收帳款／應付帳款，bundle 的 fin_rows 沒有（新版爬蟲已補）</div></div>')
    return "\n".join(out)


def chart_5y(k):
    A = k["annual"]
    return svg_rev_opm([str(r["fiscal_year"]) for r in A], [yi(r["revenue"], k["unit"]) for r in A], [r["operating_margin"] for r in A], k["cur_label"])


def chart_5q(k):
    Q = k["q5"]
    note = ""
    if len(Q) < 5:
        note = f'<p class="mini"><mark>資料缺：fin_rows 只有 {len(Q)} 季</mark>（{"、".join(q_label(r["period"]) for r in Q)}）</p>'
    if any(r["operating_margin"] is None for r in Q):
        note += '<p class="mini">推算列（年度 − 前三季）只有營收與淨利，無營業利益率；台股 Q4 因此斷點（新版爬蟲美股 Q4 已推算營業利益，台股尚未）。</p>'
    return svg_rev_opm([q_short(r["period"]) for r in Q], [yi(r["revenue"], k["unit"]) for r in Q], [r["operating_margin"] for r in Q], k["cur_label"]) + note


def ir_section(title, text, extra=""):
    body = esc(text) if text else "<mark>資料缺：無法說會摘要</mark>"
    return f'<section><h2>{title}</h2><p>{body}</p>{extra}</section>'


def ir_sections(n, latest, k):
    """法說 01–05：新版 summary 的 management_views 優先，缺的類別退回 NARRATIVE；03 一律附財報數字對照。"""
    out = []
    for key in ("business", "capacity", "profit", "outlook", "invest"):
        text, src = None, ""
        if latest and latest["views"].get(key):
            text, src = latest["views"][key], f'<p class="mini">來源：新版爬蟲實測 ir_summary {esc(latest["date"])} management_views「{esc(next(t for t, kk in TOPIC_KEYS.items() if kk == key))}」</p>'
        elif n["ir"].get(key):
            text, src = n["ir"][key], '<p class="mini">來源：本報告依舊版 summary／新聞稿人工摘錄</p>' if latest else ""
        extra = src
        if key == "profit":
            extra = (f'<p class="mini"><b>財報對照（fin_rows）</b>：營益率 {esc(k["OPM"])}（去年同季 {esc(k["OPM_LY"])}，{esc(k["OPM_D"])}）、毛利率 {esc(k["GM"])}（{esc(k["GM_LY"])}）；'
                     f'稅前淨利 {esc(k["cur_label"])} {esc(k["PT"])} 億中業外 {esc(k["NONOP"])} 億（{esc(k["NONOP_PCT"])}）。</p>') + src
        out.append(ir_section(IR_TITLES[key], text, extra))
    return "\n".join(out)


def headline_table(latest):
    if not latest or not latest["headline"]:
        return ""
    rows = "".join(f"<tr><td>{esc(x.get('metric'))}</td><td>{esc(x.get('period'))}</td><td>{esc(x.get('value'))}</td><td>{esc(x.get('yoy') or '—')}</td><td class=\"mini\">{esc(x.get('note') or '')}</td></tr>" for x in latest["headline"])
    return (f'<details><summary>法說揭露的重點數字（headline_metrics，{len(latest["headline"])} 條；法說口徑，可能含非 GAAP／自結數，與財報六節的 fin_rows 不同）</summary>'
            f'<div class="scroll"><table><tr><th>指標</th><th>期間</th><th>值</th><th>YoY</th><th>註</th></tr>{rows}</table></div></details>')


def qa_block(latest):
    if not latest:
        return "<mark>資料缺：無逐字稿或 Q&amp;A 紀錄（爬蟲 wanted 只有簡報與財報）</mark>"
    if not latest["qa"]:
        return f"<mark>資料缺：新版爬蟲 qa_highlights 為空</mark>——彙整備註：{esc(latest.get('qa_note') or '未找到本場法說的逐字稿或 Q&A 紀錄')}"
    items = "".join(f"<li><b>Q：</b>{esc(x.get('question'))}<br><b>A：</b>{esc(x.get('answer'))}</li>" for x in latest["qa"])
    return f'<ul class="qa">{items}</ul><p class="mini">來源：新版爬蟲實測 ir_summary {esc(latest["date"])} qa_highlights（LLM 自逐字稿／媒體摘要抽取）</p>'


def auo_block(latest):
    if not latest:
        return "<mark>資料缺：法說摘要沒有 AUO 視角（四支箭／Micro LED／CPO）的判讀；需在爬蟲 LLM prompt 或 build_supplier_report 的 LLM 步驟加入</mark>"
    if latest["auo"]:
        return f"{esc(latest['auo'])}<p class=\"mini\">來源：新版爬蟲實測 ir_summary {esc(latest['date'])} 的 notes（彙整備註）——爬蟲 LLM 已檢查過 AUO／Micro LED／CPO 相關說法；要再深一層（對 AUO 料號的影響）需 build_supplier_report 的 LLM 步驟依料號清單判讀。</p>"
    return "<mark>資料缺：新版爬蟲 notes 未提到是否檢查過 AUO／Micro LED／CPO 相關說法</mark>"


def watch_section(latest):
    if not latest or not (latest["positive"] or latest["watch"] or latest["open_q"]):
        return ""
    def card(title, items):
        return f'<div class="card"><h3>{title}</h3>{("<ul>" + "".join(f"<li>{esc(x)}</li>" for x in items) + "</ul>") if items else "<p class=mini>（空）</p>"}</div>'
    return (f'<section><h2>08　採購觀察｜正向訊號・觀察項・未答問題<small class="mini">（模板外補充；來自新版爬蟲 positive_signals / watch_items / open_questions）</small></h2>'
            f'<div class="three">{card("正向訊號", latest["positive"])}{card("觀察項", latest["watch"])}{card("法說未答／未揭露", latest["open_q"])}</div></section>')


def prev_summaries(sums):
    """最新一場之外的新版 summary 摘成可展開區塊（南亞 Q2 8-21）。"""
    out = []
    for s in sums[:-1]:
        views = "".join(f"<tr><td>{esc(t)}</td><td>{esc(s['views'].get(kk) or '—')}</td></tr>" for t, kk in TOPIC_KEYS.items())
        out.append(f'<details><summary>前一場法說：{esc(s["date"])}（{esc(s["period"])}，{esc(s["reported"] or "")}）的 management_views</summary>'
                   f'<div class="scroll"><table>{views}</table></div>'
                   + (f'<p class="mini">AUO 相關：{esc(s["auo"])}</p>' if s["auo"] else "") + "</details>")
    return "".join(out)


def sources(k, n, sums):
    items = []
    fin_src = k["q"]["source"]
    fin_use = ("財報六節全部數字與圖（新版爬蟲實測 financials，批次 " + esc(k["fin_batch"]) + "；共同欄位與 silver bundle fin_rows 逐值相同）"
               if k["fin_version"] == "新版實測" else "財報六節全部數字與圖（fin_rows）")
    if k["market"] in ("TPE", "TPEx"):
        items.append(("https://mopsov.twse.com.tw/mops/web/index", f"公開資訊觀測站財務報表 API（{esc(fin_src)}）", fin_use))
    else:
        items.append(((k["q"].get("source_urls") or ["#"])[0], f"SEC XBRL companyfacts（{esc(fin_src)}）", fin_use))
    for doc in k["docs"]:
        use = "法說七節、事業群表（簡報／新聞稿文字）" if doc["doc_kind"] == "Presentation" else "原始財報（僅供核對；文字匯出截斷，未用於欄位）"
        items.append((doc["source_url"], f"{esc(doc['file_name'])}（{esc(doc['doc_kind'])}，{doc['page_count']} 頁）", use))
    seen = set()
    for s in reversed(sums):
        for x in s["sources"]:
            if x.get("url") in seen:
                continue
            seen.add(x.get("url"))
            items.append((x.get("url"), f"{esc(x.get('title'))}｜{esc(x.get('media'))}", f"法說摘要（新版爬蟲實測 ir_summary {esc(s['date'])}）"))
    if k["summary"]:
        for s in k["summary"].get("sources") or []:
            if s["url"] not in seen:
                items.append((s["url"], f"{esc(s['title'])}｜{esc(s['media'])}", "法說摘要（bundle summary）"))
    for s in n.get("extra_sources") or []:
        items.append(s)
    if k["ir_url"]:
        items.append((k["ir_url"], "公司投資人關係網站", "法說會資料入口"))
    return "\n".join(f'<li><a href="{esc(u)}">{t}</a>：{use}</li>' for u, t, use in items)


# ---------------------------------------------------------------- 爬蟲 bronze：法說時間軸與資料履歷
def conference_timeline(k, crawler):
    events = {}
    for r in (crawler or {}).get("records", []):
        p = r["payload"] or {}
        if r["record_type"] == "ir_conference" and p.get("conference_date"):
            who = p.get("conference_type") or p.get("location") or "法說會"
            tag = "新版實測 DEV_SAMPLE" if p.get("source") == "DEV_SAMPLE" else (p.get("source") or "行事曆")
            events.setdefault(p["conference_date"], f"{p['conference_date']}（{who}，{tag}）")
        if r["record_type"] == "ir_document":
            for f in p.get("files") or []:
                if f.get("type") == "presentation" and f.get("doc_date"):
                    events.setdefault(f["doc_date"], f"{f['doc_date']}（簡報／新聞稿，{f.get('source') or ''}）")
    conf = k["conference"]
    if conf and conf.get("conference_date"):
        events.setdefault(conf["conference_date"], f"{conf['conference_date']}（{conf.get('conference_type') or '—'}，bundle）")
    return "／".join(events[d] for d in sorted(events))


def report_date(k, crawler):
    """財報公布日：manifest financial_report 的 doc_date（台股 TWSE_DOC 為 null）。"""
    for r in (crawler or {}).get("records", []):
        if r["record_type"] == "ir_document":
            for f in (r["payload"] or {}).get("files") or []:
                if f.get("type") == "financial_report" and f.get("doc_date"):
                    return f["doc_date"]
    return None


def new_crawler_note(k, new, cmp):
    """附錄用：新版爬蟲實測對本報告補了什麼（自動從資料算）。"""
    if not new["batch"]:
        return "<b>新版爬蟲實測：</b>本公司資料夾沒有 _新版實測.md。"
    bits = []
    if new["fin"]:
        nk = [x for x in cmp["new_keys"] if x not in ("_derived",)]
        bits.append(f"financials 多 {len(nk)} 個欄位（{'、'.join(nk)}），共同欄位 {cmp['same']} 個值相同、{cmp['filled']} 個 bundle 為 null 新版有值、"
                    f"{len(cmp['diff'])} 個數值不同{('：' + esc(str(cmp['diff'][:5]))) if cmp['diff'] else ''}"
                    + (f"；新版多的期別 {'、'.join(cmp['missing_periods'])}" if cmp["missing_periods"] else "")
                    + "→ 財報六節改用新版列，速動比／應收天數／應付天數／母公司淨利率補上")
    else:
        bits.append("新版沒有 financials")
    if new["summaries"]:
        for s in new["summaries"]:
            bits.append(f"ir_summary {s['date']}（{s['period']}）：management_views {len(s['views'])}/5 類、事業群 {len(s['segments'])} 列、headline {len(s['headline'])} 條、"
                        f"Q&A {len(s['qa'])} 條、AUO 判讀{'有' if s['auo'] else '無'}、正向／觀察／未答 {len(s['positive'])}/{len(s['watch'])}/{len(s['open_q'])} → 法說 01–08")
    else:
        bits.append("新版仍沒有 ir_summary（manifest 列 missing presentation：爬蟲端找不到本期法說簡報）→ 法說節維持空缺")
    if new["conferences"]:
        bits.append("ir_conference " + "、".join(c.get("conference_date") or "" for c in new["conferences"]) + "（source=DEV_SAMPLE，沙箱種的場次，非行事曆爬到）")
    return "<b>新版爬蟲實測（批次 " + esc(new["batch"]) + "，未進 Databricks）：</b>" + "；".join(bits) + "。"


def lineage_section(k, n, crawler, new, cmp):
    if not crawler:
        return ""
    def row(r):
        url = record_source_url(r)
        src = f'<a href="{esc(url)}">來源</a>' if url else "—"
        return (f"<tr><td>{esc(RECORD_LABEL.get(r['record_type'], r['record_type']))}<div class=\"mini\">{esc(r['record_type'])}</div></td>"
                f"<td style=\"white-space:nowrap\">{esc(record_date(r) or '—')}</td><td>{record_brief(r)}<div class=\"mini\">{esc(r['batch_path'])}</div></td>"
                f"<td>{src}</td><td class=\"mini\">{esc(r['batch_id'])}</td></tr>")
    tables = []
    for ver in ("正式批次", "新版實測"):
        recs = [r for r in crawler["records"] if r.get("version") == ver]
        if not recs:
            continue
        types = {r["record_type"] for r in recs}
        absent = [RECORD_LABEL[t] for t in ("ir_conference", "ir_summary") if t not in types]
        views = "、".join(f'<a href="{esc(v)}">{esc(v)}</a>（{esc(p)}）' for p, v, vv in crawler["views"] if vv == ver)
        tables.append(f'<h3>{esc(ver)}{"（已進 Databricks bronze／silver）" if ver == "正式批次" else "（2026-10-21 爬蟲新版 dev 批次，沙箱輸出）"}</h3>'
                      f'<p class="mini">原文見 {views}。{("<b>沒有的紀錄：</b>" + esc("、".join(absent)) + "。") if absent else ""}</p>'
                      f'<div class="scroll"><table><tr><th>紀錄</th><th>日期</th><th>內容</th><th>來源</th><th>批次</th></tr>{"".join(row(r) for r in recs)}</table></div>')
    return f"""
<section><h2>附錄　資料履歷｜爬蟲抓到的法說與文件（bronze，{esc(crawler['period'])}）</h2>
<p class="mini">來源 <code>b_ir_calendar_record.payload</code>（正式批次）與爬蟲新版沙箱輸出（新版實測），同一檔只留最新批次；silver bundle 見 <a href="{esc(k['name'])}_原始資料.html">{esc(k['name'])}_原始資料.html</a>。</p>
{"".join(tables)}
<div class="note">{new_crawler_note(k, new, cmp)}</div>
<div class="note"><b>正式批次 vs bundle：</b>{esc(n.get("crawler_note", ""))}</div>
</section>"""


# ---------------------------------------------------------------- 敘事（逐家）
def narr_glw(k):
    return dict(
        conclusion=(f"Corning 2026 Q2 營收 US$ {k['REV_Q']} 億（YoY {k['YOY']}），管理層稱連續第 9 季年增；GAAP 營益率 {k['OPM']}（去年同期 {k['OPM_LY']}）、毛利率 {k['GM']}。"
                    f"成長集中在光通訊（+32%）與太陽能（+90%），顯示玻璃所在的 Glass Innovations 只年增 1%。負債比 {k['DR']} 多年維持 58–60%，流動比 {k['CR']}x，上半年營業現金流 US$ {k['OCF']} 億高於上半年淨利 US$ {k['NI_YTD']} 億。"
                    "對 AUO 採購的意義：財務面沒有降載理由，風險在資源配置——資本支出優先給光纖與光連接器，顯示玻璃的產能與價格策略要每季追；玻璃基板關鍵世代維持 AGC／NEG 備援配額。"
                    "GAAP EPS 0.64 與 core EPS 0.78 的差距來自避險損益、一次性稅務與重組，本報告一律用 GAAP。"),
        segments=[
            dict(name="Optical Communications", revenue="US$ 2,072M", revenue_yoy="+32%", margin="21.1%", margin_yoy="+5.3 pt"),
            dict(name="Glass Innovations（顯示＋特殊材料）", revenue="US$ 1,463M", revenue_yoy="+1%", margin="24.2%", margin_yoy="+1.7 pt"),
            dict(name="Automotive", revenue="US$ 471M", revenue_yoy="+2%", margin="17.4%", margin_yoy="+0.2 pt"),
            dict(name="Solar", revenue="US$ 438M", revenue_yoy="+90%", margin="−1.6%", margin_yoy="−2.5 pt"),
            dict(name="Life Sciences & Emerging Growth", revenue="US$ 294M", revenue_yoy="−15%", margin="−7.1%", margin_yoy="−8.9 pt"),
        ],
        seg_margin_label="部門淨利率",
        seg_note="來源：2026-07-28 新聞稿（Exhibit 99）部門表，人工摘錄；新聞稿只有部門淨利（net income），無部門 OPM，利潤率欄為部門淨利／部門營收。2026 Q1 起部門重分類（Display＋Specialty Materials 合併為 Glass Innovations），前期已重編。",
        ir=dict(
            business="光通訊營收年增 32%、其中企業網路 +65%，Gen AI 產品成長更快；Glass Innovations（顯示玻璃＋特殊材料）年增 1%、淨利年增 9%；汽車 +2%；太陽能 +90%（Hemlock 多晶矽＋晶圓／模組）；生命科學與新興事業 −15%、持續虧損。",
            capacity="與 NVIDIA 的長期合作下，美國光連接器產能擴 10 倍、光纖產能擴 50% 以上；太陽能晶圓廠完成延長歲修與設備升級、持續 ramp，目標年營收 US$ 30 億以上。顯示玻璃未提產能變化。",
            profit=f"GAAP 營益率 {k['OPM']}（去年同期 {k['OPM_LY']}，{k['OPM_D']}），毛利率 {k['GM']}（{k['GM_LY']}）；core 營益率 20.9%（+190 bp）、core 毛利率 39.6%（+120 bp）、core ROIC 14.9%。業外（避險損益、利息）US$ {k['NONOP']} 億，本業獲利為主。",
            outlook="Q3 指引：core 營收 US$ 49–50 億（年增約 16%）、core EPS 0.85–0.89（年增約 28%）；太陽能自 Q3 起改善獲利。Springboard 計畫：年化營收 2026 底 US$ 200 億、2028 底 300 億、2030 底 400 億，2026 Q4–2030 Q4 營收 CAGR 19%，獲利成長快於營收。",
            invest="與 Amazon 簽多年、數十億美元的光纖／纜線／連接方案供應協議；與 NVIDIA 建立長期合作擴美國產能。5 月發行 18M 股認股權證（記入資本公積）。無 M&A；持續精簡製造據點未提及。",
            auo=None, qa=None,
        ),
        ir_src="2026-07-28 第二季財報新聞稿（SEC 8-K Exhibit 99，docs[0]）；本公司沒有 summary（法說摘要）列，也無逐字稿",
        limits=("幣別為美元，金額以「億美元」呈現。財報數字為 SEC companyfacts 的 GAAP 數字；法說節的 core（非 GAAP）指標為管理層口徑，與財報六節不可直接相減。資本支出欄位在 financials 為空（10-Q 文字有：Q2 US$422M）；季度 OCF 以年初累計對照。"
                "速動比 2021–2022 無值（SEC companyfacts 該兩年缺現金 tag）。事業群表為法說 LLM 抽取的新聞稿部門表，利潤率欄是「部門淨利」字串而非 OPM。"),
        crawler_note="爬蟲 bronze 對照（2026Q2）：文件 manifest（8-K EX-99 2026-07-28、10-Q 2026-07-29，皆 EDGAR）、兩個實體檔、財報數據（批次 000030），沒有 ir_conference 與 ir_summary；內容與 bundle 相同。7-28 法說電話會議只在新聞稿文字裡，行事曆沒有這一場。",
    )


def narr_npc(k):
    return dict(
        conclusion=(f"南亞 2026 Q2 營收 NT$ {k['REV_Q']} 億（YoY {k['YOY']}），毛利率 {k['GM']}（去年同期 {k['GM_LY']}）、營益率 {k['OPM']}（{k['OPM_LY']}），電子材料（玻纖布、銅箔基板、ABF 載板）帶動本業由 2023–2025 低谷翻揚，四大事業部 Q2 首度全面轉盈。"
                    f"但單季稅前淨利 NT$ {k['PT']} 億中業外約 NT$ {k['NONOP']} 億、占 {k['NONOP_PCT']}（上半年南亞科技權益法貢獻年增 NT$ 230.4 億、台塑石化 +104.0 億），淨利率 {k['NM']} 遠高於營益率；上半年營業現金流只有 NT$ {k['OCF']} 億，對比上半年淨利 NT$ {k['NI_YTD']} 億，獲利大多尚未變現。"
                    f"負債比 {k['DR']}、流動比 {k['CR']}x，資產負債表緩衝充足。對 AUO 採購：聚酯膜／離型膜等顯示相關料號供應面有增量（2026/10 離型膜第 5、6 套投產），但 Q3 化工、聚酯淡季停車要確認不波及；評估體質看營業利益而非淨利。"),
        segments=[
            dict(name="電子材料", revenue="占 2026 H1 營收 52.7%", revenue_yoy="H1 2025 為 44.1%", margin="19.9%", margin_yoy="+15.9 pt（2Q25 4.0%）"),
            dict(name="化工產品", revenue="占 16.9%", revenue_yoy=None, margin="2.1%", margin_yoy="轉盈（2Q25 虧損）"),
            dict(name="聚酯產品", revenue="占 15.8%", revenue_yoy=None, margin="5.3%", margin_yoy="轉盈（2Q25 虧損）"),
            dict(name="塑膠加工", revenue="占 12.7%", revenue_yoy=None, margin="9.7%", margin_yoy=None),
        ],
        seg_margin_label="Q2 營益率",
        seg_note="來源：法說摘要（2026-10-13 與 2026-09-21 summary，皆取自《2026 年上半年營運概況》簡報）；簡報給營收占比與部門營益率，沒有部門營收金額與 YoY，「轉盈」依簡報「2Q26 四大事業部首度全面轉盈」推得。",
        ir=dict(
            business="電子材料為上半年成長核心：AI 伺服器、高效運算、高階網通帶動銅箔基板、玻纖布、ABF 載板，產能利用率 9 成以上、價量齊揚，占營業利益 77.1%（1Q26 曾達 127.2%）。化工受惠乙二醇利差與庫存利益、聚酯受惠瓶用粒旺季與美國在地採購，Q2 雙雙轉盈；塑膠加工受惠電子產業與工程建案。",
            capacity="台灣離型膜第 5、6 套（各 144,000 千米平方）與聚合線改造共聚酯粒 2026/10 投產；電子級液態 CO2 2027/3；中國大陸銅箔擴建 2028/1。電子材料產線維持高開動率。",
            profit=f"營益率 {k['OPM']}（去年同期 {k['OPM_LY']}，{k['OPM_D']}）；電子材料營益率 2Q25 4.0% → 1Q26 13.1% → 2Q26 19.9%。稅前淨利 NT$ {k['PT']} 億中業外 NT$ {k['NONOP']} 億（{k['NONOP_PCT']}），為權益法收益，屬帳面；上半年 OCF NT$ {k['OCF']} 億 vs 淨利 NT$ {k['NI_YTD']} 億。",
            outlook="Q3 展望：電子材料、聚酯膜、環氧樹脂價量皆揚，中高階基板與消費電子材料供應偏緊；化工、聚酯進入淡季且受中東戰事與原料供應不確定性影響，市況偏弱、部分產線安排停車；塑膠建材需求穩定。2026 年 7 月營收 NT$ 305.73 億、年增 44.53%（近 49 個月新高，法說前公告）。媒體提醒 M8／M9 高階 CCL 驗證與擴產後供需平衡是獲利能否延續的關鍵。",
            invest="投資集中在擴產（離型膜、電子級 CO2、銅箔）；轉投資南亞科技、台塑石化貢獻大增是上半年稅前淨利躍升的主因。無 M&A 與組織整改訊息。",
            auo=None, qa=None,
        ),
        ir_src="2026-10-13 法說會摘要（2026Q3 summary）＋ 2026-09-21 法說會摘要（2026Q2 summary，爬蟲 bronze）＋ 法說簡報《2026 年上半年營運概況》；無逐字稿",
        limits=("法說資料基準為 2026 Q3（2026-10-13 法說，新版爬蟲彙整註明簡報 PDF 無法解析、內容多為 10-12 自結公告與法人報導轉述），財務數字最新只到 2026 Q2；Q3 財報 11 月中才公布。財報數字來自 MOPS（千元換算億元）；2025 Q4 季度列為推算，無毛利率與營益率，五季圖 Q4 斷點。"
                "季度 OCF 與資本支出以年初累計對照。事業群表為法說口徑：Q3 只有電子材料有營收估算與營益率，其餘三部門只有文字；Q2 那場有四部門營益率（見「前一場法說」）。法說 Q3 營益率 19.2% 為自結數，財報 Q3 未出不能對照。"),
        crawler_note=("爬蟲 bronze 對照：2026Q3 四筆（場次 10-13、彙整 10-13、簡報 manifest、財報數據）與 bundle 逐字相同；manifest 為 PARTIAL、缺 financial_report 是 Q3 財報未出。"
                      "2026Q2 另有 2026-09-21 的 ir_summary（內容比 10-13 那份細：電子材料營益率逐季、權益法增額、7 月月營收、M8／M9 驗證風險），本報告法說節已引用；2026-09-24 的 ir_summary 只找到公告。"
                      "三場法說（8-21 玉山、9-24 中信、10-13 摩根大通）在 MOPS 各一份簡報檔（0820／0910／1012），標題皆《2026 年上半年營運概況》。2026Q2 財報 PDF 已在 Volume，2026Q3 bundle 沒帶進來。"),
    )


def narr_chimei(k):
    return dict(
        conclusion=(f"奇美實業 2026 Q2 營收 NT$ {k['REV_Q']} 億（YoY {k['YOY']}），營收已連續五年下滑（2021 NT$ 1,786.7 億 → 2025 NT$ 1,136.8 億）；毛利率 {k['GM']}、營益率 {k['OPM']}，本業在損益兩平邊緣，2023–2025 三年本業皆虧損、淨利靠業外。"
                    f"上半年營業現金流 NT$ {k['OCF']} 億為負。負債比 {k['DR']}、流動比 {k['CR']}x，短期無償債風險，問題在獲利能力與現金創造。"
                    "本公司沒有法說會摘要、沒有法說場次紀錄，法說七節全部空缺。對 AUO 採購：PMMA／光學板材等關鍵料號維持 2nd source，若 OCF 連續兩個半年為負或營收再年減 10% 以上，升級 QBR 並評估降載。"),
        segments=None,
        seg_note="財報 PDF 文字匯出截斷在 20,006 字，部門資訊附註不在匯出內。",
        ir=dict(business=None, capacity=None,
                profit=f"（財報推得）營益率 {k['OPM']}（去年同期 {k['OPM_LY']}，{k['OPM_D']}）；稅前淨利 NT$ {k['PT']} 億中營業利益只有 NT$ {k['OI']} 億，淨利幾乎全靠業外。2023–2025 全年營益率 −1.37% / −0.89% / −0.41%。無法說資料可對照管理層說法。",
                outlook=None, invest=None, auo=None, qa=None),
        ir_src=None,
        limits=("沒有法說會摘要（summary 為空）、沒有法說場次（新版爬蟲 manifest 亦列 missing presentation），法說七節除「獲利能力變化」用財報數字反推外全部空缺。財報只有 2025 Q2 與 2026 Q2 兩個季度列（MOPS 半年報公司），五季圖只有兩點。"
                "2023 年淨利為負但 EPS 為正（0.05），兩者口徑不同；2026 Q2 合併淨利 NT$ 4.36 億、歸屬母公司 NT$ 9.75 億，非控制權益為負。財報 PDF 文字匯出截斷在 20,006 字。公司主檔缺產業別、官網與 IR 網址。"),
        crawler_note="爬蟲 bronze 對照（2026Q2）：只有文件 manifest（wanted 只列 financial_report，爬蟲端判定本期無法說簡報）、Q2 財報 PDF 實體檔、財報數據（批次 000030）；沒有 ir_conference、ir_summary，與 bundle 相同，確認「無法說」是來源端就沒有。",
    )


def narr_everlight(k):
    return dict(
        conclusion=(f"永光化學 2026 Q2 營收 NT$ {k['REV_Q']} 億（YoY {k['YOY']}），毛利率 {k['GM']} 較去年同期 {k['GM_LY']} 明顯改善，營益率 {k['OPM']}（{k['OPM_LY']}）；2025 全年虧損（EPS −0.21）後 2026 上半年連兩季轉盈。"
                    f"規模小（年營收不到 NT$ 100 億），五年營收由 NT$ 92.0 億降至 75.7 億。負債比 {k['DR']}、流動比 {k['CR']}x，上半年營業現金流 NT$ {k['OCF']} 億為正且高於淨利 NT$ {k['NI_YTD']} 億。"
                    "沒有法說會摘要與場次紀錄。對 AUO 採購：採購金額小，重點是供應連續性而非財務承壓；光阻、色料關鍵料號確認第二供應商認證進度；若毛利率回落至 20% 以下或連兩季本業虧損，升級 QBR。"),
        segments=None,
        seg_note="財報 PDF 文字匯出截斷在 20,006 字，部門資訊附註不在匯出內。",
        ir=dict(business=None, capacity=None,
                profit=f"（財報推得）營益率 {k['OPM']}（去年同期 {k['OPM_LY']}，{k['OPM_D']}）；毛利率 2025 Q3 15.95% → 2026 Q2 {k['GM']}，本業轉盈。2025 全年營益率 −2.59%。獲利基數小（Q2 淨利 NT$ {k['NI']} 億），一季匯損或存貨跌價即翻負。",
                outlook=None, invest=None, auo=None, qa=None),
        ir_src=None,
        limits=("沒有法說會摘要與場次（新版爬蟲 manifest 亦列 missing presentation），法說七節除「獲利能力變化」外全部空缺。財報數字來自 MOPS（千元換算億元），季度 OCF 與資本支出以年初累計對照；2025 Q4 列為推算，五季圖 Q4 無營益率。"
                "財報 PDF 文字匯出截斷在 20,006 字。公司英文名在主檔被截斷（Corporatio）。"),
        crawler_note="爬蟲 bronze 對照（2026Q2）：只有文件 manifest（wanted 只列 financial_report）、Q2 財報 PDF 實體檔、財報數據（批次 000030）；沒有 ir_conference、ir_summary，與 bundle 相同。主檔 IR 網址指向公司法說頁，爬蟲端可據此補抓是否真的沒開法說。爬蟲檔尾端貼上時截斷，解析時已補括號。",
    )


def narr_eternal(k):
    return dict(
        conclusion=(f"長興材料 2026 Q2 營收 NT$ {k['REV_Q']} 億（YoY {k['YOY']}），毛利率 {k['GM']}（去年同期 {k['GM_LY']}）、營益率 {k['OPM']}（{k['OPM_LY']}），合併稅後淨利 NT$ {k['NI']} 億（歸屬母公司 8.47 億）為近四年單季新高；三大事業群（合成樹脂、電子材料、特用材料）同步回升。"
                    f"上半年營業現金流 NT$ {k['OCF']} 億高於淨利 NT$ {k['NI_YTD']} 億。負債比 {k['DR']} 在台廠中偏高（五年由 59.25% 降至此），流動比 {k['CR']}x；董事會核准近 NT$ 20 億新資本支出（蘆竹、湖北、泰國）2027 年後開出，資金需求上升要留意。"
                    "對 AUO 採購：乾膜光阻、光學膜／特用材料維持 2nd source，新廠量產前不集中轉單；法說摘要來自財經媒體，「上半年營業利益率 24%」與財報營益率不符，引用以財報為準。"),
        segments=None,
        seg_note="法說摘要只說三大事業群「營收與獲利同步年增」，沒有數字；財報 PDF 匯出截斷，部門附註不在內。",
        ir=dict(
            business="合成樹脂、電子材料、特用材料三大事業群營收與獲利同步年增；Q2 毛利率較 Q1 明顯增長，來自產品組合優化與原物料漲價成本即時轉嫁。",
            capacity="董事會核准近 NT$ 20 億新資本支出：蘆竹廠特用材料擴產、湖北合資企業、泰國新電子材料廠；新產能預計 2027 年後陸續開出，稼動時程有不確定性。",
            profit=f"營益率 {k['OPM']}（去年同期 {k['OPM_LY']}，{k['OPM_D']}）；毛利率 2026 Q1 22.16% → Q2 {k['GM']}，營益率 5.22% → {k['OPM']}，與管理層「明顯增長」一致。媒體引述「上半年營業利益率 24%」接近毛利率，口徑有誤；「負債比率由 180 降至 174」口徑不明。",
            outlook="管理層對特用材料長期成長保持正面，將持續投入產能與技術；未給下半年具體財測。風險：歐洲市場需求疲弱、人民幣匯率波動、新產能稼動時程。",
            invest="近 NT$ 20 億資本支出（蘆竹／湖北／泰國）。現金部位約 NT$ 103 億、資產負債表規模約 NT$ 670 億（媒體轉述）。無 M&A 與組織整改訊息。",
            auo=None, qa=None,
        ),
        ir_src="2026-08-13 法說會摘要（summary；來源為 BigGo Finance、聯合新聞網、經濟日報三則報導，簡報與逐字稿未取得）",
        limits=("法說摘要來自財經媒體與富果備忘錄（新版爬蟲註明 MOPS 簡報為圖片式 PDF、財報 PDF 加密，皆無法讀字），部分指標口徑與財報不符：法說「Q2 毛利率 24.8%」與財報毛利率一致，但「上半年營業利益率 24%」實為毛利率口徑；Q2 稅後淨利 8.47 億為歸屬母公司、財報合併淨利 {NI} 億含非控制權益。"
                "財報數字來自 MOPS（千元換算億元）；季度 OCF 與資本支出以年初累計對照；2025 Q4 列為推算、五季圖 Q4 無營益率。事業群表只有營收占比文字，無金額與利潤率。應收天數 126–145 天為五家最高，與法說「現金 103 億」一起看。".replace("{NI}", k["NI"])),
        crawler_note="爬蟲 bronze 對照（2026Q2）：ir_summary（2026-09-21，批次 000002）與 bundle 逐字相同；文件 manifest 的 wanted 只列 financial_report，且沒有 ir_conference——2026-08-13 這場法說只存在於彙整文字裡，行事曆漏抓（backlog B1），簡報也因此沒抓。",
    )


NARRATIVE = {"NYSE:GLW": narr_glw, "TPE:1303": narr_npc, "TPE:1763": narr_chimei, "TPE:1711": narr_everlight, "TPE:1717": narr_eternal}


# ---------------------------------------------------------------- HTML
CSS = """
*{box-sizing:border-box}body{margin:0;background:#edf7fc;color:#111111;font:15px/1.7 system-ui,'Noto Sans TC','Microsoft JhengHei',sans-serif}
header{background:linear-gradient(110deg,#0066B3,#26A9E0);color:white;padding:34px max(22px,calc((100vw - 1100px)/2))}h1{margin:0}header p{margin:6px 0 0}
main{max-width:1100px;margin:auto;padding:20px}
.band{background:#7752A8;color:white;padding:12px 20px;border-radius:10px;margin:26px 0 14px;font-size:20px;font-weight:bold}
section{background:white;border:1px solid #cbe7f6;border-radius:15px;padding:22px;margin:15px 0;box-shadow:0 5px 20px #0066b318}
h2{margin:0 0 12px;color:#0066B3;font-size:20px}h3{color:#7752A8}
table{border-collapse:collapse;width:100%;min-width:670px}th,td{text-align:left;border-bottom:1px solid #cbe7f6;padding:9px 11px;vertical-align:top}th{background:#def3fb;color:#0066B3}
.scroll{overflow:auto}
.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}
.kpi{background:#def3fb;border-top:4px solid #26A9E0;border-radius:11px;padding:13px}.kpi:nth-child(2){border-color:#F5C400}.kpi:nth-child(3){border-color:#40A86B}.kpi:nth-child(4){border-color:#7752A8}
.kpi b{display:block;font-size:23px;color:#111111}.kpi small,.mini{font-size:12px;color:#111111}
.note{background:#fff9d9;border-left:4px solid #F5C400;padding:12px;margin:12px 0}
.two{display:grid;grid-template-columns:1fr 1fr;gap:14px}.card{padding:14px;background:#f2eefa;border:1px solid #d9cbed;border-radius:10px}
a{color:#0066B3}footer{padding:15px}
.delta-positive{color:#238451;font-weight:700}.delta-negative{color:#C62828;font-weight:700}
.trend-grid{display:grid;grid-template-columns:minmax(0,1fr);gap:26px;margin-top:26px}
.trend-card{border:1px solid #cbe7f6;border-radius:12px;padding:22px 24px;background:#fff;overflow:hidden}.trend-card h3{margin:0 0 12px;color:#7752A8;font-size:20px}.trend-card small{font-weight:normal;color:#444}
.svgchart{width:100%;height:auto;display:block}.svgchart .ax{font-size:13px;fill:#444}.svgchart .val{font-size:14px;font-weight:700;fill:#111}.svgchart .ttl{font-size:14px;font-weight:700;fill:#333}.svgchart .miss{font-size:11px;fill:#7752A8}
.chart-missing{padding:30px 12px;text-align:center;color:#444;background:#f7fbfe;border:1px dashed #cbe7f6;border-radius:10px}
.three{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}.three .card h3{margin:0 0 8px;font-size:16px}.three ul{margin:0;padding-left:18px}
ul.qa{padding-left:18px}ul.qa li{margin-bottom:10px}
details{margin:10px 0}summary{cursor:pointer;color:#0066B3}
@media(max-width:720px){.three{grid-template-columns:1fr}}
mark{background:#fff3b0;color:inherit;padding:0 3px;border-radius:3px}
code{font-size:12px;background:#f2f6fa;padding:1px 4px;border-radius:4px}
@media(max-width:720px){.grid,.two{grid-template-columns:1fr 1fr}}@media(max-width:480px){.grid,.two{grid-template-columns:1fr}}
@media print{body{background:#fff}section{box-shadow:none;break-inside:avoid}mark{background:none}}
"""


def render(k: dict, n: dict, crawler: dict | None, new: dict, cmp: dict) -> str:
    cl = k["cur_label"]
    tl = conference_timeline(k, crawler)
    conf_line = esc(tl) if tl else "<mark>資料缺：行事曆與爬蟲皆無場次</mark>"
    rd = report_date(k, crawler)
    rd_line = esc(rd) if rd else "<mark>資料缺：財報 manifest 的 doc_date 為 null（TWSE_DOC）</mark>"
    period_line = f"{k['q_label']} 財報" + (f"＋{q_label(k['period'])} 法說" if k["period"] != k["q"]["period"] else "")
    sums = new["summaries"]
    latest = sums[-1] if sums else None
    segs, seg_label, seg_note, seg_src = segments_for(n, latest)
    if latest:
        ir_src = (f'<p class="mini">法說資料來源：新版爬蟲實測 ir_summary {esc("、".join(s["date"] for s in sums))}（批次 {esc(new["batch"])}；最新一場 {esc(latest["date"])}，報告期間「{esc(latest["reported"] or "")}」）'
                  + (f'；舊版：{esc(n["ir_src"])}' if n.get("ir_src") else "") + "</p>")
    elif n.get("ir_src"):
        ir_src = f'<p class="mini">法說資料來源：{esc(n["ir_src"])}</p>'
    else:
        ir_src = '<p class="mini"><mark>資料缺：本公司沒有法說會摘要（summary）與場次紀錄（新版爬蟲實測亦無：manifest 列 missing presentation）；以下各節除「獲利能力變化」用財報數字反推外皆空缺</mark></p>'
    auo = auo_block(latest) if latest else (esc(n["ir"]["auo"]) if n["ir"].get("auo") else auo_block(None))
    qa = qa_block(latest) if latest else (esc(n["ir"]["qa"]) if n["ir"].get("qa") else qa_block(None))
    fin_line = (f"財報數字：新版爬蟲實測 financials（批次 {esc(k['fin_batch'])}，共同欄位與 silver bundle 逐值相同{'' if not cmp['diff'] else '，<b>' + str(len(cmp['diff'])) + ' 個值不同，見附錄</b>'}）"
                if k["fin_version"] == "新版實測" else "財報數字：silver bundle fin_rows")
    quick_note = ("速動比＝速動資產／流動負債；速動資產＝現金及約當現金＋按公允價值衡量之金融資產（流動）＋應收票據＋應收帳款（含關係人），新版爬蟲已算（quick_ratio）。"
                  if k["fin_version"] == "新版實測" else "速動比＝（現金及約當現金＋有價證券＋應收帳款淨額）／流動負債，bundle fin_rows 沒有分子三個欄位（新版爬蟲已補）。")
    formula_note = ("公式：毛利率＝毛利／營收；稅前淨利率＝稅前利益／營收；稅後淨利率＝歸屬母公司淨利／營收（模板口徑，新版爬蟲 net_margin_parent）；負債比＝總負債／總資產；流動比＝流動資產／流動負債；"
                    "速動比＝速動資產／流動負債；應收天數＝平均應收帳款／營收×365；應付天數＝平均應付帳款／銷貨成本×365（最早一年用期末值，其餘期初期末平均）。比率欄直接取爬蟲算好的值，稅前淨利率由本頁計算。"
                    if k["fin_version"] == "新版實測" else
                    "公式：毛利率＝毛利／營收；稅前淨利率＝稅前利益／營收；稅後淨利率＝合併淨利／營收（模板為歸屬公司淨利，bundle fin_rows 年度列無此欄）；負債比＝總負債／總資產；流動比＝流動資產／流動負債。"
                    "比率欄直接取 fin_rows（爬蟲端已算），稅前淨利率由本頁計算。速動比、應收天數、應付天數需現金、有價證券、應收、應付四欄，bundle 沒有。")

    return f"""<!doctype html>
<html lang="zh-Hant-TW">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(k['name'])}｜財報＋法說整合報告</title>
<!--
由 build_report.py 依 {TEMPLATE_REF} 產出；資料來源：範例財報/{esc(k['name'])}/{esc(k['name'])}.md（silver bundle JSON）
＋ {esc(k['name'])}_爬蟲*.md（bronze payload：頁首法說時間軸、附錄資料履歷）。
模板的 12 張 PNG 改為 inline SVG。黃底 <mark> 為資料集給不出的欄位，對照 模板覆蓋度評估.md。
-->
<style>{CSS}</style>
</head>
<body>
<header>
  <h1>{esc(k['name'])}｜財報＋法說整合報告</h1>
  <p>{esc(period_line)} ｜ {esc(k['market'])}: {esc(k['code'])}{('｜' + esc(k['industry'])) if k['industry'] else ''}</p>
  <p>財報公布：{rd_line}　·　法說會：{conf_line}</p>
  <p class="mini" style="color:#d8e8f7">產出日期：{TODAY}｜版本：{VERSION}｜金額單位：{cl} 億（原始 {esc(k['unit_note'])} 換算）｜{fin_line}</p>
</header>
<main>

<section><h2>給 AUO 採購主管的結論</h2><p>{esc(n['conclusion'])}</p></section>

<div class="band">財報資訊</div>

<section><h2>01　財報重點</h2><div class="grid">
{kpi_cards(k, segs)}
</div></section>

<section><h2>02　財報實績</h2><div class="scroll"><table>
<tr><th>指標</th><th>{k['q_label']}</th><th>{k['q_ly_label']}</th><th>同比變動／對照</th></tr>
{actual_table(k)}
</table></div>
<div class="mini" style="margin-top:12px;line-height:1.7"><p style="margin:0 0 8px">營業現金流為年初累計（YTD）對去年同期累計，非單季；流動比為資產負債表時點數據。營業利益率的同比以百分點（pt）表示。</p>
<p style="margin:0">{quick_note}</p></div></section>

<section><h2>03　事業群財務表現</h2>{segment_table(segs, seg_label, seg_note, seg_src)}</section>

<section><h2>04　五年趨勢｜營收 × OPM</h2>{chart_5y(k)}<p class="mini">年度 fin_rows（{k['annual'][0]['fiscal_year']}–{k['annual'][-1]['fiscal_year']}）；上格營收、下格營業利益率，共用年度軸。</p></section>

<section><h2>05　五季趨勢｜營收 × OPM</h2>{chart_5q(k)}<p class="mini">最近 {len(k['q5'])} 個季度列；季度與年度口徑不同，不可與第 04 節直接比較。</p></section>

<section><h2>06　近五年財務指標｜{k['annual'][0]['fiscal_year']}–{k['annual'][-1]['fiscal_year']}</h2>
<div class="scroll"><table><tr><th>指標</th>{"".join(f"<th>{r['fiscal_year']}</th>" for r in k['annual'])}</tr>
{five_year_rows(k)}
</table></div>
<div class="trend-grid">
{trend_cards(k)}
</div>
<p class="mini">{formula_note}</p></section>

<div class="band">法說會資訊</div>
{ir_src}
{headline_table(latest)}
{ir_sections(n, latest, k)}
<section><h2>06　友達4支箭與 Micro LED 相關議題</h2><p>{auo}</p></section>
<section><h2>07　Q&amp;A 重點</h2>{qa}</section>
{watch_section(latest)}
{prev_summaries(sums)}

<section><h2>資料來源與限制</h2>
<ul>
{sources(k, n, sums)}
</ul>
<div class="note"><b>限制：</b>{esc(n['limits'])} 通用限制：第 01／02 節與五季圖的淨利為合併淨利（含非控制權益），EPS 以歸屬母公司淨利計算；金額由原始單位（{esc(k['unit_note'])}）換算為億、小數第二位四捨五入；法說節文字為爬蟲 LLM 彙整（含媒體轉述），正式決策前仍應以公開資訊觀測站／SEC 及公司合併財報附註為準。</div>
</section>
{lineage_section(k, n, crawler, new, cmp)}
<footer class="mini">{esc(k['name'])} 財報與法說整合報告｜{TODAY}｜Version {VERSION}｜依 {TEMPLATE_REF} 產出</footer>
</main>
</body>
</html>
"""


# ---------------------------------------------------------------- index
CRAWLER_HELP = {
    "NYSE:GLW": "無新增（與 bundle 相同）",
    "TPE:1303": "<b>有</b>：多一份 2026Q2 法說彙整＋兩場法說場次，已併入法說節",
    "TPE:1763": "無新增；確認來源端就無法說",
    "TPE:1711": "無新增；確認來源端就無法說",
    "TPE:1717": "無新增；發現 8-13 法說場次未進行事曆",
}


def new_help(new: dict, cmp: dict | None) -> str:
    """index 用：新版爬蟲實測對報告補了什麼（短句）。"""
    if not new["batch"]:
        return "—"
    bits = []
    if new["fin"]:
        bits.append(f"財報 +{len([x for x in cmp['new_keys'] if x != '_derived'])} 欄 → 速動比／應收付天數／母公司淨利率")
    if new["summaries"]:
        s = new["summaries"][-1]
        bits.append(f"法說 01–05 全填（management_views）、Q&amp;A {len(s['qa'])} 條、事業群 {len(s['segments'])} 列、採購觀察 08")
    else:
        bits.append("仍無法說（missing presentation）")
    return "<b>有</b>：" + "；".join(bits)


def index_page(rows: list[dict]) -> str:
    body = "".join(
        f"<tr><td><b>{esc(r['name'])}</b><div class=\"mini\">{esc(r['key'])}</div></td><td>{esc(r['period'])}</td>"
        f"<td>{esc(r['conf'])}</td><td>{esc(r['summary'])}</td><td>{r['crawler']}</td><td>{r['new']}</td><td>{r['marks']}<div class=\"mini\">舊版 {r['marks_old']}</div></td>"
        f"<td><a href=\"{esc(r['name'])}/{esc(r['name'])}.html\">報告</a>｜<a href=\"{esc(r['name'])}/{esc(r['name'])}_原始資料.html\">原始資料</a>｜{r['crawler_links']}</td></tr>"
        for r in rows)
    return f"""<!doctype html>
<html lang="zh-Hant-TW"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>範例財報｜財報＋法說整合報告 × 兩種資料來源</title><style>{CSS}</style></head>
<body>
<header><h1>供應商 財報＋法說整合報告 × 兩種資料來源</h1>
<p>每家一個資料夾：<b>報告</b>（依 v20261007 版型產出）、<b>原始資料</b>（Databricks silver bundle，報告的輸入）、<b>爬蟲資料</b>（bronze payload：正式批次＝已進 Databricks；新版實測＝2026-10-21 爬蟲新版 dev 批次）</p>
<p class="mini" style="color:#d8e8f7">產出日期：{TODAY}｜版本：{VERSION}</p></header>
<main>
<section><h2>五家供應商</h2>
<div class="scroll"><table><tr><th>公司</th><th>bundle 期別</th><th>法說場次（行事曆＋爬蟲）</th><th>法說彙整</th><th>正式批次 bronze 對報告的幫助</th><th>新版爬蟲實測對報告的幫助</th><th>黃底數</th><th>頁面</th></tr>
{body}</table></div>
<div class="note">黃底 <mark>資料缺</mark> 為資料集給不出的欄位；「舊版」黃底數＝只用 bundle＋正式批次時的數字。覆蓋度結論與對 pipeline 的建議見 <code>模板覆蓋度評估.md</code>。</div>
</section>
</main>
<footer class="mini">範例財報｜{TODAY}｜Version {VERSION}</footer>
</body></html>
"""


def build_one(name: str, d: dict, crawler: dict | None, use_new: bool = True):
    """回傳 (page_html, k, new, cmp)；use_new=False 時忽略新版實測（用來算舊版黃底數）。"""
    new = pick_new(crawler) if use_new else dict(fin=None, fin_rec=None, summaries=[], conferences=[], manifests=[], batch=None)
    cmp = None
    new_rows = None
    if new["fin"]:
        new_rows = rows_from_new_fin(new["fin"], new["fin_rec"])
        cmp = compare_fin(d["fin_rows"], new_rows)
    k = build_k(d, new_rows)
    n = NARRATIVE[k["key"]](k)
    if not use_new:
        crawler = dict(crawler, records=[r for r in crawler["records"] if r.get("version") != "新版實測"],
                       views=[v for v in crawler["views"] if v[2] != "新版實測"]) if crawler else None
    return render(k, n, crawler, new, cmp), k, new, cmp


def main():
    views = build_all(TODAY)          # 先產兩種來源檢視頁，順便拿到解析結果
    rows = []
    for name in COMPANIES:
        folder = HERE / name
        d = load(folder / f"{name}.md")
        crawler = views[name]["crawler"]
        page_html, k, new, cmp = build_one(name, d, crawler)
        marks_old = build_one(name, d, crawler, use_new=False)[0].count("<mark>") - 1
        (folder / f"{name}.html").write_text(page_html, encoding="utf-8")
        marks = page_html.count("<mark>") - 1          # 扣掉 HTML 註解裡那個
        cmp_txt = f"fin 共同欄位 same={cmp['same']} filled={cmp['filled']} diff={len(cmp['diff'])} newkeys={len(cmp['new_keys'])}" if cmp else "無新版 fin"
        print(f"{name:12s} latest={k['q']['period']}  q5={len(k['q5'])}  fin={k['fin_version']}  mark={marks}（舊版 {marks_old}）  bytes={len(page_html.encode('utf-8')):,}  {cmp_txt}")
        if cmp and cmp["diff"]:
            print("   數值不同：", cmp["diff"])
        rows.append(dict(name=name, key=k["key"], period=d["period"], marks=marks, marks_old=marks_old,
                         conf=conference_timeline(k, crawler) or "無",
                         summary=(f"{k['summary']['period']}（{k['summary'].get('crawled_at', '')[:10]}）" if k["summary"] else "無")
                         + (f"＋新版 {len(new['summaries'])} 場" if new["summaries"] else ""),
                         crawler=CRAWLER_HELP[k["key"]], new=new_help(new, cmp),
                         crawler_links="｜".join(f'<a href="{esc(name)}/{esc(v)}">爬蟲資料 {esc(p)}{"（新版）" if vv == "新版實測" else ""}</a>' for p, v, vv in (crawler or {}).get("views", [])) or "—"))
    (HERE / "index.html").write_text(index_page(rows), encoding="utf-8")
    print("index.html")


if __name__ == "__main__":
    main()
