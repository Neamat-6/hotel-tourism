from odoo import fields, models, api
import toolz as T
import toolz.curried as TC


class StandardDailySalesXlsxReport(models.AbstractModel):
  _inherit = 'report.standard_daily_sales.standard_daily_sales_xlsx_report'


  def _prepare_payment_data(self, docids, form_data):
    payment_query = """
    SELECT AJ.NAME,
      SUM(AP.AMOUNT) AS REVENUE,
      AP.AUDIT_DATE  AS DAY
      FROM ACCOUNT_PAYMENT AS AP
      INNER JOIN HOTEL_BOOKING AS HB ON HB.ID = AP.BOOKING_ID
        AND AP.AUDIT_DATE BETWEEN SYMMETRIC  %(today_date)s AND DATE_TRUNC('year', TO_DATE( %(today_date)s, 'YYYY-MM-DD'))::DATE
        AND HB.COMPANY_ID = %(company_id)s
      LEFT JOIN ACCOUNT_MOVE AS AM ON AM.ID = AP.MOVE_ID
      LEFT JOIN ACCOUNT_JOURNAL AS AJ ON AJ.ID = AM.JOURNAL_ID
    WHERE AP.POS_SESSION_ID IS NULL
    GROUP BY AJ.NAME,AP.AUDIT_DATE
    """
    self.env.cr.execute(payment_query, {
        "today_date": form_data['today_date'],
        "company_id": self.env.company.id,
    })
    payment_data = self.env.cr.dictfetchall()
    today_date = fields.Date.from_string(form_data['today_date'])
    grouped_data = T.pipe(
        payment_data,
        TC.groupby('name'),
        TC.valmap(
            TC.compose_left(
                lambda lines: self._classify_data(lines, today_date),
                TC.valmap(lambda lines: {"revenue": sum(T.pluck('revenue', lines))}),
            )),
    )
    structured_data = [
        ("title", [["Payments"]]),
        ("total", [[None, "Today", "M.T.D", "Y.T.D"]]),
    ]

    for payment_name, data in grouped_data.items():
      structured_data.append(("total", [self._prepare_line(payment_name, data)]))
    return structured_data
