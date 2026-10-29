#!/usr/bin/env python3
"""把每家公司的兩個來源檔各轉成一頁 HTML，讓讀者看「目前資料長什麼樣」：

- `<公司>/<公司>.md`（實為 JSON）：Databricks silver 表 join 後的 bundle
  （`build_ir_report` [c09] `load_company_bundle` 的回傳形狀）→ `<公司>_原始資料.html`
- `<公司>/<公司>_爬蟲.md`：bronze `b_ir_calendar_record.payload` 原文（爬蟲每個 JSON 檔一列）
  → `<公司>_爬蟲資料.html`

也提供 `parse_crawler_md()` 給 build_report.py 用（資料履歷區塊）。
用法：由 build_report.py 一併呼叫；或 `python3 build_sources.py` 只產來源檢視頁。
"""
from __future__ import annotations

import html
import json
import pathlib
import re

HERE = pathlib.Path(__file__).resolve().parent
SEP = "=" * 100

COMPANIES = ["Corning", "南亞塑膠工業", "奇美實業", "臺灣永光化學工業", "長興材料工業"]

RECORD_LABEL = {
    "ir_conference": "法說場次",
    "ir_summary": "法說彙整",
    "ir_document": "文件清單（manifest）",
    "ir_document_file": "實體檔",
    "ir_financials": "財報數據",
    "app_company": "公司主檔",
}
RECORD_SILVER = {
    "ir_conference": "s_ir_calendar_conference",
    "ir_summary": "s_ir_calendar_summary",
    "ir_document": "s_ir_calendar_document_file（展開 files[]）",
    "ir_document_file": "s_ir_calendar_document_file ＋ Volume 實體檔 → parse_documents → s_ir_calendar_document_text",
    "ir_financials": "s_ir_calendar_financials（annual[] + quarterly[] 一期一列）",
    "app_company": "s_ir_calendar_company",
}

CSS_BASE = """
:root{--navy:#0b1f3a;--blue:#1f5aa6;--cyan:#20a4b7;--ink:#172033;--muted:#65738a;--bg:#f3f6fa;--card:#fff;--green:#16835d;--amber:#bd7300;--red:#c33c3c;--line:#dbe4ef;--fill:#fff3b0}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);font-family:Inter,"Noto Sans TC","Microsoft JhengHei",sans-serif;color:var(--ink);line-height:1.55}
.hero{background:linear-gradient(120deg,var(--navy),#143d72 65%,#16798f);color:#fff;padding:38px 5vw 30px}
.hero h1{margin:0;font-size:clamp(22px,3.5vw,36px)}
.hero p{margin:8px 0 0;color:#d8e8f7}
.badge{display:inline-block;padding:5px 10px;border-radius:999px;background:#ffffff20;border:1px solid #ffffff50;font-size:12px;margin-bottom:12px}
.wrap{max-width:1220px;margin:auto;padding:24px}
.card{background:#fff;border:1px solid var(--line);border-radius:16px;padding:20px;box-shadow:0 8px 26px #1a3b6610}
.mt{margin-top:16px}
.note,.small{font-size:12px;color:var(--muted)}
h2{font-size:20px;margin:6px 0 14px}
h3{font-size:15px;margin:14px 0 8px}
table{width:100%;border-collapse:collapse;font-size:13px}
th,td{padding:7px 8px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
th{color:var(--muted);font-weight:600;background:#f8fafc;white-space:nowrap}
td.num,th.num{text-align:right;white-space:nowrap}
.kv td:first-child{color:var(--muted);white-space:nowrap;width:220px}
.kv{table-layout:fixed}.kv td{overflow-wrap:anywhere}.kv td table{table-layout:fixed;width:100%}.kv td table td:first-child{white-space:normal;width:auto;color:inherit}
.null{color:#b0b8c4;font-style:italic}
.tag{display:inline-block;padding:2px 8px;border-radius:999px;font-size:12px;font-weight:600;color:#fff;margin-right:6px}
.t-ir_conference{background:#1f5aa6}.t-ir_summary{background:#16835d}.t-ir_document{background:#bd7300}.t-ir_document_file{background:#8a6d3b}.t-ir_financials{background:#20a4b7}.t-app_company{background:#65738a}
pre{background:#0b1f3a;color:#e6eefc;padding:14px;border-radius:10px;overflow:auto;font-size:12px;line-height:1.45;max-height:520px}
details summary{cursor:pointer;color:var(--blue);font-size:13px;margin:6px 0}
.callout{border-left:4px solid var(--amber);background:#fff8e8;padding:12px 16px;border-radius:8px;margin-top:12px;font-size:13px}
ul,ol{padding-left:20px;margin:6px 0}
li{margin:4px 0}
a{color:var(--blue);word-break:break-all}
mark{background:var(--fill);color:inherit;padding:0 3px;border-radius:3px}
.toc a{margin-right:14px;font-size:13px}
footer{padding:18px 0 42px;color:var(--muted);font-size:12px;text-align:center}
@media print{body{background:#fff}.card{box-shadow:none;break-inside:avoid}pre{max-height:none}}
"""


