from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    cashier_custody_id = fields.Many2one('cashier.custody')
