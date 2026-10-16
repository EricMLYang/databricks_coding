"""meeting_extracted_w1_t2_extract 的測試。

[c02]～[c05] 純 Python（prompt 組裝、LLM 回覆解析、後處理驗證），
[c07] 用本機 Spark 跑段落選取 / 流水號 / supersedes。
測試資料全是虛構（假 token、假 entity_id、example 網域）；不打 LLM（[c06] 不載入），
LLM 回覆用手寫 JSON 模擬。
"""

import json
from datetime import date, datetime

import pytest
from nbload import load_cells

NB = "jobs/meeting_record/meeting_extracted_w1_t2_extract/notebook.ipynb"
NB_CLEAN = "jobs/meeting_record/meeting_extracted_w1_t1_clean/notebook.ipynb"
NB_002 = "jobs/meeting_record/meeting_extracted_migration/002_meeting_neutral_tables.ipynb"


@pytest.fixture(scope="module")
def mod():
    return load_cells(NB, ["c02", "c03", "c04", "c05", "c07"], name="w1t2")


@pytest.fixture(scope="module")
def clean_mod():
    return load_cells(NB_CLEAN, ["c02", "c03"], name="w1t1b_for_t2")


@pytest.fixture(scope="module")
def specs():
    return load_cells(NB_002, ["c02", "c03", "c04"], name="mig002_for_t2")


CLEAN_TEXT = (
    "<P02>:\nSent: 2026-08-13 10:00\nSubject: RE: M270QAN06.A spec\n\n"
    "AUO Model Name: M270QAN06.A | Interface: 4ch LVDS | MP: Jan'27\n"
    "量產出貨VLRR不良目前603 ppm，TCL要求400 dppm以下。\n"
    "8/27 已提供終簽。下次會議 9/10。"
)
SEG = {
    "pk_seq": 7,
    "segment_no": 2,
    "sub_no": 0,
    "unit": "bu",
    "create_date": datetime(2026, 8, 14, 8),
    "mail_date": date(2026, 8, 14),
    "subject_clean": "M270QAN06.A spec",
    "segment_date": date(2026, 8, 13),
    "date_inferred": False,
    "content_type": "thread_reply",
    "parties": ["acer.example", "auo.com"],
    "customer_hint": "acer",
    "app_hint": "MNT",
    "clean_text": CLEAN_TEXT,
    "clean_len": len(CLEAN_TEXT),
    "cleaner_version": "0.1",
}
PK_TOKENS = {
    "P01": {"side": "auo", "company": "auo", "kind": "person", "is_forwarder": True},
    "P02": {"side": "customer", "company": "acer", "kind": "person", "is_forwarder": False},
    "P03": {"side": "auo", "company": "auo", "kind": "person", "is_forwarder": False},
    "G01": {"side": "customer", "company": "acer", "kind": "group", "is_forwarder": False},
}
PARTS = [
    {
        "kind": "person",
        "token": "P02",
        "display_name_raw": "Amy Wang 王小美",
        "name_zh": "王小美",
        "name_en": "Amy Wang",
    },
    {
        "kind": "group",
        "token": "G01",
        "display_name_raw": "MNT PM",
        "name_zh": None,
        "name_en": None,
    },
    {
        "kind": "person",
        "token": "P03",
        "display_name_raw": "Li",
        "name_zh": "李",
        "name_en": "Li",
    },  # 太短不算
]
ALIASES = [
    ("acer", "acer"),
    ("Acer", "acer"),
    ("TCL", "tcl"),
    ("Samsung", "samsung"),
    ("Samsung VD", "samsung_vd"),
    ("VD", "samsung_vd"),
    ("三星", "samsung"),
]


def _ctx(mod, **kw):
    exact, ordered = mod.build_alias_index(ALIASES)
    ctx = {
        "pk_tokens": PK_TOKENS,
        "s3_patterns": mod.name_patterns_of(PARTS),
        "alias_exact": exact,
        "alias_ordered": ordered,
        "prompt_version": "0.1",
        "model": "test-model",
        "nnn_offset": 0,
    }
    ctx.update(kw)
    return ctx


