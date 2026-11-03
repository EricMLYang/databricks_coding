#!/usr/bin/env python3
"""把每家公司資料夾的資料依《SCM 財報和法說報告 v20261007》版型產出 HTML。

模板：PM_Head/projects/MI_Crawler/ir_calendar/doc/20261021_SCM財報和法說報告html格式v20261007.html（3M 範例、AUO 配色）
版型：給採購主管的結論 → 財報六節（重點 KPI／實績表／事業群／五年圖／五季圖／五年指標表＋10 小圖）→ 法說七節 → 資料來源與限制。

資料（每家一個資料夾 <公司>/）：
- <公司>.md（實為 JSON）：Databricks silver bundle（company + fin_rows + summary + conference + docs）。**可以沒有**：
  只有爬蟲檔的公司（例：3M、中光電投控，2026-11-03 沙箱爬取）由 bundle_from_crawler() 直接從爬蟲紀錄組出同形狀的 bundle。
- <公司>_爬蟲*.md：bronze payload（正式批次＝已進 Databricks；檔名含「新版實測」＝爬蟲新版沙箱 dev 批次）。
  新版 financials 取代 bundle fin_rows 當財報六節資料源（共同欄位逐值比對，差異印在 console 與附錄）；
  新版 summary 的 management_views 填法說 01–05、qa_highlights 填 07、notes 的 AUO 判讀句填 06、business_segments 填 03 與 01。

2026-11-03 第一版調整（需求方回饋，見 jobs/ir_calendar/範例財報/模板覆蓋度評估.md §9）：
1. 01 財報重點後兩格：法說沒給事業群營收／占比時，改由程式依「變動幅度」自動挑兩個指標（pick_highlights），
   不再出現「資料缺」。build_ir_report 管線由 LLM 挑，這裡是零 token 的規則版。
2. 數字取位：營收／營業現金流／應收天數／應付天數取整數；毛利率／淨利率／負債比／流動比／速動比取小數第一位；EPS 取小數第一位。
   數字一律靠右；負數用紅字括弧，例如 (0.9)。
3. 敘事層不再逐家手寫（舊版 NARRATIVE 把 Q2 的數字寫死，換期別就錯）：結論、限制由資料自動組句；
   「對 AUO 採購的意義」一句維持人工（PROCUREMENT_NOTES，不隨期別變）。

用法：python3 build_report.py            # 在本資料夾執行，另產 index.html
"""
from __future__ import annotations

import html
import json
import pathlib
import re

from build_sources import (
    RECORD_LABEL,
    build_all,
    discover_companies,
    is_new_fin,
    is_new_summary,
    record_brief,
    record_date,
    record_source_url,
)

HERE = pathlib.Path(__file__).resolve().parent
TODAY = "2026-11-03"
VERSION = "v5"
TEMPLATE_REF = "doc/20261021_SCM財報和法說報告html格式v20261007.html"
LAYOUT_NOTE = "2026-11-03 第一版調整：數字取位／靠右／負數紅字括弧；01 重點格無事業群數字時自動改列變動最大的指標"

MISSING = '<mark>資料缺</mark>'

# 模板配色（AUO）
C_BLUE, C_LBLUE, C_PURPLE, C_YELLOW, C_GREEN, C_INK = "#0066B3", "#26A9E0", "#7752A8", "#F5C400", "#40A86B", "#111111"
C_BARFILL, C_GRID, C_NEG = "#cfeafa", "#e3eef5", "#C62828"


