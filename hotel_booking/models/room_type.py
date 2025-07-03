# -*- coding: utf-8 -*-
from odoo import api, fields, models


class HotelRoomType(models.Model):
    _name = 'hotel.room.type'
    _description = 'Hotel Room Type'

    name = fields.Char(string="Room Type", required=True)
    hotel_id = fields.Many2one("hotel.hotel", required=True)
    default_number_of_guest = fields.Integer(string="Default No of Guest", default=1)