def _item(**kw):
    base = {
        "statement_type": "fact",
        "speaker_token": "P02",
        "speaker_side": "auo",
        "customer_raw": "acer",
        "app": "MNT",
        "app_basis": "model_prefix",
        "model_nos": ["M270QAN06.A"],
        "topic_tags": ["spec"],
        "free_tags": ["LVDS"],
        "summary": "<P02> 說明 M270QAN06.A 用 4ch LVDS，MP Jan'27",
        "quote": "Interface: 4ch LVDS | MP: Jan'27",
        "event_date": "2026-08-13",
        "date_basis": "segment_header",
        "time_refs": [{"when": "2027-01", "what": "MP"}],
        "numbers": [],
        "terms_mentioned": ["MP"],
        "confidence": 0.9,
    }
    base.update(kw)
    return base


# ---------- [c03] shared ----------
def test_shared_functions_match_clean_notebook(mod, clean_mod):
    for s in ["  Ａ B ", "Hello, World!", "量產 603 ppm"]:
        assert mod.normalize_text(s) == clean_mod.normalize_text(s)
        assert mod.norm_space(s) == clean_mod.norm_space(s)
        assert mod.sha1_hex(s) == clean_mod.sha1_hex(s)


# ---------- [c04] prompt ----------
def test_prompt_constants(mod):
    assert mod.PROMPT_VERSION_IN_CELL == "0.2"
    assert "【人名（嚴格）】" in mod.SYSTEM_PROMPT_L1
    sp = mod.SYSTEM_PROMPT_L1
    assert 6_000 < len(sp) < 20_000
    for t in mod.TOPIC_TAGS:
        assert t in sp
    for t in mod.STATEMENT_TYPES:
        assert t in sp
    assert "segment_note" in sp and "items" in sp
    assert not mod.EMAIL_ANY_RE.search(sp)


def test_user_prompt_has_tokens_but_no_names(mod):
    up = mod.build_user_prompt(SEG, PK_TOKENS)
    assert "- P01: auo / auo（轉寄人，不是發言人）" in up
    assert "- P02: customer / acer" in up
    assert "- G01: 群組，customer / acer（不是發言人）" in up
    assert "thread 標頭 Sent:" in up and "2026-08-13" in up
    assert CLEAN_TEXT in up
    assert not mod.EMAIL_ANY_RE.search(up)
    assert mod.s3_hits([up], mod.name_patterns_of(PARTS)) == 0
    up2 = mod.build_user_prompt(dict(SEG, date_inferred=True, content_type="inline_minutes"), {})
    assert "以信件日期代替" in up2 and "沒有解析到參與者" in up2


# ---------- [c05] parse ----------
def test_parse_llm_json_tolerates_fences_and_prose(mod):
    good = {"segment_note": "", "items": [_item()]}
    assert mod.parse_llm_json(json.dumps(good, ensure_ascii=False))[0] == good
    assert mod.parse_llm_json("```json\n" + json.dumps(good) + "\n```")[0] == good
    assert mod.parse_llm_json("以下是結果：\n" + json.dumps(good) + "\n以上。")[0] == good
    assert mod.parse_llm_json("")[1] == "empty response"
    assert mod.parse_llm_json("not json")[1] == "no JSON object found"
    assert "invalid JSON" in mod.parse_llm_json('{"items": [}')[1]
    assert "items" in mod.parse_llm_json('{"foo": 1}')[1]
    too_many = {"items": [_item()] * (mod.MAX_ITEMS_PER_SEGMENT + 1)}
    assert "too many" in mod.parse_llm_json(json.dumps(too_many))[1]


