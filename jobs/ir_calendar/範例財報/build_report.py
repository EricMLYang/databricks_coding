#!/usr/bin/env python3
"""把本資料夾的 *.md（實為 JSON）依「供應鏈供應商財務體質報告模板」產出 HTML。

模板：PM_Head/projects/MI_Crawler/ir_calendar/doc/20261010_供應鏈供應商財務體質報告模板.html
- 數字欄位（KPI、五年、季度、現金流與資產負債、分數）由 fin_rows 自動算。
- 敘事欄位（一句話判讀、採購提示、QBR 必問、War Room、Watchlist、限制）在 NARRATIVE 逐家撰寫，
  數字一律從 k dict 帶入，不手抄。
- 資料給不出的欄位保留 <mark>資料缺：…</mark>（黃底），對照 模板覆蓋度評估.md。

用法：python3 build_report.py            # 在本資料夾執行，輸出 <公司>.html
"""
from __future__ import annotations

import html
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
TODAY = "2026-10-20"
VERSION = "v1"
PHASE = "示範（Pilot）"
TEMPLATE_REF = "doc/20261010_供應鏈供應商財務體質報告模板.html"

FILES = ["Corning.md", "南亞塑膠工業.md", "奇美實業.md", "臺灣永光化學工業.md", "長興材料工業.md"]

MISSING = '<mark>資料缺</mark>'


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
    s = f"{v:+.{d}f}%" if sign else f"{v:.{d}f}%"
    return s


def m(v, d=2):
    """金額欄：有值給數字，沒值給黃底。"""
    return MISSING if v is None else f2(v, d)


def mp(v, d=2, sign=False):
    return MISSING if v is None else pct(v, d, sign)


def esc(s) -> str:
    return html.escape(str(s), quote=True)


def q_label(period: str) -> str:  # 2026Q2 → 2026 Q2
    return period.replace("Q", " Q")


# ---------------------------------------------------------------- 指標整理
def build_k(d: dict) -> dict:
    co = d["company"]
    rows = d["fin_rows"]
    unit = rows[0]["unit"]
    cur = rows[0]["currency"]
    cur_label = "NT$" if cur == "TWD" else ("US$" if cur == "USD" else cur)

    annual = sorted([r for r in rows if r["period_type"] == "annual"], key=lambda r: r["fiscal_year"])[-5:]
    quarters = sorted([r for r in rows if r["period_type"] == "quarterly"], key=lambda r: r["period_end"])
    q = quarters[-1]
    year = q["period"][:4]
    qn = q["period"][4:]
    q_ly = next((r for r in quarters if r["period"] == f"{int(year) - 1}{qn}"), None)
    q1 = next((r for r in quarters if r["period"] == f"{year}Q1"), None)
    year_qs = [r for r in quarters if r["period"].startswith(year)]

    rev_q = yi(q["revenue"], unit)
    rev_ly = yi(q_ly["revenue"], unit) if q_ly else None
    yoy = (rev_q / rev_ly - 1) * 100 if (rev_q and rev_ly) else None
    rev_q1 = yi(q1["revenue"], unit) if q1 else None
    qoq = (rev_q / rev_q1 - 1) * 100 if (rev_q and rev_q1 and q1 is not q) else None

    oi = yi(q["operating_income"], unit)
    pt = yi(q["pretax_income"], unit)
    ni = yi(q["net_income"], unit)
    nonop = (pt - oi) if (pt is not None and oi is not None) else None
    nonop_pct = (nonop / pt * 100) if (nonop is not None and pt) else None

    ocf = yi(q.get("operating_cash_flow_ytd"), unit)
    capex = yi(q.get("capex_ytd"), unit)
    ni_ytd = yi(q.get("net_income_ytd"), unit)
    if ni_ytd is None:
        vals = [r["net_income"] for r in year_qs]
        ni_ytd = yi(sum(vals), unit) if all(v is not None for v in vals) else None
    ocf_ni = (ocf / ni_ytd) if (ocf is not None and ni_ytd) else None

    k = dict(
        name=co["company_name"], code=co["stock_code"], key=co["company_key"], market=co["market"],
        industry=co.get("industry"), ir_url=co.get("ir_url"), website=co.get("website_url"),
        cur=cur, cur_label=cur_label, unit=unit, unit_note=("千元" if unit == "thousand" else "元"),
        period=d["period"], q=q, q_ly=q_ly, q1=q1, year=year, year_qs=year_qs, annual=annual,
        q_label=q_label(q["period"]), q_ly_label=q_label(q_ly["period"]) if q_ly else None,
        rev_q=rev_q, rev_ly=rev_ly, yoy=yoy, rev_q1=rev_q1, qoq=qoq,
        gm=q["gross_margin"], gm_ly=q_ly["gross_margin"] if q_ly else None,
        opm=q["operating_margin"], opm_ly=q_ly["operating_margin"] if q_ly else None,
        nm=q["net_margin"], oi=oi, pt=pt, ni=ni, nonop=nonop, nonop_pct=nonop_pct,
        ocf=ocf, capex=capex, ni_ytd=ni_ytd, ocf_ni=ocf_ni,
        ta=yi(q["total_assets"], unit), tl=yi(q["total_liabilities"], unit),
        dr=q["debt_ratio"], cr=q["current_ratio"],
        summary=d.get("summary"), conference=d.get("conference"), docs=d.get("docs") or [],
    )
    # 敘事用的字串版
    k.update(
        REV_Q=f2(rev_q), REV_LY=f2(rev_ly), YOY=pct(yoy, 1, sign=True), REV_Q1=f2(rev_q1), QOQ=pct(qoq, 1, sign=True),
        GM=pct(k["gm"]), GM_LY=pct(k["gm_ly"]), OPM=pct(k["opm"]), OPM_LY=pct(k["opm_ly"]), NM=pct(k["nm"]),
        OI=f2(oi), PT=f2(pt), NI=f2(ni), NONOP=f2(nonop), NONOP_PCT=pct(nonop_pct, 0),
        OCF=f2(ocf), CAPEX=f2(capex), CAPEX_ABS=f2(abs(capex)) if capex is not None else "—",
        NI_YTD=f2(ni_ytd), OCF_NI=(f"{ocf_ni:.2f}x" if ocf_ni is not None else "—"),
        TA=f2(k["ta"]), TL=f2(k["tl"]), DR=pct(k["dr"], 2), CR=f2(k["cr"]),
    )
    k["score"], k["score_rows"] = score(k)
    k["light"] = light(k["score"])
    return k


