from odoo import fields, models, api


class HotelBooking(models.Model):
    _inherit = 'hotel.booking'

    aiosell_channel = fields.Char()
    aiosell_booking_ref = fields.Char()
    aiosell_cm_booking_ref = fields.Char()
    aiosell_segment = fields.Char()
    aiosell_pah = fields.Boolean()
    aiosell_booking_date = fields.Datetime()
    aiosell_apply_daily_price = fields.Boolean(string='Apply Daily Price')
