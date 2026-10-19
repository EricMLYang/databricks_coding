"""meeting_extracted_w1_t1_mail 的測試：[c02]～[c05] 純 Python 規則，[c06] Spark 接線。

測試資料全是虛構（假名、example 網域），格式照 PM_Head 去識別化樣本：md `**From:**` 標頭、
純文字 `From:` 多行標頭、Outlook 殘渣、免責段、IMCEAEX 假位址、ITEM 紀要。
"""

from datetime import date, datetime

import pytest
from nbload import load_cells

NB = "jobs/meeting_record/meeting_extracted_w1_t1_mail/notebook.ipynb"
NB_002 = "jobs/meeting_record/meeting_extracted_migration/002_meeting_neutral_tables.ipynb"


@pytest.fixture(scope="module")
def mod():
    return load_cells(NB, ["c02", "c03", "c04", "c05", "c06"], name="w1t1")


@pytest.fixture(scope="module")
def specs():
    return load_cells(NB_002, ["c02", "c03", "c04"], name="mig002_for_w1")


PLAIN_THREAD = """Dear all,

see below

From:
 Amy Wang 王小美
 &lt;Amy.Wang@auo.com&gt;
Sent: Tuesday, October 6, 2026 3:26 PM
To: CustA, P01 &lt;P01.CustA@acer.example&gt;; Bob Lin 林小寶
 &lt;Bob.Lin@auo.com&gt;; CustA, P02
 &lt;IMCEAEX-_o=ExchangeLabs_cn=Recipients-CustA+2C+20P02@te.example&gt;
Cc: MNT PM &lt;MNT_PM@acer.example&gt;; 8B09 &lt;HQ.8B09@acer.example&gt;
Subject: RE: AUO Monthly Meeting

Hi P01,
Only single mode.
BR
&nbsp;&nbsp; AW

-----Original Appointment-----
From: CustA, P01 &lt;P01.CustA@acer.example&gt;

Sent: Friday, July 17, 2026 9:41 AM
To: Amy Wang 王小美;
 Bob Lin 林小寶
Cc: MNT PM
Subject: AUO Monthly Meeting
When: 2026年8月13日星期四
下午
 03:30-下午
 05:00 (UTC+08:00) 台北。
Where: 8B09 (Taipei)
&nbsp;
Dear all,
Please reserve your time.

---------------------------------------------------------------
Acer has pledged to source 100% renewable electricity by 2035.
This email contains information that is for the sole use of the intended recipient.
---------------------------------------------------------------
"""

MD_THREAD = (
    "**From:** Amy Wang 王小美 <Amy.Wang@auo.com>\n**Sent:** Wednesday, August 26, 2026 10:16 AM\n"
    "**To:** CustA, P03 <P03.CustA@acer.example>; Bob Lin 林小寶 <Bob.Lin@auo.com>\n"
    "**Cc:** MNT\\_PM <MNT\\_PM@acer.example>\n**Subject:** RE: AUO Monthly Meeting\n\n"
    "Summary:\n1. 2ch LVDS 27 QHD 100Hz\n2. 4ch LVDS 27 UHD 100Hz\n\n"
    "![影像被寄件者移除。](cid:~WRD0000.jpg)\n\n"
    "| a | ![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAAB) |\n"
)


def _src(**kw):
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
        "mail_subject": "FW: RE: AUO Monthly Meeting",
        "mail_body_md": None,
        "mail_without_fw": None,
        "mail_body": None,
        "mail_body_html": None,
        "is_fw": True,
        "has_attach": 0,
        "is_test": False,
    }
    return {**base, **kw}


