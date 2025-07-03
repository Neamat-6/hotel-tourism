# -*- coding: utf-8 -*-
import calendar
import random
from datetime import datetime

from dateutil.relativedelta import relativedelta

from odoo import models, api, fields


class HotelBookingDashboard(models.Model):
    _inherit = 'hotel.booking'

    def has_move_line(self, booking_line):
        return bool(self.env['account.move.line'].search([('source_booking_id', '=', booking_line.id)]))

    @api.model
    def get_tiles_data(self):
        audit_date = self.env.company.audit_date
        check_in_folios = self.env['booking.folio'].search([('check_in_date', '=', audit_date)])
        check_out_folios = self.env['booking.folio'].search([('check_out_date', '=', audit_date)])
        cancel_folios = self.env['booking.folio'].search([('state', '=', 'cancelled')])
        stay_rooms = self.env['hotel.room'].search([('stay_state', 'in', self.get_room_stay_status())])
        customers = self.env['res.partner'].search([('travel_type', '!=', False)])
        amount_room = self.env['booking.folio.line'].search([
            ('type', '=', 'room_charge'), ('payment_id', '=', False), ('day', '=', audit_date)
        ]).filtered(lambda fl: fl.folio_id.state != 'cancelled' and self.has_move_line(fl.folio_id.booking_line_id))
        amount_untaxed = self.env['booking.folio.line'].search([
            ('type', '!=', 'tax'), ('payment_id', '=', False), ('day', '=', audit_date)
        ]).filtered(lambda fl: fl.folio_id.state != 'cancelled' and self.has_move_line(fl.folio_id.booking_line_id))
        amount_tax = self.env['booking.folio.line'].search([
            ('type', '=', 'tax'), ('payment_id', '=', False), ('day', '=', audit_date)
        ]).filtered(lambda fl: fl.folio_id.state != 'cancelled' and self.has_move_line(fl.folio_id.booking_line_id))

        amount_room_sum = sum(amount_room.mapped('amount'))
        amount_untaxed_sum = sum(amount_untaxed.mapped('amount'))
        amount_tax_sum = sum(amount_tax.mapped('amount'))
        symbol = self.env.company.currency_id.symbol
        not_paid = self.env['booking.folio'].search([
            ('state', 'not in', ['cancelled', 'draft']), ('price_due', '>', 0)
        ])
        total_rooms = len(self.env.company.related_hotel_id.room_ids)
        if total_rooms:
            avg_room_price = amount_room_sum / total_rooms
        else:
            avg_room_price = 0

        return {
            'check_in_folios': len(check_in_folios),
            'check_out_folios': len(check_out_folios),
            'cancel_folios': len(cancel_folios),
            'stay_bookings': len(stay_rooms),
            'customers': len(customers),
            'amount_room': amount_room_sum,
            'amount_untaxed': amount_untaxed_sum,
            'amount_tax': amount_tax_sum,
            'symbol': symbol,
            'occupancy': self.env['room.type'].get_occupancy(),
            'not_paid': len(not_paid),
            'avg_room_price': avg_room_price
        }

    @api.model
    def get_top_customers(self):
        query = '''SELECT res_partner.name AS partner,sum(amount_total) AS total
                    FROM account_move
                    INNER JOIN res_partner ON res_partner.id =account_move.partner_id
                    WHERE account_move.move_type='out_invoice' AND account_move.state='posted'
                    GROUP BY res_partner.id 
                    ORDER BY total DESC Limit 10 '''
        self._cr.execute(query)
        top_customer = self._cr.dictfetchall()

        total = []
        for record in top_customer:
            total.append(record.get('total'))
        partner = []
        for record in top_customer:
            partner.append(record.get('partner'))
        final = [total, partner]

        return final
