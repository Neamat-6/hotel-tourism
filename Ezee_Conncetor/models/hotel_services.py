from odoo import fields, models, api


class HotelServices(models.Model):
    _inherit = 'hotel.services'

    ezee_charge_id = fields.Many2one('ezee.extra.charge')
