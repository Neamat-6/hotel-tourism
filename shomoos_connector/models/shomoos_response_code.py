from odoo import fields, models, api


class ShomoosResponseCode(models.Model):
    _name = 'shomoos.response.code'

    api_name = fields.Char(required=True)
    api_category = fields.Selection(
        selection=[('success', 'Success'), ('no_data', 'No Data found'), ('failed', 'Failed'),('invalid_data', 'Invalid Information')], required=True)
    fault_code = fields.Integer(required=True)
    fault_description = fields.Text(required=True)
