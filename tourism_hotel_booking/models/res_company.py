from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    # Bank Details
    bank_name = fields.Char()
    account_name = fields.Char()
    account_number = fields.Char()
    account_iban = fields.Char()
    account_swift = fields.Char()