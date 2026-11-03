company_key = NYSE:GLW, period = 2026Q3, 檔案數 = 6

====================================================================================================
[ir_conference] calendar/2026-10-27_NYSEGLW_2026Q3.json  (batch dev_20261103T232657)
{
  "record_type": "ir_conference",
  "company_key": "NYSE:GLW",
  "company_name": "Corning Incorporated",
  "english_name": "Corning",
  "stock_code": "GLW",
  "market": "NYSE",
  "category": "SUPPLIER",
  "period": "2026Q3",
  "fiscal_period": "2026Q3",
  "source_fiscal_period": null,
  "conference_date": "2026-10-27",
  "start_time": null,
  "end_time": null,
  "time_basis": "LOCAL_DATE_ONLY",
  "local_timezone": "America/New_York",
  "local_conference_date": "2026-10-27",
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
  "remark": "[當地日 2026-10-27（America/New_York），時間未知，台北日可能為隔日]",
  "recipients": [
    "A00"
  ],
  "revision": 0,
  "crawled_at": "2026-11-03T23:28:01+08:00"
}

====================================================================================================
[ir_document] docs/NYSE_GLW/2026Q3/manifest.json  (batch dev_20261103T232657)
{
  "record_type": "ir_document",
  "company_key": "NYSE:GLW",
  "company_name": "Corning Incorporated",
  "stock_code": "GLW",
  "market": "NYSE",
  "category": "SUPPLIER",
  "period": "2026Q3",
  "fiscal_period": "2026Q3",
  "conference_date": "2026-10-27",
  "local_conference_date": "2026-10-27",
  "status": "DONE",
  "wanted": [
    "presentation",
    "financial_report"
  ],
  "missing": [],
  "files": [
    {
      "type": "financial_report",
      "file": "financial_report_20261029_23e8c06f.htm",
      "path": "docs/NYSE_GLW/2026Q3/financial_report_20261029_23e8c06f.htm",
      "source": "EDGAR",
      "source_url": "https://www.sec.gov/Archives/edgar/data/24741/000002474126000279/glw-20260930.htm",
      "title": "10-Q filing 2026-10-29",
      "doc_date": "2026-10-29",
      "sha256": "23e8c06f15fb2167dd6a43c310cd3ed7bb36d2bb97de618e3a1aff5017337617",
      "bytes": 1833118,
      "fetched_at": "2026-11-03T23:28:05+08:00"
    },
    {
      "type": "presentation",
      "file": "presentation_20261027_3b7278b8.htm",
      "path": "docs/NYSE_GLW/2026Q3/presentation_20261027_3b7278b8.htm",
      "source": "EDGAR",
      "source_url": "https://www.sec.gov/Archives/edgar/data/24741/000002474126000273/glw-20261027xex99xq32026.htm",
      "title": "8-K EX-99 2026-10-27",
      "doc_date": "2026-10-27",
      "sha256": "3b7278b853f9bad1c01926c88b10a9981bab20544251872208528ce5c143d616",
      "bytes": 723662,
      "fetched_at": "2026-11-03T23:28:06+08:00"
    }
  ],
  "generated_at": "2026-11-03T23:28:06+08:00"
}

====================================================================================================
[ir_document_file] docs/NYSE_GLW/2026Q3/Corning_Q3CY26_Financial_Statements.htm  (batch dev_20261103T232657)
實體檔：/private/tmp/claude-501/-Users-ericmlyang-Coding-databricks-coding/98040114-a886-49ae-8c3d-28d10cb6ed13/scratchpad/ircal_sandbox/out/docs/NYSE_GLW/2026Q3/financial_report_20261029_23e8c06f.htm
{
  "path": "docs/NYSE_GLW/2026Q3/Corning_Q3CY26_Financial_Statements.htm",
  "record_type": "ir_document_file",
  "sha256": "23e8c06f15fb2167dd6a43c310cd3ed7bb36d2bb97de618e3a1aff5017337617",
  "bytes": 1833118,
  "company_key": "NYSE:GLW",
  "company_slug": "Corning",
  "category": "SUPPLIER",
  "period": "2026Q3",
  "doc_kind": "Financial_Statements",
  "fiscal_label": null,
  "source_file": "financial_report_20261029_23e8c06f.htm",
  "source_url": "https://www.sec.gov/Archives/edgar/data/24741/000002474126000279/glw-20260930.htm",
  "doc_date": "2026-10-29"
}

