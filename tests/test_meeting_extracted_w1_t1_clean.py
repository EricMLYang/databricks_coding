"""meeting_extracted_w1_t1_clean 的測試：[c02]～[c05] 純 Python 規則，[c06] Spark 接線。

測試資料全是虛構（假名、example 網域），格式照 PM_Head 去識別化樣本：md `**From:**` 標頭、
純文字 `From:` 多行標頭、Appointment、ITEM 紀要（型號行、m月d日）、Word 表格攤平後的短行。
"""

from datetime import date, datetime

import pytest
from nbload import load_cells

NB = "jobs/meeting_record/meeting_extracted_w1_t1_clean/notebook.ipynb"
NB_MAIL = "jobs/meeting_record/meeting_extracted_w1_t1_mail/notebook.ipynb"
NB_002 = "jobs/meeting_record/meeting_extracted_migration/002_meeting_neutral_tables.ipynb"


@pytest.fixture(scope="module")
def mod():
    return load_cells(NB, ["c02", "c03", "c04", "c05", "c06"], name="w1t1b")


@pytest.fixture(scope="module")
def mail_mod():
    return load_cells(NB_MAIL, ["c02", "c03", "c04", "c05", "c06"], name="w1t1_for_clean")


@pytest.fixture(scope="module")
def specs():
    return load_cells(NB_002, ["c02", "c03", "c04"], name="mig002_for_clean")


# 參與者（第一支會產出的形狀）；人名全部虛構
PARTS = [
    {
        "segment_no": 0,
        "token": "P01",
        "role": "forwarder",
        "kind": "person",
        "display_name_raw": "0300001/王小美/amywang/DTDDB0",
        "name_zh": "王小美",
        "name_en": None,
        "email": None,
        "email_domain": None,
        "emp_id": "0300001",
        "account": "amywang",
    },
    {
        "segment_no": 1,
        "token": "P01",
        "role": "from",
        "kind": "person",
        "display_name_raw": "Amy Wang 王小美",
        "name_zh": "王小美",
        "name_en": "Amy Wang",
        "email": "amy.wang@auo.com",
        "email_domain": "auo.com",
        "emp_id": None,
        "account": None,
    },
    {
        "segment_no": 1,
        "token": "P02",
        "role": "to",
        "kind": "person",
        "display_name_raw": "CustA, Quinn",
        "name_zh": None,
        "name_en": "Quinn CustA",
        "email": "quinn.custa@acer.example",
        "email_domain": "acer.example",
        "emp_id": None,
        "account": None,
    },
    {
        "segment_no": 1,
        "token": "G01",
        "role": "cc",
        "kind": "group",
        "display_name_raw": "MNT PM",
        "name_zh": None,
        "name_en": "MNT PM",
        "email": "mnt_pm@acer.example",
        "email_domain": "acer.example",
        "emp_id": None,
        "account": None,
    },
    {
        "segment_no": 2,
        "token": "P02",
        "role": "from",
        "kind": "person",
        "display_name_raw": "CustA, Quinn",
        "name_zh": None,
        "name_en": "Quinn CustA",
        "email": "quinn.custa@acer.example",
        "email_domain": "acer.example",
        "emp_id": None,
        "account": None,
    },
    {
        "segment_no": 2,
        "token": "P03",
        "role": "to",
        "kind": "person",
        "display_name_raw": "Will Chen 陳小威",
        "name_zh": "陳小威",
        "name_en": "Will Chen",
        "email": None,
        "email_domain": None,
        "emp_id": None,
        "account": None,
    },
]

MD_THREAD = (
    "FYI, see below.\n\n"
    "**From:** Amy Wang 王小美 <amy.wang@auo.com>\n**Sent:** Wednesday, August 26, 2026 10:16 AM\n"
    "**To:** CustA, Quinn <quinn.custa@acer.example>\n**Cc:** MNT PM <mnt_pm@acer.example>\n"
    "**Subject:** RE: AUO Monthly Meeting\n\n"
    "Hi Quinn,\nSummary of today's meeting with Acer:\n"
    '1. 27" QHD 100Hz M270DAN07.D will keep 2ch LVDS; Acer asks for 4ch option by Q4.\n'
    '2. M270QAN06.A 27" UHD 100Hz sample plan: TCON sample in August, G6 outline unchanged.\n'
    "3. Acer confirmed the monthly allocation will stay at 30K for September.\n"
    "Regards,\nAmy Wang\n\n"
    "-----Original Appointment-----\n"
    "**From:** CustA, Quinn <quinn.custa@acer.example>\n**Sent:** Friday, July 17, 2026 9:41 AM\n"
    "**To:** Will Chen 陳小威\n**Subject:** AUO Monthly Meeting\n"
    "**When:** 2026年8月13日星期四 下午 03:30-下午 05:00 (UTC+08:00) 台北。\n"
    "**Where:** 8B09 (Taipei)\n\n"
    "Dear all, please reserve your time. 陳小威 will join. Thanks, Quinn CustA\n"
)

