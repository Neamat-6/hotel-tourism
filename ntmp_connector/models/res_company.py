from odoo import fields, models, api


class Company(models.Model):
    _inherit = 'res.company'

    apply_ntmp = fields.Boolean(string='Apply NTMP', default=True)
    ntmp_username = fields.Char(string='NTMP Username')
    ntmp_password = fields.Char(string='NTMP Password')
    ntmp_key = fields.Char(string='NTMP x-Gateway-APIKey')
    ntmp_token = fields.Char(string='NTMP Authorization')  # does token have expiry date??
    ntmp_channel = fields.Char(string='NTMP Channel')


class ResPartner(models.Model):
    _inherit = 'res.partner'

    gender_id = fields.Many2one('ntmp.gender')
    customer_type_id = fields.Many2one('ntmp.customer.type')
    visit_purpose_id = fields.Many2one('ntmp.visit.purpose', string='Purpose of Visit')
