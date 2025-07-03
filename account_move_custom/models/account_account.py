from odoo import api, fields, models


class AccountAccount(models.Model):
    _inherit = 'account.account'

    new_account_id = fields.Many2one("account.account")
    add_account = fields.Boolean("Add Account")