MINUTES = (
    "Dear Sirs,\n\nTCL Account meeting minutes如下\n\n\nITEM\n\n\n9月3日\n\n\n\n"
    "T430QVN04.5\n91.43T14.5T0\n7A/S02\n(IC:NT60816)\n\n\n"
    "* ITO 新光罩(穿透率4.5 & 色域提升) Y26 新機型, 新光罩穿透率未達預期, "
    "故暫不推此新光罩 (海信改68pin)\n"
    "* 量產出貨VLRR不良目前820 ppm(TCL要求500 dppm以下)，Fab持續改善particle & leakage攔檢。\n"
    "Allocation : 1月31K, 2月18K, 3月42K, 4月33K, 5月44K, 6月29K, 7月40.2K, 8月47K, "
    "9月27K, 10月12K\n"
    "限簽80K + 60K+120K+90K+130K+250K(結至8月出貨餘97K)\n\n\n\n"
    "T550QVN10.F\n91.55T45.FT0\n55.55T45.C35\n8A/M11\n(IC:RM97169, POL:BMC)A4\n\n\n"
    "* LC Bubble: TCL已同意量產7/E上改善條件, (對內:7/E未上, 預計8/B上改善對策)\n"
    "* Flash IC : TCL 只同意供應商A/供應商B, 不同意供應商C\n"
    "* JI S11轉廠 AUO RA 驗證: 8/7光學, 8/30 T500；JI S11驗證樣品需求 2 + 6片: "
    "6片預計9/7入庫, 下周二出貨\n"
    "Allocation : 1月0K, 3月24K, 4月27K, 5月18.4K, 6月25K, 7月36.1K, 8月47.5K, "
    "9月33K, 10月22K(對外壓35K)\n"
    "* 8/27 TCL提供終簽\n"
)

ALIASES = [
    ("Acer", "acer"),
    ("宏碁", "acer"),
    ("TCL", "tcl"),
    ("Samsung VD", "samsung_vd"),
    ("VD", "samsung_vd"),
    ("Samsung", "samsung"),
    ("三星", "samsung"),
    ("HP", "hp"),
]
# s_semantic_entity.app_default 在表裡是 ARRAY<STRING>（001 用 | 切）；函式也接受 "TV|MNT" 字串
APP_DEFAULTS = {
    "acer": ["NB", "MNT"], "tcl": ["TV"], "samsung_vd": "TV|MNT", "hp": "NB|MNT", "lenovo": "NB",
}
DUP_DDL = (
    "pk_seq bigint, segment_no int, sub_no int, content_hash string, "
    "create_date timestamp, dup_of string"
)


def _mail(**kw):
    base = {
        "pk_seq": 1,
        "drupal_id": "9",
        "drupal_link": None,
        "unit": "bu",
        "create_date": datetime(2026, 10, 6, 8, 16),
        "mail_date": date(2026, 10, 6),
        "mail_datetime": datetime(2026, 10, 6, 16, 5),
        "subject_raw": "FW: RE: AUO Monthly Meeting",
        "subject_clean": "AUO Monthly Meeting",
        "forwarder_token": "P01",
        "forwarder_dept_code": "DTDDB0",
        "meeting_when": datetime(2026, 8, 13, 15, 30),
        "meeting_where": "8B09 (Taipei)",
        "body_source_field": "mail_body_md",
        "body_conflict": False,
        "body_display": MD_THREAD,
        "is_fw": True,
        "attach_count": 0,
    }
    base.update(kw)
    return base


