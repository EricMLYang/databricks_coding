# ruff: noqa: E501 - 測試資料照爬蟲實際 JSON 形狀，逐字保留比對齊寬度重要
"""ir_calendar_consume_batches 的純函式 cell 測試（[c02]～[c06]），並比對建表 notebook 的 DDL 欄位。

測試資料的形狀照爬蟲實際產出（ir_calendar/out/ 下的 calendar、summaries、docs manifest、master、batches manifest）。
bronze 列用 [c05] bronze_row 組出、silver 用 [c06] 的 transform 在本機 pyspark 跑。
"""

import json
import re
from datetime import date, datetime, timezone

import pytest
from nbload import ROOT, load_cells, nbtool

CONSUME_NB = "jobs/ir_calendar/consume_batches/notebook.ipynb"
INIT_NB = "jobs/ir_calendar/init_tables/notebook.ipynb"
UTC = timezone.utc  # noqa: UP017 - 本機 Python 3.10
NOW = datetime(2026, 9, 21, 1, 0, tzinfo=UTC)


@pytest.fixture(scope="module")
def mod(spark):  # 依賴 spark：cell 內的 F.* 要有 SparkContext
    return load_cells(CONSUME_NB, ["c02", "c03", "c04", "c05", "c06"], name="ircal")


@pytest.fixture(scope="module")
def ddl_columns():
    """執行建表 notebook 的 [c02] 與 [c10]～[c15]（預先塞入 catalog 等變數），從 DDL 抓欄位名。"""
    nb = nbtool.load(str(ROOT / INIT_NB))
    ns = {"catalog": "c", "schema": "s", "domain": "ir_calendar"}
    for tag in ["c02", "c10", "c11", "c12", "c13", "c14", "c15"]:
        exec(nbtool.source_of(nb["cells"][nbtool.find(nb, tag)]), ns)
    out = {}
    for (layer, short), ddl in ns["DDLS"].items():
        body = ddl.split("(", 1)[1].rsplit("\n)", 1)[0]
        out[(layer, short)] = [m.group(1) for m in re.finditer(r"^\s{2}(\w+)\s+\w", body, re.M)]
    return out


# ---------- [c03] 純函式 ----------


def test_parse_listing_skips_parent_and_sort_links(mod):
    html = """
    <a href="../">Parent</a> <a href="?C=M;O=A">Name</a>
    <a href="000001_20260918T081002/">000001_20260918T081002/</a>
    <a href="000002_20260918T171003/">x</a> <a href="health.json">health.json</a>
    <a href="000002_20260918T171003/">dup</a> <a href="https://x/y/">abs</a>
    """
    assert mod.parse_listing(html) == [
        "000001_20260918T081002",
        "000002_20260918T171003",
        "health.json",
    ]


def test_pick_new_batches_sorted_and_filtered(mod):
    names = ["000003_20260919T081002", "junk", "000001_20260918T081002", "000002_20260918T171003"]
    assert mod.pick_new_batches(names, 1) == [
        (2, "000002_20260918T171003"),
        (3, "000003_20260919T081002"),
    ]


def test_check_prev_seq(mod):
    mod.check_prev_seq({"batch_id": "b", "prev_seq": None}, 0)
    mod.check_prev_seq({"batch_id": "b", "prev_seq": 4}, 4)
    with pytest.raises(mod.MissingBatch):
        mod.check_prev_seq({"batch_id": "b", "prev_seq": 5}, 4)


def test_volume_target_uses_manifest_fields_not_filename(mod):
    f = {
        "path": "docs/HK_1070/2026Q2/TCL-Electronics_Q2CY26_Presentation.pdf",
        "category": "CUSTOMER",
        "company_slug": "TCL-Electronics",
    }
    assert mod.volume_target("/Volumes/c/s/v", f) == (
        "/Volumes/c/s/v/brand_customer/TCL-Electronics/TCL-Electronics_Q2CY26_Presentation.pdf"
    )
    assert mod.volume_target("/Volumes/c/s/v", {"path": "docs/x/y/a.pdf"}) == (
        "/Volumes/c/s/v/uncategorized/_unknown_company/a.pdf"
    )


