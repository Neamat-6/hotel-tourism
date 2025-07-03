from odoo import fields, models, api


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    ezee_journal_type = fields.Char('Ezee Payment Type',
                                    help='Such as: Cash, Mada Card, Visa Card, Master Card, City Ledger, ...')
    is_credit_payment = fields.Boolean('City Ledger Journal')


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    folio_id = fields.Many2one('hotel.folio')
