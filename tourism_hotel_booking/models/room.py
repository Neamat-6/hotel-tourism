# -*- coding: utf-8 -*-
from odoo import api, fields, models


class HotelRoom(models.Model):
    _inherit = 'hotel.room'
    _description = 'Hotel Room'


    tourism_booking_line_id = fields.Many2one('tourism.hotel.booking.line')