# ---------- [c03] 初洗 ----------
def test_clean_display_rules(mod):
    raw = (
        "Normal\n90\nDocumentEmail\nEN-US\n{font-family:新細明體; mso-font-charset:136;}\n"
        "Hi &amp; hello&nbsp;there\n\n![影像被寄件者移除。](cid:~WRD.jpg)\n"
        "see [the link](https://example.com/x) now\n\n"
        "CONFIDENTIALITY REMINDER: This email may include confidential information.\n\n"
        "---------------------------------------------------------------\n\n"
        "real content M270QAN06.A"
    )
    out = mod.clean_display(raw, "mail_body")
    assert (
        "Normal" not in out
        and "DocumentEmail" not in out
        and "font-family" not in out
        and "\n90\n" not in out
    )
    assert "Hi & hello there" in out
    assert "cid:" not in out and "the link" in out and "https://" not in out
    # 0.2：CSS 殘渣整行刪只限 400 字內；長的正文行含 mso- 要留（整封併成一行時不能整封陪葬）
    long_line = "real content with mso-list mention " * 15
    assert mod.clean_display(long_line, "mail_body").startswith("real content")
    assert mod.clean_display("short junk {mso-style-priority:99;}", "mail_body") == ""
    assert "CONFIDENTIALITY" not in out and "------" not in out
    assert out.endswith("real content M270QAN06.A")


def test_clean_display_base64_and_md_escape(mod):
    out = mod.clean_display(MD_THREAD, "mail_body_md")
    assert "base64" not in out and "[image]" in out and "cid:" not in out
    assert "MNT_PM@acer.example" in out  # \_ 還原


def test_choose_body_order(mod):
    long_md = "x " * 100
    f, raw, disp = mod.choose_body(_src(mail_body_md=long_md, mail_without_fw="short"))
    assert f == "mail_body_md" and raw == long_md and len(disp) >= 150
    f, _, disp = mod.choose_body(_src(mail_body_md="too short", mail_without_fw="wofw text longer"))
    assert (f, disp) == ("mail_without_fw", "wofw text longer")  # 都 < 150：取初洗後最長的（D28）
    f, _, disp = mod.choose_body(_src(mail_body="body only"))
    assert (f, disp) == ("mail_body", "body only")
    assert mod.choose_body(_src()) == ("none", None, "")


def test_choose_body_skips_junk_without_fw(mod):
    """D28：ETL 的 mail_without_fw 只剩 Word 文件屬性殘渣（九成空行）時，正文在 mail_body，
    不能因為它非空就選。"""
    junk = (
        "\n" * 8 + "Normal\n130\nDocumentEmail\nfalse\n\n\nfalse\nfalse\n\nEN-US\nZH-TW\nX-NONE\n"
        + "\n" * 6 + "MicrosoftInternetExplorer4\n" + "\n" * 300
        + "<!--\n/* Font Definitions */\n" + "\n" * 60
    )
    assert len(junk) > 300
    assert mod.clean_display(junk, "mail_without_fw") == ""  # 0.2 連 <!-- 那兩行也清掉
    body = (
        "From: Amy Wang 王小美\nSent: Tuesday, October 6, 2026 3:26 PM\n"
        "Subject: RE: AUO Monthly Meeting\n\n"
        + "M270QAN06.A 客戶要求 Q4 增加 10K 片，PM 回覆看產能。" * 6
    )
    f, raw, disp = mod.choose_body(_src(mail_body_md="", mail_without_fw=junk, mail_body=body))
    assert f == "mail_body" and raw == body and len(disp) >= 150
    # 三欄都不到 150 字：取初洗後最長的，不是順序在前的
    longer = "a bit longer body text here"
    f, _, disp = mod.choose_body(_src(mail_without_fw="Normal\n\nhi", mail_body=longer))
    assert (f, disp) == ("mail_body", longer)
    # 只有殘渣 → none
    assert mod.choose_body(_src(mail_without_fw=junk)) == ("none", None, "")


