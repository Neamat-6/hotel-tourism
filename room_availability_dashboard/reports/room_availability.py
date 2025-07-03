from odoo import fields, models, api
from dateutil.relativedelta import relativedelta

import odoo.addons.room_availability_dashboard.controllers.controllers as RoomAvailabilityDashboardController

class RoomAvailabilityReport(models.AbstractModel):
    _name = 'report.room_availability_dashboard.room_availability_report'

    @api.model
    def _get_report_values(self, docids, data=None):
        availability_filter_apply = RoomAvailabilityDashboardController.RoomAvailabilityFilter()
        if not docids and data.get('docids', False):
            docids = data['docids']
        docs = self.env['room.availability.dashboard'].browse(docids)
        doc = docs[0]
        days = []
        date_start = doc.start_date
        date_end = doc.end_date
        params = {
            'start_date': fields.Date.to_string(date_start),
            'end_date': fields.Date.to_string(date_end),
             'company': ','.join(map(str,doc.hotel_id.company_id.ids)),
             }
        result = availability_filter_apply.availability_filter_apply(data = params)
        for day in result.get('days'):
            days.append({
                'date': day[0],
                'day': day[1],
                'check_in_count': day[2],
                'arrival_count': day[31],
                'check_out_count': day[4],
                'exp_check_out_count': day[15],
                'total_rooms': day[6],
                'booked_rooms': day[7],
                'exp_booked_rooms': day[19],
                'available_rooms': day[8],
                'exp_available_rooms': day[20],
                'occupancy': day[9],
                'exp_occupancy': day[21],
                'cancelled_count': day[10],
                'inhouse_count': day[12],
                'exp_inhouse_count': day[17],
            })
        # total_rooms = self.env['hotel.room'].search_count([('hotel_id', '=', doc.hotel_id.id)])
        # out_of_order = self.env.ref('hotel_booking.data_hotel_room_stay_status_ooo')
        # total_rooms = self.env['hotel.room'].search_count([
        #     ('hotel_id', '=', doc.hotel_id.id), ('stay_state', '!=', out_of_order.id)
        # ])

        # cancelled_folios = self.env['booking.folio'].search([
        #     ('state', '=', 'cancelled'), ('check_in', '!=', False)
        # ])

        # while date_start <= date_end:
        #     check_in_folios = self.env['booking.folio'].search([
        #         ('state', 'in', ['confirmed', 'draft']), ('check_in', '!=', False),
        #         ('check_in_date', '=', date_start),
        #     ])
        #     arrival_folios = self.env['booking.folio'].search([
        #         ('state', '!=', 'cancelled'), ('check_in', '!=', False),
        #         ('check_in_date', '=', date_start),
        #     ])
        #     check_out_folios = self.env['booking.folio'].search([
        #         ('room_id', '!=', False), ('state', '=', 'checked_in'),
        #         ('check_in', '!=', False), ('check_out_date', '=', date_start),
        #     ])
        #     exp_check_out_folios = self.env['booking.folio'].sudo().search([
        #         ('check_in', '!=', False), ('check_out_date', '=', date_start), ('state', '!=', 'cancelled')
        #     ])

        #     # inhouse
        #     inhouse_folios = self.env['booking.folio'].sudo().search([
        #         ('check_in', '!=', False), ('state', '=', 'checked_in'),
        #         ('id', 'not in', check_out_folios.ids), ('id', 'not in', check_in_folios.ids)
        #     ]).filtered(lambda f:  f.check_in_date <= date_start <= f.check_out_date)
        #     exp_inhouse_folios = self.env['booking.folio'].sudo().search([
        #         ('check_in', '!=', False), ('state', '!=', 'cancelled'),
        #         ('id', 'not in', check_out_folios.ids), ('id', 'not in', exp_check_out_folios.ids), ('id', 'not in', check_in_folios.ids)
        #     ]).filtered(lambda f:  f.check_in_date <= date_start <= f.check_out_date)

        #     booked_folios = self.env['booking.folio'].search([
        #         ('state', 'not in', ['cancelled', 'draft', 'checked_out']), ('room_id', '!=', False),
        #         ('check_in', '!=', False), ('check_in_date', '=', date_start)
        #     ])
        #     cancelled_folios_lst = []
        #     for folio in cancelled_folios:
        #         if date_start in folio.get_dates_between(folio.check_in_date, folio.check_out_date):
        #             cancelled_folios_lst.append(folio.id)

        #     booked_rooms = len(check_in_folios) + len(inhouse_folios)
        #     exp_booked_rooms = len(check_in_folios) + len(exp_inhouse_folios)
        #     if total_rooms:
        #         booked_factor = booked_rooms / total_rooms
        #         exp_booked_factor = exp_booked_rooms / total_rooms
        #     else:
        #         booked_factor = 0
        #         exp_booked_factor = 0
        #     vals = {
        #         'date': date_start.strftime('%d/%m'),
        #         'day': date_start.strftime('%a'),
        #         'check_in_count': len(check_in_folios),
        #         'arrival_count': len(arrival_folios),
        #         'check_out_count': len(check_out_folios),
        #         'exp_check_out_count': len(exp_check_out_folios),
        #         'total_rooms': total_rooms,
        #         'booked_rooms': booked_rooms,
        #         'exp_booked_rooms': exp_booked_rooms,
        #         'available_rooms': int(total_rooms - booked_rooms),
        #         'exp_available_rooms': int(total_rooms - exp_booked_rooms),
        #         'occupancy': round(booked_factor * 100, 2),
        #         'exp_occupancy': round(exp_booked_factor * 100, 2),
        #         'cancelled_count': len(cancelled_folios_lst),
        #         'inhouse_count': len(inhouse_folios),
        #         'exp_inhouse_count': len(exp_inhouse_folios),
        #     }
        #     days.append(vals)
        #     date_start += relativedelta(days=1)
        return {
            'doc_ids': docs.ids,
            'doc_model': 'room.availability.dashboard',
            'docs': docs,
            'days': days,
        }
