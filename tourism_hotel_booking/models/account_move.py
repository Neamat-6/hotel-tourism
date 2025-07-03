# -*- coding: utf-8 -*-
from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    tourism_booking_id = fields.Many2one('tourism.hotel.booking', store=True)
    tourism_booking_room_id = fields.Many2one('hotel.room', compute='_compute_tourism_booking_data', store=False)  # For the report
    tourism_booking_room_type_id = fields.Many2one('hotel.room.type', compute='_compute_tourism_booking_data',
                                           store=False)  # For the report
    visa_booking_id = fields.Many2one('visa.booking')
    transportation_booking_id = fields.Many2one('transportation.booking')
    hotel_contract_id = fields.Many2one('hotel.contract')

    def _compute_tourism_booking_data(self):
        for move in self:
            move.booking_room_id = move.tourism_booking_id.room_id
            move.booking_room_type_id = move.tourism_booking_id.room_type_id


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    tourism_source_booking_id = fields.Many2one('tourism.hotel.booking.line')
    tourism_hotel_id = fields.Many2one('hotel.hotel', related='tourism_source_booking_id.hotel_id', store=True)
    tourism_room_type_id = fields.Many2one('hotel.room.type', string='Room Type', related='tourism_source_booking_id.room_type_id',
                                   store=True)
    tourism_room_id = fields.Many2one('hotel.room', string='Room', related='tourism_source_booking_id.room_id', store=True)
    tourism_price = fields.Float('Price', related='tourism_source_booking_id.price', store=True)
    tourism_number_of_adults = fields.Integer(string='Adults', related='tourism_source_booking_id.number_of_adults', store=True)
    tourism_number_of_children = fields.Integer(string='Children', related='tourism_source_booking_id.number_of_children', store=True)
    tourism_check_in = fields.Datetime(string='Check In', default=fields.Datetime.now(), related='tourism_source_booking_id.check_in',
                               store=True)
    tourism_check_out = fields.Datetime(string='Check Out', default=fields.Datetime.now(),
                                related='tourism_source_booking_id.check_out', store=True)
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    number_of_days = fields.Float(string='Days', related='tourism_source_booking_id.date_diff', store=True)
    tourism_booking_id = fields.Many2one('tourism.hotel.booking', related='move_id.tourism_booking_id')


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    tourism_booking_id = fields.Many2one('tourism.hotel.booking')

    def _create_payment_vals_from_wizard(self):
        vals = super()._create_payment_vals_from_wizard()
        vals['tourism_booking_id'] = self.tourism_booking_id.id
        return vals


class AccountInvoice(models.Model):
    _inherit = "account.payment"

    tourism_booking_id = fields.Many2one('tourism.hotel.booking', domain=[('amount_due', '>', 0)], context={'ignore_record_rule': True})

    partner_id = fields.Many2one(related='tourism_booking_id.partner_id', readonly=False)