====================================================================================================
[ir_document_file] docs/NYSE_GLW/2026Q3/Corning_Q3CY26_Presentation.htm  (batch dev_20261103T232657)
實體檔：/private/tmp/claude-501/-Users-ericmlyang-Coding-databricks-coding/98040114-a886-49ae-8c3d-28d10cb6ed13/scratchpad/ircal_sandbox/out/docs/NYSE_GLW/2026Q3/presentation_20261027_3b7278b8.htm
{
  "path": "docs/NYSE_GLW/2026Q3/Corning_Q3CY26_Presentation.htm",
  "record_type": "ir_document_file",
  "sha256": "3b7278b853f9bad1c01926c88b10a9981bab20544251872208528ce5c143d616",
  "bytes": 723662,
  "company_key": "NYSE:GLW",
  "company_slug": "Corning",
  "category": "SUPPLIER",
  "period": "2026Q3",
  "doc_kind": "Presentation",
  "fiscal_label": null,
  "source_file": "presentation_20261027_3b7278b8.htm",
  "source_url": "https://www.sec.gov/Archives/edgar/data/24741/000002474126000273/glw-20261027xex99xq32026.htm",
  "doc_date": "2026-10-27"
}

====================================================================================================
[ir_financials] financials/NYSE_GLW.json  (batch dev_20261103T232657)
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
      "equity": 12307000000,
      "accounts_receivable": 2779000000,
      "accounts_payable": 1979000000,
      "current_assets": 8936000000,
      "current_liabilities": 5628000000,
      "total_assets": 30976000000,
      "inventory": 3077000000,
      "equity_parent": 11807000000,
      "cash": 1526000000,
      "total_liabilities": 18669000000,
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
      "equity": 11070000000,
      "accounts_receivable": 2053000000,
      "accounts_payable": 1472000000,
      "current_assets": 7992000000,
      "current_liabilities": 4919000000,
      "total_assets": 27735000000,
      "inventory": 2724000000,
      "equity_parent": 10686000000,
      "cash": 1768000000,
      "total_liabilities": 16665000000,
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
      "equity": 11868000000,
      "accounts_receivable": 1572000000,
      "accounts_payable": 1466000000,
      "current_assets": 7212000000,
      "current_liabilities": 4319000000,
      "total_assets": 28500000000,
      "inventory": 2666000000,
      "equity_parent": 11551000000,
      "cash": 1779000000,
      "total_liabilities": 16632000000,
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
      "equity": 12275000000,
      "accounts_receivable": 1721000000,
      "accounts_payable": 1804000000,
      "current_assets": 7453000000,
      "current_liabilities": 5175000000,
      "total_assets": 29499000000,
      "inventory": 2904000000,
      "equity_parent": 12008000000,
      "total_liabilities": 17224000000,
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
      "equity": 12545000000,
      "accounts_receivable": 2004000000,
      "accounts_payable": 1612000000,
      "current_assets": 7659000000,
      "current_liabilities": 4806000000,
      "total_assets": 30154000000,
      "inventory": 2481000000,
      "equity_parent": 12333000000,
      "total_liabilities": 17609000000,
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
      "period": "2026Q3",
      "period_end": "2026-09-30",
      "revenue": 4855000000,
      "gross_profit": 1810000000,
      "cost_of_revenue": 3045000000,
      "operating_income": 911000000,
      "pretax_income": 968000000,
      "net_income": 680000000,
      "eps": 0.78,
      "net_income_parent": 680000000,
      "operating_cash_flow_ytd": 3140000000,
      "investing_cash_flow_ytd": -1005000000,
      "total_assets": 34126000000,
      "total_liabilities": 19838000000,
      "current_assets": 11342000000,
      "current_liabilities": 6585000000,
      "cash": 2537000000,
      "accounts_receivable": 3101000000,
      "inventory": 3646000000,
      "accounts_payable": 2492000000,
      "equity": 14288000000,
      "equity_parent": 13671000000,
      "derived": [
        "operating_cash_flow",
        "investing_cash_flow"
      ],
      "source_urls": [
        "https://data.sec.gov/api/xbrl/companyfacts/CIK0000024741.json"
      ],
      "gross_margin": 37.28,
      "operating_margin": 18.76,
      "pretax_margin": 19.94,
      "net_margin": 14.01,
      "net_margin_parent": 14.01,
      "debt_ratio": 58.13,
      "current_ratio": 1.72,
      "quick_assets": 5638000000,
      "quick_ratio": 0.86,
      "operating_cash_flow": 1061000000,
      "investing_cash_flow": -443000000
    },
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
        "net_income",
        "operating_cash_flow",
        "investing_cash_flow"
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
      "cash": 1648000000,
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
      "quick_assets": 4157000000,
      "quick_ratio": 0.75,
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
  "generated_at": "2026-11-03T23:26:58"
}

