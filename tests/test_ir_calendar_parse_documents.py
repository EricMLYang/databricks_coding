# ruff: noqa: E501 - 測試資料照 ai_parse_document 實際 JSON 形狀，逐字保留比對齊寬度重要
"""ir_calendar_parse_documents 的純函式 cell 測試（[c02]～[c06]），並比對建表 notebook [c16]～[c18] 的 DDL 欄位。

ai_parse_document 的輸出用假 JSON（形狀依官方文件 2.0：document.pages / document.elements / error_status）。
"""

import json
import re
from datetime import datetime, timezone

import pytest
from nbload import ROOT, load_cells, nbtool
from pyspark.sql.types import StringType, StructField, StructType

PARSE_NB = "jobs/ir_calendar/parse_documents/notebook.ipynb"
INIT_NB = "jobs/ir_calendar/init_tables/notebook.ipynb"
UTC = timezone.utc  # noqa: UP017 - 本機 Python 3.10
T1 = datetime(2026, 9, 22, 1, 0, tzinfo=UTC)
T2 = datetime(2026, 9, 22, 2, 0, tzinfo=UTC)


@pytest.fixture(scope="module")
def mod(spark):  # 依賴 spark：cell 內的 F.* 要有 SparkContext
    return load_cells(PARSE_NB, ["c02", "c03", "c04", "c05", "c06"], name="irparse")


@pytest.fixture(scope="module")
def ddl_columns():
    """執行建表 notebook 的 [c02] 與 [c16]～[c18]，從 DDL 抓欄位名。"""
    nb = nbtool.load(str(ROOT / INIT_NB))
    ns = {"catalog": "c", "schema": "s", "domain": "ir_calendar"}
    for tag in ["c02", "c16", "c17", "c18"]:
        exec(nbtool.source_of(nb["cells"][nbtool.find(nb, tag)]), ns)
    out = {}
    for (layer, short), ddl in ns["DDLS"].items():
        body = ddl.split("(", 1)[1].rsplit("\n)", 1)[0]
        out[(layer, short)] = [m.group(1) for m in re.finditer(r"^\s{2}(\w+)\s+\w", body, re.M)]
    return out


# ---------- 測試資料 ----------

VP = "/Volumes/c/s/v/brand_customer/TCL-Electronics/TCL-Electronics_Q2CY26_Financial_Statements.pdf"
VP_PRES = "/Volumes/c/s/v/brand_customer/TCL-Electronics/TCL-Electronics_Q2CY26_Presentation.pdf"
VP_SUP = "/Volumes/c/s/v/supplier/Corning/Corning_Q2CY26_Press_Release.pdf"

DOC_FILE_ROWS = [
    # volume_path, file_name, company_key, company_slug, category, period, doc_kind, fiscal_label, sha256, bytes
    (VP, "TCL-Electronics_Q2CY26_Financial_Statements.pdf", "HK:1070", "TCL-Electronics", "CUSTOMER", "2026Q2", "Financial_Statements", None, "ae05", 467327),
    (VP_PRES, "TCL-Electronics_Q2CY26_Presentation.pdf", "HK:1070", "TCL-Electronics", "CUSTOMER", "2026Q2", "Presentation", None, "b001", 1000),
    (VP_SUP, "Corning_Q2CY26_Press_Release.pdf", "NYSE:GLW", "Corning", "SUPPLIER", "2026Q2", "Press_Release", "FY2026Q2", "c002", 2000),
]
DOC_FILE_SCHEMA = ("volume_path string, file_name string, company_key string, company_slug string, category string, "
                   "period string, doc_kind string, fiscal_label string, sha256 string, bytes long")