# ---------------------------------------------------------------- 數字工具
def load(p: pathlib.Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"), strict=False)


def yi(v, unit: str):
    """原始值 → 億（TW 千元 /1e5；美元 one /1e8）。"""
    if v is None:
        return None
    factor = {"one": 1.0, "thousand": 1e3, "million": 1e6}[unit]
    return v * factor / 1e8


def esc(s) -> str:
    return html.escape(str(s), quote=True)


# 取位規則（2026-11-03 需求方）：money／days 整數；pct／ratio／eps 一位小數；pt（百分點差）一位
DECIMALS = {"money": 0, "days": 0, "pct": 1, "ratio": 1, "eps": 1, "pt": 1, "x": 1}
SUFFIX = {"pct": "%", "pt": " pt", "x": "x"}


def fmt_plain(v, kind="money", *, sign=False) -> str:
    """純文字數字（敘事、SVG 標籤用）：依 kind 取位，負數用括弧 (0.9)，正數可加 +。None → —。"""
    if v is None:
        return "—"
    d = DECIMALS[kind]
    body = f"{abs(v):,.{d}f}{SUFFIX.get(kind, '')}"
    if v < 0 and round(abs(v), d) != 0:
        return f"({body})"
    return ("+" if sign and v > 0 else "") + body


def fmt(v, kind="money", *, sign=False, missing=MISSING) -> str:
    """HTML 數字：同 fmt_plain，負數再套紅字；None → 黃底資料缺（或 missing）。"""
    if v is None:
        return missing
    s = fmt_plain(v, kind, sign=sign)
    return f'<span class="neg">{s}</span>' if s.startswith("(") else s


def num_td(inner: str, extra_cls: str = "") -> str:
    return f'<td class="num {extra_cls}">{inner}</td>' if extra_cls else f'<td class="num">{inner}</td>'


def q_label(period: str) -> str:  # 2026Q2 → 2026 Q2
    return period.replace("Q", " Q")


def q_short(period: str) -> str:  # 2026Q2 → 26 Q2
    return period[2:4] + " Q" + period[-1]


def ratio_pct(a, b):
    return (a / b * 100) if (a is not None and b) else None


def delta_value(cur, prev, kind="pct"):
    """同比變動值：kind=pct 以百分比、pt 以百分點、x 以倍數差。回傳 (值, 顯示 kind) 或 (None, 說明)。"""
    if cur is None or prev is None:
        return None, None
    if kind == "pct":
        if prev == 0:
            return None, "—"
        if prev < 0:  # 基期為負，百分比無意義
            return None, ("轉正（基期為負）" if cur >= 0 else "仍為負（基期為負）")
        return (cur / prev - 1) * 100, "pct"
    if kind == "pt":
        return cur - prev, "pt"
    return cur - prev, "x"


def delta_cell(cur, prev, kind="pct"):
    """同比變動欄：正綠（+2.4%）、負紅括弧（(2.9%)）；缺值黃底。"""
    v, k = delta_value(cur, prev, kind)
    if v is None:
        return MISSING if k is None else f'<span class="mini">{k}</span>'
    if v > 0:
        return f'<span class="delta-positive">{fmt_plain(v, k, sign=True)}</span>'
    if v < 0:
        return f'<span class="delta-negative">{fmt_plain(v, k)}</span>'
    return fmt_plain(v, k)


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
    g = lambda r, key: (r.get(key) if r else None)

    k = dict(
        name=co["company_name"], code=co["stock_code"], key=co["company_key"], market=co["market"],
        industry=co.get("industry"), ir_url=co.get("ir_url"), english=co.get("english_name"),
        cur=cur, cur_label=cur_label, unit=unit, unit_note=("千元" if unit == "thousand" else "元"),
        period=d["period"], q=q, q_ly=q_ly, year=year, annual=annual, quarters=quarters, q5=q5,
        q_label=q_label(q["period"]), q_ly_label=q_label(q_ly["period"]) if q_ly else "去年同季",
        rev_q=rev_q, rev_ly=rev_ly, yoy=yoy,
        gm=q["gross_margin"], gm_ly=g(q_ly, "gross_margin"),
        opm=q["operating_margin"], opm_ly=g(q_ly, "operating_margin"),
        nm=q["net_margin"], nm_ly=g(q_ly, "net_margin"),
        eps=q["eps"], eps_ly=g(q_ly, "eps"),
        oi=oi, pt=pt, ni=ni, nonop=nonop, nonop_pct=ratio_pct(nonop, pt),
        ocf_ytd=ocf_ytd, ocf_ytd_ly=ocf_ytd_ly, ni_ytd=ni_ytd, capex_ytd=yi(q.get("capex_ytd"), unit),
        cr=q["current_ratio"], cr_ly=g(q_ly, "current_ratio"),
        qr=q.get("quick_ratio"), qr_ly=g(q_ly, "quick_ratio"),          # 新版爬蟲才有
        nmp=q.get("net_margin_parent"),
        dr=q["debt_ratio"], dr_ly=g(q_ly, "debt_ratio"), ta=yi(q["total_assets"], unit), tl=yi(q["total_liabilities"], unit),
        summary=d.get("summary"), conference=d.get("conference"), docs=d.get("docs") or [],
        fin_version="新版實測" if fin_new_rows else "bundle", fin_batch=rows[0].get("batch_id"), fin_path=rows[0].get("batch_path"),
        nmp_all=all(r.get("net_margin_parent") is not None for r in annual),   # 五年都有母公司淨利率 → 第 06 節用模板口徑
        from_crawler=bool(d.get("_from_crawler")),
    )
    k.update(  # 敘事用字串（純文字、依取位規則）
        REV_Q=fmt_plain(rev_q), REV_LY=fmt_plain(rev_ly), YOY=fmt_plain(yoy, "pct", sign=True),
        GM=fmt_plain(k["gm"], "pct"), GM_LY=fmt_plain(k["gm_ly"], "pct"),
        OPM=fmt_plain(k["opm"], "pct"), OPM_LY=fmt_plain(k["opm_ly"], "pct"), NM=fmt_plain(k["nm"], "pct"),
        OI=fmt_plain(oi), PT=fmt_plain(pt), NI=fmt_plain(ni), NONOP=fmt_plain(nonop),
        NONOP_PCT=fmt_plain(k["nonop_pct"], "pct") if k["nonop_pct"] is None else f"{k['nonop_pct']:.0f}%",
        OCF=fmt_plain(ocf_ytd), NI_YTD=fmt_plain(ni_ytd), CAPEX=fmt_plain(k["capex_ytd"]),
        DR=fmt_plain(k["dr"], "pct"), CR=fmt_plain(k["cr"], "ratio"), TA=fmt_plain(k["ta"]),
        EPS=fmt_plain(k["eps"], "eps"), EPS_LY=fmt_plain(k["eps_ly"], "eps"),
        OPM_D=(fmt_plain(k["opm"] - k["opm_ly"], "pt", sign=True) if k["opm"] is not None and k["opm_ly"] is not None else "—"),
        QR=fmt_plain(k["qr"], "ratio"), QR_LY=fmt_plain(k["qr_ly"], "ratio"),
    )
    return k


# ---------------------------------------------------------------- 新版爬蟲實測（沙箱 dev 批次）
TOPIC_KEYS = {"事業體／產品線重點": "business", "擴產／產能變化": "capacity", "獲利能力變化": "profit", "未來市場預測": "outlook", "投資／M&A／組織整改": "invest",
              "AUO 相關議題": "auo"}   # 第六類：爬蟲 2026-10-21 新版 prompt 的 auo_topics（2026-11-03 沙箱批次起會出現）→ 法說 06
IR_TITLES = {"business": "01　事業體／產品線重點", "capacity": "02　擴產／產能變化", "profit": "03　獲利能力變化", "outlook": "04　未來市場預測", "invest": "05　投資／M&amp;A／組織整改"}


def pick_new(crawler: dict | None) -> dict:
    """從合併後的爬蟲紀錄挑出新版（version=新版實測）的 financials / summary / conference / manifest / 實體檔。"""
    out = dict(fin=None, fin_rec=None, summaries=[], conferences=[], manifests=[], files=[], batch=None)
    for r in (crawler or {}).get("records", []):
        if r.get("version") != "新版實測" or r["payload"] is None:
            continue
        p, t = r["payload"], r["record_type"]
        out["batch"] = max(out["batch"] or "", r["batch_id"])
        if t == "ir_financials" and is_new_fin(p):
            if out["fin_rec"] is None or r["batch_id"] >= out["fin_rec"]["batch_id"]:
                out["fin"], out["fin_rec"] = p, r
        elif t == "ir_summary" and is_new_summary(p):
            out["summaries"].append(ir_from_summary(p))
        elif t == "ir_conference":
            out["conferences"].append(p)
        elif t == "ir_document":
            out["manifests"].append(p)
        elif t == "ir_document_file":
            out["files"].append(p)
    out["summaries"].sort(key=lambda s: (s["date"] or "", s["period"] or ""))
    return out


def rows_from_new_fin(p: dict, rec: dict) -> list[dict]:
    """新版 financials payload → 與 bundle fin_rows 同形狀的列（period_type / period / fiscal_year / currency / unit / source / batch_*）。"""
    base = dict(currency=p.get("currency"), unit=p.get("unit"), source=p.get("source"), batch_id=rec["batch_id"], batch_path=rec["batch_path"])
    rows = [dict(base, period_type="annual", period=f"{a['fiscal_year']}FY", **a) for a in p.get("annual") or []]
    rows += [dict(base, period_type="quarterly", fiscal_year=int(q["period"][:4]), **q) for q in p.get("quarterly") or []]
    return rows


def compare_fin(old_rows: list[dict], new_rows: list[dict]) -> dict:
    """bundle fin_rows 與新版列共同欄位逐值比對 → {same, filled（bundle 為 null、新版有值）, diff:[(期別, 欄, 舊, 新)], new_keys, missing_periods}。"""
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


def bundle_from_crawler(name: str, crawler: dict | None) -> dict | None:
    """沒有 <公司>.md（silver bundle）時，從新版爬蟲紀錄組出同形狀的 bundle：company / fin_rows / period / conference / docs。"""
    new = pick_new(crawler)
    if not new["fin"]:
        return None
    fin = new["fin"]
    conf = sorted(new["conferences"], key=lambda c: c.get("conference_date") or "")
    latest_conf = conf[-1] if conf else None
    company = dict(company_key=fin["company_key"], company_name=fin.get("company_name") or name, stock_code=fin.get("stock_code"),
                   market=fin.get("market"), category_name=fin.get("category"), industry=None, ir_url=None,
                   english_name=(latest_conf or {}).get("english_name"))
    docs = []
    for f in new["files"]:
        docs.append(dict(file_name=pathlib.PurePosixPath(f.get("path") or f.get("source_file") or "").name, doc_kind=f.get("doc_kind"),
                         page_count=None, source_url=f.get("source_url"), period=f.get("period")))
    periods = sorted({c.get("period") for c in new["conferences"] + new["manifests"] if c.get("period")})
    rows = rows_from_new_fin(fin, new["fin_rec"])
    period = periods[-1] if periods else max(r["period"] for r in rows if r["period_type"] == "quarterly")
    return dict(company=company, fin_rows=rows, period=period, summary=None,
                conference=(dict(conference_date=latest_conf.get("conference_date"), conference_type=latest_conf.get("conference_type")) if latest_conf else None),
                docs=docs, _from_crawler=True)


def _seg_has_num(x: dict) -> bool:
    return bool(x.get("revenue") or x.get("operating_margin") or x.get("margin"))


def segments_for(sums: list[dict]):
    """第 03 節的列：最新一場 summary 的 business_segments；最新一場沒有數字就往前找有數字的那場（註明沿用）。
    回傳 (segs, 利潤率欄名, 註, 來源說明)。"""
    if not sums:
        return None, "營益率", None, None
    latest = sums[-1]
    chosen, note = None, None
    for s in reversed(sums):
        if any(_seg_has_num(x) for x in s["segments"]):
            chosen = s
            break
    if chosen is None:
        if latest["segments"]:
            chosen = latest
            note = "法說未揭露各事業群金額與利潤率，只有文字描述。"
        else:
            return None, "營益率", "法說摘要沒有事業群資料。", None
    elif chosen is not latest:
        note = f"最新一場法說（{latest['date']}）未給事業群數字，沿用 {chosen['date']}（{chosen['period']}）那場。"
    segs = [dict(name=x.get("segment"), revenue=x.get("revenue"), revenue_yoy=x.get("revenue_yoy"), margin=x.get("operating_margin"),
                 margin_yoy=x.get("opm_yoy"), note=x.get("note")) for x in chosen["segments"]]
    src = f"新版爬蟲實測 ir_summary {chosen['date']}（{chosen['period']}）的 business_segments，LLM 自簡報／新聞稿抽取；欄位為原文字串"
    return segs, "營益率（法說口徑）", note, src


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


def _val_label(v, kind, unit_in_label=""):
    """SVG 柱頂／點旁的數值標籤：依取位規則，負數 (x.x) 紅字。回傳 (文字, 顏色或 None)。"""
    s = fmt_plain(v, kind)
    if kind != "pct":
        s += unit_in_label
    return s, (C_NEG if v < 0 else None)


def svg_bars(labels, vals, *, kind="money", unit="", line=True, h=260, w=1000, note_missing="推算列無此值"):
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
        txt, color = _val_label(v, kind)
        g.append(f'<rect x="{x - bw / 2:.1f}" y="{min(y0, y1):.1f}" width="{bw:.1f}" height="{abs(y0 - y1):.1f}" fill="{C_BARFILL}" stroke="{C_INK}" stroke-width="1">'
                 f'<title>{esc(lab)}：{esc(txt)}{esc(unit) if kind != "pct" else ""}</title></rect>')
        ly = y1 - 10 if v >= 0 else y1 + 16
        g.append(f'<text x="{x:.1f}" y="{ly:.1f}" text-anchor="middle" class="val"{f" fill={chr(34)}{color}{chr(34)}" if color else ""}>{esc(txt)}</text>')
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
    t1, h1 = 30, 200
    rmax = max([v for v in rev if v is not None] + [0])
    top = _nice_max(rmax)
    Y1 = lambda v: t1 + (top - v) / top * h1
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
    for v in (sorted({obot, 0.0, otop}) if obot < 0 else (0.0, otop / 2, otop)):
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
            ly = Y1(r) - 8 if Y1(r) - 8 > t1 + 6 else Y1(r) + 18
            g.append(f'<rect x="{x - bw / 2:.1f}" y="{Y1(r):.1f}" width="{bw:.1f}" height="{Y1(0) - Y1(r):.1f}" fill="{C_BARFILL}" stroke="{C_INK}"><title>{esc(lab)} 營收 {fmt_plain(r)}</title></rect>'
                     f'<text x="{x:.1f}" y="{ly:.1f}" text-anchor="middle" class="val">{fmt_plain(r)}</text>')
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
            ly = y - 11 if y - 11 > t2 + 8 else y + 22
            txt, color = _val_label(v, "pct")
            g.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5.5" fill="{C_YELLOW}" stroke="{C_PURPLE}" stroke-width="2"><title>OPM {esc(txt)}</title></circle>'
                     f'<text x="{x:.1f}" y="{ly:.1f}" text-anchor="middle" class="val" fill="{color or C_PURPLE}">{esc(txt)}</text>')
    g.append("</svg>")
    return "".join(g)


