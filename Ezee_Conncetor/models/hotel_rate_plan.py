from odoo import api, fields, models


class RatePlan(models.Model):
    _inherit = 'hotel.rate.plan'

    rate_id = fields.Char(string='Rate Plan ID')
    ezee_rate_plan_id = fields.Many2one("ezee.rate.plan",string='Ezee Rate Plan')