PAYLOAD_OK = {
    "document": {
        "pages": [{"id": 0}, {"id": 1}],
        "elements": [
            {"id": 0, "type": "section_header", "content": "Q2 2026 Results", "page_id": 0, "bbox": [{"coord": [1, 2, 3, 4], "page_id": 0}]},
            {"id": 1, "type": "text", "content": "Revenue grew 10%.", "page_id": 0},
            {"id": 2, "type": "figure", "content": "", "description": "Bar chart of revenue by segment", "page_id": 1},
            {"id": 3, "type": "table", "content": "| a | b |\n|---|---|\n| 1 | 2 |", "page_id": 1},
        ],
    },
    "metadata": {"version": "2.0", "id": "x", "file_metadata": {"pages": 2}},
    "error_status": None,
    "extra_future_field": {"ignored": True},
}
PAYLOAD_PARTIAL = {**PAYLOAD_OK, "error_status": [{"page_id": 1, "error_message": "timeout"}]}
PAYLOAD_NO_DOC = {"metadata": {"version": "2.0"}, "error_status": [{"error_message": "corrupted"}]}


def _work(row, attempt=0):
    vp, fn, ck, slug, cat, period, kind, label, sha, size = row
    return {"volume_path": vp, "sha256": sha, "file_name": fn, "company_key": ck, "company_slug": slug,
            "category": cat, "period": period, "doc_kind": kind, "fiscal_label": label, "bytes": size,
            "attempt": attempt}


@pytest.fixture(scope="module")
def df_docs(spark):
    return spark.createDataFrame(DOC_FILE_ROWS, schema=DOC_FILE_SCHEMA)


def _parsed_df(mod, spark, rows):
    """(row, attempt, payload_obj) → transform_parse_result 的輸入 → PARSE_SCHEMA 形狀。"""
    data = [{**mod.to_work(_work(r, a)), "payload": None if p is None else json.dumps(p, ensure_ascii=False)}
            for r, a, p in rows]
    schema = StructType([*mod.WORK_SCHEMA.fields, StructField("payload", StringType())])   # 不用 .add：會改到模組的 schema
    return mod.transform_parse_result(spark.createDataFrame(data, schema=schema), now=T1, job_run_id="run-1")


# ---------- [c03] 純函式 ----------


def test_parse_options_only_presentation_gets_figure_description(mod):
    assert mod.parse_options("Presentation") == {"version": "2.0", "descriptionElementTypes": "figure"}
    assert mod.parse_options("Financial_Statements") == {"version": "2.0"}
    assert mod.parse_options(None) == {"version": "2.0"}


def test_options_sql_is_sorted_and_escaped(mod):
    assert mod.options_sql({"version": "2.0", "descriptionElementTypes": "figure"}) == (
        "map('descriptionElementTypes', 'figure', 'version', '2.0')"
    )
    assert mod.options_sql({"k": "it's"}) == "map('k', 'it''s')"


def test_plan_chunks_groups_by_options_then_company(mod):
    work = [mod.to_work(_work(r)) for r in DOC_FILE_ROWS]
    chunks = mod.plan_chunks(work, chunk_size=10)
    # 兩種選項 → 兩組；同組內分類 / 公司排序
    assert [[w["volume_path"] for w in c] for c in chunks] == [[VP_PRES], [VP, VP_SUP]]
    assert all(len({w["options_key"] for w in c}) == 1 for c in chunks)
    assert [len(c) for c in mod.plan_chunks(work, chunk_size=1)] == [1, 1, 1]


def test_backoff_and_rate_limit_detection(mod):
    assert mod.backoff_seconds(1, False) == 30 and mod.backoff_seconds(2, False) == 60
    assert mod.backoff_seconds(1, True) == 120
    assert mod.is_rate_limit(Exception("HTTP 429 Too Many Requests"))
    assert not mod.is_rate_limit(Exception("file not found"))


def test_strip_dbfs(mod, spark):
    df = spark.createDataFrame([("dbfs:/Volumes/c/s/v/a.pdf",), ("/Volumes/c/s/v/b.pdf",)], "path string")
    assert [r[0] for r in df.select(mod.strip_dbfs(df.path)).collect()] == ["/Volumes/c/s/v/a.pdf", "/Volumes/c/s/v/b.pdf"]