# ---------------------------------------------------------------- 01 財報重點：後兩格的自動挑選
def _seg_text(v) -> str:
    """事業群原文字串：負號開頭改紅字括弧，其餘原樣。"""
    if v is None:
        return "—"
    s = esc(v).strip()
    m = re.match(r"^[−-]\s*([\d.,]+\s*(?:%|x|pt|億|M|B)?)(.*)$", s)
    if m:                                   # 「−1.6%」「-3%（約 -US$5,400 萬）」→ (1.6%)、(3%)（約 …）
        return f'<span class="neg">({m[1].strip()})</span>{m[2]}'
    if s.startswith("+"):
        return f'<span class="delta-positive">{s}</span>'
    return s


def pick_highlights(k: dict, segs, latest) -> tuple[list[str], str | None]:
    """01 財報重點第 3、4 格。優先事業群（有營收／占比／營益率數字者）；不足兩格時依「同比變動幅度」自動挑財報指標補位，
    仍不足再用法說 headline_metrics。回傳 (卡片 HTML 清單, 說明)。規則版（零 token）；build_ir_report 管線由 LLM 挑。"""
    cards, picked_from = [], []
    for s in [x for x in (segs or []) if x.get("revenue") or x.get("margin")][:2]:
        if s.get("revenue"):
            cards.append(f'<div class="kpi">{esc(s["name"])} 營收<b>{_seg_text(s["revenue"])}</b><small>YoY {_seg_text(s.get("revenue_yoy"))}</small></div>')
        else:
            cards.append(f'<div class="kpi">{esc(s["name"])} 營益率<b>{_seg_text(s["margin"])}</b><small>YoY {_seg_text(s.get("margin_yoy"))}；法說未給營收金額</small></div>')
    if len(cards) >= 2:
        return cards[:2], None
    cl = k["cur_label"]
    # 候選：(標題, 現值, 去年同季, 顯示 kind, 同比 kind, 顯示單位)
    cands = [
        ("毛利率", k["gm"], k["gm_ly"], "pct", "pt", ""),
        ("稅後淨利率", k["nm"], k["nm_ly"], "pct", "pt", ""),
        (f"每股盈餘（{k['cur']}）", k["eps"], k["eps_ly"], "eps", "pct", ""),
        (f"營業現金流（{k['year']} 年初累計）", k["ocf_ytd"], k["ocf_ytd_ly"], "money", "pct", f"{cl} 億"),
        ("速動比（倍）", k["qr"], k["qr_ly"], "ratio", "x", ""),
        ("負債比", k["dr"], k["dr_ly"], "pct", "pt", ""),
        ("流動比（倍）", k["cr"], k["cr_ly"], "ratio", "x", ""),
    ]
    scored = []
    for title, cur, prev, kind, dkind, unit in cands:
        if cur is None or prev is None:
            continue
        base = abs(prev) if prev else None
        score = (abs(cur - prev) / base) if base else (abs(cur - prev) or 0)
        if kind == "pct" and dkind == "pt":                       # 比率：用百分點差本身排序（10 pt 很大）
            score = abs(cur - prev) / 10
        scored.append((score, title, cur, prev, kind, dkind, unit))
    scored.sort(key=lambda x: -x[0])
    n_seg = len(cards)
    for score, title, cur, prev, kind, dkind, unit in scored:
        if len(cards) >= 2:
            break
        big = f"{esc(cl)} {fmt(cur, kind)} 億" if kind == "money" else fmt(cur, kind)
        cards.append(f'<div class="kpi">{esc(title)}<b>{big}</b><small>YoY {delta_cell(cur, prev, dkind)}（{k["q_ly_label"]}：{fmt(prev, kind)}{" 億" if kind == "money" else ""}）</small></div>')
        picked_from.append(title)
    if len(cards) < 2 and latest and latest["headline"]:
        for hmetric in latest["headline"]:
            if len(cards) >= 2:
                break
            cards.append(f'<div class="kpi">{esc(hmetric.get("metric"))}（法說口徑）<b>{esc(hmetric.get("value"))}</b><small>{esc(hmetric.get("period") or "")} YoY {esc(hmetric.get("yoy") or "—")}</small></div>')
            picked_from.append(f"法說 {hmetric.get('metric')}")
    while len(cards) < 2:
        cards.append('<div class="kpi">事業群營收<b><mark>資料缺</mark></b><small>fin_rows 無部門別；法說／財報未提供，亦無可補位的指標</small></div>')
    note = None
    if picked_from:
        head = "法說未揭露事業群營收／占比，第 3、4 格" if n_seg == 0 else f"法說只揭露 {n_seg} 個事業群的數字，其餘格"
        note = head + "改列同比變動最大的指標（規則版自動挑選：" + "、".join(picked_from) + "；build_ir_report 管線由 LLM 依重要性挑）。"
    return cards[:2], note


def kpi_cards(k, segs, latest):
    cards = [
        f'<div class="kpi">{k["q_label"]} 營收<b>{k["cur_label"]} {fmt(k["rev_q"])} 億</b><small>YoY {delta_cell(k["rev_q"], k["rev_ly"], "pct")}（{k["q_ly_label"]}：{fmt(k["rev_ly"])} 億）</small></div>',
        f'<div class="kpi">營業利益率<b>{fmt(k["opm"], "pct")}</b><small>YoY {delta_cell(k["opm"], k["opm_ly"], "pt")}（{k["q_ly_label"]}：{fmt(k["opm_ly"], "pct")}）</small></div>',
    ]
    extra, note = pick_highlights(k, segs, latest)
    return "\n".join(cards + extra), note