def test_quote_in_text_ignores_whitespace_and_width(mod):
    assert mod.quote_in_text("Interface:4chLVDS", CLEAN_TEXT)
    assert mod.quote_in_text("量產出貨 VLRR 不良目前 603 ppm", CLEAN_TEXT)
    assert mod.quote_in_text("ＴＣＬ要求400 dppm以下", CLEAN_TEXT)  # 全形 → NFKC
    assert not mod.quote_in_text("TCL 要求 300 dppm", CLEAN_TEXT)
    assert not mod.quote_in_text("", CLEAN_TEXT) and not mod.quote_in_text(None, CLEAN_TEXT)
    # 第三層：LLM 抄 quote 時清掉 md 殘渣 / 改標點，字沒變就算過
    text = "Allocation : 1****月23K, 2月25K ;** **限簽100K + 50K ~~ 實際cost在估算中 | MP: Jan'27"
    assert mod.quote_in_text("Allocation：1月23K，2月25K；限簽100K+50K", text)
    assert mod.quote_in_text("實際 cost 在估算中, MP Jan 27", text)
    assert not mod.quote_in_text("Allocation 1月33K", text)
    # 「…」/「...」串接片段：每片依序要找到；短片段不計；逆序不算
    assert mod.quote_in_text("1月23K ... 限簽100K … 實際cost在估算中", text)
    assert not mod.quote_in_text("限簽100K ... 1月23K", text)
    assert not mod.quote_in_text("1月23K ... 這句沒有", text)
    assert mod.quote_in_text("...", text) is False


def test_item_key_stable_and_sensitivity(mod):
    k1 = mod.item_key_of(7, 2, "TCL要求400 dppm以下")
    assert k1 == mod.item_key_of(7, 2, " TCL 要求 400 dppm 以下。") and k1 != mod.item_key_of(
        7, 3, "TCL要求400 dppm以下"
    )
    assert mod.item_id_of("bu", 7, 2, 0, 3) == "BU-MTG-7-2-0-003"
    assert mod.sensitivity_of("TCL 要求 400 dppm 以下") == "S2"
    assert mod.sensitivity_of("請採購先備 10K 原材") == "S2"
    assert mod.sensitivity_of("Allocation 5 月 50K") == "S2"
    assert mod.sensitivity_of("2026 BP 方向未定") == "S1"
    assert mod.sensitivity_of("改用 SMK AG25 偏光板") == "S0"
    assert mod.sensitivity_of("OK 可以") == "S0"  # 單獨的 K 不算


def test_normalize_customer(mod):
    exact, ordered = mod.build_alias_index(ALIASES)
    assert mod.normalize_customer("acer", exact, ordered) == "acer"
    assert mod.normalize_customer("Acer Inc.", exact, ordered) == "acer"
    assert mod.normalize_customer("Samsung VD", exact, ordered) == "samsung_vd"
    assert mod.normalize_customer("三星 VD 事業部", exact, ordered) == "samsung_vd"  # 長別名先吃
    assert mod.normalize_customer("Samsung", exact, ordered) == "samsung"
    assert mod.normalize_customer("vd", exact, ordered) == "samsung_vd"  # 精確可以短
    assert mod.normalize_customer("DVD player", exact, ordered) is None  # 短別名不做包含比對
    assert mod.normalize_customer(None, exact, ordered) is None
    # [c21] 別名表更新後補對：只回傳對得上的，None / 重複略過
    assert mod.renormalize_customers(
        ["acer", "unknownco", None, "Samsung VD", "acer"], exact, ordered
    ) == {"acer": "acer", "Samsung VD": "samsung_vd"}


def test_resolve_speaker(mod):
    assert mod.resolve_speaker("P02", PK_TOKENS) == ("P02", "customer", None)
    assert mod.resolve_speaker("<p03>", PK_TOKENS) == ("P03", "auo", None)
    assert mod.resolve_speaker(None, PK_TOKENS) == (None, None, None)
    assert mod.resolve_speaker("P01", PK_TOKENS) == (None, None, "forwarder")
    assert mod.resolve_speaker("G01", PK_TOKENS) == (None, None, "group")
    assert mod.resolve_speaker("P09", PK_TOKENS) == (None, None, "unknown_token")
    assert mod.resolve_speaker("Amy", PK_TOKENS) == (None, None, "unknown_token")


