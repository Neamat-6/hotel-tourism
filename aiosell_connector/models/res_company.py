from odoo import fields, models, api


class Company(models.Model):
    _inherit = 'res.company'

    enable_aiosell = fields.Boolean()
    aiosell_code = fields.Char(string='Aiosell Code')
