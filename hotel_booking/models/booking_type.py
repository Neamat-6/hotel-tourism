from odoo import fields, models, api


class BookingType(models.Model):
    _name = 'booking.type'
    _description = 'Reservation Type'

    name = fields.Char()
