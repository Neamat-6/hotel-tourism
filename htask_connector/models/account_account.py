from odoo import fields, models, api


class Account(models.Model):
    _inherit = 'account.account'

    ezee_account_name = fields.Char('Ezee Particular Name')
