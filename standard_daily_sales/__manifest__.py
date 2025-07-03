{
  "name": "Standard Daily Sales",
  "summary": "Standard Daily Sales Report",
  "depends": ["report_xlsx_dynamic","hotel_booking"],
  "data": [
    "security/ir.model.access.csv",
    "reports/standard_daily_sales_report_action.xml",
    "wizards/standard_daily_sales_report_wizard.xml",
  ],
  "external_dependencies": {
    "python": ["toolz"],
  },
}