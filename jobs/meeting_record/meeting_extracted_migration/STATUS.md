# 會議紀錄萃取（meeting_extracted）現況與接手說明

> 最後更新：2026-10-15。給下一個接手的人或 Agent：**先讀完本檔再動手**。每完成一步就回來更新「進度」與「下一步」。

## 1. 這是什麼

把 `b_internal_meeting_record`（業務轉寄進來的會議紀錄信）清洗、去識別化、拆成原子條目，再對照 Sales Brief 填報。

- **規格（終點圖）**：PM_Head repo
  `projects/ForwardDeployedEngineer/15_experiments/MI/mi_datahub_table/ai_function_and_job_info/metting_record/01_meeting_to_sales_brief_進階規劃.md`（v0.4.1）。
  本檔只記**與規格不同的決定**與實際進度；規格沒被推翻的地方照規格做。
- 規格 §11.1「最小切片」決定 Phase 0–1 先做什麼；§2.3 規定 migration / 探勘 / 定期 Job 三類程式分開。

## 2. 檔案地圖

| 路徑 | 類別 | 說明 |
|---|---|---|
| `jobs/meeting_record/meeting_extracted_phase0_explore/` | Phase 0 探勘（一次性，已完成） | 只讀統計 notebook；`phase0_result.md` 是 2026-06-01～10-14 實跑結果（JSON） |
| `jobs/meeting_record/meeting_extracted_migration/` | 一次性 migration | 流水號 notebook，見本資料夾 `README.md`；**不得由 W1 / W2 呼叫** |
| `jobs/meeting_record/meeting_extracted_w1_*`（未建） | 定期 Job | 中立層週跑 T1-a → T1-m → T1-c → T1-b → T2 |
| `jobs/meeting_record/meeting_extracted_w2_*`（未建） | 定期 Job | Sales Brief 鏡頭月跑 T3 → T4 → T5 |
| `tests/test_meeting_extracted_*.py` | 本機測試 | 純函式 cell 測試 |

既有、與本案無關但同資料夾：`jobs/meeting_record/meeting_record_explore/`（看單封信原文，可用 pk_seq 查）、`meeting_record_weekly_report/`。

## 3. 已拍板的決定（偏離規格處，以此為準）

| # | 決定 | 取代規格的 |
|---|---|---|
| D1 | 資料夾一律放 `jobs/meeting_record/` 下、前綴 `meeting_extracted_` | §2.3 的 `migration/`、`phase0/`、`jobs/meeting_brief/`、`lib/` |
| D2 | **使用者只能把 notebook 內容複製貼上到 Databricks**，不能上傳檔案、不用 Git folder。設定、種子、詞表、prompt 一律內嵌在 notebook cell（CSV 格式字串或 Python 常數），本機用測試驗證內嵌內容合法 | §2.3 / §6 的 `config/*.yaml`、`prompts/*.md` |
| D3 | 共用純函式不另做 `lib/` 套件，放在各 notebook 的 cell | §2.3 `lib/` |
| D4 | `b_internal_meeting_record` **整表都算 BU**，不做單位過濾（主旨幾乎沒有 `[BU]` 標頭，部門代碼 14 種） | §6.8、`unit_filter.yaml` |
| D5 | 公司 / 別名對照表放 `micenter.mi3_datahub_prod.s_semantic_entity`、`s_semantic_entity_alias`（照 repo 命名慣例）；**不建在 `mi3_semantic`**（那只是 SemanticLayerPlan 預留位置、尚不存在）；不建 `b_` 層（種子即原始層） | §6.3 |
| D6 | `brief_month` 窗口：以 `g_sales_brief_market_intelligence` 每 app × 期別的 `max(submitted_at)` 為截止點（上期截止後～本期截止）。**必須可微調**：`window_mode`（submitted_at / calendar / fixed_day）、`grace_days`、個別 app × 期別 `overrides`；對照格記 `window_start / window_end` | §6.5 日曆月（待決 #3） |
| D7 | 待決 #1（三正文欄不一致）視為已解決：Phase 0 衝突 0%，pk 193 已確認三欄同一封信。一致性改抽樣 | §4.1 (a) 4 |
| D8 | LLM 費用不是限制；不需 Batch API 優化 | §10.1 |
| D9 | 公司種子（2026-10-15 使用者決定）：**Samsung 拆** `samsung_vd`（TV / MNT，Sales Brief 的 Samsung）與 `samsung`（非 VD / 分不出事業部；`samsung.com` 網域、素材只寫「Samsung / 三星」歸此）。**T3 規則：`customer = samsung` 且 `app ∈ {TV, MNT}` 視同 `samsung_vd`**。BenQ 與 Qisda **不合併**。`auodplus.com` 是集團子公司 → `entity_type = affiliate`、`side = auo`。LG `TV\|MNT`、BenQ `MNT`、Qisda `MNT`、Inventec `NB`、S-Core = Samsung SDS 子公司（partner）、Sumika = 住華（supplier）是推測值，使用者授權先用 | §6.3 初表 |
| D10 | 信件品質問題（38% 無 md、base64 圖片翻倍、23% 整封重複）**先在我們這邊做防呆**，不先找 ETL owner：T1-m 三個正文欄都套初洗、刪 base64、mail 層 `body_hash` 去重、`has_headers` 標記 | – |
| D11 | 中立層四張表 `CLUSTER BY (pk_seq)`，不做 partition；View 用 `CREATE OR REPLACE`，表改欄開新流水號 `ALTER TABLE ADD COLUMNS` | §3 型別由 Agent 定 |

