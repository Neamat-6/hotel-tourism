from odoo import fields, models


class DailyRevenue(models.TransientModel):
    _inherit = 'daily.revenue'
    _description = 'Daily Revenue'

    rate_plan_ids = fields.Many2many('hotel.rate.plan')


    def get_folio_lines(self,start):
        result = super().get_folio_lines(start)
        if self.rate_plan_ids:
            result = result.filtered(lambda line: line.folio_id.booking_line_id.rate_plan in self.rate_plan_ids)
        return result

    def get_returned_view(self):
        result = super().get_returned_view()
        if self._context.get('daily_revenue_by_rate_plan'):
            result = {
                **result,
                'view_id':
                    self.env.ref('hotel_booking_folio.daily_revenue_by_rate_plan_view_form').id,
                'name':
                    'Daily Revenue by Rate Plan',
            }
        return result


