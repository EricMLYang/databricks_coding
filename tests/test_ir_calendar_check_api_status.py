"""ir_calendar_check_api_status 的純函式 cell 測試（[c02]、[c03]）。

status 回應的形狀照 API Spec 的範例；api_period_col 與 fiscal_period_for_api 必須算出同一個值，
否則 [c12] 的「期望列數」會跟實際送出去的 fiscalPeriod 對不起來。
"""

from datetime import datetime, timezone

import pytest
from nbload import load_cells

CHECK_NB = "jobs/ir_calendar/check_api_status/notebook.ipynb"
CONSUME_NB = "jobs/ir_calendar/consume_batches/notebook.ipynb"
UTC = timezone.utc  # noqa: UP017 - 本機 Python 3.10
NOW = datetime(2026, 9, 22, 3, 30, tzinfo=UTC)

STATUS_BODY = {
    "success": True,
    "data": {
        "tables": [
            {"tableName": "app_company", "rowCount": 120,
             "lastUpdatedAt": "2026-09-22T01:00:00", "hoursSinceLastUpdate": 2.5},
            {"tableName": "app_ir_conference", "rowCount": 450,
             "lastUpdatedAt": "2026-09-21T00:30:00", "hoursSinceLastUpdate": 27.0},
        ],
        "lastCompaniesBatch": {
            "executedAt": "2026-09-22T01:00:00", "success": True,
            "created": 10, "updated": 5, "unchanged": 2, "failed": 0, "failureSummaries": [],
        },
        "lastConferencesBatch": {
            "executedAt": "2026-09-21T00:30:00", "success": True,
            "created": 8, "updated": 3, "unchanged": 1, "failed": 1,
            "failureSummaries": ["stockCode=2330, fiscalPeriod=Q2: 查無對應公司"],
        },
    },
}


@pytest.fixture(scope="module")
def mod(spark):  # 依賴 spark：api_period_col 用 F.*
    return load_cells(CHECK_NB, ["c02", "c03"], name="ircal_status")


def test_envelope_data_ok(mod):
    assert mod.envelope_data(STATUS_BODY)["tables"][0]["tableName"] == "app_company"


def test_envelope_data_accepts_info_key(mod):
    """實際系統把資料放在 info（規格寫的是 data），兩種都要能解析。"""
    body = {"success": True, "code": "OK", "message": "", "correlationId": "abc",
            "info": STATUS_BODY["data"]}
    assert mod.envelope_data(body)["tables"][0]["tableName"] == "app_company"
    # 完全沒有 envelope、整包就是資料的情況
    assert mod.envelope_data(STATUS_BODY["data"])["tables"][1]["rowCount"] == 450


def test_envelope_data_rejects_failure(mod):
    with pytest.raises(RuntimeError):
        mod.envelope_data({"success": False, "code": "E_AUTH", "message": "unauthorized"})
    with pytest.raises(ValueError) as e:      # 找不到資料物件時要把原文帶出來，才知道系統回了什麼
        mod.envelope_data({"success": True, "code": "OK", "message": "no data", "info": "not-a-dict"})
    assert "not-a-dict" in str(e.value)


def test_status_tables_normalises(mod):
    rows = mod.status_tables(mod.envelope_data(STATUS_BODY))
    assert [r["table"] for r in rows] == ["app_company", "app_ir_conference"]
    assert rows[1]["rows"] == 450 and rows[1]["api_hours"] == 27.0
    assert mod.status_tables({}) == []          # 沒有 tables[] 不能炸


def test_hours_since_honours_naive_timezone(mod):
    """不帶時區的字串照 naive_tz 解讀；帶時區的照原值。實測系統回的是台北時間。"""
    assert mod.hours_since("2026-09-21T00:30:00", NOW) == pytest.approx(27.0)                    # 預設 UTC
    assert mod.hours_since("2026-09-21T08:30:00", NOW, mod.TAIPEI) == pytest.approx(27.0)        # 台北
    assert mod.hours_since("2026-09-21T00:30:00Z", NOW, mod.TAIPEI) == pytest.approx(27.0)       # 有時區就不動
    assert mod.hours_since("2026-09-21T08:30:00+08:00", NOW) == pytest.approx(27.0)
    assert mod.hours_since(None, NOW) is None
    assert mod.hours_since("not-a-time", NOW) is None