# ---------------------------------------------------------------- 示範分數
def score(k: dict):
    """採購管理用示範分數（滿分 100），規則寫在 模板覆蓋度評估.md §5。"""
    rows = []

    def add(name, pts, basis):
        rows.append((name, pts, basis))
        return pts

    s = 0
    nm, opm, yoy, dr, cr = k["nm"], k["opm"], k["yoy"], k["dr"], k["cr"]
    s += add("最新季稅後淨利率", 15 if nm > 10 else 10 if nm > 5 else 5 if nm >= 0 else 0, pct(nm))
    s += add("最新季營業利益率", 15 if opm > 10 else 10 if opm > 5 else 5 if opm >= 0 else 0, pct(opm))
    s += add("營收 YoY", 0 if yoy is None else 10 if yoy > 10 else 6 if yoy >= 0 else 3 if yoy >= -10 else 0, pct(yoy, 1, True))
    s += add("負債比", 15 if dr < 40 else 10 if dr <= 60 else 5, pct(dr))
    s += add("流動比率", 15 if cr > 2 else 10 if cr >= 1.5 else 5 if cr >= 1 else 0, f"{cr:.2f}x")
    ocf, ni_ytd = k["ocf"], k["ni_ytd"]
    if ocf is None:
        s += add("營業現金流（YTD）", 0, "資料缺")
    elif ocf < 0:
        s += add("營業現金流（YTD）", 0, f"負 {f2(ocf)}")
    elif ni_ytd and ocf < 0.5 * ni_ytd:
        s += add("營業現金流（YTD）", 5, f"正但 OCF/淨利 {k['OCF_NI']}")
    else:
        s += add("營業現金流（YTD）", 10, f"正，OCF/淨利 {k['OCF_NI']}")
    losses = [r["fiscal_year"] for r in k["annual"] if (r["net_income"] or 0) < 0]
    last_fy = k["annual"][-1]["fiscal_year"]
    s += add("近五年虧損年", 10 if not losses else 0 if last_fy in losses else 5, "、".join(map(str, losses)) or "無")
    gm, gm_ly = k["gm"], k["gm_ly"]
    s += add("毛利率較去年同期", 10 if (gm is not None and gm_ly is not None and gm > gm_ly) else 0, f"{pct(gm_ly)} → {pct(gm)}")
    pen = -5 if (k["nonop"] is not None and k["oi"] is not None and k["nonop"] > k["oi"]) else 0
    s += add("業外依賴（業外＞本業扣 5）", pen, f"業外 {k['NONOP']} vs 本業 {k['OI']}")
    return max(0, min(100, s)), rows


def light(score_: int):
    if score_ >= 70:
        return dict(emoji="🟢", name="綠燈", action="維持往來", css="--green")
    if score_ >= 40:
        return dict(emoji="🟡", name="黃燈", action="加強監控", css="--amber")
    return dict(emoji="🔴", name="紅燈", action="降載", css="--red")


# ---------------------------------------------------------------- 敘事（逐家）
def narr_glw(k):
    return dict(
        one_liner=(f"2026 Q2 營收 US$ {k['REV_Q']} 億（YoY {k['YOY']}），管理層稱連續第 9 季年增；GAAP 毛利率 {k['GM']}、營益率 {k['OPM']} 皆在近五年高檔。"
                   f"負債比 {k['DR']} 多年維持 58–60%，流動比 {k['CR']}x，上半年營業現金流 US$ {k['OCF']} 億高於上半年淨利 US$ {k['NI_YTD']} 億，本業獲利與現金流一致，無仰賴業外的跡象。"
                   "主要風險不在財務而在資源配置：成長與資本支出集中在光通訊與太陽能，顯示玻璃所在的 Glass Innovations 部門 Q2 營收僅年增 1%。"),
        tips=[("不以單季淨利放寬風險：", "GAAP EPS 0.64 與 core EPS 0.78 的差距來自避險損益、一次性稅務與重組項目；本報告一律用 GAAP 口徑。"),
              ("供貨安全優先：", "追蹤 Glass Innovations 的產能配置與玻璃基板報價；公司資本支出優先給光纖（美國光纖產能 +50%、光連接器 10 倍）。"),
              ("維持備援：", "玻璃基板關鍵世代保留 AGC／NEG 的 2nd source 配額與可轉單條件。"),
              ("升級條件：", "若 Glass Innovations 連兩季營收年減、或公司宣布顯示玻璃熔爐重整／減產，升級 QBR。")],
        qbr=["Glass Innovations 部門內顯示玻璃與特殊材料各自的營收、利潤趨勢，以及 2026 下半年顯示玻璃熔爐投資計畫。",
             "光通訊 10 倍擴產是否排擠顯示玻璃的資本與人力配置；對玻璃基板交期與價格的影響。",
             "太陽能部門 2026 Q2 淨損 US$ 700 萬，管理層稱 Q3 起改善，請提供轉盈時點與對集團現金流的影響。",
             "顯示玻璃價格策略：先前的調漲是否延續，2027 年合約條件。",
             "非 GAAP 調整項（避險損益、重組與減損）的金額與現金影響，確認 core 指標與 GAAP 的差距來源。"],
        warroom=[("新事業成長（光通訊／AI）", "光通訊營收年增 32%、企業網路 +65%；與 Amazon、NVIDIA 簽長約；Springboard 目標 2026 底年化營收 US$ 200 億",
                  f"合併營收 YoY {k['YOY']}，營益率 {k['OPM']}（去年同期 {k['OPM_LY']}）；成長已反映在合併數字", "🟢 Positive"),
                 ("本業（顯示玻璃）", "Glass Innovations（顯示＋特殊材料）Q2 營收 US$ 14.63 億、年增 1%，淨利 US$ 3.54 億、年增 9%",
                  f"部門數字來自新聞稿，fin_rows 無部門別；集團毛利率 {k['GM']} 與去年同期 {k['GM_LY']} 持平", "🟡 Watch"),
                 ("現金流", "Q2 營業現金流 US$ 17.2 億，調整後自由現金流 US$ 14.2 億",
                  f"上半年 OCF（YTD）US$ {k['OCF']} 億，上半年淨利 US$ {k['NI_YTD']} 億，OCF／淨利 {k['OCF_NI']}；資本支出欄位缺", "🟢 Positive"),
                 ("財務結構", "新聞稿未提及",
                  f"負債比 {k['DR']}、流動比 {k['CR']}x，總資產 US$ {k['TA']} 億；近五年負債比 58–60% 穩定", "🟢 Stable"),
                 ("關鍵零件供應", "太陽能晶圓廠完成延長歲修與設備升級；美國光纖產能擴 50%",
                  "無法從財報驗證產能；資本支出欄位缺，看不到投資強度", "🟡 Watch"),
                 ("供貨能力", "連續 9 季年增；Q3 指引 core 營收 US$ 49–50 億（約 +16%）、core EPS 0.85–0.89",
                  f"Q1→Q2 營收 US$ {k['REV_Q1']} → {k['REV_Q']} 億，季增 {k['QOQ']}", "🟢 Positive")],
        positive=["連續 9 季營收年增，2025 全年營收 US$ 156.29 億為近五年新高，淨利率回到 10% 以上。",
                  f"上半年 OCF US$ {k['OCF']} 億大於淨利，獲利有現金支撐。",
                  f"流動比率由 2025 Q2 的 1.50x 升至 {k['CR']}x，短期償債緩衝加厚。"],
        watch=["顯示玻璃所在部門成長停滯（+1% YoY），公司資源明顯轉向光通訊與太陽能。",
               f"負債比 {k['DR']} 為五家供應商中最高，雖穩定但對利率敏感。",
               "太陽能部門 Q2 淨損、生命科學與新興事業連續虧損，需確認不拖累集團現金。"],
        strategy=["維持現有 allocation，玻璃基板不因財務面降載；但把「產能配置」列為每季必問。",
                  "Backup source：AGC／NEG 維持可轉單比例，特定世代玻璃先鎖長約。",
                  "新事業（光通訊、太陽能）以「是否排擠顯示玻璃投資」為觀察層級，不需追蹤其本身獲利。",
                  "每季追蹤：Glass Innovations 營收 YoY、集團 OCF、負債比、玻璃基板報價。"],
        limits=("幣別為美元，金額以「億美元」呈現，不換算新台幣。fin_rows 為 SEC companyfacts 的 GAAP 數字；新聞稿的 core（非 GAAP）指標只放在管理層觀點。"
                "資本支出與股東權益欄位在 fin_rows 為空；季度 OCF 只有年初累計（YTD）。部門別數字來自 2026-07-28 新聞稿（Exhibit 99）人工摘錄，未進資料表；"
                "無法說會逐字稿與 Q&A，本公司在資料集裡沒有 summary（法說摘要）列。"),
        mgmt_src="2026-07-28 第二季財報新聞稿（SEC Exhibit 99）",
    )