# ---------------------------------------------------------------- 共用
def esc(s) -> str:
    return html.escape("" if s is None else str(s), quote=True)


def pretty(obj) -> str:
    return esc(json.dumps(obj, ensure_ascii=False, indent=2))


def val(v) -> str:
    """kv 表的值：None 顯示 null；list / dict 轉 JSON；URL 變連結。"""
    if v is None:
        return '<span class="null">null</span>'
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (list, dict)):
        if not v:
            return '<span class="null">[]</span>' if isinstance(v, list) else '<span class="null">{}</span>'
        return f"<pre style=\"max-height:240px;margin:0\">{pretty(v)}</pre>"
    s = str(v)
    if s.startswith("http://") or s.startswith("https://"):
        return f'<a href="{esc(s)}">{esc(s)}</a>'
    return esc(s)


def kv_table(d: dict, keys=None) -> str:
    keys = keys or list(d.keys())
    rows = "".join(f"<tr><td>{esc(k)}</td><td>{val(d.get(k))}</td></tr>" for k in keys)
    return f'<table class="kv"><tbody>{rows}</tbody></table>'


def num(v, d=0) -> str:
    if v is None:
        return '<span class="null">—</span>'
    if isinstance(v, (int, float)):
        return f"{v:,.{d}f}"
    return esc(v)


def ul(items) -> str:
    if not items:
        return '<span class="null">[]</span>'
    return "<ul>" + "".join(f"<li>{esc(x)}</li>" for x in items) + "</ul>"


def page(title: str, badge: str, sub: str, body: str, footer: str) -> str:
    return f"""<!doctype html>
<html lang="zh-Hant-TW">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<style>{CSS_BASE}</style>
</head>
<body>
<header class="hero">
  <div class="badge">{badge}</div>
  <h1>{esc(title)}</h1>
  <p>{sub}</p>
</header>
<main class="wrap">
{body}
</main>
<footer>{footer}</footer>
</body>
</html>
"""


# ---------------------------------------------------------------- 爬蟲檔解析
def loads_lenient(raw: str):
    """json.loads；失敗時假設是貼上時尾端被截斷（最後一個值完整、只缺右括號），依未閉合的括號補齊再試。"""
    try:
        return json.loads(raw, strict=False)
    except ValueError:
        pass
    stack, in_str, escp = [], False, False
    for ch in raw:
        if in_str:
            if escp:
                escp = False
            elif ch == "\\":
                escp = True
            elif ch == '"':
                in_str = False
        elif ch == '"':
            in_str = True
        elif ch in "{[":
            stack.append("}" if ch == "{" else "]")
        elif ch in "}]" and stack:
            stack.pop()
    fixed = raw.rstrip().rstrip(",") + "".join(reversed(stack))
    try:
        return json.loads(fixed, strict=False)
    except ValueError:
        return None


def parse_crawler_md(path: pathlib.Path) -> dict:
    """解析 print_crawler_payload 的輸出：首行 company_key / period / 檔案數，之後每段 `=`*100 分隔。

    回傳 {company_key, period, n, records:[{record_type, batch_path, batch_id, volume_path, payload|None, raw}]}。
    payload 解析失敗（截斷）時為 None，raw 保留原文。
    """
    text = path.read_text(encoding="utf-8")
    head, *blocks = text.split(SEP + "\n")
    m = re.search(r"company_key = (.+?), period = (.+?), 檔案數 = (\d+)", head)
    out = dict(company_key=m[1], period=m[2], n=int(m[3]), records=[])
    for b in blocks:
        lines = b.strip("\n").split("\n")
        hm = re.match(r"\[(\w+)\] (\S+)\s+\(batch (\S+)\)", lines[0])
        if not hm:
            continue
        rec = dict(record_type=hm[1], batch_path=hm[2], batch_id=hm[3], volume_path=None, payload=None, raw=None)
        i = 1
        if i < len(lines) and lines[i].startswith("實體檔："):
            rec["volume_path"] = lines[i][len("實體檔："):]
            i += 1
        raw = "\n".join(lines[i:]).strip()
        rec["raw"] = raw
        rec["payload"] = loads_lenient(raw)
        rec["truncated"] = rec["payload"] is not None and not raw.endswith("}")
        out["records"].append(rec)
    out["records"].sort(key=lambda r: (r["batch_id"], r["record_type"], r["batch_path"]))
    return out


