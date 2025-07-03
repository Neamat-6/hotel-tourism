# -*- coding: utf-8 -*-
import datetime
import re

from odoo import http, SUPERUSER_ID
from odoo.http import request, content_disposition
from dateutil.relativedelta import relativedelta


class InternalDashboardController(http.Controller):

    @http.route('/internal-dashboard/filter-apply', auth='public', type='json')
    def internal_dashboard_filter_apply(self, **kw):
        days = []
        data = kw['data']
        start_date = data['start_date']
        end_date = data['end_date']
        company_split = data['company'].split(',')
        company = [int(x) for x in company_split]
        hotel = request.env['res.company'].browse(company).mapped('related_hotel_id').mapped('id')
        out_of_order = request.env.ref('hotel_booking.data_hotel_room_stay_status_ooo')
        stay_over = request.env.ref('hotel_booking.data_hotel_room_stay_status')
        arrived = request.env.ref('hotel_booking.data_hotel_room_stay_status_arrived')
        arrival = request.env.ref('hotel_booking.data_hotel_room_stay_status_arrival')
        due_out = request.env.ref('hotel_booking.data_hotel_room_stay_status_duo_out')
        vacant = request.env.ref('hotel_booking.hotel_room_stay_status_vacant')
        dirty = request.env.ref('hotel_booking.hotel_room_status_dirty')
        clean = request.env.ref('hotel_booking.hotel_room_status_clean')
        # out of order at date of filter
        total_rooms = request.env['hotel.room'].search([('hotel_id', 'in', hotel)])
        # checking the dates are selected or not
        if start_date != 'null' and end_date != 'null':
            start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
        elif start_date == 'null' and end_date != 'null':
            end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
            start_date = end_date
        elif start_date != 'null' and end_date == 'null':
            start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date = start_date
        else:
            start_date = request.env.company.audit_date
            end_date = request.env.company.audit_date

        while start_date <= end_date:
            # ooo rooms
            total_ooo_rooms = request.env['hotel.room'].search([
                ('hotel_id', 'in', hotel), ('stay_state', '=', out_of_order.id),
            ]).filtered(lambda r:  r.out_of_order_from <= start_date <= r.out_of_order_to)
            # net total rooms
            net_total_rooms = total_rooms - total_ooo_rooms
            # stay-over rooms
            stay_over_rooms = request.env['hotel.room'].search([
                ('stay_state', 'in', [stay_over.id, arrived.id]), ('hotel_id', 'in', hotel)
            ])
            # due-out
            due_out_rooms = request.env['hotel.room'].search([('stay_state', '=', due_out.id), ('hotel_id', 'in', hotel)])
            # checked-out vacant rooms
            checked_out_vacant_rooms = request.env['booking.folio'].sudo().search([
                ('room_id', '!=', False), ('company_id', 'in', company), ('state', '=', 'checked_out'),
                ('check_in', '!=', False), ('check_out_date', '=', start_date)
            ]).filtered(lambda f: f.room_id.stay_state.id == vacant.id).mapped('room_id')
            # dirty arrival/stay-over rooms
            dirty_rooms = request.env['hotel.room'].search([
                ('stay_state', 'in', [stay_over.id, arrived.id]), ('state', '=', dirty.id), ('hotel_id', 'in', hotel)
            ])
            # dirty vacant rooms
            dirty_vacant_rooms = request.env['hotel.room'].search([
                ('stay_state', '=', vacant.id), ('state', '=', dirty.id), ('hotel_id', 'in', hotel)
            ])
            # clean vacant rooms
            clean_vacant_rooms = request.env['hotel.room'].search([
                ('stay_state', '=', vacant.id), ('state', '=', clean.id), ('hotel_id', 'in', hotel)
            ])
            # assigned rooms
            assigned_rooms = request.env['booking.folio'].sudo().search([
                ('room_id', '!=', False), ('company_id', 'in', company),
                ('state', '!=', 'cancelled'), ('check_in', '!=', False)
            ]).filtered(lambda f: f.room_id.stay_state.id == arrival.id).mapped('room_id')
            vals = (
                start_date.strftime('%d/%m'),
                total_rooms.ids,
                total_ooo_rooms.ids,
                net_total_rooms.ids,
                stay_over_rooms.ids,
                due_out_rooms.ids,
                checked_out_vacant_rooms.ids,
                dirty_rooms.ids,
                dirty_vacant_rooms.ids,
                clean_vacant_rooms.ids,
                assigned_rooms.ids,
            )
            days.append(vals)
            start_date += relativedelta(days=1)

        return {'data': days}