def test_is_stale_treats_naive_as_taipei(mod):
    now = datetime(2026, 9, 19, 0, 0, tzinfo=UTC)  # 台北 08:00
    assert not mod.is_stale("2026-09-18T15:57:01+08:00", now, 24)
    assert mod.is_stale("2026-09-17T15:57:01", now, 24)  # 視為台北時間，已超過 24h
    assert mod.is_stale(None, now, 24)


def test_endpoint_for_fallback(mod):
    f = {"path": "api/x.json", "endpoint": "ir-conferences/sync"}
    assert mod.endpoint_for(f) == "ir-conferences/sync"
    assert mod.endpoint_for({"path": "api/companies_sync.json"}) == "companies/sync"
    assert mod.endpoint_for({"path": "api/other.json"}) is None


@pytest.mark.parametrize(("mode", "value", "expected"), [
    ("quarter", "2026Q3", "Q3"),
    ("quarter", "FY2026Q3", "Q3"),
    ("quarter", "Q2", "Q2"),
    ("quarter", "q4", "Q4"),
    ("quarter", "2026上半年", None),      # 取不到季別就送 None，不亂猜
    ("quarter", None, None),
    ("null", "2026Q3", None),
    ("as_is", "2026Q3", "2026Q3"),
    ("as_is", None, None),
])
def test_fiscal_period_for_api(mod, mode, value, expected):
    assert mod.fiscal_period_for_api(value, mode) == expected


def test_fiscal_period_for_api_rejects_unknown_mode(mod):
    with pytest.raises(ValueError, match="api_fiscal_period"):
        mod.fiscal_period_for_api("2026Q3", "Q")


def _conf_payload():
    return {"batch_id": "000007_20260922T081002", "rows": [
        {"stockCode": "2409", "fiscalPeriod": "2026Q3", "conferenceDate": "2026-10-28"},
        {"stockCode": "3481", "fiscalPeriod": "FY2026Q3", "conferenceDate": "2026-10-29"},
        {"stockCode": "6116", "conferenceDate": "2026-11-04"},          # 沒這個欄位就不補
    ]}


@pytest.mark.parametrize(("mode", "sent"), [
    ("quarter", ["Q3", "Q3", "absent"]),
    ("null", [None, None, "absent"]),
    ("as_is", ["2026Q3", "FY2026Q3", "absent"]),
])
def test_apply_fiscal_period_rewrites_rows_only(mod, mode, sent):
    payload = _conf_payload()
    out, changed = mod.apply_fiscal_period(payload, mode)

    assert [r.get("fiscalPeriod", "absent") for r in out["rows"]] == sent
    assert out["rows"][0]["conferenceDate"] == "2026-10-28"             # 其他欄位照舊
    assert out["batch_id"] == payload["batch_id"]
    assert payload["rows"][0]["fiscalPeriod"] == "2026Q3"               # 原 body 不被改（bronze 收原文）
    assert changed == ({} if mode == "as_is" else {"2026Q3": sent[0], "FY2026Q3": sent[1]})


def test_apply_fiscal_period_passes_through_other_payloads(mod):
    company = {"rows": [{"stockCode": "2409", "companyName": "友達"}]}
    assert mod.apply_fiscal_period(company, "quarter") == (company, {})
    assert mod.apply_fiscal_period({"rows": []}, "null") == ({"rows": []}, {})
    assert mod.apply_fiscal_period({"data": 1}, "null") == ({"data": 1}, {})


# ---------- 測試資料（形狀照爬蟲實際產出）----------

