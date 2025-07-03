from odoo import fields, models, api


class HotelDefaultRoom(models.Model):
    _name = 'hotel.default.room'
    _description = 'Hotel Default Room'

    product_id = fields.Many2one('product.product', 'Product_id',
                                 required=True, delegate=True,
                                 ondelete='cascade')

    floor_id = fields.Many2one('hotel.floor')
    sequence = fields.Integer('Sequence', default=10)
    booking_ok = fields.Boolean('Can be booked', default=True)
    telephone_extension = fields.Char(string='Telephone Ext.')
    room_size = fields.Char(string="Room Size")
    note = fields.Text()
