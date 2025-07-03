from odoo import fields, models, api


class CustomerType(models.Model):
    _name = 'ntmp.customer.type'
    _description = 'Customer Type'

    code = fields.Char(required=True, string='Cust Type ID')
    name = fields.Char(required=True, string='Cust Type AR')
    name_en = fields.Char(required=True, string='Cust Type EN')
