from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    is_copied = fields.Boolean(copy=False)
