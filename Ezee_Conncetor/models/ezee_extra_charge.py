from odoo import fields, models, api


class EzeeExtraCharge(models.Model):
    _name = 'ezee.extra.charge'
    _description = 'Ezee Extra Charge'

    name = fields.Char(required=True)
    ezee_id = fields.Char(required=True, string='Ezee ID')
    short_code = fields.Char()
    rate = fields.Float()
    hotel_id = fields.Many2one('hotel.hotel')
    company_id = fields.Many2one('res.company')
