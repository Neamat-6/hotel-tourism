# -*- coding: utf-8 -*-
from odoo import fields, models


class HotelFloor(models.Model):
    _name = 'hotel.floor'
    _description = 'Hotel Floor'

    name = fields.Char(string="Floor Name", required=True)
    sequence = fields.Integer('Sequence', default=10)
    room_ids = fields.One2many('hotel.room', 'floor_id')
    hotel_id = fields.Many2one("hotel.hotel", required=True)
    room_count = fields.Integer(compute="_compute_room_count", string="No. of Rooms")
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, required=True)
    floor_level = fields.Selection(string="Floor Level", selection=[('lower', 'Lower'), ('middle', 'Middle'), ('upper', 'Upper')], required=False)

    def _compute_room_count(self):
        for floor in self:
            floor.room_count = len(floor.room_ids)