def test_name_patterns_and_s3_mask(mod):
    pats = mod.name_patterns_of(
        PARTS + [{"kind": "person", "token": "P05", "name_en": "Will Chen"}]
    )
    # 長的先換（同長度照字串排）；群組與太短的不算；英文名首字另成一條（區分大小寫）
    assert [
        (rx.pattern.count(r"[\s\-_.]*") + 1 if "A-Za-z0-9" in rx.pattern else 0, repl)
        for rx, repl in pats
    ] == [
        (0, "<P02>"),  # Amy Wang 王小美（含中文 → 子字串）
        (2, "<P05>"),  # Chen, Will
        (2, "<P02>"),  # Wang, Amy
        (2, "<P05>"),  # Will Chen
        (2, "<P02>"),  # Amy Wang
        (1, "<P05>"),  # Will（首字）
        (1, "<P02>"),  # Amy（首字）
        (0, "<P02>"),  # 王小美
    ]
    assert mod.s3_mask("<P02> 說明規格", pats) == ("<P02> 說明規格", 0)
    assert mod.s3_mask("王小美 說明規格", pats) == ("<P02> 說明規格", 1)
    assert mod.s3_mask("聯絡 amy@acer.example", pats) == ("聯絡 <email>", 1)
    assert mod.s3_mask("wang, amy 回覆", pats) == ("<P02> 回覆", 1)  # 全名不分大小寫
    assert mod.s3_mask("Amy Wang 王小美 與 Amy 同意", pats) == (
        "<P02> 與 <P02> 同意",
        2,
    )  # 長的先換，不留半截
    assert mod.s3_mask("分享給 MNT 成員（Amy, Juno）", pats) == (
        "分享給 MNT 成員（<P02>, Juno）",
        1,
    )
    assert mod.s3_mask("we are willing to; AMY; maximum", pats) == (
        "we are willing to; AMY; maximum",
        0,
    )  # 首字區分大小寫、整字
    assert mod.s3_mask("Will 確認 Amy-Wang 的 Samsung", pats) == ("<P05> 確認 <P02> 的 Samsung", 2)
    assert mod.s3_mask(None, pats) == (None, 0) and mod.s3_mask("王小美", pats) == ("<P02>", 1)
    assert mod.s3_hits(["王小美 說", None, "x@y.example"], pats) == 2
    # 沒有 token 的參與者列 → <P00>，不會漏遮
    assert mod.s3_mask(
        "Bob Lee 到", mod.name_patterns_of([{"kind": "person", "name_en": "Bob Lee"}])
    ) == ("<P00> 到", 1)