def actual_table(k):
    cl = k["cur_label"]
    new = k["fin_version"] == "新版實測"
    rows = [
        (f"營收（{cl} 億）", fmt(k["rev_q"]), fmt(k["rev_ly"]), delta_cell(k["rev_q"], k["rev_ly"], "pct")),
        ("營業利益率", fmt(k["opm"], "pct"), fmt(k["opm_ly"], "pct"), delta_cell(k["opm"], k["opm_ly"], "pt")),
        (f"每股盈餘（{esc(k['cur'])}）", fmt(k["eps"], "eps"), fmt(k["eps_ly"], "eps"), delta_cell(k["eps"], k["eps_ly"], "pct")),
        (f"營業現金流（{cl} 億，{k['year']} 年初累計）", fmt(k["ocf_ytd"]), fmt(k["ocf_ytd_ly"]) + ('<span class="mini">（去年同期累計）</span>' if k["ocf_ytd_ly"] is not None else ""), delta_cell(k["ocf_ytd"], k["ocf_ytd_ly"], "pct")),
        ("流動比（倍）", fmt(k["cr"], "ratio"), fmt(k["cr_ly"], "ratio"), delta_cell(k["cr"], k["cr_ly"], "x")),
        ("速動比（倍）", fmt(k["qr"], "ratio") if new else "<mark>資料缺：bundle 無現金／有價證券／應收帳款欄位</mark>",
         fmt(k["qr_ly"], "ratio") if new else MISSING, delta_cell(k["qr"], k["qr_ly"], "x") if new else "—"),
    ]
    return "".join(f"<tr><td>{a}</td>{num_td(b)}{num_td(c)}{num_td(d)}</tr>" for a, b, c, d in rows)


def segment_table(segs, margin_label, seg_note, src):
    if not segs:
        return f'<p><mark>資料缺：fin_rows 無部門別，法說摘要／財報文字也沒有可用的事業群數字</mark>{("　" + esc(seg_note)) if seg_note else ""}</p>'
    has_note = any(s.get("note") for s in segs)
    body = "".join(f"<tr><td>{esc(s['name'])}</td>{num_td(_seg_text(s.get('revenue')))}{num_td(_seg_text(s.get('revenue_yoy')))}{num_td(_seg_text(s.get('margin')))}{num_td(_seg_text(s.get('margin_yoy')))}"
                   + (f"<td class=\"mini\">{esc(s.get('note') or '')}</td>" if has_note else "") + "</tr>" for s in segs)
    return (f'<div class="scroll"><table><tr><th>事業群</th><th class="num">營收</th><th class="num">營收 YoY</th><th class="num">{esc(margin_label)}</th><th class="num">YoY</th>{"<th>法說說明</th>" if has_note else ""}</tr>{body}</table></div>'
            + (f'<p class="mini">{esc(seg_note)}</p>' if seg_note else "") + (f'<p class="mini">來源：{esc(src)}</p>' if src else ""))


def five_year_rows(k):
    u, cl = k["unit"], k["cur_label"]
    A = k["annual"]
    def row(label, fn, kind):
        return f"<tr><td>{label}</td>" + "".join(num_td(fmt(fn(r), kind)) for r in A) + "</tr>"
    nm_label, nm_fn = ("稅後淨利率（%，歸屬母公司）", lambda r: r.get("net_margin_parent")) if k["nmp_all"] else ("稅後淨利率（%，合併口徑）", lambda r: r["net_margin"])
    rows = [
        row(f"營收（{cl} 億）", lambda r: yi(r["revenue"], u), "money"),
        row("毛利率（%）", lambda r: r["gross_margin"], "pct"),
        row("淨利率（稅前）（%）", lambda r: ratio_pct(r["pretax_income"], r["revenue"]), "pct"),
        row(nm_label, nm_fn, "pct"),
        row(f"EPS（{esc(k['cur'])}）", lambda r: r["eps"], "eps"),
        row(f"營業現金流（{cl} 億）", lambda r: yi(r["operating_cash_flow"], u), "money"),
        row("負債比（%）", lambda r: r["debt_ratio"], "pct"),
        row("流動比（x）", lambda r: r["current_ratio"], "ratio"),
    ]
    if k["fin_version"] == "新版實測":
        rows += [row("速動比（x）", lambda r: r.get("quick_ratio"), "ratio"), row("應收天數（days）", lambda r: r.get("dso_days"), "days"), row("應付天數（days）", lambda r: r.get("dpo_days"), "days")]
    else:
        missing = f'<td colspan="{len(A)}"><mark>資料缺：bundle fin_rows 無現金／有價證券／應收／應付欄位（新版爬蟲已有）</mark></td>'
        rows += [f"<tr><td>速動比（x）</td>{missing}</tr>", f"<tr><td>應收天數（days）</td>{missing}</tr>", f"<tr><td>應付天數（days）</td>{missing}</tr>"]
    return "".join(rows)


def trend_cards(k):
    u, cl = k["unit"], k["cur_label"]
    A = k["annual"]
    labels = [str(r["fiscal_year"]) for r in A]
    nm_spec = ("稅後淨利率", "(%，歸屬母公司)", [r.get("net_margin_parent") for r in A], "pct", "%") if k["nmp_all"] else ("稅後淨利率", "(%，合併口徑)", [r["net_margin"] for r in A], "pct", "%")
    specs = [
        ("毛利率", "(%)", [r["gross_margin"] for r in A], "pct", "%"),
        ("淨利率（稅前）", "(%)", [ratio_pct(r["pretax_income"], r["revenue"]) for r in A], "pct", "%"),
        nm_spec,
        ("EPS", f"({esc(k['cur'])})", [r["eps"] for r in A], "eps", ""),
        ("營業現金流", f"({cl} 億)", [yi(r["operating_cash_flow"], u) for r in A], "money", ""),
        ("負債比", "(%)", [r["debt_ratio"] for r in A], "pct", "%"),
        ("流動比", "(x)", [r["current_ratio"] for r in A], "ratio", ""),
    ]
    if k["fin_version"] == "新版實測":
        specs += [("速動比", "(x)", [r.get("quick_ratio") for r in A], "ratio", ""),
                  ("應收天數", "(days)", [r.get("dso_days") for r in A], "days", ""),
                  ("應付天數", "(days)", [r.get("dpo_days") for r in A], "days", "")]
    out = [f'<div class="trend-card"><h3>{t} <small>{s}</small></h3>{svg_bars(labels, vals, kind=kind, unit=unit, note_missing="該年來源無值")}</div>' for t, s, vals, kind, unit in specs]
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
    """法說 01–05：新版 summary 的 management_views 優先，缺的類別退回自動句（只有 03 有）；03 一律附財報數字對照。"""
    out = []
    for key in ("business", "capacity", "profit", "outlook", "invest"):
        text, src = None, ""
        if latest and latest["views"].get(key):
            text, src = latest["views"][key], f'<p class="mini">來源：新版爬蟲實測 ir_summary {esc(latest["date"])} management_views「{esc(next(t for t, kk in TOPIC_KEYS.items() if kk == key))}」</p>'
        elif n["ir"].get(key):
            text, src = n["ir"][key], '<p class="mini">來源：無法說文字，由財報數字自動組句</p>'
        extra = src
        if key == "profit":
            extra = (f'<p class="mini"><b>財報對照（fin_rows）</b>：營益率 {esc(k["OPM"])}（去年同季 {esc(k["OPM_LY"])}，{esc(k["OPM_D"])}）、毛利率 {esc(k["GM"])}（{esc(k["GM_LY"])}）；'
                     f'稅前淨利 {esc(k["cur_label"])} {esc(k["PT"])} 億中業外 {esc(k["NONOP"])} 億（{esc(k["NONOP_PCT"])}）。</p>') + src
        out.append(ir_section(IR_TITLES[key], text, extra))
    return "\n".join(out)


def headline_table(latest):
    if not latest or not latest["headline"]:
        return ""
    rows = "".join(f"<tr><td>{esc(x.get('metric'))}</td><td>{esc(x.get('period'))}</td>{num_td(_seg_text(x.get('value')))}{num_td(_seg_text(x.get('yoy')))}<td class=\"mini\">{esc(x.get('note') or '')}</td></tr>" for x in latest["headline"])
    return (f'<details><summary>法說揭露的重點數字（headline_metrics，{len(latest["headline"])} 條；法說口徑，可能含非 GAAP／自結數，與財報六節的 fin_rows 不同）</summary>'
            f'<div class="scroll"><table><tr><th>指標</th><th>期間</th><th class="num">值</th><th class="num">YoY</th><th>註</th></tr>{rows}</table></div></details>')


def qa_block(latest):
    if not latest:
        return "<mark>資料缺：無逐字稿或 Q&amp;A 紀錄（爬蟲 wanted 只有簡報與財報）</mark>"
    if not latest["qa"]:
        return f"<mark>資料缺：新版爬蟲 qa_highlights 為空</mark>——彙整備註：{esc(latest.get('qa_note') or '未找到本場法說的逐字稿或 Q&A 紀錄')}"
    items = "".join(f"<li><b>Q：</b>{esc(x.get('question'))}<br><b>A：</b>{esc(x.get('answer'))}</li>" for x in latest["qa"])
    return f'<ul class="qa">{items}</ul><p class="mini">來源：新版爬蟲實測 ir_summary {esc(latest["date"])} qa_highlights（LLM 自逐字稿／媒體摘要抽取）</p>'


