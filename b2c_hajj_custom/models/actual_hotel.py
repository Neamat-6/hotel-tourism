from odoo import fields, models, api


class ActualHotel(models.Model):
    _name = 'actual.hotel'
    _description = 'Actual Hotel Name'

    name = fields.Char()
    hotel_id = fields.Many2one('hotel.hotel')
