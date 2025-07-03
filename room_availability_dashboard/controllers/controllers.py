# -*- coding: utf-8 -*-
import datetime
import re

from odoo import http, SUPERUSER_ID
from odoo.http import request, content_disposition
from dateutil.relativedelta import relativedelta
# rrule
from dateutil.rrule import rrule, DAILY
import toolz as T
import toolz.curried as TC


class RoomAvailabilityFilter(http.Controller):

    @http.route('/availability/filter-apply', auth='public', type='json')
    def availability_filter_apply(self, **kw):
        days = []
        data = kw['data']
        start_date = data['start_date']
        end_date = data['end_date']
        company_split = data['company'].split(',')
        company = [int(x) for x in company_split]
        hotel = request.env['res.company'].browse(company).mapped('related_hotel_id').mapped('id')
        out_of_order = request.env.ref('hotel_booking.data_hotel_room_stay_status_ooo')
        # out of order at date of filter
        total_rooms = request.env['hotel.room'].search_count([
            ('hotel_id', 'in', hotel), ('stay_state', '!=', out_of_order.id)
        ])
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

        cancelled_folios = request.env['booking.folio'].search([
            ('state', '=', 'cancelled'), ('check_in', '!=', False), ('company_id', 'in', company)
        ])

        while start_date <= end_date:
            #arrival
            check_in_folios = request.env['booking.folio'].sudo().search([
                ('state', 'in', ['confirmed', 'draft']), ('company_id', 'in', company),
                ('check_in', '!=', False), ('check_in_date', '=', start_date)
            ])
            arrival_folios = request.env['booking.folio'].sudo().search([
                ('state', '!=', 'cancelled'), ('company_id', 'in', company),
                ('check_in', '!=', False), ('check_in_date', '=', start_date)
            ])
            actual_check_in_folios = request.env['booking.folio'].sudo().search([
                ('state', '=', 'checked_in'), ('company_id', 'in', company),
                ('check_in', '!=', False), ('check_in_date', '=', start_date)
            ])
            check_out_folios = request.env['booking.folio'].sudo().search([
                ('room_id', '!=', False), ('company_id', 'in', company),
                ('state', '=', 'checked_in'), ('check_in', '!=', False),
                ('check_out_date', '=', start_date)
            ])
            actual_check_out_folios = request.env['booking.folio'].sudo().search([
                ('room_id', '!=', False), ('company_id', 'in', company),
                ('state', '=', 'checked_out'), ('check_in', '!=', False),
                ('check_out_date', '=', start_date)
            ])
            exp_check_out_folios = request.env['booking.folio'].sudo().search([
                ('company_id', 'in', company), ('check_in', '!=', False),
                ('check_out_date', '=', start_date), ('state', '!=', 'cancelled')
            ])
            actual_inhouse_folios = request.env['booking.folio'].sudo().search([
                ('check_in', '!=', False), ('company_id', 'in', company), ('state', '=', 'checked_in'),
            ]).filtered(lambda f:  f.check_in_date <= start_date < f.check_out_date)
            dash_inhouse_folios = request.env['booking.folio'].sudo().search([
                ('check_in', '!=', False), ('company_id', 'in', company), ('state', 'in', ['checked_in', 'draft', 'confirmed']),
            ]).filtered(lambda f:  f.check_in_date <= start_date < f.check_out_date)
            inhouse_folios = request.env['booking.folio'].sudo().search([
                ('check_in', '!=', False), ('company_id', 'in', company), ('state', '=', 'checked_in'),
                ('id', 'not in', check_out_folios.ids), ('id', 'not in', check_in_folios.ids),
            ]).filtered(lambda f:  f.check_in_date <= start_date <= f.check_out_date)

            exp_inhouse_folios = request.env['booking.folio'].sudo().search([
                ('check_in', '!=', False), ('company_id', 'in', company), ('state', '!=', 'cancelled'),
                ('id', 'not in', check_out_folios.ids), ('id', 'not in', exp_check_out_folios.ids), ('id', 'not in', check_in_folios.ids),
            ]).filtered(lambda f:  f.check_in_date <= start_date <= f.check_out_date)
            # allotted
            allotted_folios = request.env['booking.folio'].sudo().search([
                ('check_in', '!=', False), ('check_out', '!=', False), ('company_id', 'in', company), ('is_allotted', '=', True),
            ]).filtered(lambda f:  f.check_in_date <= start_date <= f.check_out_date)
            unconfirmed_allotted_folios = allotted_folios.filtered(lambda f:  f.state == 'draft')
            confirmed_allotted_folios = allotted_folios.filtered(lambda f:  f.state not in ['draft', 'cancelled'])


            booked_rooms = len(check_in_folios) + len(inhouse_folios)
            booked_folio_ids = check_in_folios.ids
            booked_folio_ids.extend(inhouse_folios.ids)
            # exp
            exp_booked_rooms = len(check_in_folios) + len(exp_inhouse_folios)
            exp_booked_folio_ids = check_in_folios.ids
            exp_booked_folio_ids.extend(exp_inhouse_folios.ids)
            if total_rooms:
                booked_factor = booked_rooms / total_rooms
                exp_booked_factor = exp_booked_rooms / total_rooms
                dash_factor = len(actual_inhouse_folios) / total_rooms
                dash_factor2 = len(dash_inhouse_folios) / total_rooms
            else:
                booked_factor = 0
                exp_booked_factor = 0
                dash_factor = 0
                dash_factor2 = 0
            # cancelled
            cancelled_folios_lst = []
            for folio in cancelled_folios:
                dates_lst = folio.get_dates_between(folio.check_in_date, folio.check_out_date)
                if start_date in dates_lst:
                    cancelled_folios_lst.append(folio.id)
            # adults
            total_adults_count = 0
            total_child_count = 0
            for f in check_in_folios:
                total_adults_count += f.room_type_id.mini_adults
            for f in check_in_folios:
                total_child_count += f.room_type_id.mini_children

            vals = (
                start_date.strftime('%d/%m'),
                start_date.strftime('%a'),
                len(check_in_folios),
                check_in_folios.ids,
                len(check_out_folios),
                check_out_folios.ids,
                total_rooms,
                booked_rooms,
                int(total_rooms - booked_rooms),
                round(booked_factor * 100, 2),
                len(cancelled_folios_lst),  #10
                cancelled_folios_lst,
                len(inhouse_folios),
                inhouse_folios.ids,
                booked_folio_ids,
                len(exp_check_out_folios),
                exp_check_out_folios.ids,
                len(exp_inhouse_folios),
                exp_inhouse_folios.ids,
                exp_booked_rooms,
                int(total_rooms - exp_booked_rooms),  # 20
                round(exp_booked_factor * 100, 2),
                exp_booked_folio_ids,
                total_adults_count,
                total_child_count,
                len(actual_check_in_folios),
                len(actual_check_out_folios),
                len(actual_inhouse_folios),
                len(dash_inhouse_folios),
                round(dash_factor * 100, 2),
                round(dash_factor2 * 100, 2),  # 30
                len(arrival_folios),
                arrival_folios.ids,
                len(unconfirmed_allotted_folios),
                unconfirmed_allotted_folios.ids,
                len(confirmed_allotted_folios),
                confirmed_allotted_folios.ids,
            )

            days.append(vals)
            start_date += relativedelta(days=1)
        # print(days)
        return {
            'days': days
        }

    @http.route('/availability/download', type='http', auth="public", website=True)
    def download_availability_report(self, **kw):
        data = kw['data']
        start_date = data['start_date']
        end_date = data['end_date']
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
            end_date = start_date + relativedelta(days=3)
        wizard = request.env['room.availability.dashboard'].sudo().create({
            'hotel_id': request.env.company.related_hotel_id.id,
            'start_date': start_date,
            'end_date': end_date,
        })

        report_sudo = request.env.ref('room_availability_dashboard.action_room_availability_report').with_user(SUPERUSER_ID)
        method_name = '_render_qweb_pdf'
        report = getattr(report_sudo, method_name)([wizard.id], data={'report_type': 'pdf'})[0]
        reporthttpheaders = [
            ('Content-Type', 'application/pdf'), ('Content-Length', len(report)),
        ]
        filename = "RoomAvailability.pdf"
        reporthttpheaders.append(('Content-Disposition', content_disposition(filename)))
        return request.make_response(report, headers=reporthttpheaders)


    # get all room types
    @http.route('/availability/get_room_types', auth='public', type='json')
    def get_room_types(self, **kw):
        query = """
        SELECT RT.ID AS ROOM_TYPE_ID,
            RT.NAME AS ROOM_TYPE_NAME,
            HR.SEQUENCE AS ROOM_NUMBER,
            HR.ID AS ROOM_ID
        FROM HOTEL_ROOM AS HR
        LEFT JOIN ROOM_TYPE AS RT ON RT.ID = HR.ROOM_TYPE
        WHERE HR.COMPANY_ID = %(company_id)s
        """

        company_id = int(kw.get('data',{}).get('company',0))
        request.env.cr.execute(query, {'company_id': company_id})
        room_types = request.env.cr.dictfetchall()
        grouped_room_types = T.pipe(
            room_types,
            TC.groupby('room_type_id'),

        )
        room_types = request.env['room.type'].search([('company_id','=',company_id)])
        return {
            'room_types':{room_type.id:room_type.name for room_type in room_types},
            'grouped_room_type_details': grouped_room_types,
        }


    # get room name
    @http.route('/availability/get_room_name', auth='public', type='json')
    def get_room_name(self, **kw):
        room_type_id = kw.get('data',{}).get('room_type_id','')
        company_id = int(kw.get('data',{}).get('company',0))
        room_ids = request.env['hotel.room'].search([('room_type_id','=',room_type_id),('company_id','=',company_id)]).mapped('name')
        return {
            'room_ids': room_ids
        }