def auo_block(latest):
    if not latest:
        return "<mark>資料缺：法說摘要沒有 AUO 視角（四支箭／Micro LED／CPO）的判讀；需在爬蟲 LLM prompt 或 build_ir_report 的 LLM 步驟加入</mark>"
    if latest["views"].get("auo"):
        return f"{esc(latest['views']['auo'])}<p class=\"mini\">來源：新版爬蟲實測 ir_summary {esc(latest['date'])} management_views「AUO 相關議題」（爬蟲 prompt 的 auo_topics：四支箭、Micro LED、車用／智慧座艙、CPO／光通訊、與 AUO 的直接合作）；要再深一層（對 AUO 料號的影響）需 build_ir_report 的 LLM 步驟依料號清單判讀。</p>"
    if latest["auo"]:
        return f"{esc(latest['auo'])}<p class=\"mini\">來源：新版爬蟲實測 ir_summary {esc(latest['date'])} 的 notes（彙整備註）——爬蟲 LLM 已檢查過 AUO／Micro LED／CPO 相關說法；要再深一層（對 AUO 料號的影響）需 build_ir_report 的 LLM 步驟依料號清單判讀。</p>"
    return "<mark>資料缺：新版爬蟲 notes 未提到是否檢查過 AUO／Micro LED／CPO 相關說法</mark>"


def watch_section(latest):
    if not latest or not (latest["positive"] or latest["watch"] or latest["open_q"]):
        return ""
    def card(title, items):
        return f'<div class="card"><h3>{title}</h3>{("<ul>" + "".join(f"<li>{esc(x)}</li>" for x in items) + "</ul>") if items else "<p class=mini>（空）</p>"}</div>'
    return (f'<section><h2>08　採購觀察｜正向訊號・觀察項・未答問題<small class="mini">（模板外補充；來自新版爬蟲 positive_signals / watch_items / open_questions）</small></h2>'
            f'<div class="three">{card("正向訊號", latest["positive"])}{card("觀察項", latest["watch"])}{card("法說未答／未揭露", latest["open_q"])}</div></section>')


def prev_summaries(sums):
    """最新一場之外的新版 summary 摘成可展開區塊。"""
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
    fin_use = ("財報六節全部數字與圖（新版爬蟲實測 financials，批次 " + esc(k["fin_batch"]) + ("；共同欄位與 silver bundle fin_rows 逐值相同" if not k["from_crawler"] else "；本公司無 silver bundle") + "）"
               if k["fin_version"] == "新版實測" else "財報六節全部數字與圖（fin_rows）")
    if k["market"] in ("TPE", "TPEx"):
        items.append(("https://mopsov.twse.com.tw/mops/web/index", f"公開資訊觀測站財務報表 API（{esc(fin_src)}）", fin_use))
    else:
        items.append(((k["q"].get("source_urls") or ["#"])[0], f"SEC XBRL companyfacts（{esc(fin_src)}）", fin_use))
    seen_docs = set()
    for doc in k["docs"]:
        if not doc.get("source_url") or doc["source_url"] in seen_docs:
            continue
        seen_docs.add(doc["source_url"])
        use = "法說七節、事業群表（簡報／新聞稿文字）" if doc.get("doc_kind") == "Presentation" else "原始財報（僅供核對；未用於欄位）"
        pages = f"，{doc['page_count']} 頁" if doc.get("page_count") else ""
        items.append((doc["source_url"], f"{esc(doc.get('file_name'))}（{esc(doc.get('doc_kind'))}{pages}）", use))
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
    """財報公布日：manifest financial_report 的 doc_date（台股 TWSE_DOC 為 null）；多期取最新。"""
    dates = []
    for r in (crawler or {}).get("records", []):
        if r["record_type"] == "ir_document":
            for f in (r["payload"] or {}).get("files") or []:
                if f.get("type") == "financial_report" and f.get("doc_date"):
                    dates.append(f["doc_date"])
    return max(dates) if dates else None


def new_crawler_note(k, new, cmp):
    """附錄用：新版爬蟲實測對本報告補了什麼（自動從資料算）。"""
    if not new["batch"]:
        return "<b>新版爬蟲實測：</b>本公司資料夾沒有 _新版實測.md。"
    bits = []
    if new["fin"] and cmp:
        nk = [x for x in cmp["new_keys"] if x not in ("_derived",)]
        bits.append(f"financials 多 {len(nk)} 個欄位（{'、'.join(nk)}），共同欄位 {cmp['same']} 個值相同、{cmp['filled']} 個 bundle 為 null 新版有值、"
                    f"{len(cmp['diff'])} 個數值不同{('：' + esc(str(cmp['diff'][:5]))) if cmp['diff'] else ''}"
                    + (f"；新版多的期別 {'、'.join(cmp['missing_periods'])}" if cmp["missing_periods"] else "")
                    + "→ 財報六節改用新版列，速動比／應收天數／應付天數／母公司淨利率補上")
    elif new["fin"]:
        bits.append("financials 來自新版爬蟲（本公司無 silver bundle 可比對）→ 財報六節全部用新版列")
    else:
        bits.append("新版沒有 financials")
    if new["summaries"]:
        for s in new["summaries"]:
            bits.append(f"ir_summary {s['date']}（{s['period']}）：management_views {len([v for v in s['views'] if v != 'auo'])}/5 類{'＋AUO' if s['views'].get('auo') else ''}、事業群 {len(s['segments'])} 列、headline {len(s['headline'])} 條、"
                        f"Q&A {len(s['qa'])} 條、AUO 判讀{'有' if s['auo'] else '無'}、正向／觀察／未答 {len(s['positive'])}/{len(s['watch'])}/{len(s['open_q'])} → 法說 01–08")
    else:
        bits.append("新版仍沒有 ir_summary（manifest 列 missing presentation：爬蟲端找不到本期法說簡報）→ 法說節維持空缺")
    if new["conferences"]:
        bits.append("ir_conference " + "、".join(c.get("conference_date") or "" for c in new["conferences"]) + "（source=DEV_SAMPLE，沙箱指定的場次，非行事曆爬到）")
    return "<b>新版爬蟲實測（最新批次 " + esc(new["batch"]) + "，未進 Databricks）：</b>" + "；".join(bits) + "。"


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
        batches = "、".join(sorted({r["batch_id"] for r in recs}))
        tables.append(f'<h3>{esc(ver)}{"（已進 Databricks bronze／silver）" if ver == "正式批次" else f"（爬蟲新版沙箱 dev 批次：{esc(batches)}）"}</h3>'
                      f'<p class="mini">原文見 {views}。{("<b>沒有的紀錄：</b>" + esc("、".join(absent)) + "。") if absent else ""}</p>'
                      f'<div class="scroll"><table><tr><th>紀錄</th><th>日期</th><th>內容</th><th>來源</th><th>批次</th></tr>{"".join(row(r) for r in recs)}</table></div>')
    bundle_link = (f'silver bundle 見 <a href="{esc(k["name"])}_原始資料.html">{esc(k["name"])}_原始資料.html</a>。' if not k["from_crawler"]
                   else "本公司沒有 silver bundle（尚未進 Databricks），報告直接由新版爬蟲紀錄組出。")
    return f"""
<section><h2>附錄　資料履歷｜爬蟲抓到的法說與文件（bronze，{esc(crawler['period'])}）</h2>
<p class="mini">來源 <code>b_ir_calendar_record.payload</code>（正式批次）與爬蟲新版沙箱輸出（新版實測），同一檔只留最新批次；{bundle_link}</p>
{"".join(tables)}
<div class="note">{new_crawler_note(k, new, cmp)}</div>
<div class="note"><b>正式批次 vs bundle：</b>{esc(n.get("crawler_note") or "無正式批次可比對。")}</div>
</section>"""


