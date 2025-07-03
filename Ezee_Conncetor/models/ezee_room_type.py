from odoo import api, fields, models


class EzeeRateType(models.Model):
    _name = 'ezee.room.type'
    _description = 'Ezee Room Type'

    name = fields.Char("Name", required=True)
    code = fields.Char(string='Ezee ID')
    short_code = fields.Char()
    base_adult_occupancy = fields.Integer()
    base_child_occupancy = fields.Integer()
    max_adult_occupancy = fields.Integer()
    max_child_occupancy = fields.Integer()
    hotel_id = fields.Many2one('hotel.hotel')
    company_id = fields.Many2one('res.company')
