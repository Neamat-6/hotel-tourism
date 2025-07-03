from odoo import _, api, fields, models


class StandardDailySalesReportWizard(models.TransientModel):
  _name = 'standard.daily.sales.report.wizard'
  _description = 'Standard Daily Sales Report Wizard'

  today_date = fields.Date(
      string='Today Date',
      required=True,
      default=fields.Date.today,
  )

  def action_generate_report(self):
    data = {
        'today_date': self.today_date,
    }
    return self.env.ref('standard_daily_sales.standard_daily_sales_xlsx_action').report_action(
        self,
        data=data,
    )
