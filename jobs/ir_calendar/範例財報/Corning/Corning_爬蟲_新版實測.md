company_key = NYSE:GLW, period = 2026Q2, 檔案數 = 6

====================================================================================================
[ir_conference] calendar/2026-07-28_NYSEGLW_2026Q2.json  (batch dev_20261021T103341)
{
  "record_type": "ir_conference",
  "company_key": "NYSE:GLW",
  "company_name": "Corning Incorporated",
  "english_name": "Corning",
  "stock_code": "GLW",
  "market": "NYSE",
  "category": "SUPPLIER",
  "period": "2026Q2",
  "fiscal_period": "2026Q2",
  "source_fiscal_period": null,
  "conference_date": "2026-07-28",
  "start_time": null,
  "end_time": null,
  "time_basis": "LOCAL_DATE_ONLY",
  "local_timezone": "America/New_York",
  "local_conference_date": "2026-07-28",
  "local_start_time": null,
  "local_end_time": null,
  "conference_type": null,
  "location": null,
  "meeting_link": null,
  "document_url": null,
  "status": "SCHEDULED",
  "importance": 5,
  "source": "DEV_SAMPLE",
  "source_url": null,
  "confidence": null,
  "remark": "[當地日 2026-07-28（America/New_York），時間未知，台北日可能為隔日]",
  "recipients": [
    "A00"
  ],
  "revision": 0,
  "crawled_at": "2026-10-21T10:33:41+08:00"
}

====================================================================================================
[ir_document] docs/NYSE_GLW/2026Q2/manifest.json  (batch dev_20261021T103341)
{
  "record_type": "ir_document",
  "company_key": "NYSE:GLW",
  "company_name": "Corning Incorporated",
  "stock_code": "GLW",
  "market": "NYSE",
  "category": "SUPPLIER",
  "period": "2026Q2",
  "fiscal_period": "2026Q2",
  "conference_date": "2026-07-28",
  "local_conference_date": "2026-07-28",
  "status": "DONE",
  "wanted": [
    "presentation",
    "financial_report"
  ],
  "missing": [],
  "files": [
    {
      "type": "financial_report",
      "file": "financial_report_20260729_8ec64114.htm",
      "path": "docs/NYSE_GLW/2026Q2/financial_report_20260729_8ec64114.htm",
      "source": "EDGAR",
      "source_url": "https://www.sec.gov/Archives/edgar/data/24741/000002474126000255/glw-20260630.htm",
      "title": "10-Q filing 2026-07-29",
      "doc_date": "2026-07-29",
      "sha256": "8ec64114a483e82d5216eb4b5787c141f4e3ea3613f5000eb899d2f8cf8f0ef6",
      "bytes": 1754476,
      "fetched_at": "2026-10-21T10:28:09+08:00"
    },
    {
      "type": "presentation",
      "file": "presentation_20260728_c1c96c78.htm",
      "path": "docs/NYSE_GLW/2026Q2/presentation_20260728_c1c96c78.htm",
      "source": "EDGAR",
      "source_url": "https://www.sec.gov/Archives/edgar/data/24741/000002474126000253/glw-20260728xex99xq22026.htm",
      "title": "8-K EX-99 2026-07-28",
      "doc_date": "2026-07-28",
      "sha256": "c1c96c78837d73fff5706a7768b48b9f1b39fef47622c39b7b0a534127eaa729",
      "bytes": 682724,
      "fetched_at": "2026-10-21T10:28:10+08:00"
    }
  ],
  "generated_at": "2026-10-21T10:33:42+08:00"
}

====================================================================================================
[ir_document_file] docs/NYSE_GLW/2026Q2/Corning_Q2CY26_Financial_Statements.htm  (batch dev_20261021T103341)
實體檔：C:\Users\local_18060116\Temp\claude\C--Users-1806011-Projects-PM-Head-projects-MI-Crawler\dc1912fb-8cf2-4ebd-aefd-77450a8d4f13\scratchpad\ircal_sandbox\out\docs\NYSE_GLW\2026Q2\financial_report_20260729_8ec64114.htm
{
  "path": "docs/NYSE_GLW/2026Q2/Corning_Q2CY26_Financial_Statements.htm",
  "record_type": "ir_document_file",
  "sha256": "8ec64114a483e82d5216eb4b5787c141f4e3ea3613f5000eb899d2f8cf8f0ef6",
  "bytes": 1754476,
  "company_key": "NYSE:GLW",
  "company_slug": "Corning",
  "category": "SUPPLIER",
  "period": "2026Q2",
  "doc_kind": "Financial_Statements",
  "fiscal_label": null,
  "source_file": "financial_report_20260729_8ec64114.htm",
  "source_url": "https://www.sec.gov/Archives/edgar/data/24741/000002474126000255/glw-20260630.htm",
  "doc_date": "2026-07-29"
}