## 4. Phase 0 結論（決定 T1 規則）

完整數字見 `../meeting_extracted_phase0_explore/phase0_result.md`。

| 發現 | 對設計的影響 |
|---|---|
| 量：6–9 月測試期 54 封；宣導後 10/1–10/12 已 436 封，持續增加 | 照正式量設計，不做 PoC 捷徑 |
| `mail_body_md` 非空只有 62%（規格門檻 80% 未過）；正文來源 md 286 / `mail_without_fw` 175 / `mail_body` 7 / 無 22 | `mail_without_fw` 是正式來源；它**沒有 From/To 標頭** → 這些信參與者只有轉寄人。要加 `has_headers` 欄。原因待問 ETL owner |
| md 來源中 92% 有 `**From:** / **Sent:**` 標頭；`Sent:` 日期 1,746 筆只有 2 筆解析失敗（含秒數格式） | 分段可行；T1-b 加 `MMMM d, yyyy h:mm:ss a` 格式；正規化要處理 U+00A0 |
| 粗估類型：紀要 257、未分類短信 153、noise 65、thread 13 | 信多半是給高層的紀要，往返少 → T1-b 以 ITEM 表頭 / 型號行分段為主 |
| md 超大：表格儲存格內 `data:image/...;base64,`，**每轉寄一次圖片數翻倍**（4→8→…→64）；`mail_body` 超大是大量 `[文字](網址)` 連結 | T1-m 初洗加：刪 base64 圖片、連結縮成文字 |
| `mail_without_fw` 也有 Word 殘渣（`Normal / DocumentEmail / EN-US …`） | 規格 §4.1 (b) 規則 2 改為三個正文欄都套 |
| 整封正文完全相同 23%；segment 重複 17.8%，同段最多出現 9 封 | 需要 **mail 層**（展示表 `body_hash / dup_of_pk`）與 segment 層（`content_hash / dup_of`）兩層去重 |
| 40.6% 的信對不到已知客戶；新網域 lge / benq / qisda / inventec / s-core / sumika | 已補進 001 種子；關卡持續列出對不到的網域 |
| 頂層 `mail_to / mail_cc / mail_bcc` 全空 | 參與者只能從 `mail_from` 與正文標頭解析 |
| Sales Brief：`brand_code` 實際值 MNT `Asus/Dell/HP/Samsung`、NB `Acer/Asus/Dell/HP/Lenovo/MSI`、TV `Hisense/Samsung/TCL/TPV`；四面向 = `summary_futureOutlook / techProduct / pricing / otherInfo`（brand 與 app summary 表都有）；`market_intelligence` 的 `field_key` 同四值 | 待決 #10 解決；facet 對照 market_outlook / product_tech / price / other |
| 沒有部門代碼對照表 | `dept_name` 先 NULL（待決 #13） |

## 5. 進度

| 步驟 | 狀態 |
|---|---|
| Phase 0 探勘 | ✅ 完成（2026-10-14） |
| `001_semantic_entity` v1（公司 20、別名 68） | ✅ 2026-10-14 已在 Databricks 正式執行；無重複、無孤兒 |
| `001_semantic_entity` v2（公司 21、別名 72；D9 的種子） | ✅ 2026-10-15 已在 Databricks 正式執行（entity insert 1 / update 8、alias insert 4 / update 4；無重複、無孤兒） |
| `002_meeting_neutral_tables` | ✅ 2026-10-15 已在 Databricks 正式執行：4 表（33 / 34 / 19 / 35 欄）＋ 3 View（38 / 7 / 28 欄）建立，[c30] 無 PROBLEM |
| W1（T1-a～T2） | ⬜ |
| L1 prompt | ⬜ |
| golden set | ⬜（需 PM 標註） |
| W2（T3～T5） | ⬜ |

