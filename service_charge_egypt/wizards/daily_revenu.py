from odoo import fields, models, api


class DailyRevenue(models.TransientModel):
    _inherit = 'daily.revenue'

    filter_municipality = fields.Boolean("Include Service Charge")



class DailyRevenueLine(models.TransientModel):
    _inherit = 'daily.revenue.line'

    total_municipality = fields.Float(string="Total Service Charge")