====================================================================================================
[ir_document_file] docs/NYSE_GLW/2026Q2/Corning_Q2CY26_Presentation.htm  (batch dev_20261021T103341)
實體檔：C:\Users\local_18060116\Temp\claude\C--Users-1806011-Projects-PM-Head-projects-MI-Crawler\dc1912fb-8cf2-4ebd-aefd-77450a8d4f13\scratchpad\ircal_sandbox\out\docs\NYSE_GLW\2026Q2\presentation_20260728_c1c96c78.htm
{
  "path": "docs/NYSE_GLW/2026Q2/Corning_Q2CY26_Presentation.htm",
  "record_type": "ir_document_file",
  "sha256": "c1c96c78837d73fff5706a7768b48b9f1b39fef47622c39b7b0a534127eaa729",
  "bytes": 682724,
  "company_key": "NYSE:GLW",
  "company_slug": "Corning",
  "category": "SUPPLIER",
  "period": "2026Q2",
  "doc_kind": "Presentation",
  "fiscal_label": null,
  "source_file": "presentation_20260728_c1c96c78.htm",
  "source_url": "https://www.sec.gov/Archives/edgar/data/24741/000002474126000253/glw-20260728xex99xq22026.htm",
  "doc_date": "2026-07-28"
}

====================================================================================================
[ir_financials] financials/NYSE_GLW.json  (batch dev_20261021T103341)
{
  "record_type": "ir_financials",
  "company_key": "NYSE:GLW",
  "company_name": "Corning Incorporated",
  "stock_code": "GLW",
  "market": "NYSE",
  "category": "SUPPLIER",
  "currency": "USD",
  "unit": "one",
  "source": "SEC companyfacts",
  "annual": [
    {
      "fiscal_year": 2025,
      "period_end": "2025-12-31",
      "revenue": 15629000000,
      "gross_profit": 5621000000,
      "cost_of_revenue": 10008000000,
      "operating_income": 2279000000,
      "pretax_income": 2052000000,
      "net_income": 1596000000,
      "eps": 1.83,
      "net_income_parent": 1596000000,
      "operating_cash_flow": 2695000000,
      "investing_cash_flow": -1243000000,
      "total_liabilities": 18669000000,
      "accounts_payable": 1979000000,
      "current_liabilities": 5628000000,
      "cash": 1526000000,
      "equity_parent": 11807000000,
      "total_assets": 30976000000,
      "inventory": 3077000000,
      "current_assets": 8936000000,
      "accounts_receivable": 2779000000,
      "equity": 12307000000,
      "derived": null,
      "source_urls": [
        "https://data.sec.gov/api/xbrl/companyfacts/CIK0000024741.json"
      ],
      "gross_margin": 35.97,
      "operating_margin": 14.58,
      "pretax_margin": 13.13,
      "net_margin": 10.21,
      "net_margin_parent": 10.21,
      "debt_ratio": 60.27,
      "current_ratio": 1.59,
      "quick_assets": 4305000000,
      "quick_ratio": 0.76,
      "dso_days": 56.4,
      "dpo_days": 62.9,
      "days_basis": "avg"
    },
    {
      "fiscal_year": 2024,
      "period_end": "2024-12-31",
      "revenue": 13118000000,
      "gross_profit": 4276000000,
      "cost_of_revenue": 8842000000,
      "operating_income": 1135000000,
      "pretax_income": 813000000,
      "net_income": 506000000,
      "eps": 0.58,
      "net_income_parent": 506000000,
      "operating_cash_flow": 1939000000,
      "investing_cash_flow": -744000000,
      "total_liabilities": 16665000000,
      "accounts_payable": 1472000000,
      "current_liabilities": 4919000000,
      "cash": 1768000000,
      "equity_parent": 10686000000,
      "total_assets": 27735000000,
      "inventory": 2724000000,
      "current_assets": 7992000000,
      "accounts_receivable": 2053000000,
      "equity": 11070000000,
      "derived": null,
      "source_urls": [
        "https://data.sec.gov/api/xbrl/companyfacts/CIK0000024741.json"
      ],
      "gross_margin": 32.6,
      "operating_margin": 8.65,
      "pretax_margin": 6.2,
      "net_margin": 3.86,
      "net_margin_parent": 3.86,
      "debt_ratio": 60.09,
      "current_ratio": 1.62,
      "quick_assets": 3821000000,
      "quick_ratio": 0.78,
      "dso_days": 50.4,
      "dpo_days": 60.6,
      "days_basis": "avg"
    },
    {
      "fiscal_year": 2023,
      "period_end": "2023-12-31",
      "revenue": 12588000000,
      "gross_profit": 3931000000,
      "cost_of_revenue": 8657000000,
      "operating_income": 890000000,
      "pretax_income": 816000000,
      "net_income": 581000000,
      "eps": 0.68,
      "net_income_parent": 581000000,
      "operating_cash_flow": 2005000000,
      "investing_cash_flow": -1000000000,
      "total_liabilities": 16632000000,
      "accounts_payable": 1466000000,
      "current_liabilities": 4319000000,
      "cash": 1779000000,
      "equity_parent": 11551000000,
      "total_assets": 28500000000,
      "inventory": 2666000000,
      "current_assets": 7212000000,
      "accounts_receivable": 1572000000,
      "equity": 11868000000,
      "derived": null,
      "source_urls": [
        "https://data.sec.gov/api/xbrl/companyfacts/CIK0000024741.json"
      ],
      "gross_margin": 31.23,
      "operating_margin": 7.07,
      "pretax_margin": 6.48,
      "net_margin": 4.62,
      "net_margin_parent": 4.62,
      "debt_ratio": 58.36,
      "current_ratio": 1.67,
      "quick_assets": 3351000000,
      "quick_ratio": 0.78,
      "dso_days": 47.7,
      "dpo_days": 68.9,
      "days_basis": "avg"
    },
    {
      "fiscal_year": 2022,
      "period_end": "2022-12-31",
      "revenue": 14189000000,
      "gross_profit": 4506000000,
      "cost_of_revenue": 9683000000,
      "operating_income": 1438000000,
      "pretax_income": 1797000000,
      "net_income": 1316000000,
      "eps": 1.54,
      "net_income_parent": 1316000000,
      "operating_cash_flow": 2615000000,
      "investing_cash_flow": -1355000000,
      "total_liabilities": 17224000000,
      "accounts_payable": 1804000000,
      "current_liabilities": 5175000000,
      "equity_parent": 12008000000,
      "total_assets": 29499000000,
      "inventory": 2904000000,
      "current_assets": 7453000000,
      "accounts_receivable": 1721000000,
      "equity": 12275000000,
      "derived": null,
      "source_urls": [
        "https://data.sec.gov/api/xbrl/companyfacts/CIK0000024741.json"
      ],
      "gross_margin": 31.76,
      "operating_margin": 10.13,
      "pretax_margin": 12.66,
      "net_margin": 9.27,
      "net_margin_parent": 9.27,
      "debt_ratio": 58.39,
      "current_ratio": 1.44,
      "quick_assets": null,
      "quick_ratio": null,
      "dso_days": 47.9,
      "dpo_days": 64.4,
      "days_basis": "avg"
    },
    {
      "fiscal_year": 2021,
      "period_end": "2021-12-31",
      "revenue": 14082000000,
      "gross_profit": 5063000000,
      "cost_of_revenue": 9019000000,
      "operating_income": 2112000000,
      "pretax_income": 2426000000,
      "net_income": 1906000000,
      "eps": 1.28,
      "net_income_parent": 1906000000,
      "operating_cash_flow": 3412000000,
      "investing_cash_flow": -1419000000,
      "total_liabilities": 17609000000,
      "accounts_payable": 1612000000,
      "current_liabilities": 4806000000,
      "equity_parent": 12333000000,
      "total_assets": 30154000000,
      "inventory": 2481000000,
      "current_assets": 7659000000,
      "accounts_receivable": 2004000000,
      "equity": 12545000000,
      "derived": null,
      "source_urls": [
        "https://data.sec.gov/api/xbrl/companyfacts/CIK0000024741.json"
      ],
      "gross_margin": 35.95,
      "operating_margin": 15.0,
      "pretax_margin": 17.23,
      "net_margin": 13.54,
      "net_margin_parent": 13.54,
      "debt_ratio": 58.4,
      "current_ratio": 1.59,
      "quick_assets": null,
      "quick_ratio": null,
      "dso_days": 51.9,
      "dpo_days": 65.2,
      "days_basis": "end"
    }
  ],
  "quarterly": [
    {
      "period": "2026Q2",
      "period_end": "2026-06-30",
      "revenue": 4505000000,
      "gross_profit": 1628000000,
      "cost_of_revenue": 2877000000,
      "operating_income": 698000000,
      "pretax_income": 649000000,
      "net_income": 559000000,
      "eps": 0.64,
      "net_income_parent": 559000000,
      "operating_cash_flow_ytd": 2079000000,
      "investing_cash_flow_ytd": -562000000,
      "total_assets": 32956000000,
      "total_liabilities": 19829000000,
      "current_assets": 10917000000,
      "current_liabilities": 6021000000,
      "cash": 2504000000,
      "accounts_receivable": 2932000000,
      "inventory": 3426000000,
      "accounts_payable": 2361000000,
      "equity": 13127000000,
      "equity_parent": 12560000000,
      "derived": [
        "operating_cash_flow",
        "investing_cash_flow"
      ],
      "source_urls": [
        "https://data.sec.gov/api/xbrl/companyfacts/CIK0000024741.json"
      ],
      "gross_margin": 36.14,
      "operating_margin": 15.49,
      "pretax_margin": 14.41,
      "net_margin": 12.41,
      "net_margin_parent": 12.41,
      "debt_ratio": 60.17,
      "current_ratio": 1.81,
      "quick_assets": 5436000000,
      "quick_ratio": 0.9,
      "operating_cash_flow": 1717000000,
      "investing_cash_flow": -359000000
    },
    {
      "period": "2026Q1",
      "period_end": "2026-03-31",
      "revenue": 4144000000,
      "gross_profit": 1528000000,
      "cost_of_revenue": 2616000000,
      "operating_income": 639000000,
      "pretax_income": 529000000,
      "net_income": 371000000,
      "eps": 0.43,
      "net_income_parent": 371000000,
      "operating_cash_flow": 362000000,
      "operating_cash_flow_ytd": 362000000,
      "investing_cash_flow": -203000000,
      "investing_cash_flow_ytd": -203000000,
      "total_assets": 31253000000,
      "total_liabilities": 18904000000,
      "current_assets": 9526000000,
      "current_liabilities": 5916000000,
      "cash": 1755000000,
      "accounts_receivable": 2676000000,
      "inventory": 3279000000,
      "accounts_payable": 2251000000,
      "equity": 12349000000,
      "equity_parent": 11812000000,
      "derived": null,
      "source_urls": [
        "https://data.sec.gov/api/xbrl/companyfacts/CIK0000024741.json"
      ],
      "gross_margin": 36.87,
      "operating_margin": 15.42,
      "pretax_margin": 12.77,
      "net_margin": 8.95,
      "net_margin_parent": 8.95,
      "debt_ratio": 60.49,
      "current_ratio": 1.61,
      "quick_assets": 4431000000,
      "quick_ratio": 0.75
    },
    {
      "period": "2025Q4",
      "period_end": "2025-12-31",
      "total_assets": 30976000000,
      "total_liabilities": 18669000000,
      "current_assets": 8936000000,
      "current_liabilities": 5628000000,
      "cash": 1526000000,
      "accounts_receivable": 2779000000,
      "inventory": 3077000000,
      "accounts_payable": 1979000000,
      "equity": 12307000000,
      "equity_parent": 11807000000,
      "revenue": 4215000000,
      "_derived": [
        "revenue",
        "gross_profit",
        "operating_income",
        "pretax_income",
        "net_income"
      ],
      "gross_profit": 1495000000,
      "operating_income": 672000000,
      "pretax_income": 678000000,
      "net_income": 540000000,
      "derived": [
        "revenue",
        "gross_profit",
        "operating_income",
        "pretax_income",
        "net_income",
        "operating_cash_flow",
        "investing_cash_flow"
      ],
      "source_urls": [
        "https://data.sec.gov/api/xbrl/companyfacts/CIK0000024741.json"
      ],
      "gross_margin": 35.47,
      "operating_margin": 15.94,
      "pretax_margin": 16.09,
      "net_margin": 12.81,
      "net_margin_parent": null,
      "debt_ratio": 60.27,
      "current_ratio": 1.59,
      "quick_assets": 4305000000,
      "quick_ratio": 0.76,
      "operating_cash_flow_ytd": 2695000000,
      "investing_cash_flow_ytd": -1243000000,
      "operating_cash_flow": 1052000000,
      "investing_cash_flow": -478000000
    },
    {
      "period": "2025Q3",
      "period_end": "2025-09-30",
      "revenue": 4100000000,
      "gross_profit": 1520000000,
      "cost_of_revenue": 2580000000,
      "operating_income": 589000000,
      "pretax_income": 550000000,
      "net_income": 430000000,
      "eps": 0.5,
      "net_income_parent": 430000000,
      "operating_cash_flow_ytd": 1643000000,
      "investing_cash_flow_ytd": -765000000,
      "total_assets": 29916000000,
      "total_liabilities": 17911000000,
      "current_assets": 8677000000,
      "current_liabilities": 5577000000,
      "accounts_receivable": 2509000000,
      "inventory": 3104000000,
      "accounts_payable": 2029000000,
      "equity": 12005000000,
      "equity_parent": 11536000000,
      "derived": [
        "operating_cash_flow",
        "investing_cash_flow"
      ],
      "source_urls": [
        "https://data.sec.gov/api/xbrl/companyfacts/CIK0000024741.json"
      ],
      "gross_margin": 37.07,
      "operating_margin": 14.37,
      "pretax_margin": 13.41,
      "net_margin": 10.49,
      "net_margin_parent": 10.49,
      "debt_ratio": 59.87,
      "current_ratio": 1.56,
      "quick_assets": null,
      "quick_ratio": null,
      "operating_cash_flow": 784000000,
      "investing_cash_flow": -299000000
    },
    {
      "period": "2025Q2",
      "period_end": "2025-06-30",
      "revenue": 3862000000,
      "gross_profit": 1392000000,
      "cost_of_revenue": 2470000000,
      "operating_income": 573000000,
      "pretax_income": 584000000,
      "net_income": 469000000,
      "eps": 0.54,
      "net_income_parent": 469000000,
      "operating_cash_flow_ytd": 859000000,
      "investing_cash_flow_ytd": -466000000,
      "total_assets": 28745000000,
      "total_liabilities": 17200000000,
      "current_assets": 8196000000,
      "current_liabilities": 5475000000,
      "cash": 1491000000,
      "accounts_receivable": 2298000000,
      "inventory": 3084000000,
      "accounts_payable": 1931000000,
      "equity": 11545000000,
      "equity_parent": 11116000000,
      "derived": [
        "operating_cash_flow",
        "investing_cash_flow"
      ],
      "source_urls": [
        "https://data.sec.gov/api/xbrl/companyfacts/CIK0000024741.json"
      ],
      "gross_margin": 36.04,
      "operating_margin": 14.84,
      "pretax_margin": 15.12,
      "net_margin": 12.14,
      "net_margin_parent": 12.14,
      "debt_ratio": 59.84,
      "current_ratio": 1.5,
      "quick_assets": 3789000000,
      "quick_ratio": 0.69,
      "operating_cash_flow": 708000000,
      "investing_cash_flow": -301000000
    },
    {
      "period": "2025Q1",
      "period_end": "2025-03-31",
      "revenue": 3452000000,
      "gross_profit": 1214000000,
      "cost_of_revenue": 2238000000,
      "operating_income": 445000000,
      "pretax_income": 240000000,
      "net_income": 157000000,
      "eps": 0.18,
      "net_income_parent": 157000000,
      "operating_cash_flow": 151000000,
      "operating_cash_flow_ytd": 151000000,
      "investing_cash_flow": -165000000,
      "investing_cash_flow_ytd": -165000000,
      "total_assets": 27394000000,
      "total_liabilities": 16266000000,
      "current_assets": 7644000000,
      "current_liabilities": 4523000000,
      "cash": 1359000000,
      "accounts_receivable": 2045000000,
      "inventory": 2896000000,
      "accounts_payable": 1737000000,
      "equity": 11128000000,
      "equity_parent": 10716000000,
      "derived": null,
      "source_urls": [
        "https://data.sec.gov/api/xbrl/companyfacts/CIK0000024741.json"
      ],
      "gross_margin": 35.17,
      "operating_margin": 12.89,
      "pretax_margin": 6.95,
      "net_margin": 4.55,
      "net_margin_parent": 4.55,
      "debt_ratio": 59.38,
      "current_ratio": 1.69,
      "quick_assets": 3404000000,
      "quick_ratio": 0.75
    },
    {
      "period": "2024Q4",
      "period_end": "2024-12-31",
      "total_assets": 27735000000,
      "total_liabilities": 16665000000,
      "current_assets": 7992000000,
      "current_liabilities": 4919000000,
      "cash": 1768000000,
      "accounts_receivable": 2053000000,
      "inventory": 2724000000,
      "accounts_payable": 1472000000,
      "equity": 11070000000,
      "equity_parent": 10686000000,
      "revenue": 3501000000,
      "_derived": [
        "revenue",
        "gross_profit",
        "operating_income",
        "pretax_income",
        "net_income"
      ],
      "gross_profit": 1197000000,
      "operating_income": 393000000,
      "pretax_income": 437000000,
      "net_income": 310000000,
      "derived": [
        "revenue",
        "gross_profit",
        "operating_income",
        "pretax_income",
        "net_income"
      ],
      "source_urls": [
        "https://data.sec.gov/api/xbrl/companyfacts/CIK0000024741.json"
      ],
      "gross_margin": 34.19,
      "operating_margin": 11.23,
      "pretax_margin": 12.48,
      "net_margin": 8.85,
      "net_margin_parent": null,
      "debt_ratio": 60.09,
      "current_ratio": 1.62,
      "quick_assets": 3821000000,
      "quick_ratio": 0.78,
      "operating_cash_flow_ytd": 1939000000,
      "investing_cash_flow_ytd": -744000000
    }
  ],
  "generated_at": "2026-10-21T10:33:41"
}

