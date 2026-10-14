# ruff: noqa: E501 - 測試資料一筆一行，比對齊寬度好讀
"""meeting_extracted_phase0_explore 的純函式 cell 測試（[c02]～[c06a]）。資料全為假名、假網域。"""

from datetime import date, datetime

import pytest
from nbload import load_cells

NB = "jobs/meeting_record/meeting_extracted_phase0_explore/notebook.ipynb"
SCHEMA = (
    "pk_seq bigint, drupal_id string, create_date timestamp, mail_date date, mail_datetime timestamp, "
    "mail_from string, mail_to string, mail_cc string, mail_bcc string, mail_subject string, "
    "mail_body_md string, mail_without_fw string, mail_body string, is_fw boolean, has_attach int, is_test boolean"
)

THREAD_MD = (
    "Hi team, summary of the TCL panel discussion follows. "
    * 6
    + "\n**From:** Amy Lin 林小美 <Amy.Lin@auo.com>\n**Sent:** Wednesday, August 26, 2026 10:16 AM\n"
    "**To:** Doe, John <John.Doe@cust.example>\n**Subject:** RE: TCL Monthly\n"
    + "TCL asks for T850QVN08.LT0 samples. "
    * 3
    + "\n-----Original Message-----\n**From:** Doe, John <John.Doe@cust.example>\n"
    "**Sent:** Tuesday, October 6, 2026 3:16 PM\n**To:** Amy Lin 林小美 <Amy.Lin@auo.com>\nplease update TCL schedule.\n"
    "![影像被寄件者移除。](cid:~WRD0000.jpg)\n"
)
MINUTES = (
    "ITEM\n9月3日\nT430QVN04.5 海信 TCL 量產出貨不良目前 600 ppm\nT550QVN10.F 驗證\nT850QVN08.G 樣品\n"
    + "說明內容 " * 60
)


@pytest.fixture(scope="module")
def mod():
    return load_cells(NB, ["c02", "c03", "c04", "c05", "c06", "c06a"], name="mrphase0")


@pytest.fixture(scope="module")
def df_raw(spark):
    ts = datetime(2026, 10, 6, 8, 0)
    rows = [
        # 1 thread（md 首選）
        (
            1,
            "a",
            ts,
            date(2026, 10, 6),
            ts,
            "0304048/王大明/dmwang/DTDDB0",
            "",
            "",
            "",
            "FW  TCL Monthly",
            THREAD_MD,
            None,
            None,
            True,
            0,
            False,
        ),
        # 2 同 thread 被另一人轉寄 → 段重複
        (
            2,
            "b",
            ts,
            date(2026, 10, 6),
            ts,
            "0300001/李小華/xhli/DTDDC1",
            "",
            "",
            "",
            "RE: TCL Monthly",
            THREAD_MD,
            None,
            None,
            True,
            0,
            False,
        ),
        # 3 紀要：md 太短，退到 without_fw
        (
            3,
            "c",
            ts,
            date(2026, 9, 3),
            ts,
            "0300002/陳一/yichen/DTDDB0",
            "",
            "",
            "",
            "[BU] TCL Account meeting minutes",
            "short",
            MINUTES,
            None,
            False,
            0,
            False,
        ),
        # 4 附件型、mail_from 格式不符
        (
            4,
            "d",
            ts,
            date(2026, 9, 3),
            ts,
            "someone@auo.com",
            "",
            "",
            "",
            "Review deck",
            None,
            None,
            "please refer the attached file",
            False,
            2,
            False,
        ),
        # 5 正文互相衝突：md 講 Acer、without_fw 講 Hisense
        (
            5,
            "e",
            ts,
            date(2026, 9, 1),
            ts,
            "0300003/林二/erlin/DTDDB0",
            "",
            "",
            "",
            "Acer review",
            "acer monitor roadmap discussion " * 10,
            "海信 tv allocation forecast plan " * 10,
            None,
            False,
            0,
            True,
        ),
    ]
    return spark.createDataFrame(rows, SCHEMA)


@pytest.fixture(scope="module")
def df_feat(mod, df_raw):
    return mod.with_content_type(mod.with_body_choice(mod.with_mail_features(df_raw)))


def by_pk(df):
    return {r.pk_seq: r for r in df.collect()}


