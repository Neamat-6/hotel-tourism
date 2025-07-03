from odoo import api, fields, models


class RateType(models.Model):
    _inherit = 'hotel.rate.type'

    rate_type_id = fields.Char(string='Rate Type ID')
    ezee_rate_type_id = fields.Many2one("ezee.rate.type", string='Ezee Rate Type')
