from odoo import fields, models, api


class Hotel(models.Model):
    _inherit = 'hotel.hotel'

    enable_umraheasy = fields.Boolean()
    umraheasy_code = fields.Char()
    umraheasy_partner_id = fields.Many2one('res.partner', domain="[('online_travel_agent', '=', True)]")
