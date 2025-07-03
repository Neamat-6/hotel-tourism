from odoo import fields, models, api


class RevenueSummaryLine(models.TransientModel):
    _inherit = 'revenue.summary.line'

    total_municipality = fields.Float(string="Total Service Charge")
