# ruff: noqa: E501 - 貼進 Databricks cell 用的腳本，SQL 字串不折行
# [dev] 匯出一家公司一期的報告輸入包（貼回給 Agent 套模板測試用；不是 job 的一部分）
# 在 Databricks Python cell 執行（預設 SQL 的 notebook 第一行加 %python）。
# 印出的 JSON 形狀 = build_supplier_report [c09] load_company_bundle 的回傳：
#   {company, period, fin_rows, summary, conference, docs[{…, text_md}]}
# 文件全文每份截 MAX_DOC_CHARS 字、最多 MAX_DOCS 份；分段印避免單一輸出被截，貼回時把 BEGIN～END 整段接起來。
import json

CATALOG, SCHEMA = "micenter", "mi3_datahub_prod"
COMPANY_KEY, PERIOD = "TPE:1303", "2026Q2"      # ← 改成候選清單（HANDOFF §5 Cell A）選的
MAX_DOC_CHARS, MAX_DOCS = 20000, 3


def rows(sql):
    return [r.asDict(recursive=True) for r in spark.sql(sql).collect()]  # noqa: F821 - Databricks 全域 spark


T = f"{CATALOG}.{SCHEMA}.s_ir_calendar"
company = rows(f"SELECT * FROM {T}_company WHERE company_key = '{COMPANY_KEY}' ORDER BY updated_at DESC LIMIT 1")
fin = rows(f"SELECT * FROM {T}_financials WHERE company_key = '{COMPANY_KEY}' ORDER BY period")
summary = rows(f"SELECT * FROM {T}_summary WHERE company_key = '{COMPANY_KEY}' AND period = '{PERIOD}' "
               f"ORDER BY updated_at DESC LIMIT 1")
conf = rows(f"SELECT company_key, period, conference_date, conference_type, source, revision FROM {T}_conference "
            f"WHERE company_key = '{COMPANY_KEY}' AND period = '{PERIOD}' ORDER BY revision DESC LIMIT 1")
docs = rows(f"""
SELECT t.volume_path, t.file_name, t.doc_kind, t.sha256, t.fiscal_label, t.text_chars, t.page_count, t.parse_status,
       f.source_url, t.text_md
FROM {T}_document_text t LEFT JOIN {T}_document_file f ON f.volume_path = t.volume_path
WHERE t.company_key = '{COMPANY_KEY}' AND t.period = '{PERIOD}' AND t.parse_status IN ('success', 'partial')
ORDER BY CASE t.doc_kind WHEN 'Earnings_Transcript' THEN 0 WHEN 'Presentation' THEN 1 WHEN 'Press_Release' THEN 2 ELSE 3 END
LIMIT {MAX_DOCS}
""")
for d in docs:
    if d["text_md"] and len(d["text_md"]) > MAX_DOC_CHARS:
        d["text_md"] = d["text_md"][:MAX_DOC_CHARS] + "\n…（截尾）"
        d["truncated_for_export"] = True

bundle = {"company": company[0] if company else {"company_key": COMPANY_KEY}, "period": PERIOD,
          "fin_rows": fin, "summary": summary[0] if summary else None, "conference": conf[0] if conf else None,
          "docs": docs}
out = json.dumps(bundle, ensure_ascii=False, default=str)
print(f"company={bundle['company'].get('company_name')} fin_rows={len(fin)} summary={'有' if summary else '無'} "
      f"docs={len(docs)} json_chars={len(out)}")
print("=====BUNDLE_BEGIN=====")
for i in range(0, len(out), 60000):
    print(out[i:i + 60000])
print("=====BUNDLE_END=====")
