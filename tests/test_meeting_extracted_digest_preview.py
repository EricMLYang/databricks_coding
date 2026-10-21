"""meeting_extracted_digest_preview 的測試：[c02] 常數、[c03] 版面組裝與 md / HTML 輸出。

假資料虛構、已 token 化。
"""

from datetime import date

import pytest
from nbload import load_cells

NB = "jobs/meeting_record/meeting_extracted_digest_preview/notebook.ipynb"
NB_003 = "jobs/meeting_record/meeting_extracted_migration/003_meeting_semantic_lens.ipynb"


@pytest.fixture(scope="module")
def mod():
    return load_cells(NB, ["c02", "c03"], name="digest_preview")


def _row(key, **kw):
    base = {
        "item_key": key,
        "pk_seq": 1,
        "segment_no": 1,
        "category": "event",
        "category_rule": "event",
        "app": "MNT",
        "customer": "acer",
        "term": None,
        "summary": f"摘要 {key}",
        "quote": "原文",
        "date": date(2026, 9, 3),
        "source": "acer MNT Monthly 2026-09-03 — customer",
        "statement_type": "fact",
        "topic_tag_primary": "demand",
        "content_type": "inline_minutes",
        "sensitivity": "S1",
        "confidence": 0.8,
        "dup_key": None,
        "verified": None,
        "as_of": None,
    }
    return {**base, **kw}


def test_lens_cols_exist_in_003(mod):
    spec = load_cells(NB_003, ["c02", "c03", "c04"], name="mig003_for_digest")
    cols = {c[0] for c in spec.TABLES["g_meeting_items_sem_bu"]["columns"]}
    assert set(mod.LENS_COLS) <= cols
    assert set(mod.TOPIC_ORDER) == set(mod.TOPIC_ZH)


def test_helpers(mod):
    assert mod.subject_of("acer MNT Monthly 2026-09-03 — customer") == "acer MNT Monthly"
    assert mod.subject_of("主旨沒日期 — auo") == "主旨沒日期"
    assert mod.side_of("x 2026-09-03 — customer") == "客戶" and mod.side_of(None) == "—"
    assert mod.mmdd(date(2026, 9, 3)) == "09/03"


@pytest.fixture(scope="module")
def built(mod):
    rows = [
        _row("a1", pk_seq=1, date=date(2026, 9, 3)),
        _row(
            "a2",
            pk_seq=1,
            date=date(2026, 9, 10),
            statement_type="request",
            summary="<P07> 要求分享 SPEC，cc <G01>、<P99>",
        ),
        _row("a3", pk_seq=2, date=date(2026, 9, 12), dup_key="a1"),  # 同文重複，預設略去
        _row(
            "b1",
            pk_seq=2,
            topic_tag_primary="quality",
            sensitivity="S2",
            category="intel",
            category_rule="event",
        ),
        _row("c1", pk_seq=3, topic_tag_primary="engineering", confidence=0.4, summary="含 | 直線"),
    ]
    intel = [
        _row(
            "i1", category="intel", term="INX 轉產能", as_of="2026-Q3", verified="y", summary="框架"
        ),
        _row("s1", category="semantic", term="分貨 code", summary="定義", verified=None),
    ]
    cfg = {"customer": "acer", "app": "MNT", "max_per_topic": 1, "include_dups": False}
    labels = mod.token_labels(
        [
            {"pk_seq": 1, "token": "P07", "side": "customer", "company": "acer"},
            {"pk_seq": 1, "token": "G01", "side": "customer", "company": "acer"},
            {"pk_seq": 2, "token": "P07", "side": "auo", "company": "auo"},  # 別封信的 P07，不混
        ]
    )
    sections = mod.build_sections(rows, intel, cfg, "2026-09", labels)
    return sections, mod.render_md(sections), mod.render_html(sections)


