from odoo import fields, models, api


class Gender(models.Model):
    _name = 'ntmp.gender'
    _description = 'NTMP Gender'

    code = fields.Char(required=True, string='Type ID')
    name = fields.Char(required=True, string='Type AR')
    name_en = fields.Char(required=True, string='Type EN')