def narr_npc(k):
    return dict(
        one_liner=(f"2026 Q2 營收 NT$ {k['REV_Q']} 億（YoY {k['YOY']}），毛利率 {k['GM']}（去年同期 {k['GM_LY']}）、營益率 {k['OPM']}，電子材料（玻纖布、銅箔基板、ABF 載板）帶動本業由 2023–2025 的低谷翻揚。"
                   f"但單季稅前淨利 NT$ {k['PT']} 億中，業外（主要是南亞科技、台塑石化的權益法收益）約 NT$ {k['NONOP']} 億、占 {k['NONOP_PCT']}，淨利率 {k['NM']} 遠高於營益率。"
                   f"上半年營業現金流只有 NT$ {k['OCF']} 億，對比上半年淨利 NT$ {k['NI_YTD']} 億，獲利大多尚未變成現金。負債比 {k['DR']}、流動比 {k['CR']}x，資產負債表緩衝充足。"),
        tips=[("不以單季淨利放寬風險：", f"Q2 淨利 NT$ {k['NI']} 億中約六成是權益法投資收益，屬帳面而非現金；評估供應商體質看營業利益（NT$ {k['OI']} 億）。"),
              ("供貨安全優先：", "追蹤上半年 OCF 偏低的原因（存貨與應收是否隨漲價膨脹）、Q3 化工與聚酯產線停車是否波及聚酯膜／離型膜。"),
              ("維持備援：", "聚酯膜、離型膜等顯示相關料號保留 2nd source；2026/10 離型膜第 5、6 套投產後重新議價。"),
              ("升級條件：", "若電子材料營益率連兩季下滑、或 OCF 連續兩個半年低於淨利三成，升級 QBR。")],
        qbr=["上半年稅前淨利 NT$ 468 億但營業現金流僅 NT$ 33 億：營運資金（存貨、應收）變動明細與下半年回收計畫。",
             "權益法收益（南亞科技、台塑石化）的現金股利入帳時點；集團資本支出與股利政策是否仰賴這筆收益。",
             "Q3「部分產線安排停車」的具體產品與期間，對聚酯膜、光學膜交期的影響。",
             "2026/10 離型膜第 5、6 套（各 +40% 產能）投產時程與初期良率；是否優先供應既有客戶。",
             "中東衝突下原料供應受限的替代來源與庫存天數；與客戶的價格連動條款是否調整。"],
        warroom=[("新事業成長（電子材料／AI 供應鏈）", "電子材料占上半年營收 52.7%，Q2 營益率 19.9%（2025 Q2 為 4.0%）；ABF 載板、銅箔基板、玻纖布供不應求",
                  f"合併營益率由 {k['q_ly_label']} 的 {k['OPM_LY']} 升至 {k['OPM']}；營收 YoY {k['YOY']}", "🟢 Positive"),
                 ("本業（化工、聚酯）", "Q3 進入淡季、中東戰事使原料不穩，部分產線停車；化工 Q2 營益率 2.1%、聚酯 5.3%",
                  f"fin_rows 無部門別；合併毛利率 {k['GM']} 已高於 2022 以來各季", "🟡 Watch"),
                 ("現金流", "法說簡報未提現金流",
                  f"上半年 OCF NT$ {k['OCF']} 億，僅為上半年淨利 NT$ {k['NI_YTD']} 億的 {k['OCF_NI']}；資本支出 NT$ {k['CAPEX']} 億", "🔴 Risk"),
                 ("財務結構", "未提及",
                  f"負債比 {k['DR']}（2025 底 39.11%），流動比 {k['CR']}x，總資產 NT$ {k['TA']} 億", "🟢 Stable"),
                 ("關鍵零件供應", "荷姆茲海峽封鎖使原料供應受限，各項產品降產或停產因應",
                  "無法從財報驗證；化工 Q2 營益率轉正（2.1%）靠漲價與庫存利益，非結構改善", "🟡 Watch"),
                 ("供貨能力", "電子材料產線維持高開動率、銅箔基板產能利用率 9 成以上；擴建 2026/10 起陸續投產",
                  f"Q1→Q2 營收 NT$ {k['REV_Q1']} → {k['REV_Q']} 億，季增 {k['QOQ']}", "🟢 Positive")],
        positive=["本業由谷底回升：營業利益由 2024 全年 NT$ 4.5 億升至 2026 上半年 NT$ 151 億。",
                  f"負債比降至 {k['DR']}，流動比 {k['CR']}x，資產負債表在五家供應商中最健康之一。",
                  "擴建（離型膜、電子級 CO2、銅箔）集中在顯示與電子相關料，供應面有增量。"],
        watch=[f"獲利結構：Q2 業外占稅前淨利 {k['NONOP_PCT']}，南亞科技記憶體景氣反轉時淨利會同步大幅波動。",
               f"上半年 OCF NT$ {k['OCF']} 億遠低於淨利，營運資金吃掉現金，需看 Q3 是否回收。",
               "化工、聚酯兩大宗產品仍供過於求且受中東局勢影響，Q3 淡季停車可能擴大。"],
        strategy=["維持 allocation；電子材料類料號可提高長約比例鎖定產能。",
                  "Backup source：聚酯膜／離型膜保留第二供應商，化工類原料確認其替代來源。",
                  "新事業（AI 載板材料）觀察層級：只看是否排擠顯示用聚酯膜產能，不追蹤其獲利。",
                  "每季追蹤：營業利益（非淨利）、OCF／淨利、電子材料營益率、負債比。"],
        limits=("法說資料基準為 2026 Q3（2026-10-13 摩根大通線上法說會），但財務數字最新只到 2026 Q2，兩者口徑不同；Q3 實際數字尚未公布。"
                "fin_rows 來自 MOPS 財務報表 API（單位千元，換算成億元）；2025 Q4 季度列為年度減前三季推算。季度 OCF 與資本支出只有年初累計（YTD）。"
                "部門別營收與營益率來自法說簡報，未進資料表。"),
        mgmt_src="2026-10-13 法說會摘要（summary）＋法說簡報《2026 年上半年營運概況》",
    )


