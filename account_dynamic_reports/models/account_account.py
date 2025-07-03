from odoo import api, fields, models


class AccountAccount(models.Model):
    _inherit = 'account.account'

    is_filtered_account = fields.Boolean("Is Filtered Account")


