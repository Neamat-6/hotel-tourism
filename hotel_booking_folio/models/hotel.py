from odoo import fields, models, api


class Hotel(models.Model):
    _inherit = 'hotel.hotel'

    unsettled_invoice = fields.Boolean()
    allow_overbooking = fields.Boolean()