def record_date(rec: dict) -> str:
    """資料履歷用：每種紀錄最有意義的日期。"""
    p = rec["payload"] or {}
    t = rec["record_type"]
    if t == "ir_conference":
        return p.get("conference_date") or ""
    if t == "ir_summary":
        return (p.get("crawled_at") or "")[:10]
    if t == "ir_document":
        return (p.get("generated_at") or "")[:10]
    if t == "ir_document_file":
        return p.get("doc_date") or ""
    if t == "ir_financials":
        return (p.get("generated_at") or "")[:10]
    return ""


def record_brief(rec: dict) -> str:
    """資料履歷用：一行說明（已 escape）。"""
    p = rec["payload"]
    t = rec["record_type"]
    if p is None:
        return "<mark>payload 截斷，無法解析</mark>"
    if t == "ir_conference":
        bits = [p.get("conference_type"), p.get("location"), p.get("remark")]
        meta = "，".join(x for x in (p.get("status"), p.get("confidence"), f"source {p.get('source')}" if p.get("source") else None, f"revision {p.get('revision')}") if x)
        return (esc("｜".join(str(x) for x in bits if x)) or "（無類型／地點／備註）") + f"（{esc(meta)}）"
    if t == "ir_summary":
        s = p.get("summary") or {}
        n_cp, n_kn, n_rk, n_src = len(s.get("core_points") or []), len(s.get("key_numbers") or []), len(s.get("risks") or []), len(s.get("sources") or [])
        fb = "，fallback" if p.get("fallback") else ""
        extra = "" if n_kn else "；<b>只有公告，無實質內容</b>"
        if is_new_summary(p):
            extra += (f"；<b>新版結構化欄位</b>：management_views {len(s.get('management_views') or [])} 類、事業群 {len(s.get('business_segments') or [])} 列、"
                      f"headline_metrics {len(s.get('headline_metrics') or [])} 條、Q&amp;A {len(s.get('qa_highlights') or [])} 條")
        return f"重點 {n_cp} 條、關鍵數字 {n_kn} 條、風險 {n_rk} 條、來源 {n_src} 個{esc(fb)}{extra}"
    if t == "ir_document":
        files = p.get("files") or []
        parts = [f"{esc(f.get('type'))}：{esc(f.get('title'))}（{esc(f.get('doc_date') or '無日期')}，{esc(f.get('source'))}）" for f in files]
        miss = p.get("missing") or []
        return f"wanted {esc(p.get('wanted'))}；" + "；".join(parts) + (f"；<mark>missing {esc(miss)}</mark>" if miss else "")
    if t == "ir_document_file":
        return f"{esc(p.get('doc_kind'))}，{num(p.get('bytes'))} bytes，來源檔 {esc(p.get('source_file'))}"
    if t == "ir_financials":
        return f"{esc(p.get('source'))}；年度 {len(p.get('annual') or [])} 列、季別 {len(p.get('quarterly') or [])} 列；{esc(p.get('currency'))} / {esc(p.get('unit'))}"
    return esc(str(p)[:120])


def record_source_url(rec: dict) -> str | None:
    p = rec["payload"] or {}
    t = rec["record_type"]
    if t == "ir_conference":
        return p.get("source_url")
    if t == "ir_summary":
        srcs = (p.get("summary") or {}).get("sources") or []
        return srcs[0]["url"] if srcs else None
    if t == "ir_document":
        files = p.get("files") or []
        return files[0].get("source_url") if files else None
    if t == "ir_document_file":
        return p.get("source_url")
    if t == "ir_financials":
        for r in (p.get("annual") or []) + (p.get("quarterly") or []):
            if r.get("source_urls"):
                return r["source_urls"][0]
    return None