CALENDAR_EVENT = {
    "record_type": "ir_conference", "company_key": "KRX:005930", "company_name": "三星電子",
    "english_name": "Samsung Electronics", "stock_code": "005930", "market": "KRX",
    "category": "PANEL_PEER", "period": "2026Q3", "fiscal_period": "Q3",
    "conference_date": "2026-10-28", "start_time": None, "end_time": None, "conference_type": None,
    "location": None, "meeting_link": None, "document_url": None, "status": "SCHEDULED",
    "importance": 5, "source": "SEED_ONETIME", "source_url": "https://x", "confidence": "CONFIRMED",
    "remark": "r", "recipients": [], "revision": 1, "crawled_at": "2026-08-30T10:42:25",
    "extra_field_from_future": "ignored",   # 爬蟲之後多的欄位：bronze 收、silver 忽略
}  # fmt: skip
SUMMARY = {
    "record_type": "ir_summary", "company_key": "HK:1070", "company_name": "TCL", "stock_code": "1070",
    "market": "HK", "category": "CUSTOMER", "period": "2026Q2", "fiscal_period": "Q2",
    "conference_date": "2026-08-28", "fallback": False, "recipients": ["A00"],
    "crawled_at": "2026-09-01T10:00:00+08:00",
    "summary": {"found": True, "core_points": ["a", "b"], "guidance": "g", "key_numbers": ["1"],
                "risks": ["x"], "notes": "n", "sources": [{"title": "t", "url": "u", "media": "m"}]},
}  # fmt: skip
DOC_FILE = {
    "path": "docs/HK_1070/2026Q2/TCL-Electronics_Q2CY26_Financial_Statements.pdf",
    "record_type": "ir_document_file", "sha256": "ae05", "bytes": 467327, "company_key": "HK:1070",
    "company_slug": "TCL-Electronics", "category": "CUSTOMER", "period": "2026Q2",
    "doc_kind": "Financial_Statements", "fiscal_label": None,
    "source_file": "financial_report_20260828_ae05c40e.pdf", "source_url": "https://x.pdf",
    "doc_date": "2026-08-28",
}  # fmt: skip
MASTER = {
    "record_type": "app_company", "generated_at": "2026-09-18T15:57:02", "count": 2,
    "rows": [
        {"company_key": "HK:1070", "company_name": "TCL", "english_name": "TCL Electronics",
         "stock_code": "1070", "market": "HK", "market_type": "LISTED", "category_name": "CUSTOMER",
         "industry": "品牌客戶(TV)", "website_url": "https://www.tcl.com", "ir_url": "https://ir",
         "aliases": ["TCL"], "recipients": ["A00"], "remark": None, "is_active": True,
         "profile_source": "人工", "file_slug": "TCL-Electronics"},
        {"company_key": "TPE:2353", "company_name": "宏碁", "english_name": "Acer Incorporated",
         "stock_code": "2353", "market": "TPE", "market_type": "LISTED", "category_name": "CUSTOMER",
         "industry": "電腦及週邊設備業", "website_url": None, "ir_url": None, "aliases": ["acer"],
         "recipients": ["A00"], "remark": None, "is_active": True, "profile_source": "x",
         "file_slug": "Acer"},
    ],
}  # fmt: skip
API_BODY = {"generatedAt": "2026-09-18T00:10:02Z", "rows": [{"stockCode": "005930"}]}


def _manifest(seq: int, batch_id: str, files: list[dict]) -> dict:
    return {
        "batch_id": batch_id, "seq": seq, "prev_seq": seq - 1 or None,
        "generated_at": "2026-09-18T08:10:02+08:00",
        "producer": {"mode": "daily_scan", "host": "gcp", "git_sha": "85f9bb0"}, "kind": "incremental",
        "counts": {"ir_conference": 1, "ir_document_file": 1}, "files": files,
    }  # fmt: skip