# ---------------------------------------------------------------- 敘事：自動組句 ＋ 人工維護的採購意義
# 對 AUO 採購的意義：人工維護、不隨期別變。沒有的公司用通用句。
PROCUREMENT_NOTES = {
    "NYSE:GLW": "對 AUO 採購的意義：財務面沒有降載理由，風險在資源配置——資本支出優先給光纖與光連接器，顯示玻璃的產能與價格策略要每季追；玻璃基板關鍵世代維持 AGC／NEG 備援配額。GAAP 與 core（非 GAAP）指標的差距來自避險損益、一次性稅務與重組，本報告一律用 GAAP。",
    "TPE:1303": "對 AUO 採購的意義：聚酯膜／離型膜等顯示相關料號供應面有增量（離型膜新套陸續投產），化工、聚酯淡季停車要確認不波及；權益法收益占稅前淨利比重高，評估體質看營業利益而非淨利。",
    "TPE:1763": "對 AUO 採購的意義：PMMA／光學板材等關鍵料號維持 2nd source；若營業現金流連續兩個半年為負或營收再年減 10% 以上，升級 QBR 並評估降載。",
    "TPE:1711": "對 AUO 採購的意義：採購金額小，重點是供應連續性而非財務承壓；光阻、色料關鍵料號確認第二供應商認證進度；若毛利率回落至 20% 以下或連兩季本業虧損，升級 QBR。",
    "TPE:1717": "對 AUO 採購的意義：乾膜光阻、光學膜／特用材料維持 2nd source，新廠量產前不集中轉單；媒體轉述的法說數字口徑常與財報不符，引用以財報為準。",
    "NYSE:MMM": "對 AUO 採購的意義：3M 為光學膜（增亮膜／反射膜）供應商，留意消費品與電子相關事業的需求走勢，以及 PFAS 退出對相關材料的替代品資格與供應轉換風險；依合約價格調整機制逐項審視。",
    "TPE:3718": "對 AUO 採購的意義：中光電為背光模組主要供應商，關注稼動率、客戶集中度與匯率對毛利率的影響；關鍵機種維持第二來源，新產能與產品組合調整要每季追。",
    "TPE:8215": "對 AUO 採購的意義：明基材為偏光片主要供應商，偏光片本業供過於求、本業虧損且負債比升高，供應連續性與價格談判要分開看：維持日東／住友化學備援配額，關鍵機種偏光片規格認證不集中；若營業現金流轉負或負債比再升，升級 QBR。",
}
# 正式批次 vs bundle 的對照說明（2026-10-21 評估時寫的歷史紀錄，仍成立；新公司無正式批次）
CRAWLER_NOTES = {
    "NYSE:GLW": "2026Q2 正式批次：文件 manifest（8-K EX-99 2026-07-28、10-Q 2026-07-29，皆 EDGAR）、兩個實體檔、財報數據（批次 000030），沒有 ir_conference 與 ir_summary；內容與 bundle 相同。7-28 法說電話會議只在新聞稿文字裡，行事曆沒有這一場。",
    "TPE:1303": "2026Q3 正式批次四筆（場次 10-13、彙整 10-13、簡報 manifest、財報數據）與 bundle 逐字相同；manifest 為 PARTIAL、缺 financial_report 是 Q3 財報未出。2026Q2 另有 2026-09-21 的 ir_summary（電子材料營益率逐季、權益法增額、7 月月營收、M8／M9 驗證風險）；2026-09-24 的 ir_summary 只找到公告。",
    "TPE:1763": "2026Q2 正式批次：只有文件 manifest（wanted 只列 financial_report）、Q2 財報 PDF 實體檔、財報數據（批次 000030）；沒有 ir_conference、ir_summary，與 bundle 相同，確認「無法說」是來源端就沒有。",
    "TPE:1711": "2026Q2 正式批次：只有文件 manifest（wanted 只列 financial_report）、Q2 財報 PDF 實體檔、財報數據（批次 000030）；沒有 ir_conference、ir_summary，與 bundle 相同。主檔 IR 網址指向公司法說頁，爬蟲端可據此補抓是否真的沒開法說。",
    "TPE:1717": "2026Q2 正式批次：ir_summary（2026-09-21，批次 000002）與 bundle 逐字相同；文件 manifest 的 wanted 只列 financial_report，且沒有 ir_conference——2026-08-13 這場法說只存在於彙整文字裡，行事曆漏抓（backlog B1）。",
}


def auto_narrative(k: dict, sums: list[dict]) -> dict:
    """結論／限制／法說 03 退回句，全部從 k（財報數字）與新版 summary 組句；不寫死任何期別數字。"""
    cl, latest = k["cur_label"], (sums[-1] if sums else None)
    name = k["name"]
    s = [f"{name} {k['q_label']} 營收 {cl} {k['REV_Q']} 億（YoY {k['YOY']}），毛利率 {k['GM']}（去年同季 {k['GM_LY']}）、營益率 {k['OPM']}（{k['OPM_LY']}，{k['OPM_D']}）、EPS {k['cur']} {k['EPS']}（{k['EPS_LY']}）。"]
    if k["oi"] is not None and k["oi"] < 0:
        s.append(f"本業虧損（營益率 {k['OPM']}）。")
    if k["nonop_pct"] is not None and k["pt"] and k["pt"] > 0 and k["nonop_pct"] >= 30:
        s.append(f"稅前淨利 {cl} {k['PT']} 億中業外 {k['NONOP']} 億、占 {k['NONOP_PCT']}，淨利率 {k['NM']} 明顯高於營益率，評估體質看營業利益。")
    if k["ocf_ytd"] is not None:
        cmpw = ("高於" if (k["ni_ytd"] is not None and k["ocf_ytd"] >= k["ni_ytd"]) else "低於") if k["ni_ytd"] is not None else ""
        s.append(f"{k['year']} 年初累計營業現金流 {cl} {k['OCF']} 億" + (f"，{cmpw}同期累計淨利 {k['NI_YTD']} 億" if cmpw else "")
                 + ("（為負，獲利尚未變現）。" if k["ocf_ytd"] < 0 else "。"))
    s.append(f"負債比 {k['DR']}、流動比 {k['CR']}x" + (f"、速動比 {k['QR']}x" if k["qr"] is not None else "") + "。")
    if latest:
        pos = "；".join(latest["positive"][:2]) if latest["positive"] else ""
        wat = "；".join(latest["watch"][:2]) if latest["watch"] else ""
        s.append(f"法說（{latest['date']}）" + (f"正向訊號：{pos}。" if pos else "") + (f"觀察項：{wat}。" if wat else ""))
    else:
        s.append("本期沒有法說會摘要，以下法說七節除「獲利能力變化」用財報數字反推外皆空缺。")
    s.append(PROCUREMENT_NOTES.get(k["key"], "對 AUO 採購的意義：依上列指標追蹤供應連續性；本業虧損、營業現金流轉負或負債比明顯上升時升級 QBR。"))
    conclusion = "".join(s)

    profit = (f"（財報推得）營益率 {k['OPM']}（去年同季 {k['OPM_LY']}，{k['OPM_D']}）、毛利率 {k['GM']}（{k['GM_LY']}）；"
              f"稅前淨利 {cl} {k['PT']} 億中營業利益 {k['OI']} 億、業外 {k['NONOP']} 億（{k['NONOP_PCT']}）。")

    lim = []
    if k["cur"] == "USD":
        lim.append("幣別為美元，金額以「億美元」呈現（原始單位元）；財報數字為 SEC companyfacts 的 GAAP 數字，法說節的 core／adjusted（非 GAAP）指標為管理層口徑，與財報六節不可直接相減。")
    else:
        lim.append("財報數字來自 MOPS（千元換算億元）；法說節的自結數與媒體轉述數字不等於財報，正式決策以公開資訊觀測站為準。")
    if latest and latest["period"] and latest["period"] > k["q"]["period"]:
        lim.append(f"法說資料基準為 {q_label(latest['period'])}（{latest['date']} 法說），財務數字最新只到 {k['q_label']}；{q_label(latest['period'])} 財報尚未公布，法說揭露的當季數字為自結或法說口徑。")
    if any(r["operating_margin"] is None for r in k["q5"]):
        lim.append("季度推算列（年度 − 前三季）無毛利率與營益率，五季圖該季斷點。")
    if len(k["q5"]) < 5:
        lim.append(f"fin_rows 只有 {len(k['q5'])} 個季度列（半年報公司或來源不足），五季圖只有 {len(k['q5'])} 點。")
    lim.append("季度營業現金流與資本支出以年初累計對照。")
    if k["fin_version"] == "新版實測":
        qr_missing = [str(r["fiscal_year"]) for r in k["annual"] if r.get("quick_ratio") is None]
        if qr_missing:
            lim.append(f"速動比 {'、'.join(qr_missing)} 年無值（來源缺現金或應收欄位）。")
    if latest:
        if latest["segments"]:
            lim.append("事業群表為法說 LLM 抽取的原文字串（金額／占比／利潤率口徑依簡報），不是財報部門附註。")
        if latest["sources"] and all((x.get("media") or "") not in ("公司官網", "MOPS", "SEC") for x in latest["sources"]):
            lim.append("法說摘要多來自媒體轉述與法人報告，口徑可能與財報不符。")
    else:
        lim.append("沒有法說會摘要與場次（新版爬蟲 manifest 亦列 missing presentation）。")
    if k["from_crawler"]:
        lim.append("本公司尚無 Databricks silver bundle，報告直接由沙箱爬蟲紀錄組出；公司主檔的產業別、IR 網址為空。")
    return dict(conclusion=conclusion, ir=dict(profit=profit), limits=" ".join(lim), crawler_note=CRAWLER_NOTES.get(k["key"]))