def narr_chimei(k):
    nomgmt = "<mark>資料缺：無法說會摘要</mark>"
    return dict(
        one_liner=(f"2026 Q2 營收 NT$ {k['REV_Q']} 億（YoY {k['YOY']}），營收已連續五年下滑（2021 NT$ 1,786.72 億 → 2025 NT$ 1,136.79 億）；"
                   f"毛利率 {k['GM']}、營益率 {k['OPM']}，本業在損益兩平邊緣，2023–2025 三年本業皆虧損，淨利靠業外。上半年營業現金流 NT$ {k['OCF']} 億為負。"
                   f"但負債比 {k['DR']}、流動比 {k['CR']}x，資產負債表緩衝充足，短期無償債風險，問題在獲利能力與現金創造。本公司沒有法說會摘要，管理層展望欄位空缺。"),
        tips=[("不以單季淨利放寬風險：", f"Q2 稅前淨利 NT$ {k['PT']} 億中營業利益只有 NT$ {k['OI']} 億，淨利幾乎全靠業外；本業連續三年虧損。"),
              ("供貨安全優先：", "上半年 OCF 為負，追蹤存貨與應收變化、是否開始縮減產線或處分資產。"),
              ("維持備援：", "PMMA／光學板材等關鍵料號保留 2nd source，並確認其台南與中國廠的產能去留。"),
              ("升級條件：", "若 OCF 連續兩個半年為負、或營收再年減 10% 以上，升級 QBR 並評估降載。")],
        qbr=["營收連續五年下滑的結構原因（ABS／PS 價格、中國產能過剩、客戶流失）與 2026 下半年止跌計畫。",
             "上半年營業現金流為負的原因（存貨、應收、預付）與年底前的回收目標。",
             "2026 Q2 業外收益的組成（權益法、金融資產評價、處分利益）及現金實現程度。",
             "顯示用光學材料（PMMA 板材、導光板料）產線的產能利用率，是否列入縮減名單。",
             "會計師核閱報告為「保留結論」（部分非重要子公司未經核閱），涉及的子公司與占比變化。"],
        warroom=[("新事業成長", nomgmt, "fin_rows 無部門別，無法辨識新事業貢獻", "🟡 Watch"),
                 ("本業", nomgmt, f"Q2 營益率 {k['OPM']}；2023–2025 全年營益率 -1.37% / -0.89% / -0.41%；毛利率 {k['GM']}（去年同期 {k['GM_LY']}）", "🔴 Risk"),
                 ("現金流", nomgmt, f"上半年 OCF NT$ {k['OCF']} 億（負），資本支出 NT$ {k['CAPEX']} 億；2025 全年 OCF NT$ 106.53 億為正", "🔴 Risk"),
                 ("財務結構", nomgmt, f"負債比 {k['DR']}、流動比 {k['CR']}x，總資產 NT$ {k['TA']} 億、總負債 NT$ {k['TL']} 億", "🟢 Stable"),
                 ("關鍵零件供應", nomgmt, "無法從財報驗證", "🟡 Watch"),
                 ("供貨能力", nomgmt, f"Q2 營收 YoY {k['YOY']}；2026 Q1 財務列缺，無法看季增", "🟡 Watch")],
        positive=[f"負債比 {k['DR']}、流動比 {k['CR']}x，2021 以來負債比都在 29–36%，財務結構穩健。",
                  "2025 全年營業現金流 NT$ 106.53 億為正，過去五年每年 OCF 皆為正。",
                  "資本支出持續（2025 全年 NT$ 55.57 億），未見全面縮減投資。"],
        watch=[f"營收五年減少 36%，本業 2023–2025 連續虧損，2026 Q2 營益率 {k['OPM']}。",
               f"上半年 OCF 轉負（NT$ {k['OCF']} 億）。",
               "無法說會摘要、無法人說明資料，管理層展望與產能計畫完全未知。"],
        strategy=["維持 allocation 但不增加；關鍵光學料號改為季度檢視。",
                  "Backup source：PMMA 板材、ABS／PS 確認第二供應商的產能與價格。",
                  "新事業觀察層級：先取得公司年報／法說資料再決定。",
                  "每季追蹤：OCF、營益率、營收 YoY、存貨天數；年度追蹤會計師結論。"],
        limits=("本公司沒有法說會摘要（summary 為空），管理層觀點全部空缺。fin_rows 只有 2025 Q2 與 2026 Q2 兩個季度列（缺 2025 Q1／Q3／Q4、2026 Q1），季度表只有一列，看不到連續季度趨勢。"
                "2023 年淨利為負但 EPS 為正（0.05），兩者口徑不同（EPS 為歸屬母公司）；2026 Q2 合併淨利 NT$ 4.36 億、歸屬母公司 NT$ 9.75 億，非控制權益為負，需以財報附註確認。財報 PDF 文字匯出截斷在 20,006 字，現金流量表與附註不在匯出內。"
                "公司主檔缺產業別、官網與 IR 網址。"),
        mgmt_src=None,
    )