# Outlook / Word HTML 的形狀（假名、example 網域）：<head> 有 xml 條件註解與 <style>；
# 正文段落 <p class=MsoNormal>、空行是 <p><o:p>&nbsp;</o:p></p>；標頭 <b>From:</b> … <br>；
# 原始碼有軟換行；表格；cid 圖；連結；免責段。
OUTLOOK_HTML = """<html><head><meta http-equiv=Content-Type content="text/html; charset=utf-8">
<!--[if gte mso 9]><xml>
<w:WordDocument><w:View>Normal</w:View><w:Zoom>90</w:Zoom><w:DocumentKind>DocumentEmail</w:DocumentKind>
<w:TrackMoves>false</w:TrackMoves><w:LidThemeOther>EN-US</w:LidThemeOther></w:WordDocument></xml><![endif]-->
<style><!--
/* Font Definitions */
@font-face
\t{font-family:"Cambria Math";
\tpanose-1:2 4 5 3 5 4 6 3 2 4;}
p.MsoNormal, li.MsoNormal, div.MsoNormal
\t{margin:0cm;
\tfont-size:11.0pt;
\tfont-family:"Calibri",sans-serif;}
--></style></head>
<body lang=ZH-TW link="#0563C1" vlink="#954F72" style='word-wrap:break-word'>
<div class=WordSection1>
<p class=MsoNormal>Dear all,<o:p></o:p></p>
<p class=MsoNormal><o:p>&nbsp;</o:p></p>
<p class=MsoNormal>see below<o:p></o:p></p>
<p class=MsoNormal><o:p>&nbsp;</o:p></p>
<div style='border:none;border-top:solid #E1E1E1 1.0pt;padding:3.0pt 0cm 0cm 0cm'>
<p class=MsoNormal><b><span lang=EN-US>From:</span></b><span lang=EN-US> Amy Wang 王小美
&lt;Amy.Wang@auo.com&gt;<br>
<b>Sent:</b> Tuesday, October 6, 2026 3:26 PM<br>
<b>To:</b> CustA, P01 &lt;P01.CustA@acer.example&gt;<br>
<b>Subject:</b> RE: AUO Monthly Meeting<o:p></o:p></span></p>
</div>
<p class=MsoNormal><o:p>&nbsp;</o:p></p>
<p class=MsoNormal>Hi P01,<o:p></o:p></p>
<p class=MsoNormal>M270QAN06.A 客戶要求 Q4 增加
10K 片，PM 回覆看產能。<o:p></o:p></p>
<table class=MsoNormalTable border=1 cellspacing=0 cellpadding=0>
 <tr><td width=120 valign=top style='border:solid windowtext 1.0pt'>
  <p class=MsoNormal>Model<o:p></o:p></p></td>
  <td><p class=MsoNormal>Qty<o:p></o:p></p></td></tr>
 <tr><td><p class=MsoNormal>M270QAN06.A<o:p></o:p></p></td>
  <td><p class=MsoNormal>10K<o:p></o:p></p></td></tr>
</table>
<p class=MsoNormal><img width=200 height=50 id="Picture_x0020_1"
src="cid:image001.png@01DD55A6.F34EE930"><o:p></o:p></p>
<p class=MsoNormal><a href="https://example.com/x">the link</a><o:p></o:p></p>
<p class=MsoNormal>CONFIDENTIALITY REMINDER: This email may include
confidential information.<o:p></o:p></p>
</div></body></html>"""


