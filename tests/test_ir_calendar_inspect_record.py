# ruff: noqa: E501 - 測試資料一筆一行，比對齊寬度好讀
"""ir_calendar_inspect_record 的純函式 cell 測試（[c02]～[c03]）：排版與兩份 markdown 報告。"""

from datetime import date, datetime, timezone

import pytest
from nbload import load_cells

NB = "jobs/ir_calendar/inspect_record/notebook.ipynb"
UTC = timezone.utc  # noqa: UP017 - 本機 Python 3.10


@pytest.fixture(scope="module")
def mod():
    return load_cells(NB, ["c02", "c03"], name="irinspect")


SUMMARY = {
    "company_key": "TPE:2353", "company_name": "宏碁", "stock_code": "2353", "market": "TPE",
    "category": "CUSTOMER", "period": "2026Q2", "fiscal_period": "Q2",
    "conference_date": date(2026, 8, 12), "fallback": False, "found": True,
    "core_points": ["營收年增 5%", "  ", None], "guidance": "Q3 持平", "key_numbers": [], "risks": None,
    "notes": "期別對應正常",
    "sources": [{"title": "法說簡報", "url": "https://x/1.pdf", "media": "公司官網"}, {"title": None, "url": None, "media": None}],
    "summary_json": '{"found": true}', "crawled_at": datetime(2026, 8, 12, 10, 0, tzinfo=UTC),
}


def test_clip_and_one_line(mod):
    assert mod.clip(None, 5) == ""
    assert mod.clip("abc", 5) == "abc"
    assert mod.clip("abcdef", 3).startswith("abc …（共 6 字")
    assert mod.one_line("a\r\nb", 50) == "a ⏎ b"


def test_fmt_value_and_dump_row(mod):
    assert mod.fmt_value(None) == "NULL"
    assert mod.fmt_value(date(2026, 1, 2)) == "2026-01-02"
    assert mod.fmt_value(["重點"]) == '["重點"]'
    out = mod.dump_row("t", {"a": 1, "long_key": None, "text_md": "x"}, skip=("text_md",))
    assert out.splitlines() == ["===== t =====", "  a        = 1", "  long_key = NULL"]


def test_pretty_json(mod):
    assert mod.pretty_json(None) == "NULL"
    assert mod.pretty_json("not json") == "not json"
    assert mod.pretty_json('{"a":"中"}') == '{\n  "a": "中"\n}'


def test_summary_report(mod):
    md = mod.summary_report(SUMMARY)
    assert md.startswith("## 宏碁（TPE:2353）2026Q2 法說彙整")
    assert "| 法說日期 | 2026-08-12（台北日期） |" in md
    assert "| 以財報新聞稿替代 | 否 |" in md
    assert "- 營收年增 5%" in md and "- None" not in md       # 空白 / None 重點被濾掉
    assert md.count("- （無）") == 2                            # key_numbers 空陣列、risks NULL
    assert "1. 法說簡報（公司官網） https://x/1.pdf" in md
    assert "2. (無標題)" in md


def test_summary_report_all_null(mod):
    md = mod.summary_report({})
    assert "| 找到法說內容 | — |" in md and "### 備註" not in md


def test_element_line_uses_description_for_figure(mod):
    line = mod.element_line({"seq": 3, "page_id": 0, "element_type": "figure", "content": "", "description": "長條圖"}, 50)
    assert "p1" in line and "figure" in line and "[圖表描述] 長條圖" in line
    assert "p—" in mod.element_line({"seq": 1, "page_id": None, "element_type": "text", "content": "x"}, 50)


def test_document_report(mod):
    doc = {"file_name": "Acer_Q2CY26_Presentation.pdf", "volume_path": "/Volumes/c/s/v/a.pdf", "company_key": "TPE:2353",
           "period": "2026Q2", "doc_kind": "Presentation", "bytes": 2048, "page_count": 10, "element_count": 50,
           "text_chars": 12345, "parse_status": "success", "parser": "ai_parse_document", "parser_version": "2.0"}
    md = mod.document_report(doc, {"text": 30, "table": 5, "figure": 5}, [{"content": "營運概況", "page_id": 1}],
                             [{"element_type": "text", "content": "第一段", "page_id": 0}], n=100)
    assert "| 頁數 / 元素數 / 全文字數 | 10 / 50 / 12,345 |" in md
    assert "| 檔案大小 | 2 KB |" in md
    assert md.index("- text：30") < md.index("- figure：5") < md.index("- table：5")   # 筆數降冪、同數依名稱
    assert "- 營運概況（p2）" in md and "- p1 text：第一段" in md


def test_document_report_empty(mod):
    md = mod.document_report({"volume_path": "/v/x"}, {}, [], [])
    assert "element 表沒有這份文件" in md and "沒有 title / section_header" in md


def test_table_name(mod):
    cfg = {"catalog": "micenter", "schema": "mi3_datahub_prod", "domain": "ir_calendar"}
    assert mod.table_name(cfg, "silver", "summary") == "micenter.mi3_datahub_prod.s_ir_calendar_summary"