def test_token_labels_and_resolve(mod):
    parts = [
        {"pk_seq": 1, "token": "P01", "side": "auo", "company": "auo"},
        {"pk_seq": 1, "token": "P02", "side": "customer", "company": "acer"},
        {"pk_seq": 1, "token": "P02", "side": None, "company": None},  # 同 token 第二列不覆蓋
        {"pk_seq": 1, "token": "P03", "side": "third_party", "company": "inx"},
        {"pk_seq": 1, "token": "P04", "side": "unknown", "company": None},
        {"pk_seq": 1, "token": "G01", "side": "customer", "company": "acer"},
    ]
    labels = mod.token_labels(parts)
    assert labels[(1, "P01")] == "AUO 方" and labels[(1, "P02")] == "客戶方（acer）"
    assert labels[(1, "P03")] == "第三方（inx）" and labels[(1, "P04")] == "與會者"
    assert labels[(1, "G01")] == "群組（acer）"
    assert mod.resolve_tokens("<P02> 要求 <P01> 回覆，cc <G01> 與 <P99>", 1, labels) == (
        "客戶方（acer）要求 AUO 方回覆，cc 群組（acer）與與會者"
    )  # 中文鄰字的空格拿掉；「要求 AUO 方」英文開頭留空格
    assert mod.resolve_tokens("<P01> 說明 roadmap，<P03> 回覆 OK", 1, labels) == (
        "AUO 方說明 roadmap，第三方（inx）回覆 OK"
    )
    assert mod.resolve_tokens("<P02> x", 2, labels) == "與會者 x"  # 別封信的 token 不混用
    assert mod.resolve_tokens("<P02> x", 1, None) == "<P02> x"
    assert mod.resolve_tokens(None, 1, labels) == ""


def test_sections_layout(mod, built):
    sections, _, _ = built
    kinds = [(s["title"][:2], s["kind"]) for s in sections]
    assert kinds[0][1] == "title" and [k for _, k in kinds[1:]] == [
        "kv",
        "bullets",
        "table",
        "table",
        "table",
        "table",
        "bullets",
    ]
    meta = dict(sections[1]["data"])
    assert meta["條目"].startswith("4 條（原始 5，同文重複 1 條已略去）")
    assert meta["來源信件"] == "3 封" and meta["S2 條目"].startswith("1 條")
    topic = sections[3]["data"]
    assert [r[0] for r in topic["rows"]] == [
        "需求 / 預測（2）",
        "品質（1）",
        "工程 / 驗證（1）",
    ]  # 商務在前
    assert topic["rows"][0][1] == [
        "09/03 摘要 a1（acer MNT Monthly）",
        "…另 1 條",
    ]  # max_per_topic = 1
    assert topic["rows"][0][2].startswith("（示意）")
    timeline = sections[4]["data"]
    assert timeline["rows"][0][:2] == ["09/03", "事實"]
    assert [r[:3] for r in timeline["rows"] if r[0] == "09/10"] == [
        ["09/10", "要求", "客戶方（acer）要求分享 SPEC，cc 群組（acer）、與會者"]
    ]  # D33：<Pnn> 顯示成陣營
    intel = sections[5]["data"]
    assert intel["rows"][0][0] == "口徑 / 定義" and intel["rows"][0][4] == "未審"  # semantic 排前
    assert intel["rows"][1][1:3] == ["2026-Q3", "INX 轉產能"] and intel["rows"][1][4] == "通過"
    review = {r[0]: r[1] for r in sections[6]["data"]["rows"]}
    assert "分類與先驗不同（event→intel）" in review["b1"] and "S2 敏感" in review["b1"]
    assert review["c1"] == "信心 0.4"


def test_render_md_and_html(mod, built):
    _, md, html_out = built
    assert md.startswith("# acer MNT 2026-09 會議紀錄 × Sales Brief 月報（版面草稿）\n")
    assert "## 3. 主題對照：會議 × Sales Brief" in md
    assert "| 需求 / 預測（2） | 09/03 摘要 a1（acer MNT Monthly）<br>…另 1 條 |" in md
    assert "含 \\| 直線" in md  # md 表格內的 | 要跳脫
    assert (
        "<h1>acer MNT 2026-09" in html_out
        and "<li>09/03 摘要 a1（acer MNT Monthly）</li>" in html_out
    )
    assert '<span class="ph">（示意）' in html_out and "含 | 直線" in html_out
    assert "<script" not in html_out


def test_include_dups_and_empty(mod):
    rows = [_row("a1"), _row("a2", dup_key="a1", summary="<b>x</b>")]
    cfg = {"customer": "", "app": "", "max_per_topic": 5, "include_dups": True}
    sections = mod.build_sections(rows, [], cfg, "2026-09")
    assert sections[0]["title"].startswith("全部客戶 全部應用 2026-09")
    assert dict(sections[1]["data"])["條目"].startswith("2 條（原始 2，同文重複 1 條已併入）")
    html_out = mod.render_html(sections)
    assert "&lt;b&gt;x&lt;/b&gt;" in html_out and "<b>x</b>" not in html_out  # HTML 跳脫
    assert "<p>（無）</p>" in html_out  # intel 表空