def test_html_to_text_outlook(mod):
    """D29：head / style / 條件註解全刪；段落與 <br> 換行；軟換行併回；表格成 md 列；cid 圖刪；
    連結留文字。"""
    txt = mod.html_to_text(OUTLOOK_HTML)
    assert "Font Definitions" not in txt and "DocumentEmail" not in txt
    assert "<" not in txt.replace("<Amy", "").replace("<P01", "")
    assert "Dear all,\n\nsee below" in txt  # 空段落 → 空白行
    assert "From: Amy Wang 王小美 <Amy.Wang@auo.com>\nSent: Tuesday, October 6, 2026 3:26 PM" in txt
    assert "增加 10K 片" in txt  # 原始碼軟換行併成空白
    assert "| Model | Qty |" in txt and "| M270QAN06.A | 10K |" in txt
    assert "cid:" not in txt and "the link" in txt and "https://" not in txt
    assert mod.html_to_text(None) == "" and mod.html_to_text("") == ""
    # ETL 截斷：只有 <head>、停在 <style><!-- 中間（沒有 --> / </style> / </head> / <body>）
    # → 整封視為無內容，不能把幾萬字 CSS 當正文（第三次 dry_run 42 封被誤救、dup_of_pk 跳到 11%）
    cut = OUTLOOK_HTML.split("p.MsoNormal, li.MsoNormal")[0]
    assert "<body" not in cut and "</style>" not in cut and "</head>" not in cut
    assert mod.html_to_text(cut) == ""
    assert mod.choose_body(_src(mail_body_html=cut)) == ("none", None, "")
    # 沒關閉的 <!--[if 也吃到結尾
    assert mod.html_to_text("<p>ok</p><!--[if gte vml 1]><v:shape>junk mso-wrap") == "ok"
    # 整條管線：初洗後免責行刪掉、標頭區塊抓得到
    disp = mod.clean_display(txt, "mail_body_html")
    assert "CONFIDENTIAL" not in disp and "the link" in disp
    blocks = mod.find_header_blocks(disp)
    assert len(blocks) == 1 and blocks[0]["fields"]["Subject"] == "RE: AUO Monthly Meeting"
    assert blocks[0]["fields"]["To"] == "CustA, P01 <P01.CustA@acer.example>"


def test_choose_body_html_fallback(mod):
    """D29：三個文字欄都只剩殘渣才讀 HTML；文字欄夠長時不碰 HTML。"""
    junk = "\n" * 8 + "Normal\n130\nDocumentEmail\nfalse\n\nEN-US\n" + "\n" * 300
    junk += "<!--\n/* Font Definitions */\n"
    src = _src(mail_without_fw=junk, mail_body=junk, mail_body_html=OUTLOOK_HTML)
    f, raw, disp = mod.choose_body(src)
    assert f == "mail_body_html" and raw == OUTLOOK_HTML
    assert len(disp) >= 150 and "Dear all," in disp
    f, _, disp = mod.choose_body(_src(mail_body=PLAIN_THREAD, mail_body_html=OUTLOOK_HTML))
    assert f == "mail_body" and "Dear all," in disp and "Model" not in disp
    # HTML 也不到 150 字：四者取最長
    tiny = "<p>tiny html paragraph here</p>"
    f, _, disp = mod.choose_body(_src(mail_body="short body", mail_body_html=tiny))
    assert (f, disp) == ("mail_body_html", "tiny html paragraph here")
    row = mod.build_mail_row(_src(mail_without_fw=junk, mail_body_html=OUTLOOK_HTML), "bu", "0.2")
    assert row["body_source_field"] == "mail_body_html" and row["has_headers"] is True
    assert row["raw_len"] == len(OUTLOOK_HTML) and row["display_len"] == len(row["body_display"])


def test_disclaimer_keeps_lines_before_hit(mod):
    """0.2：免責只刪命中行起到段尾，之前的行保留（HTML 轉文字後段落間常沒空行）。"""
    t = "real line one\nreal line two\nCONFIDENTIAL: do not forward\nmore legal text"
    assert mod.drop_disclaimer_paragraphs(t) == "real line one\nreal line two"
    assert mod.drop_disclaimer_paragraphs("CONFIDENTIAL only\nlegal") == ""


def test_normalize_and_body_hash(mod):
    a, b = "Ｍ270 QAN06.A  改用 AG25，請備 10K", "m270qan06a 改用ag25 請備10k"
    assert mod.normalize_text(a) == mod.normalize_text(b)
    long = "內容 " * 60
    assert mod.body_hash(long) == mod.body_hash(long.replace(" ", "\n"))
    assert mod.body_hash("short") is None


