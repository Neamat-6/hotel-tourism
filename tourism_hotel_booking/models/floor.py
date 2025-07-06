# -*- coding: utf-8 -*-
from odoo import api, fields, models


class HotelFloor(models.Model):
    _name = 'tourism.hotel.floor'
    _description = 'Hotel Floor'

    name = fields.Char(string="Floor Name", required=True)
    sequence = fields.Integer('Sequence', default=10)
    room_ids = fields.One2many('tourism.hotel.room', 'floor_id')
    hotel_id = fields.Many2one("tourism.hotel.hotel", required=True)
    room_count = fields.Integer(compute="_compute_room_count", string="No. of Rooms")

    def _compute_room_count(self):
        for floor in self:
            floor.room_count = len(floor.room_ids)