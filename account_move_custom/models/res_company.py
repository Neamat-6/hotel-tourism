from odoo import fields, models, api, _


class ResCompany(models.Model):
    _inherit = "res.company"

    target_company = fields.Boolean("Target Company")