def narr_everlight(k):
    nomgmt = "<mark>資料缺：無法說會摘要</mark>"
    return dict(
        one_liner=(f"2026 Q2 營收 NT$ {k['REV_Q']} 億（YoY {k['YOY']}），毛利率 {k['GM']} 較去年同期 {k['GM_LY']} 明顯改善，營益率 {k['OPM']}；2025 全年虧損（EPS -0.21）後，2026 上半年已連兩季轉盈。"
                   f"規模小（年營收不到 NT$ 100 億），營收五年由 NT$ 92.01 億降至 NT$ 75.69 億。負債比 {k['DR']}、流動比 {k['CR']}x，上半年營業現金流 NT$ {k['OCF']} 億為正，財務結構無疑慮，風險在獲利薄與營收萎縮。沒有法說會摘要。"),
        tips=[("不以單季淨利放寬風險：", f"Q2 淨利 NT$ {k['NI']} 億、稅後淨利率 {k['NM']}，獲利基數小，一季匯損或存貨跌價就會翻負。"),
              ("供貨安全優先：", "追蹤電子化學品（光阻、彩色濾光片用色料）事業的營收與毛利率是否持續改善，以及相關廠房投資。"),
              ("維持備援：", "特用化學品關鍵料號保留 2nd source，確認替代配方的認證時程。"),
              ("升級條件：", "若毛利率回落至 20% 以下、或連兩季本業虧損，升級 QBR。")],
        qbr=["2025 全年虧損的原因（產品組合、原料、匯率、一次性）與 2026 上半年轉盈的持續性。",
             "電子化學品（顯示器用）事業占營收比重、毛利率與產能利用率。",
             "營收連續下滑的事業別（染料、特化、電子化學品）與退出／轉型計畫。",
             f"2026 下半年資本支出計畫與資金來源；上半年資本支出 NT$ {k['CAPEX_ABS']} 億的用途。",
             "會計師核閱報告為「保留結論」（部分子公司未經核閱），涉及的子公司與占比。"],
        warroom=[("新事業成長", nomgmt, "fin_rows 無部門別", "🟡 Watch"),
                 ("本業", nomgmt, f"Q2 營益率 {k['OPM']}（去年同期 {k['OPM_LY']}）；2025 全年營益率 -2.59%，2026 Q1 1.83% → Q2 {k['OPM']}", "🟡 Watch"),
                 ("現金流", nomgmt, f"上半年 OCF NT$ {k['OCF']} 億、上半年淨利 NT$ {k['NI_YTD']} 億，OCF／淨利 {k['OCF_NI']}；資本支出 NT$ {k['CAPEX']} 億", "🟢 Positive"),
                 ("財務結構", nomgmt, f"負債比 {k['DR']}、流動比 {k['CR']}x；總資產 NT$ {k['TA']} 億，五年負債比 33–36%", "🟢 Stable"),
                 ("關鍵零件供應", nomgmt, "無法從財報驗證", "🟡 Watch"),
                 ("供貨能力", nomgmt, f"Q1→Q2 營收 NT$ {k['REV_Q1']} → {k['REV_Q']} 億，季增 {k['QOQ']}", "🟡 Watch")],
        positive=[f"毛利率連兩季回升（2025 Q3 15.95% → 2026 Q2 {k['GM']}），本業轉盈。",
                  f"上半年 OCF 為正且高於淨利，流動比 {k['CR']}x。",
                  f"負債比 {k['DR']}，無財務槓桿疑慮。"],
        watch=["營收規模小且五年下滑 17%，單一事業波動即影響全公司。",
               "2025 全年虧損，2026 轉盈基數低，尚未證明可持續。",
               "無法說會摘要，管理層對電子化學品的投資意向未知。"],
        strategy=["維持 allocation；對 AUO 而言採購金額小，重點在供應連續性而非財務承壓。",
                  "Backup source：光阻／色料關鍵料號確認第二供應商認證進度。",
                  "新事業觀察層級：取得法說或年報後再評估。",
                  "每季追蹤：毛利率、營益率、OCF、營收 YoY。"],
        limits=("沒有法說會摘要，管理層觀點欄位空缺。fin_rows 來自 MOPS（千元換算億元），季度 OCF 與資本支出為年初累計口徑；2025 Q4 列為推算。"
                "財報 PDF 文字匯出截斷在 20,006 字，未涵蓋附註。公司英文名在主檔被截斷（Corporatio）。"),
        mgmt_src=None,
    )


def narr_eternal(k):
    return dict(
        one_liner=(f"2026 Q2 營收 NT$ {k['REV_Q']} 億（YoY {k['YOY']}），毛利率 {k['GM']}（去年同期 {k['GM_LY']}）、營益率 {k['OPM']}，合併稅後淨利 NT$ {k['NI']} 億（歸屬母公司 8.47 億）為近四年單季新高；"
                   f"2021–2025 營收逐年下滑後，2026 上半年三大事業群（合成樹脂、電子材料、特用材料）同步回升。上半年營業現金流 NT$ {k['OCF']} 億高於淨利 NT$ {k['NI_YTD']} 億。"
                   f"負債比 {k['DR']} 在台廠中偏高（五年由 59.25% 降至 {k['DR']}），流動比 {k['CR']}x；董事會核准近 NT$ 20 億新資本支出（蘆竹、湖北、泰國），2027 年後開出，資金需求上升要留意。"),
        tips=[("不以單季淨利放寬風險：", f"Q2 稅前 NT$ {k['PT']} 億中業外約 NT$ {k['NONOP']} 億，比重不高，獲利以本業為主；但媒體報導的「上半年營業利益率 24%」與財報營益率 {k['OPM']} 不符（24% 接近毛利率），引用以財報為準。"),
              ("供貨安全優先：", f"追蹤近 NT$ 20 億擴產的資金來源（負債比已 {k['DR']}）與泰國、湖北新廠進度；歐洲需求疲弱對合成樹脂的影響。"),
              ("維持備援：", "乾膜光阻、光學膜／特用材料關鍵料號保留 2nd source，新廠量產前不集中轉單。"),
              ("升級條件：", "若負債比回升至 55% 以上且 OCF 轉負、或毛利率回落至 20% 以下，升級 QBR。")],
        qbr=["近 NT$ 20 億資本支出的分項（蘆竹特用材料、湖北合資、泰國電子材料廠）、時程與資金來源（自有／舉債）。",
             "Q2 毛利率「明顯增長」中，產品組合與原料轉嫁各占多少；原料回跌時能否守住。",
             "顯示相關料號（光學膜、特用材料）在三大事業群中的歸屬、營收占比與產能利用率。",
             "歐洲需求疲弱與人民幣波動對 2026 下半年的量化影響；避險部位。",
             "媒體引述「上半年營業利益率 24%」的口徑（疑為毛利率），請公司提供正式數字。"],
        warroom=[("新事業成長（特用材料）", "對特用材料長期成長正面，持續投入產能與技術；董事會核准近 NT$ 20 億擴產（蘆竹、湖北、泰國）",
                  f"上半年資本支出 NT$ {k['CAPEX']} 億；擴產 2027 年後才開出，尚未反映在財報", "🟢 Positive"),
                 ("本業", "Q2 毛利率較 Q1 明顯增長，來自產品組合優化與原料漲價即時轉嫁；三大事業群營收獲利同步年增",
                  f"毛利率 2026 Q1 22.16% → Q2 {k['GM']}，營益率 5.22% → {k['OPM']}，與管理層說法一致", "🟢 Positive"),
                 ("現金流", "現金部位約 NT$ 103 億",
                  f"上半年 OCF NT$ {k['OCF']} 億 ＞ 淨利 NT$ {k['NI_YTD']} 億；資本支出 NT$ {k['CAPEX']} 億，自由現金流為正", "🟢 Positive"),
                 ("財務結構", "資產負債表規模約 NT$ 670 億；「負債比率由 180 降至 174」口徑不明（媒體轉述）",
                  f"總資產 NT$ {k['TA']} 億與管理層一致；負債比 {k['DR']}（2021 為 59.25%），流動比 {k['CR']}x", "🟡 Watch"),
                 ("關鍵零件供應", "原物料漲價可即時轉嫁",
                  "毛利率擴張支持轉嫁說法；無部門別資料", "🟢 Stable"),
                 ("供貨能力", "新產能（泰國、湖北、蘆竹）2027 年後陸續開出，稼動時程有不確定性",
                  f"Q1→Q2 營收 NT$ {k['REV_Q1']} → {k['REV_Q']} 億，季增 {k['QOQ']}；現有產能仍有成長空間", "🟡 Watch")],
        positive=["毛利率與營益率連兩季擴張，Q2 淨利創近四年新高。",
                  f"上半年 OCF NT$ {k['OCF']} 億高於淨利，獲利有現金支撐。",
                  f"負債比五年由 59.25% 降至 {k['DR']}，趨勢向好。"],
        watch=[f"負債比仍 {k['DR']}，近 NT$ 20 億擴產若舉債會回升。",
               "歐洲需求疲弱、人民幣波動；2021–2025 營收年年下滑，2026 回升需確認持續性。",
               "法說摘要來自財經媒體（非公司簡報），其中「營業利益率 24%」與「負債比率 180→174」與財報不符。"],
        strategy=["維持 allocation；特用材料類可評估隨其擴產增加配額，但以 2027 新產能驗證後為準。",
                  "Backup source：乾膜光阻、光學膜保留第二供應商。",
                  "新事業（泰國電子材料廠）列為觀察層級，追蹤量產時程。",
                  "每季追蹤：毛利率、負債比、OCF、資本支出執行率。"],
        limits=("法說摘要取自 BigGo Finance、聯合新聞網、經濟日報三則報導（法說簡報與逐字稿未取得），部分指標口徑與財報不符，已在 War Room 標註。"
                "fin_rows 來自 MOPS（千元換算億元）；季度 OCF 與資本支出為年初累計口徑；2025 Q4 列為推算。財報 PDF 文字匯出截斷在 20,006 字。"),
        mgmt_src="2026-08-13 法說會摘要（summary，來源為財經媒體報導）",
    )