def test_body_conflict(mod):
    acer = "acer meeting " * 20
    tcl = "TCL allocation " * 20
    assert (
        mod.body_conflict(
            _src(mail_body_md=acer * 2, mail_without_fw=tcl), "mail_body_md", acer * 2
        )
        is True
    )
    assert (
        mod.body_conflict(
            _src(mail_body_md=acer * 2, mail_without_fw=acer), "mail_body_md", acer * 2
        )
        is False
    )
    assert mod.body_conflict(_src(), "none", "") is False


# ---------- [c04] mail 欄位 ----------
def test_parse_mail_from_and_subject(mod):
    ok = mod.parse_mail_from(" 0300001/王小美/amywang/DTDDB0 ")
    assert ok == {
        "emp_id": "0300001",
        "name_zh": "王小美",
        "account": "amywang",
        "dept_code": "DTDDB0",
        "ok": True,
    }
    bad = mod.parse_mail_from("someone@example.com")
    assert (
        bad["ok"] is False and bad["name_zh"] == "someone@example.com" and bad["dept_code"] is None
    )
    assert mod.subject_clean("FW: RE: 回覆: AUO Monthly Meeting") == "AUO Monthly Meeting"
    assert mod.subject_clean("Review meeting") == "Review meeting"
    assert mod.subject_clean("  ") is None


def test_header_blocks_plain(mod):
    text = mod.clean_display(PLAIN_THREAD, "mail_body")
    blocks = mod.find_header_blocks(text)
    assert len(blocks) == 2
    b1, b2 = blocks
    assert b1["fields"]["From"] == "Amy Wang 王小美 <Amy.Wang@auo.com>"
    assert b1["fields"]["Sent"] == "Tuesday, October 6, 2026 3:26 PM"
    assert b1["fields"]["To"].startswith(
        "CustA, P01 <P01.CustA@acer.example>; Bob Lin 林小寶 <Bob.Lin@auo.com>"
    )
    assert b1["fields"]["Subject"] == "RE: AUO Monthly Meeting"
    assert text[b1["start"] : b1["end"]].startswith("From:") and text[
        b1["start"] : b1["end"]
    ].endswith("Monthly Meeting")
    assert (
        b2["fields"]["Sent"] == "Friday, July 17, 2026 9:41 AM"
    )  # From 與 Sent 之間有空白行也要接得上
    assert b2["fields"]["When"].startswith("2026年8月13日星期四 下午 03:30-下午 05:00")
    assert b2["fields"]["Where"] == "8B09 (Taipei)"
    assert "Dear all" not in text[b2["start"] : b2["end"]]
    assert "Acer has pledged" not in text  # 免責段已刪


def test_header_blocks_md_and_stray_from(mod):
    text = mod.clean_display(MD_THREAD, "mail_body_md")
    blocks = mod.find_header_blocks(text)
    assert len(blocks) == 1
    f = blocks[0]["fields"]
    assert (
        f["From"] == "Amy Wang 王小美 <Amy.Wang@auo.com>"
        and f["Cc"] == "MNT_PM <MNT_PM@acer.example>"
    )
    assert f["Subject"] == "RE: AUO Monthly Meeting"
    one_line = (
        "**From:** A <a@x.example> **Sent:** May 27, 2026 2:14:47 PM "
        "**To:** B <b@y.example> **Subject:** Hi\nbody"
    )
    f1 = mod.find_header_blocks(one_line)[0]["fields"]
    assert f1 == {
        "From": "A <a@x.example>",
        "Sent": "May 27, 2026 2:14:47 PM",
        "To": "B <b@y.example>",
        "Subject": "Hi",
    }
    assert (
        mod.find_header_blocks("From: the factory side\nwe agreed\n") == []
    )  # 沒有 Sent / Subject 不算標頭