# ---------- [c05] build_item_rows ----------
def test_build_item_rows_ok_and_normalization(mod):
    resp = {
        "segment_note": "",
        "items": [
            _item(),
            _item(
                statement_type="Request",
                speaker_token=None,
                speaker_side="customer",
                customer_raw="TCL",
                app="tv",
                app_basis="bogus",
                model_nos=[],
                topic_tags=["Quality", "not_a_tag"],
                free_tags=["VLRR"],
                summary="TCL 要求 VLRR 不良降到 400 dppm 以下",
                quote="TCL要求400 dppm以下",
                event_date="2026/8/13",
                date_basis="segment_header",
                time_refs="oops",
                numbers=[{"value": 400}],
                confidence=1.7,
            ),
            _item(
                speaker_token="P01",
                summary="轉寄人附註",
                quote="8/27 已提供終簽",
                event_date="2026-08-27",
                date_basis="inline_date",
                topic_tags=["price"],
                confidence=0.5,
            ),
        ],
    }
    rows, st = mod.build_item_rows(resp, None, SEG, _ctx(mod))
    assert [r["item_id"] for r in rows] == [
        "BU-MTG-7-2-0-001",
        "BU-MTG-7-2-0-002",
        "BU-MTG-7-2-0-003",
    ]
    assert (
        st["items"] == 3 and st["ok"] == 3 and st["failed_schema"] == 0 and st["failed_quote"] == 0
    )
    r0, r1, r2 = rows
    assert (
        r0["extract_status"] == "ok"
        and r0["speaker_token"] == "P02"
        and r0["speaker_side"] == "customer"
    )
    assert r0["customer"] == "acer" and r0["app"] == "MNT" and r0["event_month"] == "2026-08"
    assert r0["item_key"] == mod.item_key_of(7, 2, r0["quote"]) and r0["sensitivity"] == "S0"
    assert r0["time_refs"] == '[{"when": "2027-01", "what": "MP"}]' and r0["confidence"] == 0.9
    assert (
        r0["prompt_version"] == "0.1"
        and r0["model"] == "test-model"
        and r0["cleaner_version"] == "0.1"
    )
    assert r0["superseded"] is False and r0["supersedes_item_id"] is None
    # 第二條：大小寫 / 無效 app_basis / 無效 tag / 壞日期 / confidence 夾限 / 無發言人上限 0.7
    assert r1["statement_type"] == "request" and r1["app"] == "TV" and r1["app_basis"] == "unknown"
    assert r1["topic_tags"] == ["quality"] and r1["topic_tag_primary"] == "quality"
    assert r1["free_tags"] == ["not_a_tag", "VLRR"] and st["tags_moved"] == 1
    assert (
        r1["customer"] == "tcl" and r1["speaker_token"] is None and r1["speaker_side"] == "customer"
    )
    assert (
        r1["event_date"] == date(2026, 8, 13)
        and r1["date_basis"] == "segment_header"
        and st["date_fallback"] == 1
    )
    assert r1["time_refs"] == "[]" and r1["numbers"] == '[{"value": 400}]'
    assert r1["confidence"] == 0.7 and r1["sensitivity"] == "S2"
    # 第三條：轉寄人不得當發言人 → token NULL、side 用 LLM 的、confidence 上限
    assert (
        r2["speaker_token"] is None
        and r2["speaker_side"] == "auo"
        and st["speaker_dropped"] == {"forwarder": 1}
    )
    assert r2["event_date"] == date(2026, 8, 27) and r2["date_basis"] == "inline_date"


def test_build_item_rows_failures(mod):
    resp = {
        "segment_note": "",
        "items": [
            _item(quote="這句不在正文裡"),
            _item(statement_type="wish"),
            _item(summary="王小美 說 MP 延後"),
            _item(quote="聯絡 amy@acer.example"),
            "not an object",
            _item(summary="分享給 MNT 成員（Amy, Juno）"),
        ],
    }
    rows, st = mod.build_item_rows(resp, None, SEG, _ctx(mod, nnn_offset=5))
    assert [r["item_id"][-3:] for r in rows] == ["006", "007", "008", "009", "010", "011"]
    # S3 命中改遮罩不作廢（D26）：姓名 → <Pnn>、email → <email>，條目保留
    assert [r["extract_status"] for r in rows] == [
        "failed_quote",
        "failed_schema",
        "ok",
        "failed_quote",
        "failed_schema",
        "ok",
    ]
    assert st == {
        **st,
        "items": 6,
        "ok": 2,
        "failed_schema": 2,
        "failed_quote": 2,
        "s3": 3,
        "s3_masked": 3,
    }
    assert (
        rows[0]["summary"] and rows[0]["quote"] == "這句不在正文裡" and rows[0]["s3_masked"] == 0
    )  # failed_quote 保留內容供調 prompt
    assert rows[2]["summary"] == "<P02> 說 MP 延後" and rows[2]["s3_masked"] == 1
    assert rows[3]["quote"] == "聯絡 <email>" and rows[3]["s3_masked"] == 1
    assert rows[5]["summary"] == "分享給 MNT 成員（<P02>, Juno）" and rows[5]["s3_masked"] == 1
    pats = mod.name_patterns_of(PARTS)
    assert not any(mod.s3_hits([r["summary"], r["quote"]], pats) for r in rows)
    # quote 裡的稱呼被換成 token 後仍要能對上正文（正文已 token 化的情況）
    resp = {"segment_note": "", "items": [_item(quote="Amy Wang: Sent: 2026-08-13 10:00")]}
    seg = {**SEG, "clean_text": "<P02>: Sent: 2026-08-13 10:00\n其餘"}
    rows, st = mod.build_item_rows(resp, None, seg, _ctx(mod))
    assert rows[0]["extract_status"] == "ok" and rows[0]["quote"] == "<P02>: Sent: 2026-08-13 10:00"
    assert rows[0]["item_key"] == mod.item_key_of(7, 2, rows[0]["quote"])