# ---------- [c03] 共用函式與第一支一致 ----------
def test_shared_functions_match_mail_notebook(mod, mail_mod):
    for text in (MD_THREAD, MINUTES, "From: a\nSent: Monday, March 2, 2026 9:00 AM\nSubject: x\n"):
        assert mod.find_header_blocks(text) == mail_mod.find_header_blocks(text)
    assert mod.parse_datetime("Wednesday, August 26, 2026 10:16 AM") == mail_mod.parse_datetime(
        "Wednesday, August 26, 2026 10:16 AM"
    )
    assert mod.normalize_text("Ａb c，d") == mail_mod.normalize_text("Ａb c，d") == "abcd"


# ---------- [c04] 分段 ----------
def test_split_thread_with_separator_and_offsets(mod):
    segs = mod.split_segments(MD_THREAD, date(2026, 10, 6))
    assert [s["segment_no"] for s in segs] == [0, 1, 2]
    assert [s["kind"] for s in segs] == ["thread"] * 3
    assert MD_THREAD[segs[0]["start"] : segs[0]["end"]] == "FYI, see below.\n\n"
    assert MD_THREAD[segs[1]["start"] :].startswith("**From:** Amy Wang")
    assert MD_THREAD[segs[2]["start"] :].startswith(
        "-----Original Appointment-----"
    )  # 分隔線併入下一段
    assert segs[1]["end"] == segs[2]["start"] and segs[2]["end"] == len(MD_THREAD)
    assert (segs[1]["segment_date"], segs[1]["date_inferred"]) == (date(2026, 8, 26), False)
    assert (segs[2]["segment_date"], segs[2]["date_inferred"]) == (date(2026, 7, 17), False)
    assert segs[0]["segment_date"] == date(2026, 10, 6) and segs[0]["date_inferred"]


def test_split_minutes_by_model_lines_with_item_date(mod):
    segs = mod.split_segments(MINUTES, date(2026, 10, 6))
    assert [s["segment_no"] for s in segs] == [0, 1, 2]
    assert [s["kind"] for s in segs] == ["minutes"] * 3
    assert MINUTES[segs[1]["start"] :].startswith("T430QVN04.5")
    assert MINUTES[segs[2]["start"] :].startswith("T550QVN10.F")
    assert segs[1]["segment_date"] == date(2026, 9, 3) and not segs[1]["date_inferred"]
    assert segs[2]["segment_date"] == date(2026, 9, 3)
    assert (
        segs[0]["segment_date"] == date(2026, 10, 6) and segs[0]["date_inferred"]
    )  # ITEM 在段 0 內，不算段 0 前面的日期
    # 跨年：mail_date 1 月、紀要 12 月 → 去年
    assert mod.item_dates("ITEM\n12月20日\nT430QVN04.5", date(2027, 1, 5)) == [
        (0, date(2026, 12, 20))
    ]
    assert mod.item_dates("ITEM\n2026/9/3\nx", date(2026, 10, 6)) == [(0, date(2026, 9, 3))]


def test_split_whole_when_nothing_to_cut(mod):
    segs = mod.split_segments("Hi all, attached is the file. Thanks.", date(2026, 10, 6))
    assert len(segs) == 1 and segs[0]["kind"] == "whole" and segs[0]["segment_no"] == 0
    assert segs[0]["date_inferred"] and segs[0]["segment_date"] == date(2026, 10, 6)
    assert mod.split_segments("   \n", date(2026, 10, 6)) == []


# ---------- [c05] token 化 ----------
def test_token_map_and_apply(mod):
    tm = mod.build_token_map(PARTS)
    keys = dict(tm)
    assert (
        keys["amy.wang@auo.com"] == "<P01>"
        and keys["Wang, Amy"] == "<P01>"
        and keys["王小美"] == "<P01>"
    )
    assert keys["CustA, Quinn"] == "<P02>" and keys["Quinn CustA"] == "<P02>"
    assert keys["mnt_pm@acer.example"] == "<G01>" and "MNT PM" not in keys  # 群組只換 email
    assert keys["amywang"] == "<P01>" and keys["0300001"] == ""  # 轉寄人帳號 → token、工號刪
    assert [k for k, _ in tm] == sorted(keys, key=lambda k: (-len(k), k))  # 長的在前
    rx, lookup = mod.compile_token_regex(tm)
    out = mod.apply_tokens(
        "Amy Wang 王小美 <amy.wang@auo.com> met CustA, Quinn; cc MNT PM <MNT_PM@acer.example>. "
        "WILL CHEN said yes; we will check it. 陳小威 agreed. emp 0300001 / amywang / 10300001x",
        rx,
        lookup,
    )
    assert "<P01> <<P01>> met <P02>; cc MNT PM <<G01>>." in out  # 原字串「英名 中文名」整串一次換掉
    assert (
        "<P03> said yes; we will check it. <P03> agreed." in out
    )  # 多字不分大小寫；單字 will 不動
    assert "emp  / <P01> / 10300001x" in out  # 工號刪；夾在數字裡的不動
    assert mod.apply_tokens("nothing", None, {}) == "nothing"


