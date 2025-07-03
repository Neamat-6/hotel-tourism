# -*- coding: utf-8 -*-
import calendar
import random
from datetime import datetime, date

from dateutil.relativedelta import relativedelta

from odoo import models, api, fields


class PosDashboard(models.Model):
    _inherit = 'hotel.booking'

    @api.model
    def get_availability_company(self):
        company_string = ''
        if self.env.context.get('allowed_company_ids', False):
            company_id = self.env.context['allowed_company_ids']
            lst = [str(x) for x in company_id]
            company_string = ','.join(lst)
        return {
            'company': company_string if company_string else str(self.env.company.id)
        }

    @api.model
    def get_kanban_view(self):
        return self.env.ref('hotel_booking.res_partner_kanban_view').id

    @api.model
    def get_availability_data(self):
        days = []
        company_string = ''
        if self.env.context.get('allowed_company_ids', False):
            company_id = self.env.context['allowed_company_ids']
            lst = [str(x) for x in company_id]
            company_string = ','.join(lst)
            hotel_ids = self.env['res.company'].browse(company_id).mapped('related_hotel_id').mapped('id')
        else:
            company_id = self.env.company.ids
            hotel_ids = self.env.company.related_hotel_id.ids
        date_start = self.env.company.audit_date
        date_end = date_start + relativedelta(days=3)
        out_of_order = self.env.ref('hotel_booking.data_hotel_room_stay_status_ooo')
        total_rooms = self.env['hotel.room'].search_count([
            ('hotel_id', 'in', hotel_ids), ('stay_state', '!=', out_of_order.id)
        ])
        cancelled_folios = self.env['booking.folio'].search([
            ('state', '=', 'cancelled'), ('check_in', '!=', False), ('company_id', 'in', company_id)
        ])

        while date_start <= date_end:
            # arrival
            check_in_folios = self.env['booking.folio'].sudo().search([
                ('state', 'in', ['confirmed', 'draft']), ('company_id', 'in', company_id),
                ('check_in', '!=', False), ('check_in_date', '=', date_start)
            ])
            arrival_folios = self.env['booking.folio'].sudo().search([
                ('state', '!=', 'cancelled'), ('company_id', 'in', company_id),
                ('check_in', '!=', False), ('check_in_date', '=', date_start)
            ])
            # departure
            check_out_folios = self.env['booking.folio'].sudo().search([
                ('room_id', '!=', False), ('company_id', 'in', company_id),
                ('state', '=', 'checked_in'), ('check_in', '!=', False),
                ('check_out_date', '=', date_start)
            ])
            exp_check_out_folios = self.env['booking.folio'].sudo().search([
                ('company_id', 'in', company_id), ('check_in', '!=', False),
                ('check_out_date', '=', date_start), ('state', '!=', 'cancelled')
            ])
            # inhouse
            inhouse_folios = self.env['booking.folio'].sudo().search([
                ('check_in', '!=', False), ('company_id', 'in', company_id), ('state', '=', 'checked_in'),
                ('id', 'not in', check_out_folios.ids), ('id', 'not in', check_in_folios.ids)
            ]).filtered(lambda f:  f.check_in_date <= date_start <= f.check_out_date)
            exp_inhouse_folios = self.env['booking.folio'].sudo().search([
                ('check_in', '!=', False), ('company_id', 'in', company_id), ('state', '!=', 'cancelled'),
                ('id', 'not in', check_out_folios.ids), ('id', 'not in', exp_check_out_folios.ids), ('id', 'not in', check_in_folios.ids)
            ]).filtered(lambda f:  f.check_in_date <= date_start <= f.check_out_date)

            # allotted
            allotted_folios = self.env['booking.folio'].sudo().search([
                ('check_in', '!=', False), ('check_out', '!=', False), ('company_id', 'in', company_id), ('is_allotted', '=', True),
            ]).filtered(lambda f:  f.check_in_date <= date_start <= f.check_out_date)
            unconfirmed_allotted_folios = allotted_folios.filtered(lambda f:  f.state == 'draft')
            confirmed_allotted_folios = allotted_folios.filtered(lambda f:  f.state not in ['draft', 'cancelled'])

            cancelled_folios_lst = []
            for folio in cancelled_folios:
                if date_start in folio.get_dates_between(folio.check_in_date, folio.check_out_date):
                    cancelled_folios_lst.append(folio.id)

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
            else:
                booked_factor = 0
                exp_booked_factor = 0
            vals = [
                date_start.strftime('%d/%m'),
                date_start.strftime('%a'),
                len(check_in_folios),
                check_in_folios.ids,
                len(check_out_folios),
                check_out_folios.ids,
                total_rooms,
                booked_rooms,
                int(total_rooms - booked_rooms),
                round(booked_factor * 100, 2),
                len(cancelled_folios_lst),  # 10
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
                len(arrival_folios),
                arrival_folios.ids,
                len(unconfirmed_allotted_folios),
                unconfirmed_allotted_folios.ids,
                len(confirmed_allotted_folios),
                confirmed_allotted_folios.ids,
            ]

            days.append(vals)
            date_start += relativedelta(days=1)

        return {'days': days, 'company': company_string if company_string else str(self.env.company.id)}