# ---------------------------------------------------------------- 爬蟲資料頁
FIN_COLS = [("period", "期別"), ("fiscal_year", "年度"), ("period_end", "期末"), ("revenue", "營收"), ("cost_of_revenue", "銷貨成本"), ("gross_profit", "毛利"),
            ("operating_income", "營業利益"), ("pretax_income", "稅前"), ("net_income", "淨利"), ("net_income_parent", "母公司淨利"),
            ("eps", "EPS"), ("operating_cash_flow", "OCF"), ("operating_cash_flow_ytd", "OCF YTD"), ("capex", "資本支出"),
            ("capex_ytd", "資本支出 YTD"), ("investing_cash_flow", "投資現金流"), ("total_assets", "總資產"), ("total_liabilities", "總負債"), ("equity", "權益"),
            ("gross_margin", "毛利率%"), ("operating_margin", "營益率%"), ("pretax_margin", "稅前淨利率%"), ("net_margin", "淨利率%"), ("net_margin_parent", "母公司淨利率%"),
            ("debt_ratio", "負債比%"), ("current_ratio", "流動比"), ("derived", "推算欄")]
# 2026-10-21 新版爬蟲（dev 批次）才有的欄位：資產負債表明細與由此算出的速動比／應收付天數
FIN_COLS_NEW = [("cash", "現金"), ("fin_assets_fvtpl_current", "FVTPL 金融資產"), ("fin_assets_fvoci_current", "FVOCI 金融資產"),
                ("notes_receivable", "應收票據"), ("accounts_receivable", "應收帳款"), ("accounts_receivable_related", "應收關係人"),
                ("inventory", "存貨"), ("accounts_payable", "應付帳款"), ("accounts_payable_related", "應付關係人"),
                ("quick_assets", "速動資產"), ("quick_ratio", "速動比"), ("dso_days", "應收天數"), ("dpo_days", "應付天數"), ("days_basis", "天數基準")]
NEW_FIN_MARKER = "quick_ratio"      # 新版 financials 的識別鍵
NEW_SUM_MARKER = "management_views"  # 新版 summary 的識別鍵
RATIO_KEYS = {"eps", "gross_margin", "operating_margin", "pretax_margin", "net_margin", "net_margin_parent", "debt_ratio", "current_ratio", "quick_ratio"}
DAYS_KEYS = {"dso_days", "dpo_days"}


def is_new_fin(p: dict | None) -> bool:
    rows = ((p or {}).get("annual") or []) + ((p or {}).get("quarterly") or [])
    return any(NEW_FIN_MARKER in r for r in rows)


def is_new_summary(p: dict | None) -> bool:
    return NEW_SUM_MARKER in ((p or {}).get("summary") or {})


def fin_table(rows: list, cols=FIN_COLS) -> str:
    head = "".join(f'<th class="num">{esc(l)}</th>' for _, l in cols)
    body = []
    for r in rows:
        tds = []
        for key, _ in cols:
            v = r.get(key)
            if key == "derived":
                tds.append(f'<td class="num">{esc("、".join(v)) if v else ""}</td>')
            elif key in ("period", "period_end", "fiscal_year", "period_type", "days_basis"):
                tds.append(f'<td class="num">{esc(v) if v is not None else ""}</td>')
            elif key in RATIO_KEYS:
                tds.append(f'<td class="num">{num(v, 2)}</td>')
            elif key in DAYS_KEYS:
                tds.append(f'<td class="num">{num(v, 1)}</td>')
            else:
                tds.append(f'<td class="num">{num(v)}</td>')
        body.append("<tr>" + "".join(tds) + "</tr>")
    return f'<div style="overflow:auto"><table><thead><tr>{head}</tr></thead><tbody>{"".join(body)}</tbody></table></div>'


def _tbl(cols: list[tuple[str, str]], items: list[dict]) -> str:
    head = "".join(f"<th>{esc(l)}</th>" for _, l in cols)
    body = "".join("<tr>" + "".join(f"<td>{val(x.get(k))}</td>" for k, _ in cols) + "</tr>" for x in items)
    return f'<div style="overflow:auto"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


