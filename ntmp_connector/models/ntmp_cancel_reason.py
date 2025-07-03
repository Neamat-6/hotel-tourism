from odoo import fields, models, api


class CancelReason(models.Model):
    _name = 'ntmp.cancel.reason'
    _description = 'NTMP Cancel Reason'

    code = fields.Char(required=True, string='Reason ID')
    name = fields.Char(required=True, string='Reason EN')
