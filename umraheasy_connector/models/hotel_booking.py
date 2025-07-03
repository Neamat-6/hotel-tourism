from odoo import fields, models, api


class HotelBooking(models.Model):
    _inherit = 'hotel.booking'

    umraheasy_channel = fields.Char()
    umraheasy_booking_ref = fields.Char()
    umraheasy_cm_booking_ref = fields.Char()
    umraheasy_segment = fields.Char()
    umraheasy_pah = fields.Boolean()
    umraheasy_booking_date = fields.Datetime()
    umraheasy_apply_daily_price = fields.Boolean(string='Apply Daily Price')