def _bronze_rows(mod) -> list[dict]:
    """兩批：第 1 批含場次 / 彙整 / 實體檔 / 主檔 / api；第 2 批同一場次的 revision 2 與同一檔案的新版本。"""
    m1 = _manifest(1, "000001_20260918T081002", [
        {"path": "calendar/2026-09-18_KRX005930_2026Q3.json", "record_type": "ir_conference",
         "company_key": "KRX:005930", "period": "2026Q3", "sha256": "s1", "bytes": 10},
        {"path": "summaries/2026-08-30_HK1070_2026Q2.json", "record_type": "ir_summary",
         "company_key": "HK:1070", "period": "2026Q2", "sha256": "s2", "bytes": 10},
        DOC_FILE,
        {"path": "master/company.json", "record_type": "app_company", "sha256": "s3", "bytes": 10},
        {"path": "api/ir_conferences_sync.json", "record_type": "api_payload", "sha256": "s4",
         "bytes": 10, "endpoint": "ir-conferences/sync", "rows": 1},
    ])  # fmt: skip
    ev2 = {**CALENDAR_EVENT, "revision": 2, "conference_date": "2026-10-29"}
    doc2 = {**DOC_FILE, "sha256": "ff00", "bytes": 5}
    m2 = _manifest(2, "000002_20260919T081002", [
        {"path": "calendar/2026-09-19_KRX005930_2026Q3.json", "record_type": "ir_conference",
         "company_key": "KRX:005930", "period": "2026Q3", "sha256": "s5", "bytes": 10},
        doc2,
    ])  # fmt: skip
    vp = "/Volumes/c/s/v/brand_customer/TCL-Electronics/TCL-Electronics_Q2CY26_Financial_Statements.pdf"
    js = mod.js
    return [
        mod.manifest_bronze_row(m1, now=NOW),
        mod.bronze_row(m1, m1["files"][0], js(CALENDAR_EVENT), volume_path=None, now=NOW),
        mod.bronze_row(m1, m1["files"][1], js(SUMMARY), volume_path=None, now=NOW),
        mod.bronze_row(m1, DOC_FILE, js(DOC_FILE), volume_path=vp, now=NOW),
        mod.bronze_row(m1, m1["files"][3], js(MASTER), volume_path=None, now=NOW),
        mod.bronze_row(m1, m1["files"][4], js(API_BODY), volume_path=None, now=NOW),
        mod.manifest_bronze_row(m2, now=NOW),
        mod.bronze_row(m2, m2["files"][0], js(ev2), volume_path=None, now=NOW),
        mod.bronze_row(m2, doc2, js(doc2), volume_path=vp, now=NOW),
    ]


@pytest.fixture(scope="module")
def df_bronze(mod, spark):
    return spark.createDataFrame(_bronze_rows(mod), schema=mod.BRONZE_SCHEMA)


# ---------- [c05] bronze / batch_log 列 ----------


def test_bronze_rows_match_schema(mod, df_bronze):
    rows = _bronze_rows(mod)
    fields = [f.name for f in mod.BRONZE_SCHEMA.fields]
    for r in rows:
        assert set(r) == set(fields)
    assert df_bronze.count() == 9
    types = {r["record_type"] for r in df_bronze.select("record_type").distinct().collect()}
    assert types == {
        "batch_manifest",
        "ir_conference",
        "ir_summary",
        "ir_document_file",
        "app_company",
        "api_payload",
    }
    # payload 是 JSON 全文，未登記的欄位也在
    p = json.loads(rows[1]["payload"])
    assert p["extra_field_from_future"] == "ignored"


def test_batch_log_row_and_schema(mod, spark):
    m = _manifest(3, "000003_20260920T081002", [DOC_FILE])
    api = mod.api_result(
        endpoint="ir-conferences/sync", idem_key="k", rows=3, http_status=200, now=NOW,
        body={"success": True, "data": {"success": True, "created": 1, "updated": 1, "unchanged": 1,
                                        "failed": 0, "failures": []}},
    )  # fmt: skip
    row = mod.batch_log_row(
        m, status="SUCCESS", landed=1, bronze_rows=2, api_results=[api], now=NOW
    )
    assert set(row) == {f.name for f in mod.BATCH_LOG_SCHEMA.fields}
    assert row["generated_at"] == datetime(2026, 9, 18, 0, 10, 2, tzinfo=UTC)
    df = spark.createDataFrame([row], schema=mod.BATCH_LOG_SCHEMA)
    got = df.collect()[0]
    assert got["api_results"][0]["created"] == 1 and got["api_results"][0]["failures_json"] == "[]"
    assert got["counts"] == {"ir_conference": 1, "ir_document_file": 1}


# ---------- [c04] 欄位 helper ----------