def summary_block(s: dict, outer: dict | None = None) -> str:
    """summary 物件（爬蟲原文或 silver 列）→ 可讀區塊。"""
    srcs = s.get("sources") or []
    src_html = "<ul>" + "".join(f'<li><a href="{esc(x.get("url"))}">{esc(x.get("title"))}</a>｜{esc(x.get("media"))}</li>' for x in srcs) + "</ul>" if srcs else '<span class="null">[]</span>'
    rows = [
        ("found", val(s.get("found"))),
        ("reported_period（報告期間）", val(s.get("reported_period")) if "reported_period" in s else "<mark>原文沒有此鍵</mark>"),
        ("core_points（重點）", ul(s.get("core_points"))),
        ("guidance（展望）", val(s.get("guidance"))),
        ("key_numbers（關鍵數字）", ul(s.get("key_numbers"))),
        ("risks（風險）", ul(s.get("risks"))),
    ]
    # 2026-10-21 新版爬蟲才有的結構化欄位：逐鍵呈現，沒有的鍵標黃底
    def structured(key, cols=None, render=None):
        if key not in s:
            return "<mark>原文沒有此鍵：舊版爬蟲尚未產出</mark>"
        v = s.get(key)
        if not v:
            return '<span class="null">[]（新版有此鍵但本場沒內容）</span>'
        return render(v) if render else (_tbl(cols, v) if cols else ul(v))
    rows += [
        ("headline_metrics（法說揭露的重點數字）", structured("headline_metrics", [("metric", "指標"), ("period", "期間"), ("value", "值"), ("yoy", "YoY"), ("note", "註")])),
        ("business_segments（事業群）", structured("business_segments", [("segment", "事業群"), ("revenue", "營收"), ("revenue_yoy", "營收 YoY"), ("operating_margin", "營益率"), ("opm_yoy", "營益率 YoY"), ("note", "註")])),
        ("management_views（管理層觀點，固定五類＝模板法說 01–05）", structured("management_views", [("topic", "主題"), ("view", "內容")])),
        ("qa_highlights（Q&amp;A）", structured("qa_highlights", [("question", "問"), ("answer", "答")])),
        ("positive_signals（正向訊號）", structured("positive_signals")),
        ("watch_items（觀察項）", structured("watch_items")),
        ("open_questions（未答問題）", structured("open_questions")),
        ("notes（彙整備註）", val(s.get("notes"))),
        ("sources（來源）", src_html),
    ]
    return '<table class="kv"><tbody>' + "".join(f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in rows) + "</tbody></table>"


def render_record(rec: dict, idx: int) -> str:
    t = rec["record_type"]
    p = rec["payload"]
    label = RECORD_LABEL.get(t, t)
    head = (f'<span class="tag t-{esc(t)}">{esc(t)}</span><b>{esc(label)}</b>'
            f'<div class="small">batch_path：<code>{esc(rec["batch_path"])}</code>｜批次：{esc(rec["batch_id"])}'
            + (f'<br>實體檔：<code>{esc(rec["volume_path"])}</code>' if rec["volume_path"] else "")
            + f'<br>進 silver：{esc(RECORD_SILVER.get(t, "—"))}</div>')
    if p is None:
        body = f"<div class=\"callout\">payload 截斷，無法解析；原文如下。</div><pre>{esc(rec['raw'])}</pre>"
        return f'<section class="card mt" id="r{idx}">{head}{body}</section>'
    if rec.get("truncated"):
        head += '<div class="callout">原文尾端被截斷（貼上時少了結尾括號），解析時已補齊；最後一個值之後若還有欄位則不在此頁。</div>'

    if t == "ir_conference":
        body = kv_table(p, ["company_name", "period", "fiscal_period", "source_fiscal_period", "conference_date", "start_time", "end_time",
                            "local_conference_date", "local_start_time", "conference_type", "location", "meeting_link", "document_url",
                            "status", "importance", "source", "source_url", "confidence", "remark", "recipients", "revision", "crawled_at"])
    elif t == "ir_summary":
        meta = kv_table(p, ["company_name", "period", "fiscal_period", "conference_date", "local_conference_date", "fallback", "recipients", "crawled_at"])
        body = meta + "<h3>summary 物件</h3>" + summary_block(p.get("summary") or {})
    elif t == "ir_document":
        files = p.get("files") or []
        frows = "".join(
            f"<tr><td>{esc(f.get('type'))}</td><td>{esc(f.get('title'))}</td><td>{esc(f.get('doc_date'))}</td><td>{esc(f.get('source'))}</td>"
            f"<td class=\"num\">{num(f.get('bytes'))}</td><td><a href=\"{esc(f.get('source_url'))}\">{esc(f.get('file'))}</a></td><td>{esc((f.get('fetched_at') or '')[:19])}</td></tr>"
            for f in files)
        body = (kv_table(p, ["company_name", "period", "conference_date", "status", "wanted", "missing", "generated_at"])
                + "<h3>files[]</h3><table><thead><tr><th>type</th><th>title</th><th>doc_date</th><th>source</th><th class=\"num\">bytes</th><th>file（連到來源）</th><th>fetched_at</th></tr></thead>"
                + f"<tbody>{frows}</tbody></table>")
    elif t == "ir_document_file":
        body = kv_table(p, ["company_slug", "period", "doc_kind", "fiscal_label", "source_file", "source_url", "doc_date", "bytes", "sha256"])
    elif t == "ir_financials":
        ann, qq = p.get("annual") or [], p.get("quarterly") or []
        body = (kv_table(p, ["company_name", "currency", "unit", "source", "generated_at"])
                + f"<h3>annual[]（{len(ann)} 列）</h3>" + fin_table(ann)
                + f"<h3>quarterly[]（{len(qq)} 列）</h3>" + fin_table(qq)
                + '<div class="note">金額為原始單位（台股仟元、美股元）；季別列的 OCF / 資本支出是年初累計（YTD），新版另推算單季值；derived 標示推算值。source_urls 省略，見原始 JSON。</div>')
        if is_new_fin(p):
            body += ("<h3>新版才有的資產負債表明細與天數（annual[] ＋ quarterly[]）</h3>"
                     + fin_table(ann + qq, [("period", "期別"), ("fiscal_year", "年度")] + FIN_COLS_NEW)
                     + '<div class="note">速動資產＝現金及約當現金＋按公允價值衡量之金融資產（流動）＋應收票據＋應收帳款（含關係人）；速動比＝速動資產／流動負債。'
                       '應收天數＝平均應收帳款／營收×365、應付天數＝平均應付帳款／銷貨成本×365，days_basis＝avg 為期初期末平均、end 為期末值（最早一年）；天數只在年度列。</div>')
        else:
            body += '<div class="callout">舊版 financials：沒有現金／應收／應付／存貨明細，也沒有速動比、應收付天數、母公司淨利率。</div>'
    else:
        body = kv_table(p)
    raw = f"<details><summary>原始 JSON（{len(rec['raw']):,} 字）</summary><pre>{esc(rec['raw'])}</pre></details>"
    return f'<section class="card mt" id="r{idx}">{head}<div class="mt">{body}</div>{raw}</section>'