## 6. 下一步

### 6.1 使用者端（Databricks）

（001 v2、002 皆已執行，無待辦。）

### 6.2 W1 第一支：`meeting_extracted_w1_t1`（T1-a ～ T1-c，規則、無 LLM）

寫入 002 建的 `s_meeting_record_mail_bu`、`s_meeting_participants_bu`、`s_meeting_record_clean_bu`。先純函式＋測試，再接 Spark：

- T1-a 取數：`is_test = false`、`create_date` 水位（`run_mode = incremental / backfill`）。
- T1-m 初洗（D10）：來源選擇 md → `mail_without_fw` → `mail_body`；三欄都套規則 1–3；刪 `data:image/...;base64,`、`![…](cid:…)`、Word 殘渣、免責聲明；`[文字](網址)` 縮成文字；`has_headers`；`body_hash = sha1(normalize(body_display))` → `dup_of_pk`（命中較早 pk）；`oversize`。
- T1-c 參與者：`mail_from` 四段 → forwarder（`P01`）；md `**From:** / **To:** / **Cc:**` 標頭 → 人與群組；email 網域後綴比對 `s_semantic_entity_alias`（`alias_type = email_domain`）→ `side / company`；關卡列出對不到的網域。
- T1-b 分段與 token 化：`-----Original Message-----` / `**From:**` 切 thread；ITEM 表頭 / 型號行切紀要；`**Sent:**` 解析含 `MMMM d, yyyy h:mm:ss a`、處理 U+00A0；`display_start / end`；token 化後算 `content_hash` → `dup_of`。
- `cleaner_version = "0.1"`；W1 第一個 task 做 §2.4 的一致性檢查（別名表涵蓋近 90 天網域）。

### 6.3 之後

1. L1 prompt（規格 §5.1）內嵌成 cell 常數；附錄 A 當 few-shot；T2 寫 `g_meeting_items_bu`（`item_key`、`supersedes_item_id`、quote 必須是 `clean_text` 子字串）。
2. golden set 模板，請 PM 標。
3. 003 migration：Sales Brief 鏡頭表（§3.4、§3.5）、`v_meeting_participants_q` column mask、分應用 View。

## 7. 待使用者回覆

- **部門代碼名稱**（待決 #13）：使用者 2026-10-15 決定**先不提供**（名稱可能變動），`dept_name` 一律 NULL，不擋流程。Phase 0 轉寄人部門代碼 14 種，依封數：`DTDBB0` 183、`DTDAB0` 93、`DTDDC0` 71、`DTDBA0` 69、`DTDDB0` 28、`DTDAA0` 18、`DNB000` 11、`ABSBA0` 7、`DITA00` 4、`DNBAC0` 2、`DNBBF0` 1、`DTDCA0` 1、`DGMA0A` 1、`DTVAB0` 1。之後要填再開 003 建 `s_meeting_dept_code`（種子內嵌，形式同 001）。
- （已答）Samsung 拆 VD / 非 VD、BenQ 與 Qisda 分開、auodplus 為集團子公司 → D9；其餘推測值先用。
- （已答）信件品質問題先在我們這邊防呆 → D10；需要再去向 ETL owner 說明。

## 8. 開發注意事項

- 本機測試用 `py -3.10 -m pytest`（預設 python 3.13 會 worker crash）；本機 pyspark 3.5、Databricks 是 Spark 4.0。
- 改 `.ipynb` 用 `py -3.10 tools/nb.py`，**不要用 sed 改 notebook JSON**。含 `\n`、`\uXXXX` 的程式碼先寫成檔案再 `nb.py set <nb> <tag> <file>`；在這台機器上 shell heredoc 會把跳脫轉成實際字元。
- `pyproject.toml` 讓 ruff 排除 `*.ipynb`；明確傳 notebook 路徑給 ruff 會報 `dbutils / spark` 未定義，屬正常。
- 使用者在 serverless 跑：不用 `.cache()` / `persist`。
- 隱私：`s_meeting_record_mail_bu`、`s_meeting_participants_bu` 以外的表與 View 不得出現姓名、email、工號；**外部公司人員資訊不進 repo**（含測試資料、結果檔、本檔）。Phase 0 類輸出只回傳統計、網域、AUO 部門代碼。
- commit 前 `py -3.10 tools/nb.py strip <nb>`。
