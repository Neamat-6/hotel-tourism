# -*- coding: utf-8 -*-
from odoo import api, fields, models


class TourismHotelRoomType(models.Model):
    _name = 'tourism.hotel.room.type'
    _description = 'Tourism Hotel Room Type'

    name = fields.Char(string="Room Type", required=True)
    hotel_id = fields.Many2one("tourism.hotel.hotel", required=True)
    default_number_of_guest = fields.Integer(string="Default No of Guest", default=1)


