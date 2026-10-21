company_key = NYSE:GLW, period = 2026Q2, 檔案數 = 4

====================================================================================================
[ir_document] docs/NYSE_GLW/2026Q2/manifest.json  (batch 000002_20260921T151017)
{
  "record_type": "ir_document",
  "company_key": "NYSE:GLW",
  "company_name": "Corning Incorporated",
  "stock_code": "GLW",
  "market": "NYSE",
  "category": "SUPPLIER",
  "period": "2026Q2",
  "fiscal_period": "2026Q2",
  "conference_date": null,
  "local_conference_date": null,
  "status": "DONE",
  "wanted": [
    "presentation",
    "financial_report"
  ],
  "missing": [],
  "files": [
    {
      "type": "financial_report",
      "file": "financial_report_20260729_5ce0dc35.htm",
      "path": "docs/NYSE_GLW/2026Q2/financial_report_20260729_5ce0dc35.htm",
      "source": "EDGAR",
      "source_url": "https://www.sec.gov/Archives/edgar/data/24741/000002474126000255/glw-20260630.htm",
      "title": "10-Q filing 2026-07-29",
      "doc_date": "2026-07-29",
      "sha256": "5ce0dc355e9ec6c0d9131ad9e698e8a2bd9951426ee3ce8f51d9b7d0c8980ac1",
      "bytes": 1754361,
      "fetched_at": "2026-09-18T12:19:38+08:00"
    },
    {
      "type": "presentation",
      "file": "presentation_20260728_a2c7d546.htm",
      "path": "docs/NYSE_GLW/2026Q2/presentation_20260728_a2c7d546.htm",
      "source": "EDGAR",
      "source_url": "https://www.sec.gov/Archives/edgar/data/24741/000002474126000253/glw-20260728xex99xq22026.htm",
      "title": "8-K EX-99 2026-07-28",
      "doc_date": "2026-07-28",
      "sha256": "a2c7d546b7a4e47e985c95c3431ac49ccf94c1c5ee44115cff1a53d8e3b1ef0e",
      "bytes": 682609,
      "fetched_at": "2026-09-18T12:21:21+08:00"
    }
  ],
  "generated_at": "2026-09-21T15:10:18+08:00"
}

====================================================================================================
[ir_document_file] docs/NYSE_GLW/2026Q2/Corning_Q2CY26_Financial_Statements.htm  (batch 000002_20260921T151017)
實體檔：/Volumes/micenter/mi3_datahub_prod/micenterfile_ext/unstructured_data_file/supplier/Corning/Corning_Q2CY26_Financial_Statements.htm
{
  "path": "docs/NYSE_GLW/2026Q2/Corning_Q2CY26_Financial_Statements.htm",
  "record_type": "ir_document_file",
  "sha256": "5ce0dc355e9ec6c0d9131ad9e698e8a2bd9951426ee3ce8f51d9b7d0c8980ac1",
  "bytes": 1754361,
  "company_key": "NYSE:GLW",
  "company_slug": "Corning",
  "category": "SUPPLIER",
  "period": "2026Q2",
  "doc_kind": "Financial_Statements",
  "fiscal_label": null,
  "source_file": "financial_report_20260729_5ce0dc35.htm",
  "source_url": "https://www.sec.gov/Archives/edgar/data/24741/000002474126000255/glw-20260630.htm",
  "doc_date": "2026-07-29"
}

====================================================================================================
[ir_document_file] docs/NYSE_GLW/2026Q2/Corning_Q2CY26_Presentation.htm  (batch 000002_20260921T151017)
實體檔：/Volumes/micenter/mi3_datahub_prod/micenterfile_ext/unstructured_data_file/supplier/Corning/Corning_Q2CY26_Presentation.htm
{
  "path": "docs/NYSE_GLW/2026Q2/Corning_Q2CY26_Presentation.htm",
  "record_type": "ir_document_file",
  "sha256": "a2c7d546b7a4e47e985c95c3431ac49ccf94c1c5ee44115cff1a53d8e3b1ef0e",
  "bytes": 682609,
  "company_key": "NYSE:GLW",
  "company_slug": "Corning",
  "category": "SUPPLIER",
  "period": "2026Q2",
  "doc_kind": "Presentation",
  "fiscal_label": null,
  "source_file": "presentation_20260728_a2c7d546.htm",
  "source_url": "https://www.sec.gov/Archives/edgar/data/24741/000002474126000253/glw-20260728xex99xq22026.htm",
  "doc_date": "2026-07-28"
}

