# ruff: noqa: E501 - 測試資料一筆一行，比對齊寬度好讀
"""meeting_record_explore 的純函式 cell 測試（[c02]～[c03]）。"""

from datetime import datetime

import pytest
from nbload import load_cells

NB = "jobs/meeting_record/meeting_record_explore/notebook.ipynb"
SCHEMA = "source string, create_date timestamp, mail_from string, mail_subject string, payload string"


@pytest.fixture(scope="module")
def mod():
    return load_cells(NB, ["c02", "c03"], name="mrexplore")


@pytest.fixture(scope="module")
def df_mail(spark):
    rows = [
        ("BU", datetime(2026, 9, 22, 9, 0), "王小明 <Ming.Wang@corp.com>", "週會紀錄 9/22", '{"body": "a"}'),
        ("BU", datetime(2026, 9, 24, 9, 0), "Amy <amy@corp.com>", "專案會議", "b"),
        ("SCM", datetime(2026, 9, 24, 9, 0), "ming.wang@corp.com", "SCM 週會", "c"),
        ("SCM", datetime(2026, 9, 25, 9, 0), "scm-bot", None, None),
    ]
    return spark.createDataFrame(rows, SCHEMA)


def test_resolve_sources(mod):
    assert mod.resolve_sources("ALL") == {"BU": "b_internal_meeting_record", "SCM": "b_internal_meeting_record_scm"}
    assert mod.resolve_sources(" scm ") == {"SCM": "b_internal_meeting_record_scm"}
    with pytest.raises(ValueError):
        mod.resolve_sources("XX")


def test_filter_mail(mod, df_mail):
    def subjects(df):
        return {r.mail_subject for r in df.collect()}

    assert subjects(mod.filter_mail(df_mail, "MING.wang")) == {"週會紀錄 9/22", "SCM 週會"}
    assert subjects(mod.filter_mail(df_mail, "ming", "週會")) == {"週會紀錄 9/22", "SCM 週會"}
    assert subjects(mod.filter_mail(df_mail, "", "專案")) == {"專案會議"}
    assert mod.filter_mail(df_mail).count() == 4  # null 標題也不會被濾掉


def test_take_range(mod, df_mail):
    def got(order, a, b):
        return [r.payload for r in mod.take_range(df_mail, order, a, b).collect()]

    # desc：9/25 → 9/24（同時間依 source：BU 在 SCM 前）→ 9/22
    assert got("desc", 1, 4) == [None, "b", "c", '{"body": "a"}']
    assert got("desc", 2, 3) == ["b", "c"]
    assert got("asc", 1, 2) == ['{"body": "a"}', "b"]
    assert got("desc", 5, 6) == []


def test_format_mail(mod):
    row = {"source": "BU", "create_date": datetime(2026, 9, 22, 9, 0), "mail_from": "amy@corp.com",
           "mail_subject": "週會", "payload": '{"body": "會議內容"}', "note": "x" * 10, "extra": None}
    text = mod.format_mail(3, row, [], 5)
    assert "#3  [BU]  2026-09-22 09:00:00" in text
    assert "Subject: 週會" in text
    assert "---- payload ----" in text and "---- extra ----\n(null)" in text
    assert "xxxxx\n…（截斷，共 10 字）" in text
    assert "---- mail_from ----" not in text  # header 欄位不重複印
    assert '"body": "會議內容"' in mod.format_mail(3, row, ["payload"], 0)  # JSON 字串會排版、中文不跳脫
    assert "---- nope ----\n(無此欄位)" in mod.format_mail(3, row, ["nope"], 0)
    assert mod.format_index(12, row) == "#12   [BU] 2026-09-22 09:00:00  amy@corp.com  |  週會"
