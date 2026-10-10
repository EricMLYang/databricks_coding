# amsc_demo

- 用途：AMSC Genie Demo 的**一次性測試沙盒**。讀 Volume 上的 genie demo pack（Omdia 2Q26），建 6 張表、3 個 view、1 個 table function（全部 `amsc_` 開頭），檢核後給 Genie Space 用；`teardown=true` 時只拆除 `amsc_*` 物件。不是正式 MI DataHub 管線。
- 規劃：`PM_Head/projects/ForwardDeployedEngineer/15_experiments/MI/mi_datahub_table/amsc_demo/AMSC_Databricks_Genie_Demo_Plan.md`（v0.2 §4）
- 輸入：`{pack_dir}/manifest.yaml`（表名、欄位、型別、COMMENT、列數、檢核值都從這裡讀）、`data/*.csv`、`genie_space/amsc_views.sql`、`genie_space/genie_space.yaml`
- 輸出：`{catalog}.{schema}.amsc_fact_*` / `amsc_dim_*`（CREATE OR REPLACE + overwrite，全量重建）、`amsc_v_*`、`amsc_fn_client_supplier_mix`
- 參數（widgets）：`catalog`（micenter）、`schema`（mi3_datahub_dev）、`pack_dir`（`/Volumes/micenter/mi3_datahub_dev/test/amsc_demo`）、`teardown`（false / true）、`grant_group`（空 = 不 GRANT）、`sample_qids`（Q02,Q06,Q08）
- 排程：無，人工 Run All。serverless、job cluster 皆可（不用 cache）；需要 PyYAML（DBR 內建）。
- 負責人 / 更新日期：（填）/ 2026-10-10

## 注意

- **Omdia 授權資料**：pack 不進這個 repo；表只 GRANT 給 Demo 群組。
- 命名例外：沿用規劃的 `amsc_` 前綴（拆除時靠前綴辨識），不走 `docs/conventions.md` 2.1 的 `b_` / `s_` / `g_`。Demo 若要轉正式，依規劃 §9 重做管線。
- `mi3_datahub_dev` 是共用 schema：拆除只刪 `amsc_*`，**禁止 `DROP SCHEMA`**。

純函式測試：`tests/test_amsc_demo.py`（[c02]～[c03]）。
