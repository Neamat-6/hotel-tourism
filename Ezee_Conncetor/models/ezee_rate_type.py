from odoo import api, fields, models


class EzeeRateType(models.Model):
    _name = 'ezee.rate.type'
    _description = 'Ezee Rate Type'

    name = fields.Char("Name", required=True)
    code = fields.Char(string='ID')
    hotel_id = fields.Many2one('hotel.hotel')
    company_id = fields.Many2one('res.company')