def build_crawler_view(name: str, src: pathlib.Path, out: pathlib.Path, today: str, c: dict | None = None) -> dict:
    if c is None:
        c = parse_crawler_md(src)
        c["version"] = crawler_version(src.stem)
    counts = {}
    for r in c["records"]:
        counts[r["record_type"]] = counts.get(r["record_type"], 0) + 1
    toc = " ".join(f'<a href="#r{i}">{esc(RECORD_LABEL.get(r["record_type"], r["record_type"]))}（{esc(record_date(r) or "—")}）</a>' for i, r in enumerate(c["records"]))
    absent = [t for t in ("ir_conference", "ir_summary", "ir_document", "ir_financials") if t not in counts]
    batches = "、".join(sorted({r["batch_id"] for r in c["records"]}))
    version = c.get("version") or "正式批次"
    ver_note = ("新版爬蟲在 MI_Crawler 開發沙箱（<code>ircal_sandbox</code>）跑出的 dev 批次，<b>尚未進 Databricks</b>；"
                "ir_conference 的 <code>source</code> 為 DEV_SAMPLE（測試時種的場次，不是行事曆爬到的）。" if version == "新版實測"
                else "正式批次：已進 Databricks bronze／silver。")
    intro = f"""
<section class="card">
  <h2>這是什麼</h2>
  <p>Databricks bronze 表 <code>b_ir_calendar_record</code> 裡，爬蟲（MI_Crawler VM）交付的每個 JSON 檔原樣存成一列（<code>payload</code> 欄）。
  這一頁是 <code>{esc(src.name)}</code> 的排版版：company_key = <b>{esc(c['company_key'])}</b>、period = <b>{esc(c['period'])}</b>，共 {c['n']} 檔；
  同一 record_type ＋ batch_path 只留最新批次。<code>period</code> 為 null 的檔（財報數據）不分期別，一併列出。</p>
  <table class="kv"><tbody>
    <tr><td>爬蟲版本</td><td><b>{esc(version)}</b>（批次 {esc(batches)}）。{ver_note}</td></tr>
    <tr><td>抓到的紀錄類型</td><td>{esc("、".join(f"{RECORD_LABEL.get(k, k)} {v} 筆" for k, v in counts.items()))}</td></tr>
    <tr><td>沒有的紀錄類型</td><td>{("<mark>" + esc("、".join(RECORD_LABEL.get(k, k) for k in absent)) + "</mark>") if absent else "—"}</td></tr>
    <tr><td>對應 silver 表</td><td>見各段「進 silver」；原文另存 <code>b_ir_calendar_record.payload</code></td></tr>
  </tbody></table>
  <div class="toc mt">{toc}</div>
</section>"""
    body = intro + "".join(render_record(r, i) for i, r in enumerate(c["records"]))
    out.write_text(page(f"{name}｜爬蟲資料（bronze payload，{version}）", "ir_calendar｜來源檢視｜bronze b_ir_calendar_record",
                        f"來源檔：{esc(src.name)}｜company_key {esc(c['company_key'])}｜period {esc(c['period'])}｜產出日期：{esc(today)}",
                        body, f"由 build_sources.py 產出｜{esc(today)}"), encoding="utf-8")
    return c