def test_mail_features(df_feat):
    r = by_pk(df_feat)
    assert r[1].from_ok and r[1].dept_code == "DTDDB0"
    assert not r[4].from_ok and r[4].dept_code is None
    assert r[1].subject_clean == "TCL Monthly" and r[1].subject_prefixed
    assert r[4].subject_clean == "Review deck" and not r[4].subject_prefixed  # Review 不是 RE 前綴
    assert r[3].unit_tag == "BU" and r[1].unit_tag is None
    assert r[1].lag_days == 0 and r[3].lag_days == 33
    assert r[4].attach_count == 2 and not r[1].oversize


def test_body_choice(df_feat):
    r = by_pk(df_feat)
    assert r[1].body_source_field == "mail_body_md"
    assert r[3].body_source_field == "mail_without_fw"  # md 只有 5 字 < 150
    assert r[4].body_source_field == "mail_body"
    assert r[5].body_conflict and not r[1].body_conflict
    assert r[1].jac_md_wofw is None  # 單邊空 → 不算


def test_content_type(df_feat):
    r = by_pk(df_feat)
    assert r[1].content_type_est == "thread_reply" and r[1].n_md_from == 2 and r[1].n_orig_sep == 1
    assert r[1].n_img == 1 and r[1].est_segments == 3
    assert r[3].content_type_est == "inline_minutes" and r[3].n_models == 3
    assert r[4].content_type_est == "noise"  # 太短，先判 noise
    assert r[5].content_type_est == "unclassified"


def test_sent_values_and_repeats(mod, df_feat):
    sent = mod.explode_sent_values(df_feat)
    kinds = {(r.pk_seq, r.sent_kind) for r in sent.collect()}
    assert kinds == {(1, "en"), (2, "en")}
    ts = sorted(r.sent_ts for r in sent.where("pk_seq = 1").collect())
    assert ts == [datetime(2026, 8, 26, 10, 16), datetime(2026, 10, 6, 15, 16)]
    s = mod.segment_repeat_stats(sent).collect()[0]
    assert (s.segment_instances, s.distinct_segments, s.repeat_instances, s.max_copies) == (
        4,
        2,
        2,
        2,
    )
    assert s.repeat_rate == 0.5


def test_email_domains_no_address_kept(mod, df_feat):
    d = mod.explode_email_domains(df_feat)
    assert set(d.columns) == {"pk_seq", "domain", "is_internal"}
    got = {(r.pk_seq, r.domain, r.is_internal) for r in d.where("pk_seq = 1").collect()}
    assert got == {(1, "auo.com", True), (1, "cust.example", False)}


def test_customers(mod, df_feat):
    c = {(r.pk_seq, r.customer, r.in_subject) for r in mod.explode_customers(df_feat).collect()}
    assert (1, "TCL", True) in c
    assert (3, "Hisense", False) in c and (3, "TCL", True) in c
    assert (5, "Acer", True) in c


def test_num_profile(mod, df_feat):
    r = mod.num_profile(df_feat, ["attach_count"]).collect()[0]
    assert r.attach_count_max == 2 and r.attach_count_p50 == 0


def test_sent_nbsp(mod, spark):
    body = "**Sent:** July 27, 2026 10:29 AM   **To:** x"
    df = spark.createDataFrame(
        [(1, "s", body)], "pk_seq bigint, subject_clean string, body_raw string"
    )
    r = mod.explode_sent_values(df).collect()[0]
    assert r.sent_kind == "en" and r.sent_ts == datetime(2026, 7, 27, 10, 29)


def test_md_bloat_profile(mod, spark):
    b64 = "QUJD" * 100
    md = f"| a | b |\n|---|---|\n| 1 | 2 |\n![x](data:image/png;base64,{b64})\n\n<td>x</td> &nbsp; see https://x.example/a"
    df = spark.createDataFrame(
        [(1, md, 10, 20)],
        "pk_seq bigint, mail_body_md string, len_mail_without_fw int, len_mail_body int",
    )
    r = mod.md_bloat_profile(df).collect()[0]
    assert r.total_chars == len(md) and r.n_lines == 6 and r.n_blank_lines == 1
    assert (r.n_data_uri, r.n_base64_run, r.n_md_image, r.n_md_link) == (1, 1, 1, 0)
    assert (r.n_md_table_line, r.n_html_tag, r.n_html_entity, r.n_url) == (3, 2, 1, 1)
    assert r.share_base64_run > 0.75 and r.max_line_chars > 400 and r.len_mail_body == 20
