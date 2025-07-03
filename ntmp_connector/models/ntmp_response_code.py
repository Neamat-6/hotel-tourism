from odoo import fields, models, api


class ResponseCode(models.Model):
    _name = 'ntmp.response.code'
    _description = 'NTMP Response Code'

    api_name = fields.Char(required=True)
    category = fields.Selection(selection=[
        ('success', 'Success'), ('validation', 'Validation Error'), ('technical', 'Technical Error')
    ], required=True)
    http_code = fields.Char(required=True)
    error_code = fields.Char(required=True)
    error_description = fields.Text(required=True)
