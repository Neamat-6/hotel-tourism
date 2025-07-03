from odoo import fields, models, api


class RatePlan(models.Model):
    _inherit = 'hotel.rate.plan'

    umraheasy_code = fields.Char()
