# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

import pytz
from datetime import datetime, time
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class HotelRoom(models.Model):
    _inherit = 'hotel.room'

    updated_room_qty = fields.Integer('Update Qty', default=0)


class RoomAvailability(models.Model):
    _name = "room.availability"
    _description = 'Room Availability'
    _rec_name = 'company_id'


    @api.model
    def _default_date_from(self):
        return fields.Datetime.now().strftime('%Y-%m-01')

    @api.model
    def _default_date_to(self):
        return (datetime.today() + relativedelta(
            months=+1, day=1, days=-1)).strftime('%Y-%m-%d')

    @api.depends_context('company_id')
    def _default_company_id(self):
        if self.env.context.get('company_id'):
            return self.env.context.get('company_id')
        else:
            return self.env.company.id

    company_id = fields.Many2one('hotel.hotel', 'Hotel', default=lambda self: self.env.company,readonly=True)
    rooms_ids = fields.Many2many('hotel.room', string='Hotel Rooms')
    date_from = fields.Date(    string='Date From', required=True)
    date_to = fields.Date(   string='Date To',  required=True)
    room_availability_ids = fields.One2many(
        'room.availability.line',
        'room_availability_id',
        'Rooms Availability',compute='_compute_room_availability',store=True, readonly=False)
    room_type_availability_ids = fields.One2many(
        'room.type.availability.line',
        'room_availability_id',
        'Room Type Availability',compute='_compute_room_availability',store=True, readonly=False)
    state = fields.Selection(
        [('draft', 'Draft'), ('close', 'Closed')],
        default='draft')

    def get_total_contract_qty(self, room_id, checkin, checkout, hotel):
        contracts = self.env['hotel.contract.line'].search(
            [('state', '=', 'purchase'),('room_type', '=', room_id.id),('contract_id.hotel', '=', hotel),('start_date', '<=', checkin), ('end_date', '>=', checkout)])
        room_qty = sum(contracts.mapped('count'))
        return room_qty

    # @api.depends('rooms_ids', 'company_id', 'date_to','date_from')
    def _compute_room_availability(self):
        for rec in self :
            if rec.date_to and rec.date_from:
                rooms = self.env['hotel.room'].search([
                    ('hotel_id', '=', rec.company_id.id),
                    ('booking_ok', '=', True)])

                print(rooms)
                print(rec.company_id)
                all_data = []
                for room in rooms :
                    date_from = rec.date_from
                    date_to = rec.date_to
                    while (date_from <= date_to):
                        contract_qty = self.get_total_contract_qty(room, date_from, date_to, rec.company_id.id)
                        room_available = self.env['room.availability.line'].search([
                        ('date', '=', date_from),
                        ('room_category_id', '=', room.id),
                        ('company_id', '=', rec.company_id.id)], limit=1)
                        if not room_available:
                            all_data.append({'contract_qty':contract_qty,'room_qty':0,'date':date_from,'room_category_id':room.id,'company_id':rec.company_id.id})
                        date_from += relativedelta(days=1)
                print(all_data)
                rec.room_availability_ids = [(0, 0, line) for line in all_data]

    @api.constrains('date_from', 'date_to')
    def check_in_out_dates(self):
        """
        When date_to is less then date_from or
        date_to should be greater than the date_from date.
        """
        if self.date_to and self.date_from:
            if self.date_to < self.date_from:
                raise ValidationError(_('End date should be greater \
                                         than Start date.'))

    def copy(self, *args, **argv):
        raise UserError(_('You cannot duplicate a room availability.'))


class RoomAvailabilityLine(models.Model):
    _name = "room.availability.line"
    _description = 'Room Availability Line'

    room_availability_id = fields.Many2one(
        'room.availability', ondelete="cascade")
    room_category_id = fields.Many2one(
        'hotel.room', 'Room Category', required=True)
    date = fields.Date(
        'Date', default=fields.Date.context_today, required=True)
    room_qty = fields.Integer('Room Qty')
    contract_qty = fields.Integer('Contract Qty')
    room_cost_price = fields.Float('Room Price')
    company_id = fields.Many2one(
        'hotel.hotel', 'Company', related='room_availability_id.company_id', store=True)
    close = fields.Boolean("Close")