def test_rewrite_header(mod):
    blk = mod.find_header_blocks(MD_THREAD)[1]
    rx, lookup = mod.compile_token_regex(mod.build_token_map(PARTS))
    assert (
        mod.rewrite_header(blk, "P02", rx, lookup)
        == "<P02>:\nSent: 2026-07-17 09:41\nSubject: AUO Monthly Meeting"
    )
    # 沒有 from token → 用 token 化後的 From 值
    assert mod.rewrite_header(blk, None, rx, lookup).startswith("<P02> <<P02>>:")
    assert (
        mod.rewrite_header({"fields": {"From": "x", "Subject": "s"}}, None, None, {})
        == "x:\nSubject: s"
    )


def test_flatten_short_lines(mod):
    table = "\n\n".join(
        [
            "MP",
            "Remark",
            "AHVA",
            '27" AHVA 4K 100Hz OC',
            "M270QAN06.A",
            "27",
            "UHD",
            "100Hz",
            "NA",
            "4ch LVDS",
        ]
    )
    text = (
        "Intro line that is definitely longer than twenty chars.\n\n"
        + table
        + "\n\nClosing line that is also longer than twenty chars."
    )
    out = mod.flatten_short_lines(text)
    assert (
        'MP | Remark | AHVA | 27" AHVA 4K 100Hz OC | M270QAN06.A | 27 | UHD | 100Hz | NA | 4ch LVDS'
        in out
    )
    assert out.startswith("Intro line") and out.endswith("twenty chars.")
    short = "a\n\nb\n\nc\n\nd"
    assert mod.flatten_short_lines(short) == short  # < 8 行不動、空行保留


def test_classify(mod):
    blk = {"fields": {"From": "x", "Sent": "y", "When": "z"}}
    assert mod.classify("thread", "ITEM\n...", 100, None, 0) == "inline_minutes"
    assert (
        mod.classify("thread", "M270QAN06.A M270DAN07.D M270QAN11.5", 50, None, 0)
        == "inline_minutes"
    )
    assert mod.classify("minutes", "meeting minutes " + "x" * 800, 816, None, 0) == "inline_minutes"
    assert mod.classify("thread", "x" * 300, 300, {"fields": {"From": "x"}}, 0) == "thread_reply"
    assert mod.classify("thread", "please reserve", 14, blk, 0) == "appointment"
    assert (
        mod.classify("thread", "see attached file", 17, {"fields": {"From": "x"}}, 0)
        == "attachment_only"
    )
    assert mod.classify("whole", "x" * 200, 200, None, 2) == "attachment_only"
    assert mod.classify("whole", "hi", 2, None, 0) == "noise"
    assert (
        mod.classify("thread", "x" * 200, 200, {"fields": {"From": "x"}}, 0) == "thread_reply"
    )  # D18
    assert mod.classify("minutes", "T430QVN04.5 " + "x" * 200, 212, None, 0) == "inline_minutes"
    assert mod.classify("whole", "x" * 200, 200, None, 0) == "noise"


def test_hints(mod):
    arx, alookup = mod.compile_alias_regex(ALIASES)
    assert mod.customer_hint("Acer asks; acer again; HP once", None, arx, alookup) == "acer"
    assert (
        mod.customer_hint('Samsung VD wants 55"', None, arx, alookup) == "samsung_vd"
    )  # 長別名先吃
    assert mod.customer_hint("Samsung said", None, arx, alookup) == "samsung"
    assert mod.customer_hint("Acer and TCL", None, arx, alookup) is None  # 平手
    assert mod.customer_hint("Acer and TCL", "TCL weekly", arx, alookup) == "tcl"  # 主旨 ×3
    assert mod.customer_hint("chip hpx DVD", None, arx, alookup) is None  # 字邊界
    assert mod.customer_hint("x", None, None, {}) is None
    assert mod.app_hint("M270QAN06.A and T430QVN04.5 and M270DAN07.D", None, None, {}) == "MNT"
    assert mod.app_hint("M270QAN06.A and T430QVN04.5", None, None, {}) is None  # 平手
    assert mod.app_hint('27" QHD 100Hz panel', None, None, {}) == "MNT"
    assert mod.app_hint('55" 4K 60Hz', None, None, {}) == "TV"
    assert mod.app_hint("no model", "MNT Monthly Meeting", None, {}) == "MNT"
    assert mod.app_hint("no model", "TV and MNT", None, {}) is None
    assert mod.app_hint("no model", None, "tcl", APP_DEFAULTS) == "TV"
    assert mod.app_hint("no model", None, "acer", APP_DEFAULTS) is None  # 多 app 預設不用（array）
    assert mod.app_hint("no model", None, "hp", APP_DEFAULTS) is None  # 多 app 預設不用（字串）
    assert mod.app_hint("no model", None, "lenovo", APP_DEFAULTS) == "NB"
    assert mod.app_hint("no model", None, "nobody", APP_DEFAULTS) is None