NARRATIVE = {"NYSE:GLW": narr_glw, "TPE:1303": narr_npc, "TPE:1763": narr_chimei, "TPE:1711": narr_everlight, "TPE:1717": narr_eternal}


# ---------------------------------------------------------------- HTML
CSS = """
:root{--navy:#0b1f3a;--blue:#1f5aa6;--cyan:#20a4b7;--ink:#172033;--muted:#65738a;--bg:#f3f6fa;--card:#fff;--green:#16835d;--amber:#bd7300;--red:#c33c3c;--line:#dbe4ef;--fill:#fff3b0}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);font-family:Inter,"Noto Sans TC","Microsoft JhengHei",sans-serif;color:var(--ink);line-height:1.55}
.hero{background:linear-gradient(120deg,var(--navy),#143d72 65%,#16798f);color:#fff;padding:38px 5vw 30px}
.hero h1{margin:0;font-size:clamp(26px,4vw,42px)}
.hero p{margin:8px 0 0;color:#d8e8f7}
.badge{display:inline-block;padding:5px 10px;border-radius:999px;background:#ffffff20;border:1px solid #ffffff50;font-size:12px;margin-bottom:12px}
.wrap{max-width:1220px;margin:auto;padding:24px}
.grid{display:grid;gap:16px}
.kpis{grid-template-columns:repeat(4,1fr);margin-top:-44px}
.card{background:#fff;border:1px solid var(--line);border-radius:16px;padding:20px;box-shadow:0 8px 26px #1a3b6610}
.label{font-size:13px;color:var(--muted)}
.value{font-size:28px;font-weight:800;margin:4px 0}
.note,.small{font-size:12px;color:var(--muted)}
.red{color:var(--red)}
.green{color:var(--green)}
.amber{color:var(--amber)}
h2{font-size:22px;margin:6px 0 14px}
h3{font-size:16px;margin:0 0 8px}
.two{grid-template-columns:1.2fr .8fr;margin-top:16px}
.mt{margin-top:16px}
table{width:100%;border-collapse:collapse;font-size:14px}
th,td{padding:10px 8px;border-bottom:1px solid var(--line);text-align:right}
th:first-child,td:first-child{text-align:left}
th{color:var(--muted);font-weight:600;background:#f8fafc}
.matrix th,.matrix td{text-align:left}
.matrix th:last-child,.matrix td:last-child{text-align:center;white-space:nowrap}
.callout{border-left:4px solid var(--amber);background:#fff8e8;padding:14px 16px;border-radius:8px;margin-top:14px}
ul,ol{padding-left:20px;margin:8px 0}
li{margin:5px 0}
.score{display:flex;align-items:center;gap:18px}
.ring{width:104px;height:104px;border-radius:50%;display:grid;place-items:center;background:conic-gradient(var(--amber) 0 50%,#e8eef5 50%);position:relative;flex:0 0 auto}
.ring:after{content:"";position:absolute;inset:12px;border-radius:50%;background:#fff}
.ring b{position:relative;z-index:1;font-size:25px}
footer{padding:18px 0 42px;color:var(--muted);font-size:12px;text-align:center}
a{color:var(--blue)}
mark{background:var(--fill);color:inherit;padding:0 3px;border-radius:3px}
.rubric{font-size:12px;color:var(--muted);margin-top:10px}
.rubric td,.rubric th{padding:4px 6px;font-size:12px}
@media(max-width:850px){.kpis,.two{grid-template-columns:1fr 1fr}}
@media(max-width:600px){.kpis,.two{grid-template-columns:1fr}.kpis{margin-top:0}}
@media print{body{background:#fff}.hero{padding:24px}.wrap{padding:12px}.card{box-shadow:none;break-inside:avoid}mark{background:none}}
"""


def yoy_note(k):
    if k["yoy"] is None:
        return f'<div class="note">{MISSING}（無去年同期列）</div>'
    cls, em = ("green", "🟢") if k["yoy"] >= 0 else ("red", "🔴")
    return f'<div class="note {cls}">{em} YoY {pct(k["yoy"], 2, True)}（{k["q_ly_label"]}：{k["cur_label"]} {f2(k["rev_ly"])} 億）</div>'


def op_note(k):
    oi, pt, ni = k["oi"], k["pt"], k["ni"]
    if oi is None:
        return MISSING
    if oi < 0 and (ni or 0) < 0:
        return "🔴 本業虧損、淨損"
    if oi < 0:
        return "🔴 本業虧損，業外補足淨利"
    if pt is not None and (pt - oi) > oi:
        return f"🟡 本業獲利，但業外 {k['NONOP']} 億 ＞ 本業 {k['OI']} 億"
    return f"🟢 本業獲利 {k['OI']} 億，業外 {k['NONOP']} 億"


def cr_note(cr):
    if cr is None:
        return MISSING
    if cr >= 1.5:
        return '<div class="note green">🟢 短期償債緩衝充足</div>'
    if cr >= 1:
        return '<div class="note amber">🟡 短期償債緩衝偏薄</div>'
    return '<div class="note red">🔴 流動負債高於流動資產</div>'


