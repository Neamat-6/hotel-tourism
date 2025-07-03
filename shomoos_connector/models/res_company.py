from odoo import fields, models, api


class Company(models.Model):
    _inherit = 'res.company'

    apply_shomoos = fields.Boolean(string="Apply Shomoos")
    shomoos_user_id = fields.Char(string='Shomoos UserID')
    shomoos_request_id = fields.Char(string='Shomoos RequestID')
    shomoos_branch_code = fields.Char(string='Shomoos Branch Code')
    shomoos_branch_secret = fields.Char(string='Shomoos Branch Secret')
    shomoos_key = fields.Char(string='Shomoos APIKey')
    shomoos_lang = fields.Char(string='Shomoos Lang')
