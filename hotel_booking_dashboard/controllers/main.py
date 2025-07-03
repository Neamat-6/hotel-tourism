# -*- coding: utf-8 -*-
import datetime

from odoo import http
from odoo.http import request


class BookingFilter(http.Controller):

    @http.route('/booking/filter-apply', auth='public', type='json')
    def booking_filter_apply(self, **kw):
        stay_over = request.env.ref('hotel_booking.data_hotel_room_stay_status').id
        arrived = request.env.ref('hotel_booking.data_hotel_room_stay_status_arrived').id
        folio_domain = [('type', '!=', 'tax'), ('payment_id', '=', False), ('company_id', '=', request.env.company.id)]
        tax_folio_domain = [('type', '=', 'tax'), ('payment_id', '=', False), ('company_id', '=', request.env.company.id)]
        room_folio_domain = [('type', '=', 'room_charge'), ('payment_id', '=', False), ('company_id', '=', request.env.company.id)]

        stay_booking_selected = [room.id for room in request.env['hotel.room'].search(
            [('company_id', '=', request.env.company.id), ('stay_state', 'in', [stay_over, arrived])])]
        customer_selected = [partner.id for partner in request.env['res.partner'].search(
            [('travel_type', '!=', False), '|', ('company_id', '=', request.env.company.id), ('company_id', '=', False)])]

        data = kw['data']
        start_date = data['start_date']
        end_date = data['end_date']
        # checking the dates are selected or not
        if start_date != 'null' and end_date != 'null':
            start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()

            check_in_booking_selected = [booking.id for booking in request.env['booking.folio'].search([('check_in_date', '>=', start_date), ('check_in_date', '<=', end_date), ('state', 'not in', ['cancelled']), ('company_id', '=', request.env.company.id)])]
            check_out_booking_selected = [booking.id for booking in request.env['booking.folio'].search([('check_out_date', '>=', start_date), ('check_out_date', '<=', end_date), ('state', 'not in', ['cancelled']), ('company_id', '=', request.env.company.id)])]
            cancel_booking_selected = [booking.id for booking in request.env['booking.folio'].search([('check_in_date', '>=', start_date), ('check_in_date', '<=', end_date), ('state', '=', 'cancelled'), ('company_id', '=', request.env.company.id)])]

            folio_domain.append(('day', '>=', start_date))
            folio_domain.append(('day', '<=', end_date))
            tax_folio_domain.append(('day', '>=', start_date))
            tax_folio_domain.append(('day', '<=', end_date))
            room_folio_domain.append(('day', '>=', start_date))
            room_folio_domain.append(('day', '<=', end_date))
        elif start_date == 'null' and end_date != 'null':
            end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
            start_date = end_date

            check_in_booking_selected = [booking.id for booking in request.env['booking.folio'].search([('check_in_date', '<=', end_date), ('state', 'not in', ['cancelled']), ('company_id', '=', request.env.company.id)])]
            check_out_booking_selected = [booking.id for booking in request.env['booking.folio'].search([('check_out_date', '<=', end_date), ('state', 'not in', ['cancelled']), ('company_id', '=', request.env.company.id)])]
            cancel_booking_selected = [booking.id for booking in request.env['booking.folio'].search([('check_in_date', '<=', end_date), ('state', '=', 'cancelled'), ('company_id', '=', request.env.company.id)])]
            folio_domain.append(('day', '<=', end_date))
            tax_folio_domain.append(('day', '<=', end_date))
            room_folio_domain.append(('day', '<=', end_date))
        elif start_date != 'null' and end_date == 'null':
            start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date = start_date

            check_in_booking_selected = [booking.id for booking in request.env['booking.folio'].search([('check_in_date', '>=', start_date), ('state', 'not in', ['cancelled']), ('company_id', '=', request.env.company.id)])]
            check_out_booking_selected = [booking.id for booking in request.env['booking.folio'].search([('check_out_date', '>=', start_date), ('state', 'not in', ['cancelled']), ('company_id', '=', request.env.company.id)])]
            cancel_booking_selected = [booking.id for booking in request.env['booking.folio'].search([('check_in_date', '>=', start_date), ('state', '=', 'cancelled'), ('company_id', '=', request.env.company.id)])]
            folio_domain.append(('day', '>=', start_date))
            tax_folio_domain.append(('day', '>=', start_date))
            room_folio_domain.append(('day', '>=', start_date))
        else:
            start_date = datetime.date.today()
            end_date = datetime.date.today()

            check_in_booking_selected = [booking.id for booking in request.env['booking.folio'].search([('check_in_date', '=', datetime.date.today()), ('state', 'not in', ['cancelled'])])]
            check_out_booking_selected = [booking.id for booking in request.env['booking.folio'].search([('check_out_date', '=', datetime.date.today()), ('state', 'not in', ['cancelled'])])]
            cancel_booking_selected = [booking.id for booking in request.env['booking.folio'].search([('state', '=', 'cancelled'), ('company_id', '=', request.env.company.id)])]
            folio_domain.append(('day', '=', datetime.date.today()))
            tax_folio_domain.append(('day', '=', datetime.date.today()))
            room_folio_domain.append(('day', '=', datetime.date.today()))

        folio_lines = request.env['booking.folio.line'].search(folio_domain).filtered(lambda fl: request.env['hotel.booking'].has_move_line(fl.folio_id.booking_line_id))
        amount_untaxed_selected = sum([folio_line.amount for folio_line in folio_lines])
        tax_folio_lines = request.env['booking.folio.line'].search(tax_folio_domain).filtered(lambda fl: request.env['hotel.booking'].has_move_line(fl.folio_id.booking_line_id))
        amount_tax_selected = sum([folio_line.amount for folio_line in tax_folio_lines])
        room_folio_lines = request.env['booking.folio.line'].search(room_folio_domain).filtered(lambda fl: request.env['hotel.booking'].has_move_line(fl.folio_id.booking_line_id))
        amount_room_selected = sum([folio_line.amount for folio_line in room_folio_lines])
        occupancy = request.env['room.type'].get_occupancy(start_date, end_date, request.env.company.related_hotel_id.id)
        total_rooms = len(request.env.company.related_hotel_id.room_ids)
        if total_rooms:
            avg_room_price = amount_room_selected / total_rooms
        else:
            avg_room_price = 0

        return {
            'check_in_booking': check_in_booking_selected,
            'check_out_booking': check_out_booking_selected,
            'cancel_booking': cancel_booking_selected,
            'stay_booking': stay_booking_selected,
            'customer': customer_selected,
            'amount_untaxed': amount_untaxed_selected,
            'amount_tax': amount_tax_selected,
            'amount_room': amount_room_selected,
            'occupancy': str(round(occupancy, 2)) + '%',
            'avg_room_price': round(avg_room_price, 2),
        }
