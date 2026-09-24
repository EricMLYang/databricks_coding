# ruff: noqa: E501 - 測試資料一筆一行，比對齊寬度好讀
"""meeting_record_weekly_report 的純函式 cell 測試（[c02]～[c03]）。"""

from datetime import date, datetime

import pytest
from nbload import load_cells

NB = "jobs/meeting_record_weekly_report/notebook.ipynb"
SCHEMA = "source string, create_date timestamp, mail_from string, mail_subject string"


@pytest.fixture(scope="module")
def mod():
    return load_cells(NB, ["c02", "c03"], name="mrweekly")


@pytest.fixture(scope="module")
def df_mail(mod, spark):
    rows = [
        ("t1", datetime(2026, 9, 22, 9, 0), "王小明 <Ming.Wang@corp.com>", "週會紀錄 9/22"),
        ("t1", datetime(2026, 9, 24, 9, 0), "ming.wang@corp.com", "  專案會議  "),
        ("t1", datetime(2026, 9, 24, 10, 0), "Amy <amy@corp.com>", None),
        ("t1", datetime(2026, 9, 15, 9, 0), "Amy <amy@corp.com>", "週會紀錄 9/15"),
        ("t1", datetime(2026, 9, 16, 9, 0), "   ", ""),
        ("t2", datetime(2026, 9, 23, 9, 0), "scm-bot", "SCM 週會"),
    ]
    return mod.normalize_mail(spark.createDataFrame(rows, SCHEMA))


def test_week_range_and_label(mod):
    weeks = mod.week_range(date(2026, 9, 25), 2)  # 週五
    assert weeks == [date(2026, 9, 7), date(2026, 9, 14), date(2026, 9, 21)]
    assert mod.week_range(date(2026, 9, 21), 0) == [date(2026, 9, 21)]  # 週一
    assert mod.week_label(date(2026, 9, 14), date(2026, 9, 25)) == "9/14 ~ 9/20"
    assert mod.week_label(date(2026, 9, 21), date(2026, 9, 25)) == "9/21 ~ 9/25 (ongoing)"


def test_normalize_mail(df_mail):
    got = {(r.create_date.day, r.sender_key, r.mail_subject, r.week_start) for r in df_mail.collect()}
    assert got == {
        (22, "ming.wang@corp.com", "週會紀錄 9/22", date(2026, 9, 21)),
        (24, "ming.wang@corp.com", "專案會議", date(2026, 9, 21)),
        (24, "amy@corp.com", "(空白)", date(2026, 9, 21)),
        (15, "amy@corp.com", "週會紀錄 9/15", date(2026, 9, 14)),
        (16, "(空白)", "(空白)", date(2026, 9, 14)),
        (23, "scm-bot", "SCM 週會", date(2026, 9, 21)),
    }


def test_weekly_counts_fills_zero(mod, spark, df_mail):
    weeks = [date(2026, 9, 7), date(2026, 9, 14), date(2026, 9, 21)]
    grid = spark.createDataFrame([(t, w) for t in ["t1", "t2"] for w in weeks], "source string, week_start date")
    got = {(r.source, r.week_start.day): (r.record_count, r.sender_count) for r in mod.weekly_counts(df_mail, grid).collect()}
    assert got == {
        ("t1", 7): (0, 0), ("t1", 14): (2, 2), ("t1", 21): (3, 2),
        ("t2", 7): (0, 0), ("t2", 14): (0, 0), ("t2", 21): (1, 1),
    }


def test_sender_summary_and_report(mod, spark, df_mail):
    senders = [r.asDict() for r in mod.sender_summary(df_mail).collect()]
    ming = next(s for s in senders if s["sender_key"] == "ming.wang@corp.com")
    assert ming["mail_count"] == 2 and ming["last_at"] == datetime(2026, 9, 24, 9, 0)
    counts = [
        {"source": "t1", "week_start": date(2026, 9, 21), "record_count": 3, "sender_count": 2},
        {"source": "t1", "week_start": date(2026, 9, 14), "record_count": 2, "sender_count": 2},
    ]
    text = mod.weekly_report(counts, senders, date(2026, 9, 25), top_n=1)
    lines = text.splitlines()
    assert lines[0] == "===== t1 ====="
    assert lines[1] == "9/21 ~ 9/25 (ongoing): 3 筆 / 2 位寄件人"
    assert lines[2].strip().startswith("2") and "王小明 <Ming.Wang@corp.com>" in lines[2]
    assert lines[3].strip() == "…另 1 位"
    assert lines[4] == "9/14 ~ 9/20: 2 筆 / 2 位寄件人"


def test_sender_week_matrix(mod, df_mail):
    weeks = [date(2026, 9, 14), date(2026, 9, 21)]
    rows = {(r["source"], r["sender_key"]): r.asDict() for r in mod.sender_week_matrix(df_mail, weeks).collect()}
    amy = rows[("t1", "amy@corp.com")]
    assert (amy["09/14"], amy["09/21"], amy["total"], amy["active_weeks"]) == (1, 1, 2, 2)
    ming = rows[("t1", "ming.wang@corp.com")]
    assert (ming["09/14"], ming["09/21"], ming["total"], ming["active_weeks"]) == (0, 2, 2, 1)
    assert rows[("t2", "scm-bot")]["total"] == 1


def test_mail_detail_order(mod, df_mail):
    got = [r.create_date for r in mod.mail_detail(df_mail).where("source = 't1'").collect()]
    assert got == sorted(got, reverse=True)