====================================================================================================
[ir_summary] summaries/2026-10-27_NYSEGLW_2026Q3.json  (batch dev_20261103T232657)
{
  "record_type": "ir_summary",
  "company_key": "NYSE:GLW",
  "company_name": "Corning Incorporated",
  "stock_code": "GLW",
  "market": "NYSE",
  "category": "SUPPLIER",
  "period": "2026Q3",
  "fiscal_period": "2026Q3",
  "conference_date": "2026-10-27",
  "time_basis": "LOCAL_DATE_ONLY",
  "local_conference_date": "2026-10-27",
  "fallback": false,
  "summary": {
    "found": true,
    "reported_period": "2026 Q3（2026 年 7～9 月；康寧會計年度與日曆年相同）",
    "core_points": [
      "2026 Q3 核心營收 US$50.81 億（YoY +19%），核心 EPS US$0.91（YoY +36%），均高於公司原先指引（核心營收 US$49～50 億、核心 EPS US$0.85～0.89）",
      "光通訊事業為最大成長引擎：營收 US$23.79 億（YoY +44%），淨利 US$5.32 億（YoY +80%）創部門紀錄；企業網路營收 YoY +84%，Gen AI 產品營收 YoY 翻倍以上，成長快於 GPU 出貨",
      "Springboard 計畫（20-30-40）：Q3 年化營收 run rate 已達 US$203 億，提前達成 2026 年底 US$200 億目標；維持 2028 年底 US$300 億、2030 年底 US$400 億目標",
      "Q3 簽下四份長期、數十億美元規模客戶協議（含 Verizon、AT&T、Zayo），客戶預付現金共同承擔擴產成本與風險；前三季客戶押金淨額 US$6.39 億",
      "Glass Innovations（原顯示＋特殊材料）營收 US$15.06 億（YoY -3%），淨利 US$3.28 億（YoY -10%）；TV 出貨 -4%、NB 與手持裝置約 -20%，管理層歸因於記憶體漲價；顯示玻璃基板 Q4 起漲價，主要反映在 2027 年以後",
      "太陽能事業營收 US$4.36 億（YoY +37%）但淨損 US$700 萬，晶圓與模組廠量產爬坡慢於預期，拖累預計到 2027 年才逐步改善",
      "Q4 2026 指引：核心營收 US$52～53 億（YoY 約 +19%）、核心 EPS US$0.96～1.00（YoY 約 +36%）；2026 全年資本支出約 US$20 億，主要投入光通訊產能"
    ],
    "guidance": "Q4 2026 核心營收 US$52～53 億（YoY 約 +19%），核心 EPS US$0.96～1.00（YoY 約 +36%）；2026 全年資本支出約 US$20 億（前三季 US$13 億），主要用於光通訊擴產；營業費用成長將慢於營收；Springboard 目標維持 2028 年底年化營收 US$300 億、2030 年底 US$400 億，2027～2030 年營收 CAGR 約 19%，EPS 成長快於營收、ROIC 持續擴張、自由現金流在規劃期間持續成長；光學 scale-up 架構預期 2028 年開始加速（每 GPU 光纖數由約 16 條升至約 160 條）；太陽能長期目標為 US$30 億以上營收、獲利率高於公司平均。",
    "key_numbers": [
      "2026 Q3 核心營收 US$50.81 億（YoY +19%）；GAAP 營收 US$48.55 億（YoY +18%）",
      "2026 Q3 核心 EPS US$0.91（YoY +36%）；GAAP 稀釋 EPS US$0.78（YoY +56%）",
      "2026 Q3 核心毛利率 40.5%（YoY +150 bps）；GAAP 毛利率 37.3%",
      "2026 Q3 核心營業利益率 22.7%（YoY +310 bps）；GAAP 營業利益率 18.8%",
      "2026 Q3 GAAP 歸屬康寧淨利 US$6.80 億（YoY +58%）；核心淨利 US$7.95 億（YoY +36%）",
      "2026 Q3 核心 ROIC 16.7%（YoY +330 bps）",
      "2026 Q3 GAAP 營業現金流 US$10.61 億；資本支出 US$5.45 億；調整後自由現金流 US$6.61 億；前三季調整後自由現金流約 US$23 億",
      "2026 前三季營業現金流 US$31.40 億（去年同期 US$16.43 億）；資本支出 US$12.99 億（去年同期 US$8.50 億）",
      "光通訊 2026 Q3 營收 US$23.79 億（YoY +44%，QoQ +15%）、淨利 US$5.32 億（YoY +80%）；企業網路 YoY +84%；電信（Carrier）YoY +4%",
      "Glass Innovations 2026 Q3 營收 US$15.06 億（YoY -3%）、淨利 US$3.28 億（YoY -10%）",
      "太陽能 2026 Q3 營收 US$4.36 億（YoY +37%）、淨損 US$700 萬（去年同期淨利 US$3,000 萬）",
      "2026 Q3 年化營收 run rate US$203 億；Q4 指引中點隱含約 US$210 億",
      "2026/9/30 長期債務 US$72.67 億、一年內到期債務與短期借款 US$9.33 億；總負債 US$198.38 億；平均債務到期年限 20 年以上"
    ],
    "risks": [
      "太陽能事業量產爬坡慢於預期，Q3 淨損 US$700 萬，拖累預計 2027 年才逐步改善，且尚未達公司平均獲利率",
      "Glass Innovations 終端需求疲弱：TV 出貨 -4%、NB 與手持裝置約 -20%（記憶體漲價影響），營收與淨利同步下滑",
      "2026 資本支出約 US$20 億，市場關注資本密集度與自由現金流；財報公布後股價下跌（媒體說法不一：盤前 -2.97% 至 US$123.94／開盤 -4.4% 至 US$122.08）",
      "GAAP 營收 US$48.6 億低於分析師預估 US$50.3 億（媒體說法不一：另有媒體以核心營收 US$50.8 億對比認定小幅優於預期）",
      "新型高密度光纖產品需求超過供給，產能分配在電信與企業客戶間需取捨",
      "日圓走弱與關鍵材料、能源成本上升壓力，需靠顯示玻璃漲價與避險（日圓避險基準 150）抵銷",
      "長期客戶協議的客戶押金未來需於交貨時返還（10-Q 揭露一筆 US$10 億押金供應協議至 2029/12/31），2027～2028 年現金流時序受影響"
    ],
    "headline_metrics": [
      {
        "metric": "營收",
        "period": "2026 Q3",
        "value": "核心營收 US$50.81 億",
        "yoy": "+19%",
        "note": "GAAP 營收 US$48.55 億，YoY +18%"
      },
      {
        "metric": "毛利率",
        "period": "2026 Q3",
        "value": "核心毛利率 40.5%",
        "yoy": "+150 bps",
        "note": "GAAP 毛利率 37.3%"
      },
      {
        "metric": "營業利益率",
        "period": "2026 Q3",
        "value": "核心營業利益率 22.7%",
        "yoy": "+310 bps",
        "note": "GAAP 營業利益率 18.8%"
      },
      {
        "metric": "稅後淨利",
        "period": "2026 Q3",
        "value": "GAAP 歸屬康寧淨利 US$6.80 億",
        "yoy": "+58%",
        "note": "核心淨利 US$7.95 億，YoY +36%"
      },
      {
        "metric": "EPS",
        "period": "2026 Q3",
        "value": "核心 EPS US$0.91",
        "yoy": "+36%",
        "note": "GAAP 稀釋 EPS US$0.78，YoY +56%"
      },
      {
        "metric": "營業現金流",
        "period": "2026 Q3",
        "value": "GAAP 營業現金流 US$10.61 億",
        "yoy": null,
        "note": "前三季 US$31.40 億（去年同期 US$16.43 億）"
      },
      {
        "metric": "資本支出",
        "period": "2026 Q3",
        "value": "US$5.45 億",
        "yoy": null,
        "note": "前三季 US$12.99 億；2026 全年約 US$20 億"
      },
      {
        "metric": "其他",
        "period": "2026 Q3",
        "value": "調整後自由現金流 US$6.61 億",
        "yoy": null,
        "note": "前三季約 US$23 億"
      },
      {
        "metric": "其他",
        "period": "2026 Q3",
        "value": "核心 ROIC 16.7%",
        "yoy": "+330 bps",
        "note": null
      },
      {
        "metric": "負債比",
        "period": "2026/9/30",
        "value": "長期債務 US$72.67 億；總負債 US$198.38 億",
        "yoy": null,
        "note": "一年內到期債務與短期借款 US$9.33 億；US$15 億循環信用額度未動用"
      }
    ],
    "business_segments": [
      {
        "segment": "Optical Communications（光通訊）",
        "revenue": "US$23.79 億",
        "revenue_yoy": "+44%（QoQ +15%）",
        "operating_margin": null,
        "opm_yoy": null,
        "note": "部門淨利 US$5.32 億（YoY +80%）創紀錄；企業網路營收 YoY +84%、Gen AI 產品營收 YoY 翻倍以上；電信營收 YoY +4%，由資料中心互連（DCI）驅動；企業網路年化 run rate 自 Springboard 啟動時 US$14 億升至 US$60 億"
      },
      {
        "segment": "Glass Innovations（玻璃創新，原顯示＋特殊材料）",
        "revenue": "US$15.06 億",
        "revenue_yoy": "-3%（約 -US$5,400 萬）",
        "operating_margin": null,
        "opm_yoy": null,
        "note": "部門淨利 US$3.28 億（YoY -10%）；TV 出貨 -4%、NB 與手持裝置約 -20%（記憶體漲價影響）；More Corning 策略表現優於終端市場；顯示玻璃基板 Q4 起漲價"
      },
      {
        "segment": "Automotive（車用）",
        "revenue": "US$4.70 億",
        "revenue_yoy": "+4%（QoQ 持平）",
        "operating_margin": null,
        "opm_yoy": null,
        "note": "部門淨利 US$6,700 萬（YoY -1%）；北美 Class 8 重卡復甦抵銷輕型車 -3%"
      },
      {
        "segment": "Solar（太陽能，含 Hemlock）",
        "revenue": "US$4.36 億",
        "revenue_yoy": "+37%（約 +US$1.17 億）",
        "operating_margin": null,
        "opm_yoy": null,
        "note": "部門淨損 US$700 萬（去年同期淨利 US$3,000 萬）；晶圓與模組廠量產爬坡慢於預期；Section 232 貿易措施改善美國製產品價格與需求"
      },
      {
        "segment": "Life Sciences & Emerging Growth（生命科學與新興成長）",
        "revenue": "US$2.90 億",
        "revenue_yoy": "+1%",
        "operating_margin": null,
        "opm_yoy": null,
        "note": "部門淨損 US$2,800 萬（去年同期淨損 US$1,500 萬，淨利減少 US$1,300 萬），因新興成長事業投資；生命科學表現優於終端市場"
      }
    ],
    "management_views": [
      {
        "topic": "事業體／產品線重點",
        "view": "光通訊營收 US$23.79 億（YoY +44%）、淨利 US$5.32 億（YoY +80%）創紀錄，企業網路 +84%、Gen AI 產品翻倍以上且快於 GPU 出貨成長；Glass Innovations 營收 -3%，TV -4%、NB 與手持裝置約 -20%，靠 More Corning 策略與 Apple 合作（2026 年底前全球 iPhone 與 Apple Watch 蓋板玻璃全在肯塔基 Harrodsburg 生產）部分抵銷；車用 +4% 靠北美 Class 8 重卡復甦。"
      },
      {
        "topic": "擴產／產能變化",
        "view": "Q3 投入逾 US$5 億產能投資，2026 全年資本支出約 US$20 億主要投入光通訊；最新高密度光纖產品需求超過供給，新產能已在建置中，產能規劃支撐至 2030 年 19% CAGR；太陽能晶圓與模組廠爬坡慢於預期。客戶預付現金資助擴產（前三季押金淨額 US$6.39 億），此模式已用於玻璃與太陽能，現擴展至光通訊。"
      },
      {
        "topic": "獲利能力變化",
        "view": "核心毛利率 40.5%（+150 bps）、核心營業利益率 22.7%（+310 bps）、ROIC 16.7%（+330 bps）；光通訊淨利率由 mid-teens 升至 low 20s，尚未設新目標；太陽能仍低於公司平均獲利率、拖累程度與 Q2 相近，預計到 2027 年逐步改善；變動薪酬 Q2、Q3 偏高，Q4 應趨平；營業費用成長將慢於營收。"
      },
      {
        "topic": "未來市場預測",
        "view": "Q4 核心營收 US$52～53 億（YoY 約 +19%）、核心 EPS US$0.96～1.00（YoY 約 +36%），成長主要來自光通訊，太陽能隨產能開出貢獻；CEO 引用 Anthropic S-1 文件稱算力仍是主要瓶頸、超大規模客戶持續要求更多供應；光學 scale-up 預期 2028 年加速；DCI 機會已超過原訂十年底 US$10 億目標，將另設新目標；光纖到府也會成長。"
      },
      {
        "topic": "投資／M&A／組織整改",
        "view": "Q3 簽下四份長期數十億美元客戶協議（含 Verizon、AT&T、Zayo），客戶預付現金共擔風險；2026/9/11 設立 US$20 億 ATM 股權發行額度，管理層稱為例行性安排、目前無使用計畫；資本配置順序為有機成長、穩健資產負債表、以回購為主要現金回饋方式；日圓避險基準 150，無意降低避險比率（分析師稱由 98% 降至 94%）。未宣布新併購。"
      },
      {
        "topic": "AUO 相關議題",
        "view": "顯示玻璃基板自 2026 Q4 起漲價，主因日圓走弱與關鍵材料、能源成本上升，管理層未揭露幅度，稱 Q4 影響極小、主要反映在 2027 年以後，做法與過去類似（管理層未點名友達或任何面板廠）；本場法說未提及 Micro LED、座艙顯示或 CPO。"
      }
    ],
    "qa_highlights": [
      {
        "question": "UBS 問光通訊何時能給出新的前瞻利潤率目標、企業成本為何年減約 US$5,000 萬？",
        "answer": "CFO 稱光通訊淨利率已由 mid-teens 升至 low 20s 且仍有空間，但因太陽能仍拖累暫不設新目標；企業成本差異是變動薪酬高於常態，Q4 應趨平。"
      },
      {
        "question": "Citi 問 Gen AI 需求的持續性與融資風險，以及 scale-up 時程？",
        "answer": "CEO 引用 Anthropic S-1 稱算力為主要瓶頸、客戶只要求更多更快的新產品，故在多年協議中要求預付資金；光學 scale-up 每 GPU 光纖數由 16 升至 160，預期 2028 年加速。"
      },
      {
        "question": "Morgan Stanley 問電信與企業客戶間如何分配供給、太陽能拖累何時解除？",
        "answer": "最新高密度產品需求超過供給，優先供應長期客戶與出資擴產的客戶；太陽能 Q3 拖累與 Q2 相近，Section 232 裁定正面，預計到 2027 年緩慢改善。"
      },
      {
        "question": "BofA 問 2026 資本支出多少由客戶出資、2027～2028 年返還押金對自由現金流的影響，以及顯示玻璃漲價幅度？",
        "answer": "扣除維護性資本支出後大部分成長資本由長期協議支應，押金使現金流平滑、自由現金流可持續成長；顯示玻璃漲價主要影響 2027 年以後，不揭露幅度。"
      },
      {
        "question": "Wolfe Research 問中國光纖是否進入康寧市場？",
        "answer": "CEO 稱因更多光纖以整合連接產品形式出售（運費與關稅成本較高），對中國光纖曝險持續下降，目前非顯著壓力。"
      }
    ],
    "positive_signals": [
      "核心毛利率 40.5%、營業利益率 22.7% 持續擴張，前三季自由現金流約 US$23 億，財務體質與供應穩定度佳",
      "顯示玻璃仍維持投資與 Apple 蓋板玻璃在美集中生產，Glass Innovations 在終端市場下滑中表現優於市場（More Corning 策略）",
      "光通訊產能擴張由客戶預付資金支撐，並擴及至新型高密度光纖與 DCI 產品，供應鏈對 AI 資料中心的投入明確",
      "長期債務平均到期 20 年以上、無單一年度大額到期，US$15 億循環額度未動用"
    ],
    "watch_items": [
      "顯示玻璃基板 Q4 起漲價且幅度未揭露，對 2027 年面板廠採購成本的實際影響",
      "新型高密度光纖產品供不應求，康寧優先供應長期客戶與出資擴產客戶，非優先客戶的交期與分配風險",
      "太陽能事業淨損與爬坡延遲持續到 2027 年，對公司整體資源配置的排擠",
      "日圓避險基準 150 與材料、能源成本上升對顯示玻璃定價策略的後續調整"
    ],
    "open_questions": [
      "顯示玻璃基板漲價的具體幅度與適用期間（管理層僅說 2027 年以後反映、不揭露幅度）",
      "光通訊新的長期利潤率目標（管理層表示尚未準備好提出）",
      "DCI 新目標數字（僅說超過原 US$10 億目標、稍後另設）",
      "太陽能達到公司平均獲利率的時程（僅說緩慢改善至 2027 年，無明確時點）"
    ],
    "sources": [
      {
        "title": "Corning Delivers Outstanding Third Quarter Results（8-K Exhibit 99，2026-10-27）",
        "url": "https://www.sec.gov/Archives/edgar/data/24741/000002474126000273/glw-20261027xex99xq32026.htm",
        "media": "SEC EDGAR／Corning"
      },
      {
        "title": "Corning Incorporated Form 10-Q（quarter ended September 30, 2026）",
        "url": "https://www.sec.gov/Archives/edgar/data/24741/000002474126000279/glw-20260930.htm",
        "media": "SEC EDGAR／Corning"
      },
      {
        "title": "Corning (GLW) Q3 2026 Earnings Call Transcript",
        "url": "https://www.fool.com/earnings/call-transcripts/2026/10/27/corning-glw-q3-2026-earnings-call-transcript/",
        "media": "The Motley Fool"
      },
      {
        "title": "Earnings call transcript: Corning beats Q3 2026 estimates, stock slips",
        "url": "https://www.investing.com/news/transcripts/earnings-call-transcript-corning-beats-q3-2026-estimates-stock-slips-93CH-4975843",
        "media": "Investing.com"
      },
      {
        "title": "GLW Q3 FY2026 earnings call",
        "url": "https://finance.biggo.com/quote/GLW/earnings-call/US_GLW_2026-10-27",
        "media": "BigGo Finance"
      },
      {
        "title": "Corning Q3 2026: Optical Communications surges 44% on AI fiber demand",
        "url": "https://247wallst.com/cards/corning-q3-2026-earnings-glw-01m5ygjxkpmss5xt8bhdwb8b4d",
        "media": "24/7 Wall St."
      },
      {
        "title": "Corning Aktie: Q3 übertrifft Erwartungen, Ausblick hebt die Messlatte",
        "url": "https://goldesel.de/aktien/news/corning-aktie-q3-ubertrifft-erwartungen-ausblick-hebt-die-messlatte",
        "media": "Goldesel"
      }
    ],
    "notes": "康寧自 2026 Q1 起調整部門結構：Display 與 Specialty Materials 合併為 Glass Innovations，Hemlock 併入新設 Solar 部門，故無獨立顯示部門數字。部門層級僅揭露營收與淨利，未揭露營業利益率。GuruFocus 與康寧中文新聞稿因 403 無法讀取，Q&A 內容依據 Motley Fool 逐字稿與 Investing.com、BigGo 摘要；JPMorgan 提問者姓名各來源拼法不一故未列名。"
  },
  "recipients": [
    "A00"
  ],
  "crawled_at": "2026-11-03T23:30:43+08:00"
}