# ---------------------------------------------------------------- 原始 bundle 頁
def build_bundle_view(name: str, src: pathlib.Path, out: pathlib.Path, today: str) -> dict:
    d = json.loads(src.read_text(encoding="utf-8"), strict=False)
    co, rows, s, conf, docs = d["company"], d["fin_rows"], d.get("summary"), d.get("conference"), d.get("docs") or []
    parts = [
        ("company", "s_ir_calendar_company", "公司主檔一列"),
        ("fin_rows", "s_ir_calendar_financials", f"{len(rows)} 列（年度 {sum(r['period_type'] == 'annual' for r in rows)}、季別 {sum(r['period_type'] == 'quarterly' for r in rows)}）"),
        ("summary", "s_ir_calendar_summary", "null（無法說彙整）" if not s else f"{s.get('period')} 彙整一列（crawled_at {s.get('crawled_at')}）"),
        ("conference", "s_ir_calendar_conference", "null（無法說場次）" if not conf else f"{conf.get('conference_date')} {conf.get('conference_type')}"),
        ("docs", "s_ir_calendar_document_text", f"{len(docs)} 份（{'、'.join(x['doc_kind'] for x in docs)}）" if docs else "[]"),
    ]
    intro = f"""
<section class="card">
  <h2>這是什麼</h2>
  <p>把 Databricks silver 各表以 <code>company_key</code>（＋ <code>period</code>）join 後包成一個 JSON，
  形狀 = <code>build_ir_report</code> [c09] <code>load_company_bundle</code> 的回傳；<code>{esc(src.name)}</code> 就是這個 JSON，
  <code>build_report.py</code> 讀它產出財務體質報告。period = <b>{esc(d['period'])}</b>。</p>
  <table><thead><tr><th>鍵</th><th>來源 silver 表</th><th>內容</th></tr></thead><tbody>
  {"".join(f"<tr><td><a href='#{k}'><code>{k}</code></a></td><td><code>{t}</code></td><td>{esc(c)}</td></tr>" for k, t, c in parts)}
  </tbody></table>
  <div class="callout">silver 是從 bronze payload 轉出來的（<code>consume_batches</code> [c06]），欄位已攤平、型別已轉；
  要看爬蟲原文請看同資料夾的 <code>{esc(name)}_爬蟲資料.html</code>。</div>
</section>"""
    sec_company = f'<section class="card mt" id="company"><h2>company（公司主檔）</h2>{kv_table(co)}</section>'
    sec_fin = (f'<section class="card mt" id="fin_rows"><h2>fin_rows（財報數據，{len(rows)} 列）</h2>'
               + fin_table(sorted(rows, key=lambda r: (r["period_type"] != "annual", r["period_end"] or "")), [("period_type", "類型")] + FIN_COLS)
               + '<div class="note">金額為原始單位（currency / unit 見第一列：台股 TWD 仟元、美股 USD 元）。</div></section>')
    if s:
        s_meta = {k: v for k, v in s.items() if k not in ("summary_json",) and k not in ("core_points", "guidance", "key_numbers", "risks", "notes", "sources", "found", "headline_metrics", "management_views", "positive_signals", "watch_items", "open_questions")}
        sec_sum = (f'<section class="card mt" id="summary"><h2>summary（法說彙整）</h2>{kv_table(s_meta)}<h3>彙整內容</h3>{summary_block(s)}'
                   + (f"<details><summary>summary_json 原文</summary><pre>{esc(s.get('summary_json'))}</pre></details>" if s.get("summary_json") else "")
                   + "</section>")
    else:
        sec_sum = '<section class="card mt" id="summary"><h2>summary（法說彙整）</h2><p class="null">null — 這家在 s_ir_calendar_summary 沒有對應期別的列</p></section>'
    sec_conf = (f'<section class="card mt" id="conference"><h2>conference（法說場次）</h2>{kv_table(conf) if conf else "<p class=null>null — s_ir_calendar_conference 無對應期別的列</p>"}</section>')
    doc_parts = []
    for i, x in enumerate(docs):
        meta = {k: v for k, v in x.items() if k != "text_md"}
        txt = x.get("text_md") or ""
        doc_parts.append(f"<h3>docs[{i}]：{esc(x.get('file_name'))}（{esc(x.get('doc_kind'))}）</h3>{kv_table(meta)}"
                         f"<details><summary>text_md 全文（{len(txt):,} 字{'，匯出時截斷' if x.get('truncated_for_export') else ''}）</summary><pre style=\"white-space:pre-wrap;max-height:720px\">{esc(txt)}</pre></details>")
    sec_docs = f'<section class="card mt" id="docs"><h2>docs（解析後文件，{len(docs)} 份）</h2>{"".join(doc_parts) if docs else "<p class=null>[]</p>"}</section>'
    body = intro + sec_company + sec_fin + sec_sum + sec_conf + sec_docs
    out.write_text(page(f"{name}｜原始資料（silver bundle）", "ir_calendar｜來源檢視｜silver bundle",
                        f"來源檔：{esc(src.name)}｜company_key {esc(co['company_key'])}｜period {esc(d['period'])}｜產出日期：{esc(today)}",
                        body, f"由 build_sources.py 產出｜{esc(today)}"), encoding="utf-8")
    return d


