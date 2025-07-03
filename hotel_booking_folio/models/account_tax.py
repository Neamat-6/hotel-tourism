from odoo import fields, models, api


class Tax(models.Model):
    _inherit = 'account.tax'

    type = fields.Selection(selection=[
        ('vat', 'VAT'), ('municipality', 'Municipality')
    ], default='vat', required=True)