def test_build_item_rows_empty_and_segment_failure(mod):
    rows, st = mod.build_item_rows(
        {"segment_note": "只有會議行政", "items": []}, None, SEG, _ctx(mod)
    )
    assert (
        len(rows) == 1
        and rows[0]["extract_status"] == "empty"
        and rows[0]["item_id"] == "BU-MTG-7-2-0-000"
    )
    assert rows[0]["summary"] == "只有會議行政" and st["empty"] == 1 and st["items"] == 0
    rows, st = mod.build_item_rows(None, "invalid JSON: x", SEG, _ctx(mod, nnn_offset=2))
    assert (
        len(rows) == 1
        and rows[0]["extract_status"] == "failed_schema"
        and rows[0]["item_id"] == "BU-MTG-7-2-0-003"
    )
    assert rows[0]["summary"].startswith("[L1 failed] invalid JSON") and st["failed_schema"] == 1
    # segment_note 含姓名 → 換成 token 再落表
    rows, st = mod.build_item_rows(
        {"segment_note": "王小美 寒暄", "items": []}, None, SEG, _ctx(mod)
    )
    assert rows[0]["summary"] == "<P02> 寒暄" and rows[0]["s3_masked"] == 1 and st["s3"] == 1


def test_merge_stats(mod):
    tot = mod.merge_stats({}, {"items": 2, "speaker_dropped": {"group": 1}})
    tot = mod.merge_stats(tot, {"items": 3, "speaker_dropped": {"group": 2, "forwarder": 1}})
    assert tot == {"items": 5, "speaker_dropped": {"group": 3, "forwarder": 1}}


# ---------- [c07] Spark ----------
@pytest.fixture(scope="module")
def items_schema(specs, spark):
    return spark.createDataFrame([], specs.schema_ddl(specs.TABLES["g_meeting_items_bu"])).schema


@pytest.fixture(scope="module")
def clean_schema(specs, spark):
    return spark.createDataFrame(
        [], specs.schema_ddl(specs.TABLES["s_meeting_record_clean_bu"])
    ).schema


def _seg_row(schema, **kw):
    base = {
        "pk_seq": 1,
        "segment_no": 1,
        "sub_no": 0,
        "unit": "bu",
        "mail_date": date(2026, 9, 1),
        "content_type": "thread_reply",
        "dup_of": None,
        "cleaner_version": "0.1",
        "clean_text": "x",
        "clean_len": 1,
    }
    base.update(kw)
    return tuple(base.get(f.name) for f in schema.fields)


def _item_row(schema, **kw):
    base = {
        "item_id": "BU-MTG-1-1-0-001",
        "item_key": "k1",
        "pk_seq": 1,
        "segment_no": 1,
        "sub_no": 0,
        "unit": "bu",
        "extract_status": "ok",
        "superseded": False,
        "prompt_version": "0.1",
        "cleaner_version": "0.1",
        "model_nos": [],
        "topic_tags": [],
        "free_tags": [],
        "terms_mentioned": [],
    }
    base.update(kw)
    return tuple(base.get(f.name) for f in schema.fields)


