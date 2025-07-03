
from odoo import api, fields, models

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"
    hotel = fields.Many2one('hotel.hotel', string="Hotel")



class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')

    source_booking_id = fields.Many2one('hotel.booking.line')
    hotel_id = fields.Many2one('hotel.hotel', related='source_booking_id.hotel_id', store=True)
    room_type_id = fields.Many2one('hotel.room.type', string='Room Type', related='source_booking_id.room_type_id',
                                   store=True)
    room_id = fields.Many2one('hotel.room', string='Room', related='source_booking_id.room_id', store=True)
    price = fields.Float('Price', related='source_booking_id.price', store=True)
    check_in = fields.Datetime(string='Check In', default=fields.Datetime.now(), related='source_booking_id.check_in',
                               store=True)
    check_out = fields.Datetime(string='Check Out', default=fields.Datetime.now(),
                                related='source_booking_id.check_out', store=True)
    number_of_days = fields.Integer(string='Days', related='source_booking_id.number_of_days', store=True)





