from odoo import api, fields, models


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    is_casher_journal = fields.Boolean("Cashier Journal")
    user_id = fields.Many2one('res.users', "User")