def test_build_segment_rows_thread(mod):
    rows = mod.build_segment_rows(_mail(), PARTS, ALIASES, APP_DEFAULTS, "0.1")
    assert [r["segment_no"] for r in rows] == [1, 2]  # 段 0 太短不留
    r1, r2 = rows
    assert r1["clean_text"].startswith(
        "<P01>:\nSent: 2026-08-26 10:16\nSubject: RE: AUO Monthly Meeting\n\nHi Quinn,"
    )
    assert "amy" not in r1["clean_text"].lower() and "王小美" not in r1["clean_text"]
    assert "**To:**" not in r1["clean_text"] and "**Cc:**" not in r1["clean_text"]
    assert r1["clean_text"].rstrip().endswith("Regards,\n<P01>")
    assert (
        r1["content_type"] == "thread_reply"
        and r1["customer_hint"] == "acer"
        and r1["app_hint"] == "MNT"
    )
    assert r1["parties"] == ["acer.example", "auo.com"]
    assert (r1["segment_date"], r1["date_inferred"]) == (date(2026, 8, 26), False)
    assert r1["display_start"] < r1["display_end"] and _mail()["body_display"][
        r1["display_start"] : r1["display_end"]
    ].startswith("**From:** Amy")
    assert r1["content_hash"] and r1["dup_of"] is None and r1["_residual"] == 0
    assert r1["raw_len"] == r1["display_end"] - r1["display_start"] and r1["clean_len"] == len(
        r1["clean_text"]
    )
    assert r2["clean_text"].startswith(
        "<P02>:\nSent: 2026-07-17 09:41\nSubject: AUO Monthly Meeting\n\nDear all"
    )
    assert (
        "When" not in r2["clean_text"]
        and "Where" not in r2["clean_text"]
        and "Original Appointment" not in r2["clean_text"]
    )
    assert "<P03> will join. Thanks, <P02>" in r2["clean_text"]
    assert (
        r2["content_type"] == "appointment" and r2["content_hash"] is None and r2["_residual"] == 0
    )
    assert r2["meeting_when"] == datetime(2026, 8, 13, 15, 30) and r2["forwarder_token"] == "P01"
    assert r2["sub_no"] == 0 and r2["cleaner_version"] == "0.1" and r2["cleaned_at"] is None


