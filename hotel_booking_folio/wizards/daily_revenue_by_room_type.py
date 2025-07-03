from odoo import fields, models


class DailyRevenue(models.TransientModel):
    _inherit = 'daily.revenue'
    _description = 'Daily Revenue'

    room_type_ids = fields.Many2many('room.type')

    def get_folio_lines(self, start):
        result = super().get_folio_lines(start)
        if self.room_type_ids:
            result = result.filtered(lambda line: line.folio_id.room_type_id in self.room_type_ids)
        return result

    def get_returned_view(self):
        result = super().get_returned_view()
        if self._context.get('daily_revenue_by_room_type'):
            result = {
                **result,
                'view_id':
                    self.env.ref('hotel_booking_folio.daily_revenue_by_room_type_view_form').id,
                'name':
                    'Daily Revenue by Room Type',
            }
        return result
