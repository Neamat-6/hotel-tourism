from odoo import api, fields, models


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    is_advanced_journal = fields.Boolean("Advanced Journal")