class RoomTypeAvailabilityLine(models.Model):
    _name = "room.type.availability.line"
    _description = 'Room Availability By Type'

    room_availability_id = fields.Many2one(
        'room.availability', ondelete="cascade")
    room_type = fields.Many2one('room.type')
    room_id = fields.Many2one(
        'hotel.room', 'Room Category', required=True)
    date = fields.Date(
        'Date', default=fields.Date.context_today, required=True)
    room_qty = fields.Integer('Room Qty')
    contract_qty = fields.Integer('Contract Qty')
    room_cost_price = fields.Float('Room Price')
    company_id = fields.Many2one(
        'hotel.hotel', 'Company', related='room_availability_id.company_id', store=True)
    close = fields.Boolean("Close")
    state = fields.Many2one('hotel.room.status')


class HotelReservationLine(models.Model):
    _inherit = "hotel.booking.line"

    def get_qty_from_avaliability(self, room, checkin, checkout):
        if not checkin:
            checkin = self.checkin
        if not checkout:
            checkout = self.checkout
        check_out_date = checkout
        if checkin != checkout:
            check_out_date = checkout + relativedelta(days=-1)
        self._cr.execute("""SELECT MIN(room_qty) FROM room_availability_line
                                WHERE room_category_id=%s
                                AND company_id=%s
                                AND date BETWEEN %s AND %s""",
                         (room.id, hotel, checkin, check_out_date))
        qty = self._cr.fetchone()[0]
        if qty:
            return qty
        return False

    def check_room_closing_status(self, room, checkin=False, checkout=False, hotel=False):
        if not checkin:
            checkin = self.checkin
        if not checkout:
            checkout = self.checkout
        check_out_date = checkout
        if checkin != checkout:
            check_out_date = (self.checkout + relativedelta(days=-1))
        self._cr.execute("""SELECT id FROM room_availability_line
                            WHERE room_category_id=%s AND close=True
                            AND date BETWEEN %s AND %s
                            AND company_id=%s""",
                         (room.id, checkin, check_out_date,
                          hotel))
        status = self._cr.fetchone()
        if status:
            return True
        return False

    def get_total_room_qty(self, room, checkin, checkout, hotel):
        self._cr.execute("""SELECT MIN(room_qty) FROM room_availability_line
                            WHERE room_category_id=%s AND
                            date BETWEEN %s AND %s
                            AND company_id=%s""",
                         (room.id, checkin, checkout, hotel))
        qty = self._cr.fetchone()[0]
        if qty:
            return qty
        return False

    def get_booked_room_qty(self, room_id, checkin, checkout, hotel):

        query = """SELECT count as qty FROM
                            hotel_booking_line WHERE check_dir = True AND  room_id=%s
                            AND (%s,%s) OVERLAPS (check_in, check_out)
                            AND hotel_id=%s AND booking_state IN %s """
        args = (room_id, checkin, checkout, hotel, ('checked_in', 'confirmed', 'paid'))
        self.env.cr.execute(query, args)
        data = self.env.cr.dictfetchall()
        if not data:
            query = """SELECT count as qty FROM
                                hotel_booking_line as hbl
                                JOIN booking_line_room_rel as blr ON (hbl.id=blr.booking_line_id)
                                WHERE blr.room_id=%s
                                AND (%s,%s) OVERLAPS (hbl.check_in, hbl.check_out)
                                AND hbl.hotel_id=%s AND hbl.booking_state IN %s """
            args = (room_id, checkin, checkout, hotel, ('checked_in', 'confirmed', 'paid'))
            self.env.cr.execute(query, args)
            data = self.env.cr.dictfetchall()
        room_qty = 0
        for line in data:
            room_qty += line['qty']
        if room_qty is None:
            room_qty = 0
        return room_qty

    def get_booked_room_data(self, room_id, checkin, checkout, hotel):
        query = """SELECT id  FROM
                            hotel_booking_line WHERE check_dir = True AND  room_id=%s AND
                            (%s,%s) OVERLAPS (check_in, check_out)
                            AND hotel_id=%s """
        args = (room_id, checkin, checkout, hotel)
        self.env.cr.execute(query, args)
        data = self.env.cr.dictfetchall()
        booking_name = False
        for line in data:
            if line['id']:
                booking_name += self.env['hotel.booking.line'].browse(line['id']).booking_id.name

        return booking_name

    def get_total_contract_qty(self, room_id, checkin, checkout, hotel):
        contracts = self.env['hotel.contract.line'].search(
            [('state', '=', 'purchase'),('room_type', '=', room_id.id),('contract_id.hotel', '=', hotel),('start_date', '<=', checkin), ('end_date', '>=', checkout)])
        room_qty = sum(contracts.mapped('count'))
        return room_qty

    def get_cost_qty(self, room_id, checkin, checkout, hotel):
        contracts = self.env['hotel.contract.line'].search(
            [('state', '=', 'purchase'),('room_type', '=', room_id.id), ('contract_id.hotel', '=', hotel), ('start_date', '<=', checkin),
             ('end_date', '>=', checkout)])
        room_qty = sum(contracts.mapped('price'))
        return room_qty

    def is_reserved(self, room, date):
        x = self.env['hotel.booking.line'].search([
            ('room_id', '=', room.id), ('check_in', '>=', date), ('check_out', '<=', date)
        ])
        return x

    def get_room_value_from_daterange(self, room_id, start_date, end_date, hotel):
        booked_folios = []
        if room_id and start_date and end_date:
            date_start = datetime.strptime(start_date, DEFAULT_SERVER_DATE_FORMAT).date()
            date_end = datetime.strptime(end_date, DEFAULT_SERVER_DATE_FORMAT).date()
            room_type = self.env['room.type'].browse(room_id)
            query = """
            WITH REPORT_PER_DAY AS (
                WITH TOTAL_ROOMS_PER_TYPE AS (
                    SELECT
                        COUNT(*) AS CONTRACT_QTY,
                        HR.ROOM_TYPE,
                        RT.PRICE AS ROOM_TYPE_PRICE,
                        RT.NAME AS ROOM_TYPE_NAME,
                        HR.COMPANY_ID
                    FROM HOTEL_ROOM AS HR
                    LEFT JOIN ROOM_TYPE AS RT ON HR.ROOM_TYPE = RT.ID
                    GROUP BY HR.ROOM_TYPE,HR.COMPANY_ID,RT.PRICE,RT.NAME
                ),
                DAYS AS (SELECT generate_series(%(date_start)s::date,%(date_end)s::date,'1 day')::date AS date
                )
            SELECT * FROM DAYS JOIN TOTAL_ROOMS_PER_TYPE ON 1 =1
            ),
            BOOKED_PER_DAY_ROOM_TYPE AS (
                    SELECT
                        BFL.DAY AS DATE,
                        RT.ID AS ROOM_TYPE,
                        RT.PRICE AS PRICE,
                        0 AS TOTAL_QTY,
                        0 AS CLOSED,
                        COUNT(BFL.*) AS BOOKED
                    FROM BOOKING_FOLIO_LINE AS BFL
                    INNER JOIN BOOKING_FOLIO AS BF ON BF.ID = BFL.FOLIO_ID
                        AND BF.STATE != 'cancelled'
                        AND BF.COMPANY_ID IS NOT NULL
                        AND BF.ROOM_TYPE_ID IS NOT NULL
                        AND BF.COMPANY_ID =%(company_id)s
                        AND BFL.PARTICULARS = 'Room Charge'
                    LEFT JOIN ROOM_TYPE AS RT ON BF.ROOM_TYPE_ID = RT.ID
                    GROUP BY BFL.DAY,RT.ID
                ),
				OUT_OF_ORDER_DAYS AS (
				WITH DAYS AS (SELECT generate_series(%(date_start)s::date,%(date_end)s::date,'1 day')::date AS date)
				SELECT DAYS.DATE, HR.ROOM_TYPE, COUNT(*) AS OUT_OF_ORDER
				FROM DAYS
				LEFT JOIN HOTEL_ROOM AS HR ON DAYS.DATE BETWEEN HR.OUT_OF_ORDER_FROM AND HR.OUT_OF_ORDER_TO
				WHERE HR.COMPANY_ID = %(company_id)s
				GROUP BY DAYS.DATE,	HR.ROOM_TYPE
				)
            SELECT
                RPD.DATE,
                RPD.CONTRACT_QTY,
                0 AS TOTAL_QTY,
                0 AS CLOSED,
                COALESCE (SUM(BPDRT.BOOKED),0) AS BOOKED,
                COALESCE (SUM(OFO.OUT_OF_ORDER),0) AS OUT_OF_ORDER,
                RPD.ROOM_TYPE_PRICE AS PRICE,
                RPD.CONTRACT_QTY - COALESCE (SUM(BPDRT.BOOKED),0)  - COALESCE (SUM(OFO.OUT_OF_ORDER),0) AS AVAIL,
                RPD.ROOM_TYPE_NAME AS NAME,
                COALESCE (SUM(BPDRT.BOOKED),0) / RPD.CONTRACT_QTY  AS OCCUPANCY
            FROM REPORT_PER_DAY AS RPD
            LEFT JOIN BOOKED_PER_DAY_ROOM_TYPE AS BPDRT ON BPDRT.DATE = RPD.DATE AND BPDRT.ROOM_TYPE = RPD.ROOM_TYPE
            LEFT JOIN OUT_OF_ORDER_DAYS AS OFO ON OFO.DATE = RPD.DATE AND OFO.ROOM_TYPE = RPD.ROOM_TYPE
            WHERE RPD.COMPANY_ID = %(company_id)s AND RPD.ROOM_TYPE = %(room_type_id)s
            GROUP BY RPD.DATE,RPD.CONTRACT_QTY,RPD.ROOM_TYPE,RPD.COMPANY_ID,RPD.ROOM_TYPE_PRICE,RPD.ROOM_TYPE_NAME
            ORDER BY RPD.DATE ASC
                """
            self.env.cr.execute(query, {'date_start': date_start, 'date_end': date_end, 'company_id': hotel, 'room_type_id': room_type.id})
            booked_folios = self.env.cr.dictfetchall()
        return booked_folios

    def get_inventory_by_room_type(self, room_type_id, date_start, date_end, hotel):
        datas = []
        room_type_dict = {}
        room_type = False
        if room_type_id and date_start and date_end:
            room_type = self.env['room.type'].browse(room_type_id)
            while date_start <= date_end:
                all_rooms_count = len(room_type.room_ids)
                booked_rooms_count = 0
                for room in room_type.room_ids:
                    booked_rooms_count += self.get_booked_room_qty(room.id, date_start, date_end, hotel)
                vals = {
                    'month': date_start.strftime('%b'),
                    'date': date_start.strftime('%d'),
                    'day': date_start.strftime('%a'),
                    'ref': date_start,
                    'all_rooms_count': all_rooms_count,
                    'booked_rooms_count':   booked_rooms_count or 0,
                    'available_rooms_count':  all_rooms_count - booked_rooms_count,
                }
                datas.append(vals)
                date_start += relativedelta(days=1)
        if room_type:
            room_type_dict[room_type] = datas
        return room_type_dict

    def get_occupancy_per_day(self, date_start, date_end, company_id):
        query = """
            WITH REPORT_PER_DAY AS (
                WITH TOTAL_ROOMS_PER_TYPE AS (
                    SELECT
                        COUNT(*) AS CONTRACT_QTY,
                        HR.ROOM_TYPE,
                        HR.COMPANY_ID
                    FROM HOTEL_ROOM AS HR
                    GROUP BY HR.ROOM_TYPE,HR.COMPANY_ID
                ),
                DAYS AS (SELECT generate_series(%(date_start)s::date,%(date_end)s::date,'1 day')::date AS date
                )
            SELECT * FROM DAYS JOIN TOTAL_ROOMS_PER_TYPE ON 1 =1
            ),
            BOOKED_PER_DAY_ROOM_TYPE AS (
                    SELECT
                        BFL.DAY AS DATE,
                        RT.ID AS ROOM_TYPE,
                        0 AS TOTAL_QTY,
                        0 AS CLOSED,
                        COUNT(BFL.*) AS BOOKED
                    FROM BOOKING_FOLIO_LINE AS BFL
                    INNER JOIN BOOKING_FOLIO AS BF ON BF.ID = BFL.FOLIO_ID
                        AND BF.STATE != 'cancelled'
                        AND BF.COMPANY_ID IS NOT NULL
                        AND BF.ROOM_TYPE_ID IS NOT NULL
                        AND BF.COMPANY_ID = %(company_id)s
                        AND BFL.PARTICULARS = 'Room Charge'
                    LEFT JOIN ROOM_TYPE AS RT ON BF.ROOM_TYPE_ID = RT.ID
                    GROUP BY BFL.DAY,RT.ID
                )
            SELECT
                RPD.DATE,
                sum(RPD.CONTRACT_QTY),
                0 AS TOTAL_QTY,
                0 AS CLOSED,
                COALESCE (SUM(BPDRT.BOOKED),0) AS BOOKED,
                COALESCE (SUM(BPDRT.BOOKED),0) / sum(RPD.CONTRACT_QTY)  AS OCCUPANCY
            FROM REPORT_PER_DAY AS RPD
            LEFT JOIN BOOKED_PER_DAY_ROOM_TYPE AS BPDRT ON BPDRT.DATE = RPD.DATE AND BPDRT.ROOM_TYPE = RPD.ROOM_TYPE
            WHERE RPD.COMPANY_ID = %(company_id)s
            GROUP BY RPD.DATE,RPD.COMPANY_ID
            ORDER BY RPD.DATE ASC
        """
        self.env.cr.execute(query, {'date_start': date_start, 'date_end': date_end, 'company_id': company_id})
        occupancy_per_day = self.env.cr.dictfetchall()
        final_data = {str(day.get("date")):round(day.get("occupancy",0),3) for day in occupancy_per_day}
        return final_data