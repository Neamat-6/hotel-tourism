from odoo import fields, models, api


class PaymentType(models.Model):
    _name = 'ntmp.payment.type'
    _description = 'NTMP PaymentType'

    code = fields.Char(required=True, string='Type ID')
    name = fields.Char(required=True, string='Type AR')
    name_en = fields.Char(required=True, string='Type EN')
