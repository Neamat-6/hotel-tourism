from odoo import fields, models, api


class Product(models.Model):
    _inherit = 'product.template'

    room_charge_product = fields.Boolean()
    municipality_product = fields.Boolean()
    extra_charge_product = fields.Boolean()