def merge_crawlers(parts: list[dict]) -> dict | None:
    """多個期別／版本的爬蟲檔合併成一份：同 (version, record_type, batch_path) 留批次較新的；period 串起來；views 記每檔的頁面。"""
    if not parts:
        return None
    best = {}
    for c in parts:
        for r in c["records"]:
            key = (r["version"], r["record_type"], r["batch_path"])
            if key not in best or r["batch_id"] > best[key]["batch_id"]:
                best[key] = r
    records = sorted(best.values(), key=lambda r: (r["version"] == "新版實測", r["batch_id"], r["record_type"], r["batch_path"]))
    periods = sorted({c["period"] for c in parts})
    return dict(company_key=parts[0]["company_key"], period="＋".join(periods), periods=periods, n=len(records), records=records,
                views=[(c["period"], c["view"], c["version"]) for c in parts],
                versions=sorted({c["version"] for c in parts}))


def crawler_version(stem: str) -> str:
    return "新版實測" if "新版實測" in stem else "正式批次"


def build_all(today: str) -> dict:
    """五家各產原始資料頁 + 每個 <公司>_爬蟲*.md 一頁；回傳 {name: {"bundle": dict, "crawler": 合併後 dict|None}}。

    檔名規則：<公司>_爬蟲[_<期別>][_新版實測].md → <公司>_爬蟲資料[_<期別>][_新版實測].html；
    「新版實測」= 2026-10-21 爬蟲新版在沙箱跑出的 dev 批次（未進 Databricks），其餘為正式批次。
    """
    out = {}
    for name in COMPANIES:
        folder = HERE / name
        d = build_bundle_view(name, folder / f"{name}.md", folder / f"{name}_原始資料.html", today)
        parts = []
        for cp in sorted(folder.glob(f"{name}_爬蟲*.md")):
            suffix = cp.stem[len(f"{name}_爬蟲"):]          # ""、"_Q3"、"_新版實測"、"_Q3_新版實測"
            view = f"{name}_爬蟲資料{suffix}.html"
            c = parse_crawler_md(cp)
            c["version"] = crawler_version(cp.stem)
            for r in c["records"]:
                r["version"] = c["version"]
            build_crawler_view(name, cp, folder / view, today, c)
            c["view"] = view
            parts.append(c)
        parts.sort(key=lambda c: (c["version"] == "新版實測", c["period"]))
        out[name] = {"bundle": d, "crawler": merge_crawlers(parts)}
        print(f"{name:12s} 原始資料.html + 爬蟲資料 {len(parts)} 頁  records={out[name]['crawler']['n'] if parts else 0}")
    return out


if __name__ == "__main__":
    import datetime
    build_all(datetime.date.today().isoformat())
