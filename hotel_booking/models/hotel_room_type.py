# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError

import toolz as T
import toolz.curried as TC

class RoomType(models.Model):
    _name = 'room.type'
    _description = 'Hotel Room Type'

    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    room_ids = fields.One2many('hotel.room', 'room_type')
    rate_plan_ids = fields.One2many('hotel.rate.plan', 'room_type_id')
    room_count = fields.Integer(compute='compute_room_count')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, required=True)
    mini_adults = fields.Integer(default=1)
    mini_children = fields.Integer(default=1)
    max_adults = fields.Integer(default=1)
    max_children = fields.Integer(default=1)
    price = fields.Float()
    is_virtual = fields.Boolean()
    image = fields.Image()

    @api.constrains('mini_adults', 'max_adults')
    def check_adults(self):
        for rec in self:
            if rec.mini_adults > rec.max_adults:
                raise ValidationError(_('Minimum Adults must be less than Maximum Adults'))

    @api.constrains('mini_children', 'max_children')
    def check_children(self):
        for rec in self:
            if rec.mini_children > rec.max_children:
                raise ValidationError(_('Minimum Children must be less than Maximum Children'))

    @api.depends('room_ids')
    def compute_room_count(self):
        for rec in self:
            if rec.room_ids:
                rec.room_count = len(rec.room_ids)
            else:
                rec.room_count = False

    def action_view_rooms(self):
        return {
            'name': _('Rooms'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'view_type': 'form',
            'res_model': 'hotel.room',
            'domain': [('room_type', '=', self.id)],
            'target': 'current',
        }

    @api.model
    def get_room_type_data(self, hotel):
        # room_types = self.env['room.type'].search([('hotel_id', '=', hotel)])
        hotel_id = self.env['hotel.hotel'].browse(hotel)
        room_types = self.env['room.type'].search([('company_id', '=', hotel)])
        datas = []
        for room_type in room_types:
            vals = {
                'id': room_type.id,
                'name': room_type.name,
                'hotel_id': [hotel_id.id, hotel_id.name],
                'room_ids': [[room.id, room.name, room.state.color] for room in room_type.room_ids]
            }
            datas.append(vals)
        return datas

    def get_room_bookings(self, room, date, hotel):
        if hotel:
            query = """SELECT id  FROM
            hotel_booking_line WHERE check_dir = True AND  room_id=%s AND
            check_out >= %s AND check_in <= %s
            AND hotel_id=%s """
            args = (room, date, date, hotel)
            self.env.cr.execute(query, args)
            data = self.env.cr.dictfetchall()
            booking_name = ""
            for line in data:
                if line['id']:
                    booking_name += self.env['hotel.booking.line'].browse(line['id']).booking_id.name
            return booking_name

    def get_room_type_data_from_daterange(self, type_id, start_date, end_date,hotel):
        query = """
        WITH STAY_VIEW AS (
                WITH
                    DAYS AS (
                        SELECT GENERATE_SERIES(%(start_date)s::date,%(end_date)s::date,'1 day')::date AS date
                    ),
                    REPORT_PER_DAY AS (
                        WITH
                            HOTEL_ROOM AS (
                                    SELECT HR.ROOM_TYPE,HR.COMPANY_ID,HR.ID AS ROOM_ID
                                    FROM HOTEL_ROOM AS HR
                                )
                        SELECT * FROM DAYS
                        JOIN HOTEL_ROOM ON 1 = 1
                    ),
                    UNUSSIGNED_BOOKING AS (
                        SELECT
                            BFL.DAY AS DATE,
                            RT.ID AS ROOM_TYPE,
                            BF.COMPANY_ID,
                            BFL.ROOM_ID AS ROOM_ID,
                            HB.ID AS BOOKING_ID,
                            HB.NAME AS BOOKING_NAME,
                            RT.NAME,
                            RP.NAME AS PARTNER_NAME

                        FROM BOOKING_FOLIO_LINE AS BFL
                        INNER JOIN BOOKING_FOLIO AS BF ON BF.ID = BFL.FOLIO_ID
                            AND BF.STATE != 'cancelled'
                            AND BF.COMPANY_ID IS NOT NULL
                            AND BF.ROOM_TYPE_ID IS NOT  NULL
                            AND BF.COMPANY_ID = %(company_id)s
                            AND BFL.PARTICULARS = 'Room Charge'
                        LEFT JOIN ROOM_TYPE AS RT ON BF.ROOM_TYPE_ID = RT.ID
                        LEFT JOIN RES_PARTNER AS RP ON RP.ID = BF.PARTNER_ID
                        LEFT JOIN HOTEL_BOOKING AS HB ON HB.ID = BF.BOOKING_ID
                        WHERE BFL.ROOM_ID IS NULL AND RT.ID = 8
                        ORDER BY BFL.DAY
                    ),
                    BOOKED_PER_DAY_ROOM_TYPE AS (
                        SELECT
                            BFL.DAY AS DATE,
                            RT.ID AS ROOM_TYPE,
                            RT.NAME,
                            HB.ID AS BOOKING_ID,
                            HB.NAME AS BOOKING_NAME,
                            BFL.ROOM_ID AS ROOM_ID,
                            RP.NAME AS PARTNER_NAME

                        FROM BOOKING_FOLIO_LINE AS BFL
                        INNER JOIN BOOKING_FOLIO AS BF ON BF.ID = BFL.FOLIO_ID
                            AND BF.STATE != 'cancelled'
                            AND BF.COMPANY_ID IS NOT NULL
                            AND BF.ROOM_TYPE_ID IS NOT NULL
                            AND BF.COMPANY_ID = %(company_id)s
                            AND BFL.PARTICULARS = 'Room Charge'
                        LEFT JOIN ROOM_TYPE AS RT ON BF.ROOM_TYPE_ID = RT.ID
                        LEFT JOIN RES_PARTNER AS RP ON RP.ID = BF.PARTNER_ID
                        LEFT JOIN HOTEL_BOOKING AS HB ON HB.ID = BF.BOOKING_ID
                        ORDER BY BFL.DAY
                    ),
		            OUT_OF_ORDER_DAYS AS (
                        SELECT DAYS.DATE,HR.ID, HR.ROOM_TYPE, COUNT(*) AS OUT_OF_ORDER
                        FROM DAYS
                        LEFT JOIN HOTEL_ROOM AS HR ON DAYS.DATE BETWEEN HR.OUT_OF_ORDER_FROM AND HR.OUT_OF_ORDER_TO
                        WHERE HR.COMPANY_ID = %(company_id)s
                        GROUP BY DAYS.DATE,	HR.ROOM_TYPE,HR.ID
                        )
                SELECT
                    RPD.*,
                    BPDRT.BOOKING_ID AS BOOKING_ID,
                    CASE WHEN RPD.ROOM_ID IN (SELECT ID FROM OUT_OF_ORDER_DAYS) THEN 'Out of order' ELSE COALESCE(BPDRT.BOOKING_NAME,'Vacant') END AS BOOKING_NAME,
                    BPDRT.NAME,
                    COALESCE(BPDRT.PARTNER_NAME,'') AS PARTNER_NAME
                FROM REPORT_PER_DAY AS RPD
                LEFT JOIN BOOKED_PER_DAY_ROOM_TYPE AS BPDRT ON BPDRT.DATE = RPD.DATE
                    AND BPDRT.ROOM_TYPE = RPD.ROOM_TYPE
                    AND BPDRT.ROOM_ID = RPD.ROOM_ID
                UNION
                SELECT * FROM UNUSSIGNED_BOOKING
            )
            SELECT *,'' as ROOM_STATE,'' as COLOR FROM STAY_VIEW

            WHERE ROOM_TYPE = %(type_id)s AND DATE BETWEEN %(start_date)s AND %(end_date)s
            ORDER BY DATE"""
        self.env.cr.execute(query, {'start_date': start_date, 'end_date': end_date, 'type_id': type_id,
                                    'company_id': hotel})
        datas = self.env.cr.dictfetchall()
        grouped_data = T.pipe(
            datas,
            TC.groupby('room_id')
        )
        return grouped_data