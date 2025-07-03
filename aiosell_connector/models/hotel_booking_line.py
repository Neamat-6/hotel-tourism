from odoo import fields, models, api


class BookingLine(models.Model):
    _inherit = 'hotel.booking.line'

    def get_price_unit(self, booking_line, day):
        price_unit = super(BookingLine, self).get_price_unit(booking_line, day)
        if booking_line.booking_id.aiosell_apply_daily_price:
            price_unit = booking_line.rate_plan.sudo().rock_rate
            price_id = booking_line.booking_id.daily_price_ids.filtered(
                lambda
                    p: p.date == day and p.room_type_id.id == booking_line.room_type.id and p.rate_plan_id.id == booking_line.rate_plan.id
            )
            if price_id:
                price_id.booking_line_id = booking_line.id
                price_unit = price_id.price
        return price_unit
