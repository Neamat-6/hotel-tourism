from odoo import fields, models, api


class HotelBedType(models.Model):
    _name = 'hotel.bed.type'
    _description = 'Hotel Bed Type'

    name = fields.Char(required=True)