# ---------- [c05] select_work ----------


def test_select_work_new_docs_when_bronze_empty(mod, spark, df_docs):
    empty = spark.createDataFrame([], schema=mod.PARSE_SCHEMA)
    out = mod.select_work(df_docs, empty).orderBy("volume_path").collect()
    assert [r.volume_path for r in out] == sorted([VP, VP_PRES, VP_SUP])
    assert all(r.attempt == 0 for r in out)
    assert out[0].asDict().keys() == set(mod.WORK_FIELDS) - {"options_key"}


def test_select_work_skips_success_retries_failed_until_max_attempts(mod, spark, df_docs):
    parsed = _parsed_df(mod, spark, [
        (DOC_FILE_ROWS[0], 0, PAYLOAD_OK),        # success → 跳過
        (DOC_FILE_ROWS[1], 1, None),              # failed，attempt 變 2 → 還可重試（max 3）
        (DOC_FILE_ROWS[2], 2, PAYLOAD_NO_DOC),    # failed，attempt 變 3 → 不再排入
    ])
    out = {r.volume_path: r for r in mod.select_work(df_docs, parsed, max_attempts=3).collect()}
    assert set(out) == {VP_PRES}
    assert out[VP_PRES].attempt == 2
    # 同鍵多列時只看最新一列：後來成功了就不再排
    later_ok = _parsed_df(mod, spark, [(DOC_FILE_ROWS[1], 2, PAYLOAD_OK)]).withColumn("parsed_at", mod.F.lit(T2))
    assert mod.select_work(df_docs, parsed.unionByName(later_ok), max_attempts=3).count() == 0


def test_select_work_filters_and_force(mod, spark, df_docs):
    parsed = _parsed_df(mod, spark, [(r, 0, PAYLOAD_OK) for r in DOC_FILE_ROWS])
    assert mod.select_work(df_docs, parsed).count() == 0
    out = mod.select_work(df_docs, parsed, categories=["SUPPLIER"], force=True).collect()
    assert [r.volume_path for r in out] == [VP_SUP] and out[0].attempt == 1   # force：attempt 沿用
    assert mod.select_work(df_docs, parsed, company_keys=["HK:1070"], doc_kinds=["Presentation"], force=True).count() == 1
    # 新版本檔（sha256 不同）視為沒解析過
    new_ver = spark.createDataFrame([(*DOC_FILE_ROWS[0][:8], "ff00", 5)], schema=DOC_FILE_SCHEMA)
    assert mod.select_work(new_ver, parsed).count() == 1


# ---------- [c05] transform_parse_result / failed_rows ----------


def test_transform_parse_result_status_and_counts(mod, spark):
    out = {r.volume_path: r for r in _parsed_df(mod, spark, [
        (DOC_FILE_ROWS[0], 0, PAYLOAD_OK),
        (DOC_FILE_ROWS[1], 1, PAYLOAD_PARTIAL),
        (DOC_FILE_ROWS[2], 0, PAYLOAD_NO_DOC),
    ]).collect()}
    ok, part, bad = out[VP], out[VP_PRES], out[VP_SUP]
    assert ok.status == "success" and ok.error is None and ok.attempt == 1
    assert ok.page_count == 2 and ok.element_count == 4
    assert ok.text_chars == len("Q2 2026 Results\n\nRevenue grew 10%.\n\nBar chart of revenue by segment\n\n| a | b |\n|---|---|\n| 1 | 2 |")
    assert json.loads(ok.payload) == PAYLOAD_OK                      # payload 原文不動
    assert ok.parse_options == '{"version": "2.0"}' and ok.parser_version == "2.0"
    assert ok.job_run_id == "run-1" and ok.parsed_at.astimezone(UTC) == T1   # collect 回本機時區的 naive datetime
    assert part.status == "partial" and part.attempt == 2 and "timeout" in part.error
    assert part.parse_options == '{"descriptionElementTypes": "figure", "version": "2.0"}'
    assert bad.status == "failed" and bad.page_count is None and bad.text_chars is None