def test_junk_table_rows_and_hash_neutralizes_tokens(mod):
    banner = (
        "|  |  |\n| --- | --- |\n|  | |\n| https://www.auo.example/upload/media/e_news.png | |\n"
        "| [image] | ![x](cid:abc) |\n"
    )
    real = "| Model | Qty |\n| --- | --- |\n| M270QAN06.A | 30K |\n"
    kept = "Hello\n| Model | Qty |\n| M270QAN06.A | 30K |\n"
    assert mod.drop_junk_table_rows(banner + "Hello\n" + real) == kept
    # 橫幅當段 0：清洗後太短 → 不留
    rows = mod.build_segment_rows(
        _mail(pk_seq=5, body_display=banner + "\n" + MD_THREAD), PARTS, ALIASES, APP_DEFAULTS, "0.1"
    )
    assert [r["segment_no"] for r in rows] == [1, 2]
    # Databricks 實跑看到的段 0：簽名檔塞在表格列，左格橫幅網址、右格「英文名 中文名 職稱 email」
    sig = (
        "| https://www.auo.example/upload/media/auo/e_news/outlook/auooutlook130.jpg | "
        "**Amy 王小美**   Sales Director,  Mobile PC Display BU  **AUO Corporation,**  "
        "E amy.wang@auo.com  AUO.com |\n"
    )
    mail6 = _mail(pk_seq=6, body_display=sig + "\n" + MD_THREAD)
    rows = mod.build_segment_rows(mail6, PARTS, ALIASES, APP_DEFAULTS, "0.1")
    # 網址縮成 [url]、Amy <P01> → <P01> 後 < 150 字 → 段 0 不留
    assert [r["segment_no"] for r in rows] == [1, 2]
    assert mod.strip_urls("see https://a.example/x?y=1) and ![b](https://a.example/i.png)|z") == (
        "see [url]) and [image]|z"
    )
    # 名字只在緊接自己 token 時才換；單獨出現或接別人的 token 不動
    pats = mod.first_name_patterns(PARTS)
    txt = "Amy <P01> and Amy <P02> and Amy alone and Quinn <P02>"
    for frx, tok in pats:
        txt = frx.sub(tok, txt)
    assert txt == "<P01> and Amy <P02> and Amy alone and <P02>"
    # 同一段在另一封信裡 token 編號不同 → hash 相同
    a = "<P02>:\nSent: 2026-06-02 10:14\nSubject: weekly\n\n<P05> agreed with <G01>. " * 5
    b = a.replace("<P02>", "<P11>").replace("<P05>", "<P03>").replace("<G01>", "<G02>")
    assert mod.content_hash_of(a) == mod.content_hash_of(b)
    assert mod.content_hash_of(a) != mod.content_hash_of(a.replace("agreed", "disagreed"))


def test_build_segment_rows_minutes_and_residual(mod):
    parts = [PARTS[0]]
    rows = mod.build_segment_rows(
        _mail(
            pk_seq=2,
            body_display=MINUTES,
            body_source_field="mail_without_fw",
            subject_clean="TCL weekly",
            meeting_when=None,
        ),
        parts,
        ALIASES,
        APP_DEFAULTS,
        "0.1",
    )
    assert [r["segment_no"] for r in rows] == [1, 2]
    assert all(r["content_type"] == "inline_minutes" for r in rows)
    assert all(r["customer_hint"] == "tcl" and r["app_hint"] == "TV" for r in rows)
    assert rows[0]["segment_date"] == date(2026, 9, 3) and not rows[0]["date_inferred"]
    assert (
        "T430QVN04.5 | 91.43T14.5T0 | 7A/S02 | (IC:NT60816)" not in rows[0]["clean_text"]
    )  # 只有 4 短行，不攤
    assert rows[0]["clean_text"].startswith("T430QVN04.5\n91.43T14.5T0")
    assert rows[0]["parties"] == []
    # D20：參與者表沒有的 email → 遮成 [email] 並計 _masked；_residual（姓名殘留）仍 0
    rows = mod.build_segment_rows(
        _mail(pk_seq=3, body_display="Contact someone@nowhere.example for details. " * 5),
        parts,
        ALIASES,
        APP_DEFAULTS,
        "0.1",
    )
    assert rows[0]["_masked"] == 5 and rows[0]["_residual"] == 0
    assert rows[0]["clean_text"].startswith("Contact [email] for details.")
    assert "@" not in rows[0]["clean_text"] and rows[0]["content_type"] == "noise"


# ---------- [c06] Spark ----------
@pytest.fixture(scope="module")
def clean_schema(specs, spark):
    return spark.createDataFrame(
        [], specs.schema_ddl(specs.TABLES["s_meeting_record_clean_bu"])
    ).schema


@pytest.fixture(scope="module")
def mail_schema(specs, spark):
    return spark.createDataFrame(
        [], specs.schema_ddl(specs.TABLES["s_meeting_record_mail_bu"])
    ).schema


@pytest.fixture(scope="module")
def part_schema(specs, spark):
    return spark.createDataFrame(
        [], specs.schema_ddl(specs.TABLES["s_meeting_participants_bu"])
    ).schema


def _mail_df(spark, mail_mod, mail_schema, mails):
    """用第一支的 build_mail_row 把 Bronze 形狀變成 mail 表形狀，確保兩支接得上。"""
    rows = [
        tuple(mail_mod.build_mail_row(m, "bu", "0.1").get(f.name) for f in mail_schema.fields)
        for m in mails
    ]
    return spark.createDataFrame(rows, mail_schema)