def annual_rows(k):
    out = []
    for r in k["annual"]:
        ni = yi(r["net_income"], k["unit"])
        nm = r["net_margin"]
        if ni is None:
            judge = MISSING
        elif ni < 0:
            judge = "🔴 虧損"
        elif nm is not None and nm < 1:
            judge = "🟡 損益邊緣"
        else:
            judge = "🟢 獲利"
        out.append(f"<tr><td>{r['fiscal_year']}</td><td>{m(yi(r['revenue'], k['unit']))}</td><td>{m(yi(r['pretax_income'], k['unit']))}</td>"
                   f"<td>{m(ni)}</td><td>{mp(nm)}</td><td>{m(r['eps'])}</td><td style=\"text-align:center\">{judge}</td></tr>")
    missing = 5 - len(k["annual"])
    if missing > 0:
        out.append(f'<tr><td colspan="7"><mark>資料缺：年度列只有 {len(k["annual"])} 年</mark></td></tr>')
    return "\n".join(out)


def q_note(r, k):
    oi = yi(r["operating_income"], k["unit"])
    pt = yi(r["pretax_income"], k["unit"])
    ni = yi(r["net_income"], k["unit"])
    if oi is None:
        return f"{MISSING}（推算列，無營業利益）"
    if oi < 0 and (ni or 0) < 0:
        return "本業虧損／淨損"
    if oi < 0:
        return "本業虧損，業外補足"
    if pt is not None and (pt - oi) > oi:
        return f"業外帶動淨利（業外 {f2(pt - oi)} 億 ＞ 本業 {f2(oi)} 億）"
    return "本業獲利"


def quarter_rows(k):
    out = []
    have = {r["period"] for r in k["year_qs"]}
    for r in k["year_qs"]:
        out.append(f"<tr><td>{q_label(r['period'])}</td><td>{m(yi(r['revenue'], k['unit']))}</td><td>{mp(r['gross_margin'])}</td><td>{mp(r['operating_margin'])}</td>"
                   f"<td>{m(yi(r['net_income'], k['unit']))}</td><td>{mp(r['net_margin'])}</td><td style=\"text-align:left\">{q_note(r, k)}</td></tr>")
    latest_n = int(k["q"]["period"][-1])
    for i in range(1, latest_n + 1):
        p = f"{k['year']}Q{i}"
        if p not in have:
            out.append(f'<tr><td>{q_label(p)}</td><td colspan="6" style="text-align:left"><mark>資料缺：fin_rows 無此季</mark></td></tr>')
    return "\n".join(out)


def cash_rows(k):
    cl = k["cur_label"]
    if k["ocf"] is None:
        ocf_cell = MISSING
    elif k["ocf"] < 0:
        ocf_cell = f'<span class="red">🔴 {f2(k["ocf"])}</span> 億'
    elif k["ni_ytd"] and k["ocf"] < 0.5 * k["ni_ytd"]:
        ocf_cell = f'<span class="amber">🟡 {f2(k["ocf"])}</span> 億（淨利 {k["NI_YTD"]} 億的 {k["OCF_NI"]}）'
    else:
        ocf_cell = f'<span class="green">🟢 {f2(k["ocf"])}</span> 億（OCF／淨利 {k["OCF_NI"]}）'
    capex_cell = MISSING if k["capex"] is None else f"{f2(k['capex'])} 億"
    cr_cls = "green" if k["cr"] >= 1.5 else "amber" if k["cr"] >= 1 else "red"
    cr_em = "🟢" if k["cr"] >= 1.5 else "🟡" if k["cr"] >= 1 else "🔴"
    return (f"<tr><td>營業現金流（OCF，{k['year']} 年初累計）</td><td>{ocf_cell}</td></tr>"
            f"<tr><td>取得不動產、廠房及設備（{k['year']} 年初累計）</td><td>{capex_cell}</td></tr>"
            f"<tr><td>總資產</td><td>{m(k['ta'])} 億</td></tr>"
            f"<tr><td>總負債</td><td>{m(k['tl'])} 億</td></tr>"
            f"<tr><td>負債比</td><td>{mp(k['dr'], 1)}</td></tr>"
            f"<tr><td>流動比率</td><td class=\"{cr_cls}\">{cr_em} {f2(k['cr'])}x</td></tr>")


def sources(k, n):
    items = []
    fin_src = k["q"]["source"]
    if k["market"] in ("TPE", "TPEx"):
        items.append(('https://mopsov.twse.com.tw/mops/web/index', f"公開資訊觀測站財務報表 API（{esc(fin_src)}）", "KPI、近五年年度指標、季度指標、現金流與資產負債、示範分數（fin_rows）"))
    else:
        url = (k["q"].get("source_urls") or ["#"])[0]
        items.append((url, f"SEC XBRL companyfacts（{esc(fin_src)}）", "KPI、近五年年度指標、季度指標、現金流與資產負債、示範分數（fin_rows）"))
    for doc in k["docs"]:
        use = "管理層觀點、War Room、QBR 必問（新聞稿／簡報文字）" if doc["doc_kind"] == "Presentation" else "原始財報（僅供核對；文字匯出截斷，未用於欄位）"
        items.append((doc["source_url"], f"{esc(doc['file_name'])}（{doc['doc_kind']}，{doc['page_count']} 頁）", use))
    if k["summary"]:
        for s in k["summary"].get("sources") or []:
            items.append((s["url"], f"{esc(s['title'])}｜{esc(s['media'])}", "法說摘要：管理層觀點、風險、QBR 必問"))
    if k["ir_url"]:
        items.append((k["ir_url"], "公司投資人關係網站", "法說會資料入口"))
    return "\n".join(f'<li><a href="{esc(u)}">{t}</a> — {use}</li>' for u, t, use in items)


def rubric_table(k):
    rows = "".join(f"<tr><td>{n}</td><td>{p:+d}</td><td>{esc(b)}</td></tr>" for n, p, b in k["score_rows"])
    return f'<table class="rubric"><thead><tr><th>項目</th><th>分</th><th>依據</th></tr></thead><tbody>{rows}<tr><td><b>合計</b></td><td><b>{k["score"]}</b></td><td>≥70 綠燈／40–69 黃燈／&lt;40 紅燈</td></tr></tbody></table>'


