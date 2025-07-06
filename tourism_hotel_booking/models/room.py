# -*- coding: utf-8 -*-
from odoo import api, fields, models


class HotelRoom(models.Model):
    _name = 'tourism.hotel.room'
    _description = 'Hotel Room'

    product_id = fields.Many2one('product.product', 'Product_id',
                                 required=True, delegate=True,
                                 ondelete='cascade')
    floor_id = fields.Many2one('tourism.hotel.floor')
    room_c = fields.Float('Room Count')

    hotel_id = fields.Many2one('tourism.hotel.hotel')
    sequence = fields.Integer('Sequence', default=10)
    booking_ok = fields.Boolean('Can be booked', default=True)
    room_type_id = fields.Many2one('tourism.hotel.room.type', string='Room Type')
    facility_line_ids = fields.Many2many('tourism.hotel.room.facility')
    telephone_extension = fields.Char(string='Telephone Ext.')
    image_ids = fields.One2many('tourism.hotel.room.image', 'room_id')
    # booking_id = fields.Many2one('hotel.booking', string="Booking #")
    booking_line_id = fields.Many2one('hotel.booking.line')
    room_size = fields.Char(string="Room Size")
    note = fields.Text()

    room_vvv = fields.Float('Room avalible after booking')
    price = fields.Float('price', default=1.0)


class TourismHotelRoomFacility(models.Model):
    _name = 'tourism.hotel.room.facility'
    _description = 'Hotel Room Facility'

    facility_id = fields.Char(string="Facility")
    description = fields.Text(string="Description")
    qty = fields.Integer(default=1)
    image = fields.Binary(string="Image")


class TourismHotelRoomImage(models.Model):
    _name = 'tourism.hotel.room.image'
    _description = 'Hotel Room Image'

    room_id = fields.Many2one('tourism.hotel.room')
    image = fields.Binary(string='Image', required=True)
    name = fields.Char(string="Description")
