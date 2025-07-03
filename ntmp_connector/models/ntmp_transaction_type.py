from odoo import fields, models, api


class TransactionType(models.Model):
    _name = 'ntmp.transaction.type'
    _description = 'NTMP Transaction Type'

    code = fields.Char(required=True, string='Type ID')
    name = fields.Char(required=True, string='Type EN')