def test_select_batch_segments(mod, spark, clean_schema, items_schema):
    clean = spark.createDataFrame(
        [
            _seg_row(clean_schema, pk_seq=1, segment_no=1),  # 已萃過（同版本）
            _seg_row(clean_schema, pk_seq=1, segment_no=2),  # 只有舊 prompt 的條目 → 重萃
            _seg_row(clean_schema, pk_seq=1, segment_no=3, dup_of="1-1-0"),  # 重複段不送
            _seg_row(clean_schema, pk_seq=2, segment_no=1, content_type="noise"),  # 不可萃取
            _seg_row(
                clean_schema, pk_seq=3, segment_no=1, cleaner_version="0.2"
            ),  # 清洗版本變了 → 重萃
            _seg_row(clean_schema, pk_seq=4, segment_no=1),  # 上次 failed_schema
            _seg_row(clean_schema, pk_seq=5, segment_no=1),  # 上次 empty
            _seg_row(clean_schema, pk_seq=6, segment_no=1),  # 全新
            _seg_row(
                clean_schema, pk_seq=7, segment_no=1
            ),  # 有 ok 也有 failed_quote → retry_failed 才重打
        ],
        clean_schema,
    )
    items = spark.createDataFrame(
        [
            _item_row(items_schema, item_id="A", pk_seq=1, segment_no=1),
            _item_row(items_schema, item_id="B", pk_seq=1, segment_no=2, prompt_version="0.0"),
            _item_row(items_schema, item_id="C", pk_seq=3, segment_no=1, cleaner_version="0.1"),
            _item_row(
                items_schema, item_id="D", pk_seq=4, segment_no=1, extract_status="failed_schema"
            ),
            _item_row(items_schema, item_id="E", pk_seq=5, segment_no=1, extract_status="empty"),
            _item_row(
                items_schema, item_id="F", pk_seq=6, segment_no=1, superseded=True
            ),  # 已 superseded 不算
            _item_row(items_schema, item_id="G", pk_seq=7, segment_no=1),
            _item_row(
                items_schema, item_id="H", pk_seq=7, segment_no=1, extract_status="failed_quote"
            ),
        ],
        items_schema,
    )
    got = sorted(
        (r.pk_seq, r.segment_no)
        for r in mod.select_batch_segments(clean, items, "0.1", False).collect()
    )
    assert got == [(1, 2), (3, 1), (6, 1)]
    got = sorted(
        (r.pk_seq, r.segment_no)
        for r in mod.select_batch_segments(clean, items, "0.1", True).collect()
    )
    assert got == [(1, 2), (3, 1), (4, 1), (6, 1), (7, 1)]


def test_segment_offsets_and_supersedes(mod, spark, items_schema):
    items = spark.createDataFrame(
        [
            _item_row(
                items_schema,
                item_id="BU-MTG-1-1-0-001",
                item_key="k1",
                pk_seq=1,
                segment_no=1,
                prompt_version="0.0",
            ),
            _item_row(
                items_schema,
                item_id="BU-MTG-1-1-0-002",
                item_key="k2",
                pk_seq=1,
                segment_no=1,
                prompt_version="0.0",
            ),
            _item_row(
                items_schema,
                item_id="BU-MTG-1-1-0-003",
                item_key="k2",
                pk_seq=1,
                segment_no=1,
                prompt_version="0.0",
                extract_status="failed_quote",
            ),
            _item_row(
                items_schema, item_id="BU-MTG-9-1-0-001", item_key="k1", pk_seq=9, segment_no=1
            ),  # 別段，同 key 不算
        ],
        items_schema,
    )
    new = spark.createDataFrame(
        [
            _item_row(
                items_schema, item_id="BU-MTG-1-1-0-004", item_key="k1", pk_seq=1, segment_no=1
            ),
            _item_row(
                items_schema, item_id="BU-MTG-1-1-0-005", item_key="k9", pk_seq=1, segment_no=1
            ),
            _item_row(
                items_schema,
                item_id="BU-MTG-1-1-0-006",
                item_key="k2",
                pk_seq=1,
                segment_no=1,
                extract_status="failed_quote",
            ),
            _item_row(
                items_schema, item_id="BU-MTG-2-1-0-001", item_key="k1", pk_seq=2, segment_no=1
            ),
        ],
        items_schema,
    )
    off = {
        (r.pk_seq, r.segment_no, r.sub_no): r.nnn_max
        for r in mod.segment_offsets(items, new).collect()
    }
    assert off == {(1, 1, 0): 3}
    out = mod.with_supersedes(new, items)
    assert out.columns == items_schema.fieldNames()
    got = {r.item_id: r.supersedes_item_id for r in out.collect()}
    assert got == {
        "BU-MTG-1-1-0-004": "BU-MTG-1-1-0-001",
        "BU-MTG-1-1-0-005": None,
        "BU-MTG-1-1-0-006": None,
        "BU-MTG-2-1-0-001": None,
    }
