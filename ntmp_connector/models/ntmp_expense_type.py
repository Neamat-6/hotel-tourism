from odoo import fields, models, api


class ExpenseType(models.Model):
    _name = 'ntmp.expense.type'
    _description = 'NTMP Expense Type'

    code = fields.Char(required=True, string='Expense Type ID')
    name = fields.Char(required=True, string='Expense Type EN')
