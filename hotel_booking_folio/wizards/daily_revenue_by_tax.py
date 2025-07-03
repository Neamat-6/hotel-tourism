from odoo import fields, models


class DailyRevenue(models.TransientModel):
    _inherit = 'daily.revenue'
    _description = 'Daily Revenue'

    tax_revenue_mode = fields.Boolean("Tax Revenue Mode", default=False)


    def default_get(self, fields_list):
        values = super().default_get(fields_list)
        if self._context.get('daily_revenue_by_tax'):
            values['tax_revenue_mode'] = True
        return values

    def get_returned_view(self):
        result = super().get_returned_view()
        if self._context.get('daily_revenue_by_tax'):
            result = {
                **result,
                'view_id':
                    self.env.ref('hotel_booking_folio.daily_revenue_by_tax_view_form').id,
                'name':
                    'Daily Revenue by Tax',
            }
        return result