def _bronze(**kw):
    base = {
        "pk_seq": 1,
        "drupal_id": "9",
        "drupal_link": None,
        "create_date": datetime(2026, 10, 6, 8, 16),
        "mail_date": date(2026, 10, 6),
        "mail_datetime": datetime(2026, 10, 6, 16, 5),
        "mail_from": "0300001/王小美/amywang/DTDDB0",
        "mail_to": "",
        "mail_cc": "",
        "mail_bcc": "",
        "mail_subject": "FW: AUO Monthly Meeting",
        "mail_body_md": None,
        "mail_without_fw": None,
        "mail_body": None,
        "is_fw": True,
        "has_attach": 0,
        "is_test": False,
    }
    base.update(kw)
    return base


def test_spark_pipeline(mod, mail_mod, spark, clean_schema, mail_schema, part_schema):
    mails = [
        _bronze(pk_seq=1, mail_body_md=MD_THREAD),
        _bronze(
            pk_seq=2, mail_body_md=MD_THREAD, create_date=datetime(2026, 10, 7, 8, 0)
        ),  # 同 thread 再轉寄一次
        _bronze(pk_seq=3, mail_without_fw=MINUTES, mail_subject="TCL weekly"),
    ]
    df_mail = _mail_df(spark, mail_mod, mail_schema, mails)
    df_part = mail_mod.transform_participants(df_mail, part_schema)
    existing = spark.createDataFrame([], clean_schema)
    df_seg = mod.with_dup_of(
        mod.transform_segments(df_mail, df_part, clean_schema, ALIASES, APP_DEFAULTS, "0.1"),
        existing,
    )
    assert df_seg.columns == clean_schema.fieldNames() + ["_residual", "_masked"]
    rows = {(r.pk_seq, r.segment_no): r for r in df_seg.collect()}
    assert sorted(rows) == [(1, 1), (1, 2), (2, 1), (2, 2), (3, 1), (3, 2)]
    assert (
        rows[(1, 1)].dup_of is None and rows[(2, 1)].dup_of == "1-1-0"
    )  # 不同轉寄也命中（token 化後）
    assert rows[(2, 2)].dup_of is None  # appointment < 150 不去重
    assert (
        rows[(1, 1)].content_type == "thread_reply"
        and rows[(3, 1)].content_type == "inline_minutes"
    )
    assert (
        rows[(1, 1)].parties == ["acer.example", "auo.com"] and rows[(1, 1)].customer_hint == "acer"
    )
    assert rows[(3, 1)].customer_hint == "tcl" and rows[(3, 1)].app_hint == "TV"
    assert rows[(1, 1)].clean_text.startswith(
        "<P01>:\nSent: 2026-08-26"
    )  # 第一支：From 的人與轉寄人同名 → 共用 P01
    assert all(r._residual == 0 for r in rows.values())
    assert all("@" not in (r.clean_text or "") for r in rows.values())
    assert rows[(1, 1)].segment_date == date(2026, 8, 26) and rows[(3, 2)].segment_date == date(
        2026, 9, 3
    )


def test_with_dup_of_uses_existing_originals(mod, spark, clean_schema):
    cols = ["pk_seq", "segment_no", "sub_no", "content_hash", "create_date", "dup_of"]
    existing = spark.createDataFrame(
        [
            (10, 1, 0, "h1", datetime(2026, 9, 1), None),
            (11, 1, 0, "h1", datetime(2026, 9, 2), "10-1-0"),
            (12, 1, 0, "h2", datetime(2026, 9, 3), None),
        ],
        DUP_DDL,
    )
    batch = spark.createDataFrame(
        [
            (12, 1, 0, "h9", datetime(2026, 9, 3), None),  # 既有 pk 重洗：自己的舊列不進候選池
            (20, 1, 0, "h1", datetime(2026, 10, 1), None),  # 命中表中正本 10-1-0
            (20, 2, 0, None, datetime(2026, 10, 1), None),  # hash NULL 不參與
            (21, 1, 0, "h9", datetime(2026, 10, 2), None),
        ],  # 最後一列命中本批 12-1-0
        DUP_DDL,
    )
    out = {(r.pk_seq, r.segment_no): r.dup_of for r in mod.with_dup_of(batch, existing).collect()}
    assert out == {(12, 1): None, (20, 1): "10-1-0", (20, 2): None, (21, 1): "12-1-0"}
    assert mod.with_dup_of(batch, existing).columns == cols
