# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# ///
# DBTITLE 1,每週進數據概況報告
# MAGIC %md
# MAGIC # Meeting Record 每週進數據概況報告
# MAGIC
# MAGIC 追蹤以下兩張表的每週資料進入狀況，以 `create_date` 為基準：
# MAGIC
# MAGIC * `micenter.mi3_datahub_prod.b_internal_meeting_record`
# MAGIC * `micenter.mi3_datahub_prod.b_internal_meeting_record_scm`
# MAGIC
# MAGIC 涵蓋範圍：**過去完整 4 週 + 當下未完整的本週**。可隨時 Run All 取得最新概況。

# COMMAND ----------

# DBTITLE 1,b_internal_meeting_record 每週進數統計
# MAGIC %sql
# MAGIC WITH all_weeks AS (
# MAGIC   SELECT explode(
# MAGIC     sequence(
# MAGIC       date_trunc('week', current_date()) - INTERVAL 4 WEEKS,
# MAGIC       date_trunc('week', current_date()),
# MAGIC       INTERVAL 1 WEEK
# MAGIC     )
# MAGIC   ) AS week_start
# MAGIC ),
# MAGIC actual AS (
# MAGIC   SELECT
# MAGIC     date_trunc('week', create_date) AS week_start,
# MAGIC     COUNT(*) AS record_count
# MAGIC   FROM micenter.mi3_datahub_prod.b_internal_meeting_record
# MAGIC   WHERE create_date >= date_trunc('week', current_date()) - INTERVAL 4 WEEKS
# MAGIC   GROUP BY date_trunc('week', create_date)
# MAGIC )
# MAGIC SELECT
# MAGIC   w.week_start,
# MAGIC   date_add(w.week_start, 6) AS week_end,
# MAGIC   CASE
# MAGIC     WHEN w.week_start = date_trunc('week', current_date())
# MAGIC       THEN concat(date_format(w.week_start, 'M/d'), ' ~ ', date_format(current_date(), 'M/d'), ' (本周進行中)')
# MAGIC     ELSE concat(date_format(w.week_start, 'M/d'), ' ~ ', date_format(date_add(w.week_start, 6), 'M/d'))
# MAGIC   END AS week_label,
# MAGIC   COALESCE(a.record_count, 0) AS record_count
# MAGIC FROM all_weeks w
# MAGIC LEFT JOIN actual a ON w.week_start = a.week_start
# MAGIC ORDER BY w.week_start DESC

# COMMAND ----------

# DBTITLE 1,b_internal_meeting_record_scm 每週進數統計
# MAGIC %sql
# MAGIC WITH all_weeks AS (
# MAGIC   SELECT explode(
# MAGIC     sequence(
# MAGIC       date_trunc('week', current_date()) - INTERVAL 4 WEEKS,
# MAGIC       date_trunc('week', current_date()),
# MAGIC       INTERVAL 1 WEEK
# MAGIC     )
# MAGIC   ) AS week_start
# MAGIC ),
# MAGIC actual AS (
# MAGIC   SELECT
# MAGIC     date_trunc('week', create_date) AS week_start,
# MAGIC     COUNT(*) AS record_count
# MAGIC   FROM micenter.mi3_datahub_prod.b_internal_meeting_record_scm
# MAGIC   WHERE create_date >= date_trunc('week', current_date()) - INTERVAL 4 WEEKS
# MAGIC   GROUP BY date_trunc('week', create_date)
# MAGIC )
# MAGIC SELECT
# MAGIC   w.week_start,
# MAGIC   date_add(w.week_start, 6) AS week_end,
# MAGIC   CASE
# MAGIC     WHEN w.week_start = date_trunc('week', current_date())
# MAGIC       THEN concat(date_format(w.week_start, 'M/d'), ' ~ ', date_format(current_date(), 'M/d'), ' (本周進行中)')
# MAGIC     ELSE concat(date_format(w.week_start, 'M/d'), ' ~ ', date_format(date_add(w.week_start, 6), 'M/d'))
# MAGIC   END AS week_label,
# MAGIC   COALESCE(a.record_count, 0) AS record_count
# MAGIC FROM all_weeks w
# MAGIC LEFT JOIN actual a ON w.week_start = a.week_start
# MAGIC ORDER BY w.week_start DESC

# COMMAND ----------

# DBTITLE 1,每週進數據 Bar Chart
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['font.family'] = 'sans-serif'

sql_tpl = """
WITH all_weeks AS (
  SELECT explode(
    sequence(
      date_trunc('week', current_date()) - INTERVAL 4 WEEKS,
      date_trunc('week', current_date()),
      INTERVAL 1 WEEK
    )
  ) AS week_start
),
actual AS (
  SELECT date_trunc('week', create_date) AS week_start, COUNT(*) AS record_count
  FROM {table}
  WHERE create_date >= date_trunc('week', current_date()) - INTERVAL 4 WEEKS
  GROUP BY date_trunc('week', create_date)
)
SELECT
  CASE
    WHEN w.week_start = date_trunc('week', current_date())
      THEN concat(date_format(w.week_start,'M/d'),' ~ ',date_format(current_date(),'M/d'),' (ongoing)')
    ELSE concat(date_format(w.week_start,'M/d'),' ~ ',date_format(date_add(w.week_start,6),'M/d'))
  END AS week_label,
  COALESCE(a.record_count, 0) AS record_count
FROM all_weeks w LEFT JOIN actual a ON w.week_start = a.week_start
ORDER BY w.week_start
"""

tables = [
    ("micenter.mi3_datahub_prod.b_internal_meeting_record", "b_internal_meeting_record"),
    ("micenter.mi3_datahub_prod.b_internal_meeting_record_scm", "b_internal_meeting_record_scm"),
]

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

for ax, (fqn, short_name) in zip(axes, tables):
    df = spark.sql(sql_tpl.format(table=fqn)).toPandas()
    bars = ax.bar(df["week_label"], df["record_count"], color="#4A90D9", edgecolor="white")
    ax.set_title(short_name, fontsize=13, fontweight="bold", pad=10)
    ax.set_ylabel("record count")
    ax.set_xlabel("")
    ax.tick_params(axis="x", rotation=25, labelsize=9)
    for bar, val in zip(bars, df["record_count"]):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                str(val), ha="center", va="bottom", fontsize=11, fontweight="bold")
    ax.set_ylim(0, max(df["record_count"].max() * 1.3, 1))
    ax.spines[["top", "right"]].set_visible(False)

fig.suptitle("Meeting Record Weekly Ingestion Report", fontsize=15, fontweight="bold", y=1.02)
plt.tight_layout()
plt.show()

# COMMAND ----------

# DBTITLE 1,使用說明
# MAGIC %md
# MAGIC ---
# MAGIC ℹ️ 點擊 **Run All** 即可重新執行取得最新進數據概況。週次以週一為起始，本週顯示「本周進行中」表示該週尚未結束，數據可能持續增加。
