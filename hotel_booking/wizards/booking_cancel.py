from odoo import fields, models, api


class BookingCancel(models.TransientModel):
    _name = 'booking.cancel'
    _description = 'Booking Cancel'

    booking_id = fields.Many2one('hotel.booking')
    reason_id = fields.Many2one('booking.cancel.reason')

    def button_cancel(self):
        self.booking_id.cancel_reason_id = self.reason_id.id
        self.booking_id.state = 'cancelled'
