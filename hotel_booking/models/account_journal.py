from odoo import api, fields, models


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    is_city_ledger = fields.Boolean(string='City Ledger')
