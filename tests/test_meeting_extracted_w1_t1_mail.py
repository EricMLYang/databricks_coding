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
    f, _, disp = mod.choose_body(_src(mail_body_md="too short", mail_without_fw="wofw text"))
    assert (f, disp) == ("mail_without_fw", "wofw text")
    f, _, disp = mod.choose_body(_src(mail_body="body only"))
    assert (f, disp) == ("mail_body", "body only")
    assert mod.choose_body(_src()) == ("none", None, "")


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
