from odoo import fields, models, api


class BookingDailyPrice(models.Model):
    _name = 'booking.daily.price'
    _description = 'Booking Daily Price'

    booking_id = fields.Many2one('hotel.booking')
    booking_line_id = fields.Many2one('hotel.booking.line', ondelete='cascade')
    rate_plan_id = fields.Many2one('hotel.rate.plan')
    room_type_id = fields.Many2one('room.type', related='rate_plan_id.room_type_id', store=True)
    price_id = fields.Many2one('rate.plan.day.price')
    date = fields.Date()
    price = fields.Float()