def test_parse_datetime(mod):
    assert mod.parse_datetime("Tuesday, October 6, 2026 3:26 PM") == datetime(2026, 10, 6, 15, 26)
    assert mod.parse_datetime("May 27, 2026 2:14:47 PM") == datetime(2026, 5, 27, 14, 14)
    assert mod.parse_datetime("Friday, July 17, 2026 9:41 AM") == datetime(2026, 7, 17, 9, 41)
    assert mod.parse_datetime("Monday, March 2, 2026 12:05 AM") == datetime(2026, 3, 2, 0, 5)
    assert mod.parse_datetime(
        "2026年9月24日星期四 下午 03:30-下午 05:00 (UTC+08:00) 台北。"
    ) == datetime(2026, 9, 24, 15, 30)
    assert mod.parse_datetime("2026年9月24日") == datetime(2026, 9, 24)
    assert mod.parse_datetime("sometime next week") is None and mod.parse_datetime(None) is None


def test_build_mail_row(mod):
    row = mod.build_mail_row(_src(mail_body=PLAIN_THREAD), "bu", "0.1")
    assert row["body_source_field"] == "mail_body" and row["has_headers"] is True
    assert (
        row["subject_clean"] == "AUO Monthly Meeting"
        and row["subject_raw"] == "FW: RE: AUO Monthly Meeting"
    )
    assert (row["forwarder_emp_id"], row["forwarder_dept_code"], row["forwarder_token"]) == (
        "0300001",
        "DTDDB0",
        "P01",
    )
    assert (
        row["meeting_when"] == datetime(2026, 8, 13, 15, 30)
        and row["meeting_where"] == "8B09 (Taipei)"
    )
    assert row["raw_len"] == len(PLAIN_THREAD) and row["display_len"] == len(row["body_display"])
    assert row["body_hash"] and row["oversize"] is False and row["attach_count"] == 0
    assert (
        row["dup_of_pk"] is None and row["cleaned_at"] is None and row["cleaner_version"] == "0.1"
    )
    empty = mod.build_mail_row(_src(mail_from=None), "bu", "0.1")
    assert (
        empty["body_source_field"] == "none"
        and empty["body_display"] is None
        and empty["forwarder_token"] is None
    )


# ---------- [c05] 參與者 ----------
def test_split_recipients_and_display_name(mod):
    items = mod.split_recipients(
        "Amy Wang 王小美 <Amy.Wang@auo.com>; 'Hsu, Shawn' <Shawn.Hsu@acer.example>; MNT PM;"
        " p09@acer.example;"
        " CustA, P02 <IMCEAEX-_o=ExchangeLabs_cn=P02@te.example>;"
    )
    assert items == [
        ("Amy Wang 王小美", "amy.wang@auo.com"),
        ("Hsu, Shawn", "shawn.hsu@acer.example"),
        ("MNT PM", None),
        ("p09", "p09@acer.example"),
        ("CustA, P02", None),
    ]
    assert mod.parse_display_name("Amy Wang 王小美") == ("王小美", "Amy Wang", "person")
    assert mod.parse_display_name("Hsu, Shawn") == (None, "Shawn Hsu", "person")
    assert mod.parse_display_name("CustA, P02") == (None, "P02 CustA", "person")
    assert mod.parse_display_name("MNT PM") == (None, "MNT PM", "group")
    assert mod.parse_display_name("8B09") == (None, "8B09", "group")
    assert mod.parse_display_name("HQ.8B09") == (None, "HQ.8B09", "group")
    assert mod.parse_display_name("TC Tsai") == (None, "TC Tsai", "person")