# ---------------------------------------------------------------- HTML
CSS = """
*{box-sizing:border-box}body{margin:0;background:#edf7fc;color:#111111;font:15px/1.7 system-ui,'Noto Sans TC','Microsoft JhengHei',sans-serif}
header{background:linear-gradient(110deg,#0066B3,#26A9E0);color:white;padding:34px max(22px,calc((100vw - 1100px)/2))}h1{margin:0}header p{margin:6px 0 0}
main{max-width:1100px;margin:auto;padding:20px}
.band{background:#7752A8;color:white;padding:12px 20px;border-radius:10px;margin:26px 0 14px;font-size:20px;font-weight:bold}
section{background:white;border:1px solid #cbe7f6;border-radius:15px;padding:22px;margin:15px 0;box-shadow:0 5px 20px #0066b318}
h2{margin:0 0 12px;color:#0066B3;font-size:20px}h3{color:#7752A8}
table{border-collapse:collapse;width:100%;min-width:670px}th,td{text-align:left;border-bottom:1px solid #cbe7f6;padding:9px 11px;vertical-align:top}th{background:#def3fb;color:#0066B3}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.neg{color:#C62828}
.scroll{overflow:auto}
.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}
.kpi{background:#def3fb;border-top:4px solid #26A9E0;border-radius:11px;padding:13px}.kpi:nth-child(2){border-color:#F5C400}.kpi:nth-child(3){border-color:#40A86B}.kpi:nth-child(4){border-color:#7752A8}
.kpi b{display:block;font-size:23px;color:#111111;text-align:right;font-variant-numeric:tabular-nums}.kpi small,.mini{font-size:12px;color:#111111}
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


def render(k: dict, n: dict, crawler: dict | None, new: dict, cmp: dict | None) -> str:
    cl = k["cur_label"]
    tl = conference_timeline(k, crawler)
    conf_line = esc(tl) if tl else "<mark>資料缺：行事曆與爬蟲皆無場次</mark>"
    rd = report_date(k, crawler)
    rd_line = esc(rd) if rd else "<mark>資料缺：財報 manifest 的 doc_date 為 null（TWSE_DOC）</mark>"
    sums = new["summaries"]
    latest = sums[-1] if sums else None
    ir_period = latest["period"] if latest and latest["period"] else k["period"]
    period_line = f"{k['q_label']} 財報" + (f"＋{q_label(ir_period)} 法說" if ir_period != k["q"]["period"] else "")
    segs, seg_label, seg_note, seg_src = segments_for(sums)
    kpis, kpi_note = kpi_cards(k, segs, latest)
    if latest:
        ir_src = (f'<p class="mini">法說資料來源：新版爬蟲實測 ir_summary {esc("、".join(s["date"] for s in sums))}（最新批次 {esc(new["batch"])}；最新一場 {esc(latest["date"])}，報告期間「{esc(latest["reported"] or "")}」）</p>')
    else:
        ir_src = '<p class="mini"><mark>資料缺：本公司沒有法說會摘要（summary）與場次紀錄（新版爬蟲實測亦無：manifest 列 missing presentation）；以下各節除「獲利能力變化」用財報數字反推外皆空缺</mark></p>'
    auo = auo_block(latest)
    qa = qa_block(latest)
    if k["fin_version"] == "新版實測":
        fin_line = f"財報數字：新版爬蟲實測 financials（批次 {esc(k['fin_batch'])}" + (
            ("，共同欄位與 silver bundle 逐值相同" if not cmp["diff"] else f"，<b>{len(cmp['diff'])} 個值不同，見附錄</b>") if cmp else "，無 silver bundle 可比對") + "）"
    else:
        fin_line = "財報數字：silver bundle fin_rows"
    quick_note = ("速動比＝速動資產／流動負債；速動資產＝現金及約當現金＋按公允價值衡量之金融資產（流動）＋應收票據＋應收帳款（含關係人），新版爬蟲已算（quick_ratio）。"
                  if k["fin_version"] == "新版實測" else "速動比＝（現金及約當現金＋有價證券＋應收帳款淨額）／流動負債，bundle fin_rows 沒有分子三個欄位（新版爬蟲已補）。")
    formula_note = ("公式：毛利率＝毛利／營收；稅前淨利率＝稅前利益／營收；稅後淨利率＝歸屬母公司淨利／營收（模板口徑，新版爬蟲 net_margin_parent）；負債比＝總負債／總資產；流動比＝流動資產／流動負債；"
                    "速動比＝速動資產／流動負債；應收天數＝平均應收帳款／營收×365；應付天數＝平均應付帳款／銷貨成本×365（最早一年用期末值，其餘期初期末平均）。比率欄直接取爬蟲算好的值，稅前淨利率由本頁計算。"
                    if k["fin_version"] == "新版實測" else
                    "公式：毛利率＝毛利／營收；稅前淨利率＝稅前利益／營收；稅後淨利率＝合併淨利／營收（模板為歸屬公司淨利，bundle fin_rows 年度列無此欄）；負債比＝總負債／總資產；流動比＝流動資產／流動負債。"
                    "比率欄直接取 fin_rows（爬蟲端已算），稅前淨利率由本頁計算。速動比、應收天數、應付天數需現金、有價證券、應收、應付四欄，bundle 沒有。")
    rounding_note = "取位：營收／營業現金流／應收付天數取整數，比率與 EPS 取小數第一位；負數以紅字括弧表示，例如 (0.9)。"

    return f"""<!doctype html>
<html lang="zh-Hant-TW">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(k['name'])}｜財報＋法說整合報告</title>
<!--
由 build_report.py 依 {TEMPLATE_REF} 產出；資料來源：範例財報/{esc(k['name'])}/{esc(k['name'])}.md（silver bundle JSON，可無）
＋ {esc(k['name'])}_爬蟲*.md（bronze payload：財報六節、法說七節、頁首法說時間軸、附錄資料履歷）。
模板的 12 張 PNG 改為 inline SVG。黃底 <mark> 為資料集給不出的欄位，對照 模板覆蓋度評估.md。{LAYOUT_NOTE}。
-->
<style>{CSS}</style>
</head>
<body>
<header>
  <h1>{esc(k['name'])}｜財報＋法說整合報告</h1>
  <p>{esc(period_line)} ｜ {esc(k['market'])}: {esc(k['code'])}{('｜' + esc(k['industry'])) if k['industry'] else ''}</p>
  <p>財報公布：{rd_line}　·　法說會：{conf_line}</p>
  <p class="mini" style="color:#d8e8f7">產出日期：{TODAY}｜版本：{VERSION}｜金額單位：{cl} 億（原始 {esc(k['unit_note'])} 換算）｜{fin_line}｜{esc(LAYOUT_NOTE)}</p>
</header>
<main>

<section><h2>給 AUO 採購主管的結論</h2><p>{esc(n['conclusion'])}</p><p class="mini">結論由財報數字與法說彙整自動組句；「對 AUO 採購的意義」一句為人工維護。</p></section>

<div class="band">財報資訊</div>

<section><h2>01　財報重點</h2><div class="grid">
{kpis}
</div>{f'<p class="mini">{esc(kpi_note)}</p>' if kpi_note else ''}</section>

<section><h2>02　財報實績</h2><div class="scroll"><table>
<tr><th>指標</th><th class="num">{k['q_label']}</th><th class="num">{k['q_ly_label']}</th><th class="num">同比變動／對照</th></tr>
{actual_table(k)}
</table></div>
<div class="mini" style="margin-top:12px;line-height:1.7"><p style="margin:0 0 8px">營業現金流為年初累計（YTD）對去年同期累計，非單季；流動比為資產負債表時點數據。營業利益率的同比以百分點（pt）表示。{rounding_note}</p>
<p style="margin:0">{quick_note}</p></div></section>

