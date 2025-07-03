from odoo import fields, models, api


class VisitPurpose(models.Model):
    _name = 'ntmp.visit.purpose'
    _description = 'NTMP Visit purpose'
    
    name = fields.Char(required=True, string='Purpose of Visit AR')
    name_en = fields.Char(required=True, string='Purpose of Visit En')
    code = fields.Char(required=True, string='Purpose of Visit ID')
