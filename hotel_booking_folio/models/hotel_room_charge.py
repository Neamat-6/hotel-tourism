from odoo import fields, models, api


class HotelRoomCharge(models.Model):
    _name = 'hotel.room.charge'
    _description = 'Hotel Room Charge'

    name = fields.Char(required=True)
    charge_type = fields.Selection([
        ('manual', 'Manual'),
        ('cancellation', 'Cancellation'),
        ('no_show', 'No Show'),
        ('early', 'Early'),
        ('late', 'Late'),
    ], required=True)