====================================================================================================
[ir_summary] summaries/2026-07-28_NYSEGLW_2026Q2.json  (batch dev_20261021T103341)
{
  "record_type": "ir_summary",
  "company_key": "NYSE:GLW",
  "company_name": "Corning Incorporated",
  "stock_code": "GLW",
  "market": "NYSE",
  "category": "SUPPLIER",
  "period": "2026Q2",
  "fiscal_period": "2026Q2",
  "conference_date": "2026-07-28",
  "time_basis": "LOCAL_DATE_ONLY",
  "local_conference_date": "2026-07-28",
  "fallback": false,
  "summary": {
    "found": true,
    "reported_period": "2026 Q2（2026 年 4～6 月；Corning 會計年度與日曆年相同）",
    "core_points": [
      "2026 Q2 核心銷售額 US$4.74B（YoY +17%）、核心 EPS US$0.78（YoY +30%），優於市場預期；GAAP 銷售額 US$4.51B、GAAP 稀釋 EPS US$0.64",
      "Optical Communications 成為最大事業部：銷售 US$2.07B（YoY +32%）、部門淨利 US$438M（YoY +77%），淨利率達 21% 新高；Enterprise Networks 銷售 YoY +65% 至 US$1.27B，AI 資料中心相關銷售近乎翻倍",
      "與 NVIDIA 建立長期合作，美國光學連接製造產能擴大 10 倍、美國光纖產能擴增逾 50%；與 Amazon 簽多年期數十億美元光纖／光纜／連接協議；Meta 協議最高 US$6B（媒體說法）",
      "Solar 銷售 YoY +90% 至 US$438M，但因太陽能晶圓廠延長維修停機與設備升級（額外費用約 US$30M）本季淨損 US$7M，管理層預期 Q3 起改善",
      "2026 年起重劃部門：Display 與 Specialty Materials 合併為 Glass Innovations，新增 Solar（含 Hemlock），其餘併入 Life Sciences & Emerging Growth",
      "Springboard 計畫：年化營收 run rate 2026 年底 US$20B、2028 年底 US$30B、2030 年底 US$40B；2026 Q4～2030 Q4 銷售 CAGR 19%，獲利成長快於營收；US$20B run rate 預計由 Q4 提前至 Q3 達成",
      "Q3 財測僅與華爾街預期相當，7/28 股價收跌 12.1% 至 US$126.01，並拖累光通訊類股（Lumentum、Coherent 等）下跌"
    ],
    "guidance": "2026 Q3 核心銷售額 US$4.9B～5.0B（YoY 約 +16%）、核心 EPS US$0.85～0.89（YoY 約 +28%）；管理層稱 Q3 指引不代表減速，Solar 獲利自 Q3 起改善；2026 年資本支出約 US$2.0B，Q3、Q4 投資節奏加快並以光通訊為主；長期維持核心營業利益率 20% 以上、ROIC 朝 high-teens 邁進，年底前再更新利潤率目標；Photonics 平台目標 2030 年營收 US$10B；風險調整後高信心計畫為 2028 年 US$27B、2030 年 US$35B（Investing.com 轉述）",
    "key_numbers": [
      "2026 Q2 核心銷售額 US$4.738B（YoY +17%）；GAAP 銷售額 US$4.505B（YoY +17%）",
      "2026 Q2 核心 EPS US$0.78（YoY +30%）；GAAP 稀釋 EPS US$0.64（YoY +19%）；核心淨利 US$680M（YoY +30%）",
      "2026 Q2 核心毛利率 39.6%（YoY +120 bps）；核心營業利益率 20.9%（YoY +190 bps）；GAAP 毛利率 36.1%、GAAP 營業利益率 15.5%",
      "2026 Q2 核心 ROIC 14.9%（YoY +180 bps）",
      "2026 Q2 GAAP 營業現金流 US$1,717M；調整後自由現金流 US$1,423M；資本支出 US$422M（上年同期 US$308M）",
      "2026 H1 營業現金流 US$2,079M；H1 資本支出 US$754M（2025 H1 US$516M）",
      "截至 2026/6/30 長期債務 US$7,756M、一年內到期債務與短期借款 US$668M；總負債 US$19,829M、股東權益 US$13,127M；US$1.5B 循環信貸未動用",
      "Optical Communications 2026 Q2 銷售 US$2,072M（YoY +32%）、部門淨利 US$438M（YoY +77%）；Enterprise 銷售 US$1.27B（YoY +65%）；Carrier YoY +1%（H1 約 +17%）",
      "Solar 2026 Q2 銷售 US$438M（YoY +90%）、淨損 US$7M（上年同期淨利 US$2M）",
      "2026 Q3 指引：核心銷售額 US$4.9B～5.0B、核心 EPS US$0.85～0.89",
      "季度股息 US$0.28，2026/9/29 支付"
    ],
    "risks": [
      "AI 工廠中光學 scale-up（機櫃內垂直擴展）的採用時程難以預測，是 Springboard 上行空間的最大變數",
      "手機市場受記憶體價格影響，2026 全年出貨量預估年減 mid-teens（約 15%）；汽車市場仍疲弱（全球車市年減 2%）",
      "Solar 本季虧損，獲利改善仰賴 Q3 產能恢復；Life Sciences & Emerging Growth 銷售 YoY -15% 且淨損 US$21M",
      "2026 資本支出約 US$2.0B 且下半年加速，短期可能壓抑自由現金流",
      "Q3 指引僅符合市場預期，高估值下股價對指引敏感，7/28 單日收跌 12.1%",
      "與客戶的長期協議含權證安排（10-Q：某客戶取得 1,500 萬股 US$180 行使價權證與 300 萬股 pre-funded 權證，認列 US$296M 權證公允價值作為收入減項）"
    ],
    "headline_metrics": [
      {
        "metric": "營收",
        "period": "2026 Q2",
        "value": "核心銷售額 US$4.74B（GAAP US$4.51B）",
        "yoy": "+17%",
        "note": "優於市場預估約 US$4.62B～4.65B（各媒體預估值略異）"
      },
      {
        "metric": "毛利率",
        "period": "2026 Q2",
        "value": "核心 39.6%（GAAP 36.1%）",
        "yoy": "+120 bps",
        "note": null
      },
      {
        "metric": "營業利益率",
        "period": "2026 Q2",
        "value": "核心 20.9%（GAAP 15.5%）",
        "yoy": "+190 bps",
        "note": null
      },
      {
        "metric": "稅後淨利",
        "period": "2026 Q2",
        "value": "核心淨利 US$680M",
        "yoy": "+30%",
        "note": null
      },
      {
        "metric": "EPS",
        "period": "2026 Q2",
        "value": "核心 EPS US$0.78（GAAP 稀釋 EPS US$0.64）",
        "yoy": "核心 +30%（GAAP +19%）",
        "note": "上年同期核心 EPS US$0.60"
      },
      {
        "metric": "營業現金流",
        "period": "2026 Q2",
        "value": "GAAP 營業現金流 US$1,717M；調整後自由現金流 US$1,423M",
        "yoy": null,
        "note": "2026 H1 營業現金流 US$2,079M"
      },
      {
        "metric": "資本支出",
        "period": "2026 Q2",
        "value": "US$422M",
        "yoy": "上年同期 US$308M",
        "note": "2026 H1 US$754M；2026 全年約 US$2.0B（法說說法）"
      },
      {
        "metric": "負債比",
        "period": "2026/6/30",
        "value": "長期債務 US$7,756M；總負債 US$19,829M／股東權益 US$13,127M",
        "yoy": null,
        "note": "10-Q 未直接列示負債比；5 月償還 €300M 3.875% 2026 票據，8/15 擬贖回 US$250M 7.25% 2036 票據"
      },
      {
        "metric": "其他",
        "period": "2026 Q2",
        "value": "核心 ROIC 14.9%",
        "yoy": "+180 bps",
        "note": null
      },
      {
        "metric": "營收",
        "period": "2026 Q3（指引）",
        "value": "核心銷售額 US$4.9B～5.0B",
        "yoy": "約 +16%",
        "note": null
      },
      {
        "metric": "EPS",
        "period": "2026 Q3（指引）",
        "value": "核心 EPS US$0.85～0.89",
        "yoy": "約 +28%",
        "note": null
      }
    ],
    "business_segments": [
      {
        "segment": "Optical Communications",
        "revenue": "US$2,072M",
        "revenue_yoy": "+32%",
        "operating_margin": "部門淨利 US$438M（淨利率 21%）",
        "opm_yoy": "部門淨利 +77%",
        "note": "Enterprise Networks 銷售 US$1.27B（YoY +65%），GenAI 產品成長更快、AI 資料中心相關銷售近乎翻倍；Carrier YoY +1%（H1 約 +17%，客戶專案時程因素）"
      },
      {
        "segment": "Glass Innovations（原 Display + Specialty Materials）",
        "revenue": "US$1,463M",
        "revenue_yoy": "+1%",
        "operating_margin": "部門淨利 US$354M",
        "opm_yoy": "部門淨利 +9%",
        "note": "手機市場 2026 出貨預估年減 mid-teens，Gorilla Glass 因單機內容量提升可優於市場"
      },
      {
        "segment": "Automotive",
        "revenue": "US$471M",
        "revenue_yoy": "+2%",
        "operating_margin": "部門淨利 US$82M",
        "opm_yoy": "部門淨利 +4%",
        "note": "汽車市場仍疲弱，全球車市年減 2%"
      },
      {
        "segment": "Solar（含 Hemlock）",
        "revenue": "US$438M",
        "revenue_yoy": "+90%",
        "operating_margin": "部門淨損 US$(7)M",
        "opm_yoy": "上年同期淨利 US$2M",
        "note": "太陽能晶圓廠延長維修停機與設備升級，額外費用約 US$30M；預期 Q3 改善，目標建成 US$3B 以上營收事業"
      },
      {
        "segment": "Life Sciences & Emerging Growth",
        "revenue": "US$294M",
        "revenue_yoy": "-15%",
        "operating_margin": "部門淨損 US$(21)M",
        "opm_yoy": "上年同期淨利 US$6M",
        "note": "媒體轉述：營收 QoQ +8%、淨利 QoQ +13%"
      }
    ],
    "management_views": [
      {
        "topic": "事業體／產品線重點",
        "view": "Optical Communications 銷售 YoY +32%、淨利 +77%，Enterprise +65% 由 GenAI 資料中心連接產品驅動，AI 相關占比近乎翻倍；Carrier 本季僅 +1% 但 H1 約 +17%，FTTH 與 DCI 需求持續。Solar 銷售 +90% 但因停機虧損；手機與車用終端市場偏弱。"
      },
      {
        "topic": "擴產／產能變化",
        "view": "與 NVIDIA 長期合作將美國光學連接製造產能擴大 10 倍、美國光纖產能擴增逾 50%；高密度光學產品需求已高於現有產能；2026 資本支出約 US$2.0B，下半年加速並以光通訊為主，大型擴產皆由長期客戶協議（LTA）支撐；Solar 晶圓廠完成延長維修停機與設備升級。"
      },
      {
        "topic": "獲利能力變化",
        "view": "核心毛利率 39.6%（+120 bps）、核心營業利益率 20.9%（+190 bps）、ROIC 14.9%（+180 bps）；光通訊淨利率達 21% 新高且仍有擴張空間；Q3 利潤率提升主要來自 Solar 獲利改善；長期目標維持營業利益率 20% 以上，年底前更新新目標。"
      },
      {
        "topic": "未來市場預測",
        "view": "Q3 核心銷售額 US$4.9B～5.0B（+16%）、核心 EPS US$0.85～0.89（+28%），US$20B 年化 run rate 預計提前至 Q3 達成；Springboard 2026 Q4～2030 Q4 CAGR 19%，2030 年 US$40B；預估至 2028 年 Enterprise 每顆 GPU 光學用量增至目前 1.3～1.5 倍；scale-up 光學導入是更大但較難預測的機會。"
      },
      {
        "topic": "投資／M&A／組織整改",
        "view": "2026 年起重劃部門（Glass Innovations、Solar、Life Sciences & Emerging Growth）；與 NVIDIA、Amazon、Meta、Apple 簽署長期協議，LTA 將成為光學業務的「絕大部分」；10-Q 揭露 5/6 與一客戶建立長期合作（客戶存款 US$1.0B，附 1,500 萬股 US$180 權證）；Solar 將持續提高半導體級多晶矽比例。"
      }
    ],
    "qa_highlights": [
      {
        "question": "Citi：Q3 強勁但為何 Q4 成長有限？",
        "answer": "CFO Schlesinger：Q3 指引隱含提前達成 US$20B run rate，成長率從約 15% 加速至接近 20%，沒有隱含其他事業部門的負面訊息；Weeks 補充只是不想在 5 月後再次上調計畫。"
      },
      {
        "question": "UBS：5 月以來 Photonics／scale-up 供應鏈有延遲傳聞，計畫有無改變？2027 年 Photonics 能否達十億美元級？",
        "answer": "Weeks：基本觀點沒有改變，外界臆測多於業界實際變化；未給 2027 年數字，僅維持 2030 年 US$10B Photonics 目標並按季更新。"
      },
      {
        "question": "Wolfe Research：LTA 在光學業務占比與定價策略？",
        "answer": "Weeks：LTA 占比將是絕大部分，大型擴產皆有 LTA 支撐；定價不是單純漲光纖價格，而是透過創新降低客戶成本、加快部署並分享價值。"
      },
      {
        "question": "Bank of America：Q3 指引變動因素？Enterprise 營收季增約 US$300M 但淨利率未見明顯槓桿？",
        "answer": "Schlesinger：Q3 不代表減速，Enterprise 仍是主要貢獻；手機市場因記憶體價格下半年明顯轉弱、車市疲軟；光學利潤率將持續提升。"
      },
      {
        "question": "Susquehanna：是否增加半導體級多晶矽配置？scale-up 與 FAU 是否已納入 Springboard？",
        "answer": "Weeks：會持續提高半導體級多晶矽比例但太陽能仍占重要營收；Enterprise 光纖與 Photonics 的 FAU 已納入計畫，上行空間取決於光學端口占比與 scale-up 在 AI 工廠的普及程度。"
      }
    ],
    "positive_signals": [
      "光通訊需求高於產能且由 NVIDIA、Amazon、Meta 等長期協議鎖定，美國連接產能擴大 10 倍、光纖 +50%，供應鏈投資方向明確",
      "核心毛利率與營業利益率連續擴張，光通訊淨利率達 21%，公司有資源持續投資 Photonics 與產能",
      "Solar／Hemlock 將提高半導體級多晶矽比例，並已完成設備升級，Q3 起獲利改善",
      "Glass Innovations 在手機市場下滑下仍 YoY +1%、淨利 +9%，Gorilla Glass 單機內容量提升支撐表現"
    ],
    "watch_items": [
      "AI 工廠光學 scale-up 的採用時程與光學端口占比，為 Photonics US$10B 目標的關鍵變數",
      "手機市場 2026 出貨預估年減 mid-teens、全球車市年減 2%，影響 Glass Innovations 與 Automotive 需求",
      "2026 資本支出約 US$2.0B 且下半年加速，自由現金流與擴產進度需持續追蹤",
      "Solar 部門能否如期於 Q3 轉正；Life Sciences & Emerging Growth 銷售 -15% 且虧損"
    ],
    "open_questions": [
      "光學端口占比（管理層稱機密）與 scale-up 採用速度的具體判斷",
      "2027 年 Photonics 營收規模，管理層只給 2030 年 US$10B 目標",
      "LTA 在光學業務的具體占比與定價／漲價幅度",
      "Enterprise 營收大增但營運槓桿未明顯顯現的完整原因，以及新的營業利益率目標（留待年底）"
    ],
    "sources": [
      {
        "title": "Corning 8-K Exhibit 99（2026 Q2 業績新聞稿）",
        "url": "https://www.sec.gov/Archives/edgar/data/24741/000002474126000253/glw-20260728xex99xq22026.htm",
        "media": "SEC EDGAR"
      },
      {
        "title": "Corning Form 10-Q（2026/6/30 止季度）",
        "url": "https://www.sec.gov/Archives/edgar/data/24741/000002474126000255/glw-20260630.htm",
        "media": "SEC EDGAR"
      },
      {
        "title": "Corning's Strong Second-Quarter 2026 Financial Results Demonstrate Progress on Recently Upgraded Springboard Plan",
        "url": "https://www.businesswire.com/news/home/20260727590976/en/Cornings-Strong-Second-Quarter-2026-Financial-Results1-Demonstrate-Progress-on-Recently-Upgraded-Springboard-Plan",
        "media": "Business Wire（Corning 新聞稿）"
      },
      {
        "title": "Earnings call transcript: Corning beats Q2 2026 estimates but shares sink",
        "url": "https://www.investing.com/news/transcripts/earnings-call-transcript-corning-beats-q2-2026-estimates-but-shares-sink-93CH-4817120",
        "media": "Investing.com"
      },
      {
        "title": "Corning Inc (GLW) Q2 2026 Earnings Call Highlights: Strong Growth in Optical Communications",
        "url": "https://finance.yahoo.com/markets/stocks/articles/corning-inc-glw-q2-2026-210222441.html",
        "media": "Yahoo Finance／GuruFocus"
      },
      {
        "title": "康寧財報優於預期但財測平淡，股價跳水拖累光通訊類股",
        "url": "https://finance.technews.tw/2026/07/29/cornings-strong-second-quarter-2026-financial-results/",
        "media": "科技新報（轉載 MoneyDJ）"
      },
      {
        "title": "康寧 AI 光通訊需求爆發帶動獲利大增 30% 上修長期成長目標至 2030 年 400 億美元",
        "url": "https://statementdog.com/news/17258",
        "media": "財報狗"
      }
    ],
    "notes": "股價反應媒體說法不一：Investing.com 稱盤前跌 18.47%、年初至今 +64%；MoneyDJ 稱 7/28 收跌 12.1% 至 US$126.01、年初至今 +43.91%；財報狗稱年初至今約 +39%。財報狗引用的參考資料中另有一則標題稱 Q2 營收未達預估，與多數報導的「優於預期」相矛盾（媒體說法不一）。Springboard CAGR 19% 的起算點各媒體表述略異（2026 Q4 起 vs 自 Springboard 起點）。法說未提及 Micro LED、CPO 或與 AUO 的直接合作，故無 AUO 相關議題一筆。"
  },
  "recipients": [
    "A00"
  ],
  "crawled_at": "2026-10-21T10:37:35+08:00"
}

