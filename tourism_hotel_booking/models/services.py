
from odoo import api, fields, models

class HotelServices(models.Model):
    _name = 'tourism.hotel.services'

    name = fields.Char(string="Name", required=True)
    product_id = fields.Many2one("product.product", string="Product", required=True)
    price = fields.Float(string="Price")
