from odoo import fields, models, api


class RoomTypeAvailability(models.Model):
    _name = 'room.type.availability'
    _description = 'Room Type Availability'

    booking_id = fields.Many2one('hotel.booking')
    room_type_id = fields.Many2one('room.type')
    qty_available = fields.Integer()
    date = fields.Date()