@pytest.mark.parametrize("session_tz", ["UTC", "Asia/Taipei", "America/New_York"])
def test_ts_col_is_session_timezone_independent(mod, spark, session_tz):
    """無時區字串視為台北；結果的 epoch 秒不隨 spark.sql.session.timeZone 改變。
    用 unix_timestamp 比較：collect() 回來的 naive datetime 會被轉成 driver 本機時區，不適合直接比。"""
    old = spark.conf.get("spark.sql.session.timeZone")
    spark.conf.set("spark.sql.session.timeZone", session_tz)
    try:
        df = spark.createDataFrame(
            [
                ("2026-08-30T10:42:25",),
                ("2026-09-15T07:59:25Z",),
                ("2026-09-18T15:57:01+08:00",),
                ("",),
                (None,),
            ],
            ["s"],
        )
        out = [
            r[0]
            for r in df.select(
                mod.F.unix_timestamp(mod.ts_col(mod.F.col("s"))).alias("e")
            ).collect()
        ]
        exp = [
            int(datetime(2026, 8, 30, 2, 42, 25, tzinfo=UTC).timestamp()),  # 無時區 → 台北 → UTC
            int(datetime(2026, 9, 15, 7, 59, 25, tzinfo=UTC).timestamp()),
            int(datetime(2026, 9, 18, 7, 57, 1, tzinfo=UTC).timestamp()),
            None,
            None,
        ]
        assert out == exp
    finally:
        spark.conf.set("spark.sql.session.timeZone", old)


def test_date_col_no_timezone_shift(mod, spark):
    df = spark.createDataFrame(
        [("2026-10-28",), ("2026-10-28T23:30:00+08:00",), ("",), (None,)], ["s"]
    )
    out = [r[0] for r in df.select(mod.date_col(mod.F.col("s")).alias("d")).collect()]
    assert out == [date(2026, 10, 28), date(2026, 10, 28), None, None]


# ---------- [c06] silver transform ----------


def test_transform_conference_keeps_every_revision(mod, df_bronze):
    out = mod.transform_conference(df_bronze).orderBy("revision").collect()
    assert [r["revision"] for r in out] == [1, 2]
    assert out[0]["conference_date"] == date(2026, 10, 28)
    assert out[1]["conference_date"] == date(2026, 10, 29)
    assert out[0]["importance"] == 5 and out[0]["recipients"] == []
    assert out[0]["batch_id"] == "000001_20260918T081002" and out[0]["seq"] == 1
    assert "extra_field_from_future" not in out[0].asDict()


def test_transform_summary(mod, df_bronze):
    r = mod.transform_summary(df_bronze).collect()[0]
    assert r["found"] is True and r["core_points"] == ["a", "b"]
    assert r["sources"][0]["media"] == "m"
    assert json.loads(r["summary_json"])["notes"] == "n"  # 原文保留
    assert r["fallback"] is False


def test_transform_document_file_latest_wins(mod, df_bronze):
    all_rows = mod.transform_document_file(df_bronze).collect()
    assert len(all_rows) == 2
    latest = mod.latest_per_key(
        mod.transform_document_file(df_bronze), mod.TABLE_KEYS["document_file"]
    ).collect()
    assert len(latest) == 1
    assert latest[0]["sha256"] == "ff00" and latest[0]["seq"] == 2
    assert latest[0]["file_name"] == "TCL-Electronics_Q2CY26_Financial_Statements.pdf"
    assert latest[0]["doc_date"] == date(2026, 8, 28)


def test_transform_company_explodes_rows(mod, df_bronze):
    out = {r["company_key"]: r for r in mod.transform_company(df_bronze).collect()}
    assert set(out) == {"HK:1070", "TPE:2353"}
    assert out["HK:1070"]["file_slug"] == "TCL-Electronics" and out["HK:1070"]["aliases"] == ["TCL"]
    assert out["TPE:2353"]["website_url"] is None


def test_silver_transforms_match_ddl(mod, df_bronze, ddl_columns):
    """每張 silver 表：transform 輸出欄位 + updated_at == DDL 欄位（順序也一致）。"""
    for short, transform in mod.SILVER_TRANSFORMS.items():
        got = transform(df_bronze).columns + ["updated_at"]
        assert got == ddl_columns[("silver", short)], f"{short}: transform 與 DDL 欄位不一致"
        for k in mod.TABLE_KEYS[short]:
            assert k in got


def test_bronze_schemas_match_ddl(mod, ddl_columns):
    assert [f.name for f in mod.BRONZE_SCHEMA.fields] == ddl_columns[("bronze", "record")]
    assert [f.name for f in mod.BATCH_LOG_SCHEMA.fields] == ddl_columns[("bronze", "batch_log")]
    assert set(mod.SILVER_TRANSFORMS) == {s for (layer, s) in ddl_columns if layer == "silver"}