def test_transform_parse_result_matches_schema_and_ddl(mod, spark, ddl_columns):
    df = _parsed_df(mod, spark, [(DOC_FILE_ROWS[0], 0, PAYLOAD_OK)])
    assert df.columns == [f.name for f in mod.PARSE_SCHEMA.fields] == ddl_columns[("bronze", "document_parse")]
    # 型別也要能塞回 PARSE_SCHEMA（append 到 Delta 時 schema 要相容）
    spark.createDataFrame(df.collect(), schema=mod.PARSE_SCHEMA).count()


def test_failed_rows_match_schema(mod, spark):
    chunk = [mod.to_work(_work(DOC_FILE_ROWS[1], attempt=1))]
    rows = mod.failed_rows(chunk, "boom " * 1000, now=T1, job_run_id=None)
    assert list(rows[0]) == [f.name for f in mod.PARSE_SCHEMA.fields]
    assert rows[0]["status"] == "failed" and rows[0]["attempt"] == 2 and rows[0]["payload"] is None
    assert len(rows[0]["error"]) == 2000
    r = spark.createDataFrame(rows, schema=mod.PARSE_SCHEMA).collect()[0]
    assert r.parse_options == '{"descriptionElementTypes": "figure", "version": "2.0"}'


# ---------- [c06] silver ----------


@pytest.fixture(scope="module")
def df_bronze(mod, spark):
    """三檔：一檔兩個版本（舊 failed、新 success）、一檔 partial、一檔 failed 無 payload。"""
    older = _parsed_df(mod, spark, [(DOC_FILE_ROWS[0], 0, PAYLOAD_NO_DOC)])
    newer = _parsed_df(mod, spark, [
        (DOC_FILE_ROWS[0], 1, PAYLOAD_OK),
        (DOC_FILE_ROWS[1], 0, PAYLOAD_PARTIAL),
        (DOC_FILE_ROWS[2], 0, None),
    ]).withColumn("parsed_at", mod.F.lit(T2))
    return older.unionByName(newer)


def test_transform_document_text_latest_per_doc(mod, df_bronze):
    out = {r.volume_path: r for r in mod.transform_document_text(df_bronze).collect()}
    assert set(out) == {VP, VP_PRES}                                   # failed 無 payload 的不進 silver
    assert out[VP].parse_status == "success" and out[VP].text_md.startswith("Q2 2026 Results\n\nRevenue")
    assert "Bar chart of revenue by segment" in out[VP].text_md         # 圖表用描述代替
    assert out[VP].text_chars == len(out[VP].text_md)
    assert out[VP_PRES].parse_status == "partial"


def test_transform_document_element_explodes_in_order(mod, df_bronze):
    out = [r for r in mod.transform_document_element(df_bronze).filter(mod.F.col("volume_path") == VP).orderBy("seq").collect()]
    assert [(r.element_id, r.seq, r.page_id, r.element_type) for r in out] == [
        (0, 0, 0, "section_header"), (1, 1, 0, "text"), (2, 2, 1, "figure"), (3, 3, 1, "table"),
    ]
    assert out[2].content == "" and out[2].description == "Bar chart of revenue by segment"
    assert out[0].category == "CUSTOMER" and out[0].company_key == "HK:1070"


def test_silver_transforms_match_ddl(mod, df_bronze, ddl_columns):
    """每張 silver 表：transform 輸出欄位 + updated_at == DDL 欄位（順序也一致）。"""
    for short, transform in mod.SILVER_TRANSFORMS.items():
        got = transform(df_bronze).columns + ["updated_at"]
        assert got == ddl_columns[("silver", short)], f"{short}: transform 與 DDL 欄位不一致"
        for k in mod.TABLE_KEYS[short]:
            assert k in got
    assert set(mod.SILVER_TRANSFORMS) == {s for (layer, s) in ddl_columns if layer == "silver"}
