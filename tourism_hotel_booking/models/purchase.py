
from odoo import api, fields, models

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    tourism_hotel = fields.Many2one('tourism.hotel.hotel', string="Hotel")
    tourism_booking_id = fields.Many2one('tourism.hotel.booking')



class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"


    source_tourism_booking_id = fields.Many2one('tourism.hotel.booking.line')
    tourism_hotel_id = fields.Many2one('tourism.hotel.hotel', related='source_tourism_booking_id.hotel_id', store=True)
    tourism_room_type_id = fields.Many2one('tourism.hotel.room.type', string='Room Type', related='source_tourism_booking_id.room_type_id',
                                   store=True)
    tourism_room_id = fields.Many2one('tourism.hotel.room', string='Room', related='source_tourism_booking_id.room_id', store=True)
    tourism_price = fields.Float('Price', related='source_tourism_booking_id.price', store=True)
    tourism_check_in = fields.Datetime(string='Check In', default=fields.Datetime.now(), related='source_tourism_booking_id.check_in',
                               store=True)
    tourism_check_out = fields.Datetime(string='Check Out', default=fields.Datetime.now(),
                                related='source_tourism_booking_id.check_out', store=True)
    tourism_number_of_days = fields.Integer(string='Days', related='source_tourism_booking_id.number_of_days', store=True)