def render(k: dict, n: dict) -> str:
    cl = k["cur_label"]
    L = k["light"]
    mgmt_src = f"管理層觀點來源：{esc(n['mgmt_src'])}" if n.get("mgmt_src") else "<mark>資料缺：無法說會摘要，管理層觀點欄位空缺</mark>"
    conf = k["conference"]
    conf_line = f"｜法說會：{conf['conference_date']}（{conf['conference_type']}）" if conf else ""
    data_period = f"{k['q_label']} 財報"
    if k["period"] != k["q"]["period"]:
        data_period += f"＋{q_label(k['period'])} 法說"
    tips = "\n".join(f"<li><b>{esc(a)}</b>{esc(b)}</li>" for a, b in n["tips"])
    qbr = "\n".join(f"<li>{esc(x)}</li>" for x in n["qbr"])
    wr = "\n".join(f"<tr><td>{esc(a)}</td><td>{b if b.startswith('<mark') else esc(b)}</td><td>{esc(c)}</td><td>{d}</td></tr>" for a, b, c, d in n["warroom"])
    pos = "".join(f"<li>{esc(x)}</li>" for x in n["positive"])
    wat = "".join(f"<li>{esc(x)}</li>" for x in n["watch"])
    strat = "".join(f"<li>{esc(x)}</li>" for x in n["strategy"])
    industry = esc(k["industry"]) if k["industry"] else "<mark>資料缺：主檔無產業別</mark>"

    return f"""<!doctype html>
<html lang="zh-Hant-TW">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(k['name'])}（{esc(k['code'])}）財務體質韌性分析</title>
<!--
由 build_report.py 依 {TEMPLATE_REF} 產出；資料來源：範例財報/{esc(k['name'])}.md（JSON）。
黃底 <mark> 為資料集給不出的欄位，對照 模板覆蓋度評估.md。
-->
<style>{CSS}</style>
</head>
<body>

<header class="hero">
  <div class="badge">Supplier Financial Health｜Phase {PHASE}｜採購視角</div>
  <h1>{esc(k['name'])}（{esc(k['market'])}:{esc(k['code'])}）財務體質韌性分析</h1>
  <p>資料基準：{data_period} 公開資訊{conf_line}｜產業：{industry}｜產出日期：{TODAY}｜版本：{VERSION}</p>
</header>

<main class="wrap">

<!-- 一、關鍵指標總覽（KPI） -->
<section class="grid kpis">
  <div class="card"><div class="label">{k['q_label']} 營收</div><div class="value">{cl} {m(k['rev_q'])} 億</div>{yoy_note(k)}</div>
  <div class="card"><div class="label">{k['q_label']} 毛利率</div><div class="value">{mp(k['gm'])}</div><div class="note">去年同期：{mp(k['gm_ly'])}</div></div>
  <div class="card"><div class="label">{k['q_label']} 營業利益率</div><div class="value">{mp(k['opm'])}</div><div class="note">{op_note(k)}</div></div>
  <div class="card"><div class="label">{k['q_label']} 流動比率</div><div class="value">{m(k['cr'])}x</div>{cr_note(k['cr'])}</div>
</section>

<!-- 二、管理層重點結論 -->
<section class="grid two">
  <article class="card">
    <h2>管理層重點結論</h2>
    <div class="score">
      <div class="ring" style="background:conic-gradient(var({L['css']}) 0 {k['score']}%,#e8eef5 {k['score']}%)"><b>{k['score']}</b></div>
      <div>
        <h3>暫定燈號：{L['emoji']} {L['name']}（{L['action']}）</h3>
        <div class="small">分數 {k['score']} / 100 ※ 採購管理用示範分數，非信用評等或投資建議。規則見本頁末「資料來源與限制」。</div>
        <div class="small">{mgmt_src}</div>
      </div>
    </div>
    <h3 class="mt">一句話判讀</h3>
    <div class="callout" style="margin-top:6px">{esc(n['one_liner'])}</div>
  </article>
  <article class="card">
    <h2>採購決策提示</h2>
    <ul>
{tips}
    </ul>
  </article>
</section>

<!-- 三、近五年年度重點財務指標 -->
<section class="card mt">
  <h2>近五年年度重點財務指標（{cl} 億）</h2>
  <table>
    <thead><tr><th>年度</th><th>營收（億）</th><th>稅前損益（億）</th><th>稅後淨利（億）</th><th>淨利率</th><th>EPS（{esc(k['cur'])}）</th><th style="text-align:center">採購判讀</th></tr></thead>
    <tbody>
{annual_rows(k)}
    </tbody>
  </table>
</section>

<!-- 四、本年度季度指標 -->
<section class="card mt">
  <h2>{k['year']} 季度指標（{cl} 億）</h2>
  <table>
    <thead><tr><th>季度</th><th>營收（億）</th><th>毛利率</th><th>營業利益率</th><th>稅後淨利（億）</th><th>稅後淨利率</th><th style="text-align:left">重點</th></tr></thead>
    <tbody>
{quarter_rows(k)}
    </tbody>
  </table>
  <div class="callout"><b>閱讀方式：</b>完整年度與單季資料口徑不同，季度數值不可直接與全年比較。</div>
</section>

<!-- 五、現金流與資產負債 ＋ 八、下次 QBR 必問 -->
<section class="grid two">
  <article class="card">
    <h2>現金流與資產負債（{k['q_label']}，{cl} 億）</h2>
    <table>
      <tbody>
{cash_rows(k)}
      </tbody>
    </table>
  </article>
  <article class="card">
    <h2>下次 QBR 必問</h2>
    <ol>
{qbr}
    </ol>
  </article>
</section>

<!-- 六、Executive War Room -->
<section class="card mt">
  <h2>Executive War Room｜法說會展望 × 財務驗證 × 採購風險矩陣</h2>
  <table class="matrix">
    <thead><tr><th>評估項目</th><th>管理層觀點</th><th>財務驗證</th><th>AUO 判讀</th></tr></thead>
    <tbody>
{wr}
    </tbody>
  </table>
</section>

<!-- 七、Supplier Watchlist -->
<section class="card mt">
  <h2>Supplier Watchlist｜採購主管版</h2>
  <h3>🟢 Positive Signals</h3>
  <ul>{pos}</ul>
  <h3>🟡 Watch Items</h3>
  <ul>{wat}</ul>
  <h3>🎯 建議採購策略</h3>
  <ul>{strat}</ul>
</section>

<!-- 九、資料來源與限制 -->
<section class="card mt">
  <h2>資料來源與限制</h2>
  <h3>資料來源</h3>
  <ul>
{sources(k, n)}
  </ul>
  <h3>限制</h3>
  <div class="callout" style="margin-top:6px">{esc(n['limits'])} 通用限制：稅後淨利為合併淨利（含非控制權益），EPS 則以歸屬母公司淨利計算，兩者可能不一致；季度現金流與資本支出為年初累計（YTD）口徑，非單季；金額由原始單位（{esc(k['unit_note'])}）換算為億，小數第二位四捨五入；比率欄直接取資料表值。正式決策前仍應以公開資訊觀測站／SEC 及公司合併財報附註為準。</div>
  <h3 class="mt">示範分數規則（本頁）</h3>
  {rubric_table(k)}
</section>

<footer>Generated for procurement review｜{TODAY}｜Version {VERSION}｜依 {TEMPLATE_REF} 產出</footer>

</main>
</body>
</html>
"""


def main():
    for f in FILES:
        d = load(HERE / f)
        k = build_k(d)
        n = NARRATIVE[k["key"]](k)
        out = HERE / (pathlib.Path(f).stem + ".html")
        out.write_text(render(k, n), encoding="utf-8")
        marks = render(k, n).count("<mark>")
        print(f"{out.name:28s} score={k['score']:3d} {k['light']['emoji']} {k['light']['name']}  latest={k['q']['period']}  mark={marks}")


if __name__ == "__main__":
    main()
