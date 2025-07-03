from odoo import fields, models


class HotelServices(models.Model):
    _name = 'hotel.services'

    name = fields.Char(string="Name", required=True)
    product_id = fields.Many2one("product.product", string="Product", required=True)
    price = fields.Float(string="Price")
    type = fields.Selection(selection=[
        ('food', 'Food Package'),
        ('beverage', 'Beverage'),
        ('laundry', 'Laundry'),
        ('rent', 'Rent')
    ], required=True)
