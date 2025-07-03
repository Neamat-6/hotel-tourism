from odoo import api, fields, models


class BusType(models.Model):
    _name = 'bus.type'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', tracking=True)
    capacity = fields.Integer(string='Capacity')
