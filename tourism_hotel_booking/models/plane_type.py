from odoo import api, fields, models


class PlaneType(models.Model):
    _name = 'plane.type'
    _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', tracking=True)
    class_type = fields.Selection(string="Class Type",
                                  selection=[('economy', 'Economy'), ('business', 'Business'), ('vip', 'VIP')],
                                  required=True, tracking=True)
    capacity = fields.Integer(string='Capacity', required=True)
