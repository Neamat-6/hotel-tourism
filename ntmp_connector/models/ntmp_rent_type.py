from odoo import fields, models, api


class RentType(models.Model):
    _name = 'ntmp.rent.type'
    _description = 'NTMP Rent Type'

    code = fields.Char(required=True, string='Rent Type Name ID')
    name = fields.Char(required=True, string='Rent Type Name AR')
    name_en = fields.Char(required=True, string='Rent Type Name EN')