<section><h2>03　事業群財務表現</h2>{segment_table(segs, seg_label, seg_note, seg_src)}</section>

<section><h2>04　五年趨勢｜營收 × OPM</h2>{chart_5y(k)}<p class="mini">年度 fin_rows（{k['annual'][0]['fiscal_year']}–{k['annual'][-1]['fiscal_year']}）；上格營收、下格營業利益率，共用年度軸。</p></section>

<section><h2>05　五季趨勢｜營收 × OPM</h2>{chart_5q(k)}<p class="mini">最近 {len(k['q5'])} 個季度列；季度與年度口徑不同，不可與第 04 節直接比較。</p></section>

<section><h2>06　近五年財務指標｜{k['annual'][0]['fiscal_year']}–{k['annual'][-1]['fiscal_year']}</h2>
<div class="scroll"><table><tr><th>指標</th>{"".join(f"<th class=num>{r['fiscal_year']}</th>" for r in k['annual'])}</tr>
{five_year_rows(k)}
</table></div>
<div class="trend-grid">
{trend_cards(k)}
</div>
<p class="mini">{formula_note}{rounding_note}</p></section>

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
<div class="note"><b>限制：</b>{esc(n['limits'])} 通用限制：第 01／02 節與五季圖的淨利為合併淨利（含非控制權益），EPS 以歸屬母公司淨利計算；金額由原始單位（{esc(k['unit_note'])}）換算為億；法說節文字為爬蟲 LLM 彙整（含媒體轉述），正式決策前仍應以公開資訊觀測站／SEC 及公司合併財報附註為準。</div>
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
        bits.append(f"財報 +{len([x for x in cmp['new_keys'] if x != '_derived'])} 欄 → 速動比／應收付天數／母公司淨利率" if cmp else "財報全部來自新版爬蟲")
    if new["summaries"]:
        s = new["summaries"][-1]
        bits.append(f"法說 {len(new['summaries'])} 場（最新 {s['date']}）：01–05 {len([v for v in s['views'] if v != 'auo'])}/5、Q&amp;A {len(s['qa'])} 條、事業群 {len(s['segments'])} 列、採購觀察 08")
    else:
        bits.append("仍無法說（missing presentation）")
    return "<b>有</b>：" + "；".join(bits)


def index_page(rows: list[dict]) -> str:
    body = "".join(
        f"<tr><td><b>{esc(r['name'])}</b><div class=\"mini\">{esc(r['key'])}</div></td><td>{esc(r['period'])}</td>"
        f"<td>{esc(r['conf'])}</td><td>{esc(r['summary'])}</td><td>{r['crawler']}</td><td>{r['new']}</td><td class=\"num\">{r['marks']}<div class=\"mini\">舊版 {r['marks_old']}</div></td>"
        f"<td><a href=\"{esc(r['name'])}/{esc(r['name'])}.html\">報告</a>｜{r['bundle_link']}｜{r['crawler_links']}</td></tr>"
        for r in rows)
    return f"""<!doctype html>
<html lang="zh-Hant-TW"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>範例財報｜財報＋法說整合報告 × 兩種資料來源</title><style>{CSS}</style></head>
<body>
<header><h1>供應商 財報＋法說整合報告 × 兩種資料來源</h1>
<p>每家一個資料夾：<b>報告</b>（依 v20261007 版型產出，{esc(LAYOUT_NOTE)}）、<b>原始資料</b>（Databricks silver bundle，報告的輸入；沒有的公司直接由爬蟲紀錄組 bundle）、<b>爬蟲資料</b>（bronze payload：正式批次＝已進 Databricks；新版實測＝爬蟲新版沙箱 dev 批次，檔名尾碼 _1103 為 2026-11-03 重抓）</p>
<p class="mini" style="color:#d8e8f7">產出日期：{TODAY}｜版本：{VERSION}</p></header>
<main>
<section><h2>{len(rows)} 家供應商</h2>
<div class="scroll"><table><tr><th>公司</th><th>期別</th><th>法說場次（行事曆＋爬蟲）</th><th>法說彙整</th><th>正式批次 bronze 對報告的幫助</th><th>新版爬蟲實測對報告的幫助</th><th class="num">黃底數</th><th>頁面</th></tr>
{body}</table></div>
<div class="note">黃底 <mark>資料缺</mark> 為資料集給不出的欄位；「舊版」黃底數＝只用 bundle＋正式批次時的數字（無 bundle 的公司為 —）。覆蓋度結論與對 pipeline 的建議見 <code>模板覆蓋度評估.md</code>。</div>
</section>
</main>
<footer class="mini">範例財報｜{TODAY}｜Version {VERSION}</footer>
</body></html>
"""


def build_one(name: str, d: dict, crawler: dict | None, use_new: bool = True):
    """回傳 (page_html, k, new, cmp)；use_new=False 時忽略新版實測（用來算舊版黃底數）。"""
    new = pick_new(crawler) if use_new else dict(fin=None, fin_rec=None, summaries=[], conferences=[], manifests=[], files=[], batch=None)
    cmp = None
    new_rows = None
    if new["fin"]:
        new_rows = rows_from_new_fin(new["fin"], new["fin_rec"])
        if not d.get("_from_crawler"):
            cmp = compare_fin(d["fin_rows"], new_rows)
    k = build_k(d, new_rows)
    n = auto_narrative(k, new["summaries"])
    if not use_new:
        crawler = dict(crawler, records=[r for r in crawler["records"] if r.get("version") != "新版實測"],
                       views=[v for v in crawler["views"] if v[2] != "新版實測"]) if crawler else None
    return render(k, n, crawler, new, cmp), k, new, cmp


def main():
    views = build_all(TODAY)          # 先產兩種來源檢視頁，順便拿到解析結果（含沒有 bundle 的公司）
    rows = []
    for name in discover_companies():
        folder = HERE / name
        crawler = views[name]["crawler"]
        d = views[name]["bundle"]
        if d is None:
            d = bundle_from_crawler(name, crawler)
            if d is None:
                print(f"{name:12s} 跳過：沒有 <公司>.md，爬蟲檔也沒有新版 financials")
                continue
        page_html, k, new, cmp = build_one(name, d, crawler)
        marks = page_html.count("<mark>") - 1          # 扣掉 HTML 註解裡那個
        marks_old = (build_one(name, d, crawler, use_new=False)[0].count("<mark>") - 1) if not d.get("_from_crawler") else None
        (folder / f"{name}.html").write_text(page_html, encoding="utf-8")
        cmp_txt = f"fin 共同欄位 same={cmp['same']} filled={cmp['filled']} diff={len(cmp['diff'])} newkeys={len(cmp['new_keys'])} 新期別={cmp['missing_periods']}" if cmp else ("無 bundle" if d.get("_from_crawler") else "無新版 fin")
        print(f"{name:12s} latest={k['q']['period']}  q5={len(k['q5'])}  fin={k['fin_version']}  summaries={len(new['summaries'])}  mark={marks}（舊版 {marks_old}）  bytes={len(page_html.encode('utf-8')):,}  {cmp_txt}")
        if cmp and cmp["diff"]:
            print("   數值不同：", cmp["diff"])
        rows.append(dict(name=name, key=k["key"], period=d["period"], marks=marks, marks_old=marks_old if marks_old is not None else "—",
                         conf=conference_timeline(k, crawler) or "無",
                         summary=(f"{k['summary']['period']}（{k['summary'].get('crawled_at', '')[:10]}）" if k["summary"] else "無")
                         + (f"＋新版 {len(new['summaries'])} 場" if new["summaries"] else ""),
                         crawler=CRAWLER_HELP.get(k["key"], "—（無正式批次）"), new=new_help(new, cmp),
                         bundle_link=(f'<a href="{esc(name)}/{esc(name)}_原始資料.html">原始資料</a>' if not d.get("_from_crawler") else "原始資料：無 bundle"),
                         crawler_links="｜".join(f'<a href="{esc(name)}/{esc(v)}">爬蟲資料 {esc(p)}{"（新版）" if vv == "新版實測" else ""}</a>' for p, v, vv in (crawler or {}).get("views", [])) or "—"))
    (HERE / "index.html").write_text(index_page(rows), encoding="utf-8")
    print("index.html")


if __name__ == "__main__":
    main()
