from odoo import fields, models, api
import re
import ast

class AccountMove(models.Model):
    _inherit = 'account.move'

    ezee_unique_id = fields.Char(string='Ezee Unique ID')
    is_htask_move = fields.Boolean(string='Is Htask Move')


class Partner(models.Model):
    _inherit = 'res.partner'

    company_id = fields.Many2one(default=False, tracking=True)

    @api.model
    def create(self, vals):
        record = super().create(vals)
        if vals.get('company_id'):
            record.company_id = False
        return record


class AccountAccount(models.Model):
    _inherit = 'account.account'

    ezee_api = fields.Boolean(string='Ezee API')


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    ezee_api = fields.Boolean(string='Ezee API')
    ezee_journal_type = fields.Char('Ezee Payment Type',
                                    help='Such as: Cash, Mada Card, Visa Card, Master Card, City Ledger, ...')


class ResCompany(models.Model):
    _inherit = 'res.company'

    auth_code = fields.Char(string='Authentication Code')
    hotel_code = fields.Char(string='Hotel Code')
    max_try = fields.Char(string='Max Try')


class Logging(models.Model):
    _inherit = 'ir.logging'

    error = fields.Text(string="Error")

    def resync_payload(self):
        """Button Resync payload from logging to pos session
        called from cron job"""
        for rec in self:
            message = rec.message
            payload = ast.literal_eval(message)
            self.env['create.ezee.invoice'].sudo().create_ezee_invoice(payload)
            rec.unlink()