====================================================================================================
[ir_financials] financials/NYSE_GLW.json  (batch 000030_20261016T031002)
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
      "operating_cash_flow": 2695000000,
      "current_liabilities": 5628000000,
      "current_assets": 8936000000,
      "total_liabilities": 18669000000,
      "total_assets": 30976000000,
      "derived": null,
      "source_urls": [
        "https://data.sec.gov/api/xbrl/companyfacts/CIK0000024741.json"
      ],
      "gross_margin": 35.97,
      "operating_margin": 14.58,
      "net_margin": 10.21,
      "debt_ratio": 60.27,
      "current_ratio": 1.59
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
      "operating_cash_flow": 1939000000,
      "current_liabilities": 4919000000,
      "current_assets": 7992000000,
      "total_liabilities": 16665000000,
      "total_assets": 27735000000,
      "derived": null,
      "source_urls": [
        "https://data.sec.gov/api/xbrl/companyfacts/CIK0000024741.json"
      ],
      "gross_margin": 32.6,
      "operating_margin": 8.65,
      "net_margin": 3.86,
      "debt_ratio": 60.09,
      "current_ratio": 1.62
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
      "operating_cash_flow": 2005000000,
      "current_liabilities": 4319000000,
      "current_assets": 7212000000,
      "total_liabilities": 16632000000,
      "total_assets": 28500000000,
      "derived": null,
      "source_urls": [
        "https://data.sec.gov/api/xbrl/companyfacts/CIK0000024741.json"
      ],
      "gross_margin": 31.23,
      "operating_margin": 7.07,
      "net_margin": 4.62,
      "debt_ratio": 58.36,
      "current_ratio": 1.67
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
      "operating_cash_flow": 2615000000,
      "current_liabilities": 5175000000,
      "current_assets": 7453000000,
      "total_liabilities": 17224000000,
      "total_assets": 29499000000,
      "derived": null,
      "source_urls": [
        "https://data.sec.gov/api/xbrl/companyfacts/CIK0000024741.json"
      ],
      "gross_margin": 31.76,
      "operating_margin": 10.13,
      "net_margin": 9.27,
      "debt_ratio": 58.39,
      "current_ratio": 1.44
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
      "operating_cash_flow": 3412000000,
      "current_liabilities": 4806000000,
      "current_assets": 7659000000,
      "total_liabilities": 17609000000,
      "total_assets": 30154000000,
      "derived": null,
      "source_urls": [
        "https://data.sec.gov/api/xbrl/companyfacts/CIK0000024741.json"
      ],
      "gross_margin": 35.95,
      "operating_margin": 15.0,
      "net_margin": 13.54,
      "debt_ratio": 58.4,
      "current_ratio": 1.59
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
      "operating_cash_flow_ytd": 2079000000,
      "total_assets": 32956000000,
      "total_liabilities": 19829000000,
      "current_assets": 10917000000,
      "current_liabilities": 6021000000,
      "derived": null,
      "source_urls": [
        "https://data.sec.gov/api/xbrl/companyfacts/CIK0000024741.json"
      ],
      "gross_margin": 36.14,
      "operating_margin": 15.49,
      "net_margin": 12.41,
      "debt_ratio": 60.17,
      "current_ratio": 1.81
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
      "operating_cash_flow": 362000000,
      "operating_cash_flow_ytd": 362000000,
      "total_assets": 31253000000,
      "total_liabilities": 18904000000,
      "current_assets": 9526000000,
      "current_liabilities": 5916000000,
      "derived": null,
      "source_urls": [
        "https://data.sec.gov/api/xbrl/companyfacts/CIK0000024741.json"
      ],
      "gross_margin": 36.87,
      "operating_margin": 15.42,
      "net_margin": 8.95,
      "debt_ratio": 60.49,
      "current_ratio": 1.61
    },
    {
      "period": "2025Q4",
      "period_end": "2025-12-31",
      "total_assets": 30976000000,
      "total_liabilities": 18669000000,
      "current_assets": 8936000000,
      "current_liabilities": 5628000000,
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
        "net_income"
      ],
      "source_urls": [
        "https://data.sec.gov/api/xbrl/companyfacts/CIK0000024741.json"
      ],
      "gross_margin": 35.47,
      "operating_margin": 15.94,
      "net_margin": 12.81,
      "debt_ratio": 60.27,
      "current_ratio": 1.59
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
      "operating_cash_flow_ytd": 1643000000,
      "total_assets": 29916000000,
      "total_liabilities": 17911000000,
      "current_assets": 8677000000,
      "current_liabilities": 5577000000,
      "derived": null,
      "source_urls": [
        "https://data.sec.gov/api/xbrl/companyfacts/CIK0000024741.json"
      ],
      "gross_margin": 37.07,
      "operating_margin": 14.37,
      "net_margin": 10.49,
      "debt_ratio": 59.87,
      "current_ratio": 1.56
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
      "operating_cash_flow_ytd": 859000000,
      "total_assets": 28745000000,
      "total_liabilities": 17200000000,
      "current_assets": 8196000000,
      "current_liabilities": 5475000000,
      "derived": null,
      "source_urls": [
        "https://data.sec.gov/api/xbrl/companyfacts/CIK0000024741.json"
      ],
      "gross_margin": 36.04,
      "operating_margin": 14.84,
      "net_margin": 12.14,
      "debt_ratio": 59.84,
      "current_ratio": 1.5
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
      "operating_cash_flow": 151000000,
      "operating_cash_flow_ytd": 151000000,
      "total_assets": 27394000000,
      "total_liabilities": 16266000000,
      "current_assets": 7644000000,
      "current_liabilities": 4523000000,
      "derived": null,
      "source_urls": [
        "https://data.sec.gov/api/xbrl/companyfacts/CIK0000024741.json"
      ],
      "gross_margin": 35.17,
      "operating_margin": 12.89,
      "net_margin": 4.55,
      "debt_ratio": 59.38,
      "current_ratio": 1.69
    },
    {
      "period": "2024Q4",
      "period_end": "2024-12-31",
      "total_assets": 27735000000,
      "total_liabilities": 16665000000,
      "current_assets": 7992000000,
      "current_liabilities": 4919000000,
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
      "net_margin": 8.85,
      "debt_ratio": 60.09,
      "current_ratio": 1.62
    }
  ],
  "generated_at": "2026-10-16T03:10:24"
}