def test_naive_tz_table(mod):
    assert mod.NAIVE_TZ_BY_NAME == {"taipei": mod.TAIPEI, "utc": mod.UTC}


def test_real_status_shape(mod):
    """系統實際回的形狀（envelope 用 info、時間是台北時間、小數秒 7 位）要吃得下。"""
    body = {
        "success": True, "code": 200, "message": None, "correlationId": "d1bc84",
        "info": {
            "tables": [
                {"tableName": "app_company", "rowCount": 176,
                 "lastUpdatedAt": "2026-09-22T09:10:04.93982", "hoursSinceLastUpdate": 5.308672087722222},
                {"tableName": "app_ir_conference", "rowCount": 9,
                 "lastUpdatedAt": "2026-09-22T09:11:41.653557", "hoursSinceLastUpdate": 5.2818071607777775},
            ],
            "lastConferencesBatch": {"executedAt": "2026-09-22T09:11:41.6535573", "success": True,
                                     "created": 9, "updated": 0, "unchanged": 0, "failed": 0,
                                     "failureSummaries": []},
        },
    }
    data = mod.envelope_data(body)
    assert [t["rows"] for t in mod.status_tables(data)] == [176, 9]
    now = datetime(2026, 9, 22, 6, 28, tzinfo=UTC)      # = 台北 14:28
    h = mod.hours_since("2026-09-22T09:10:04.93982", now, mod.TAIPEI)
    assert h == pytest.approx(5.3, abs=0.05)            # 與 API 的 5.3087 一致 → 系統時間是台北時間
    assert mod.hours_since("2026-09-22T09:10:04.93982", now, mod.UTC) == pytest.approx(h - 8, abs=0.05)
    assert mod.batch_stats(data["lastConferencesBatch"])["created"] == 9


def test_batch_stats(mod):
    s = mod.batch_stats(mod.envelope_data(STATUS_BODY)["lastConferencesBatch"])
    assert mod.fmt_stats(s) == "created=8 updated=3 unchanged=1 failed=1"
    assert s["failures"] == ["stockCode=2330, fiscalPeriod=Q2: 查無對應公司"]
    assert mod.batch_stats(None) == {}


@pytest.mark.parametrize(
    ("value", "quarter"),
    [("2026Q2", "Q2"), ("FY2026Q3", "Q3"), ("q4", "Q4"), ("Q1", "Q1"),
     ("FULL_YEAR", None), ("", None), (None, None)],
)
def test_fiscal_period_for_api_matches_consume(mod, value, quarter):
    """與 consume [c03] 的同名函式同值：兩邊不一致，[c12] 的對照就沒有意義。"""
    consume = load_cells(CONSUME_NB, ["c02", "c03"], name="ircal_consume")
    assert mod.fiscal_period_for_api(value, "quarter") == quarter
    assert mod.fiscal_period_for_api(value, "quarter") == consume.fiscal_period_for_api(value, "quarter")
    assert mod.fiscal_period_for_api(value, "null") is None
    assert mod.fiscal_period_for_api(value, "as_is") == value


def test_api_period_col_matches_python(mod, spark):
    """Column 版與 Python 版必須一致（[c12] 用 Column 版算期望列數，[c13] 用 Python 版顯示）。"""
    values = ["2026Q2", "FY2026Q3", "q4", "Q1", "FULL_YEAR", None]
    # 用 SQL VALUES 建表（不走 createDataFrame）：本機 pyspark 的 Python worker 不必啟動，測試比較穩。
    literals = ", ".join("(NULL)" if v is None else f"('{v}')" for v in values)
    df = spark.sql(f"SELECT * FROM VALUES {literals} AS t(fiscal_period)")
    for mode in ("quarter", "null", "as_is"):
        got = [r[0] for r in df.select(mod.api_period_col(df["fiscal_period"], mode)).collect()]
        assert got == [mod.fiscal_period_for_api(v, mode) for v in values], mode