def test_extract_participants_tokens(mod):
    row = mod.build_mail_row(_src(mail_body=PLAIN_THREAD), "bu", "0.1")
    rows = mod.extract_participants(row)
    by = {(r["segment_no"], r["role"], r["display_name_raw"]): r for r in rows}
    fw = by[(0, "forwarder", "0300001/王小美/amywang/DTDDB0")]
    assert (fw["token"], fw["name_zh"], fw["emp_id"], fw["dept_code"], fw["kind"]) == (
        "P01",
        "王小美",
        "0300001",
        "DTDDB0",
        "person",
    )
    # 轉寄人在 thread 的 From 以「英名 中文名 <email>」出現 → 同 token，並帶 email
    amy = by[(1, "from", "Amy Wang 王小美")]
    assert (
        amy["token"] == "P01"
        and amy["email"] == "amy.wang@auo.com"
        and amy["email_domain"] == "auo.com"
    )
    p01_a = by[(1, "to", "CustA, P01")]
    p01_b = by[(2, "from", "CustA, P01")]
    assert p01_a["token"] == p01_b["token"] and p01_a["email"] == "p01.custa@acer.example"
    bob_with = by[(1, "to", "Bob Lin 林小寶")]
    bob_without = by[(2, "to", "Bob Lin 林小寶")]
    assert (
        bob_with["token"] == bob_without["token"] and bob_without["email"] is None
    )  # 第二段沒 email 靠中文名合併
    assert (
        by[(1, "cc", "MNT PM")]["token"].startswith("G")
        and by[(1, "cc", "8B09")]["kind"] == "group"
    )
    assert by[(1, "cc", "MNT PM")]["token"] == by[(2, "cc", "MNT PM")]["token"]
    assert by[(1, "to", "CustA, P02")]["email"] is None  # IMCEAEX
    keys = [(r["segment_no"], r["token"], r["role"]) for r in rows]
    assert len(keys) == len(set(keys))
    assert all(
        r["side"] is None and r["company"] is None and r["resolver_version"] == "0.1" for r in rows
    )
    assert (
        mod.extract_participants({"pk_seq": 2, "forwarder_name_zh": None, "body_display": None})
        == []
    )


# ---------- [c06] Spark ----------
@pytest.fixture(scope="module")
def schemas(specs, spark):
    def schema_of(t):
        return spark.createDataFrame([], specs.schema_ddl(specs.TABLES[t])).schema

    return schema_of("s_meeting_record_mail_bu"), schema_of("s_meeting_participants_bu")


@pytest.fixture(scope="module")
def ref_tables(spark):
    alias = spark.createDataFrame(
        [
            ("email_domain", "auo.com", "auo.com", "auo", True),
            ("email_domain", "acer.example", "acer.example", "acer", True),
            ("email_domain", "webex.example", "webex.example", "mail_service", True),
            ("email_domain", "old.example", "old.example", "acer", False),
            ("name", "Acer", "acer", "acer", True),
        ],
        "alias_type string, alias string, alias_norm string, entity_id string, is_active boolean",
    )
    entity = spark.createDataFrame(
        [("auo", "auo", True), ("acer", "customer", True), ("mail_service", "ignore", True)],
        "entity_id string, side string, is_active boolean",
    )
    return alias, entity


def test_spark_pipeline(mod, spark, schemas, ref_tables):
    mail_schema, part_schema = schemas
    alias, entity = ref_tables
    srcs = [
        _src(pk_seq=1, mail_body=PLAIN_THREAD),
        _src(pk_seq=2, mail_body_md=MD_THREAD * 3, create_date=datetime(2026, 10, 7, 9, 0)),
        _src(
            pk_seq=3, mail_body_md=MD_THREAD * 3, create_date=datetime(2026, 10, 8, 9, 0)
        ),  # 與 2 整封相同
        _src(pk_seq=4, mail_without_fw="noise", is_test=False),
    ]
    df_src = spark.createDataFrame(
        [tuple(s[c] for c in mod.SOURCE_COLS) for s in srcs],
        ", ".join(
            f"{c} {t}"
            for c, t in zip(
                mod.SOURCE_COLS,
                [
                    "bigint",
                    "string",
                    "string",
                    "timestamp",
                    "date",
                    "timestamp",
                    "string",
                    "string",
                    "string",
                    "string",
                    "string",
                    "string",
                    "string",
                    "string",
                    "string",  # mail_body_html（D29）
                    "boolean",
                    "int",
                    "boolean",
                ],
                strict=True,
            )
        ),
    )
    existing = spark.createDataFrame([], mail_schema)
    df_mail = mod.with_dup_of_pk(mod.transform_mail(df_src, mail_schema, "bu", "0.1"), existing)
    assert df_mail.columns == mail_schema.fieldNames()
    rows = {r.pk_seq: r for r in df_mail.collect()}
    assert (
        rows[1].has_headers
        and rows[1].body_source_field == "mail_body"
        and rows[1].meeting_when == datetime(2026, 8, 13, 15, 30)
    )
    assert rows[2].dup_of_pk is None and rows[3].dup_of_pk == 2 and rows[4].dup_of_pk is None
    assert rows[4].body_hash is None and rows[4].body_source_field == "mail_without_fw"

    df_part = mod.resolve_side(mod.transform_participants(df_mail, part_schema), alias, entity)
    assert set(df_part.columns) == set(part_schema.fieldNames())
    p = {(r.pk_seq, r.segment_no, r.role, r.display_name_raw): r for r in df_part.collect()}
    fw = p[(1, 0, "forwarder", "0300001/王小美/amywang/DTDDB0")]
    assert (fw.side, fw.company, fw.token) == ("auo", "auo", "P01")
    assert (
        p[(1, 1, "from", "Amy Wang 王小美")].side,
        p[(1, 1, "from", "Amy Wang 王小美")].company,
    ) == ("auo", "auo")
    assert (p[(1, 1, "to", "CustA, P01")].side, p[(1, 1, "to", "CustA, P01")].company) == (
        "customer",
        "acer",
    )
    assert p[(1, 2, "to", "Bob Lin 林小寶")].side == "unknown"  # 無 email
    assert p[(1, 1, "cc", "MNT PM")].side == "customer"  # 群組也有 email → 可判公司
    assert len(p) == df_part.count()  # 鍵無重複


def test_resolve_side_suffix_and_ignore(mod, spark, schemas, ref_tables):
    _, part_schema = schemas
    alias, entity = ref_tables
    base = {f.name: None for f in part_schema.fields}
    rows = [
        {
            **base,
            "pk_seq": 9,
            "segment_no": 1,
            "token": "P02",
            "role": "to",
            "email_domain": "ab1.corpnet.auo.com",
        },
        {
            **base,
            "pk_seq": 9,
            "segment_no": 1,
            "token": "P03",
            "role": "to",
            "email_domain": "webex.example",
        },
        {
            **base,
            "pk_seq": 9,
            "segment_no": 1,
            "token": "P04",
            "role": "to",
            "email_domain": "old.example",
        },
        {
            **base,
            "pk_seq": 9,
            "segment_no": 1,
            "token": "P05",
            "role": "to",
            "email_domain": "notauo.com",
        },
    ]
    df = spark.createDataFrame(
        [tuple(r[f.name] for f in part_schema.fields) for r in rows], part_schema
    )
    got = {r.token: (r.side, r.company) for r in mod.resolve_side(df, alias, entity).collect()}
    assert got == {
        "P02": ("auo", "auo"),
        "P03": ("unknown", None),
        "P04": ("unknown", None),
        "P05": ("unknown", None),
    }


def test_with_dup_of_pk_uses_existing_rows(mod, spark, schemas):
    mail_schema, _ = schemas
    base = {f.name: None for f in mail_schema.fields}

    def mk(pk, h, d):
        return tuple(
            {**base, "pk_seq": pk, "body_hash": h, "create_date": d}[f.name]
            for f in mail_schema.fields
        )

    existing = spark.createDataFrame(
        [mk(1, "h", datetime(2026, 1, 1)), mk(5, "h", datetime(2026, 1, 5))], mail_schema
    )
    batch = spark.createDataFrame(
        [
            mk(5, "h", datetime(2026, 1, 5)),
            mk(7, "h", datetime(2026, 1, 7)),
            mk(8, "x", datetime(2026, 1, 8)),
        ],
        mail_schema,
    )
    got = {r.pk_seq: r.dup_of_pk for r in mod.with_dup_of_pk(batch, existing).collect()}
    assert got == {5: 1, 7: 1, 8: None}  # 本批的 5 重算仍指向既有的 1；8 首次出現
