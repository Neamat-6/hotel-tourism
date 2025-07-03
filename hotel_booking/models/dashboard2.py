# -*- coding: utf-8 -*-
import ast
import calendar
import json
from datetime import datetime, timedelta, date
from odoo import api, fields, models
from odoo.exceptions import UserError


COL_WIDTH = "150px"


class HotelBookingDashboard(models.TransientModel):
    _name = 'hotel.booking.dashboard2'
    _description = 'Hotel Dashboard Booking'

    def default_dates(self):
        today = datetime.now().date()
        return {
            'date_from': today.replace(day=1),
            'date_to': today.replace(day=calendar.monthrange(today.year, today.month)[1]),
        }

    name = fields.Char(default='Booking Dashboard')
    hotel_id = fields.Many2one("hotel.hotel")
    date_from = fields.Date(default=lambda x: x.default_dates()['date_from'])
    date_to = fields.Date(default=lambda x: x.default_dates()['date_to'])
    search_room_type_ids = fields.Many2many('hotel.room.type', domain="[('hotel_id','=',hotel_id)]")
    search_room_ids = fields.Many2many('hotel.room', domain="[('hotel_id','=',hotel_id)]")
    search_floor_ids = fields.Many2many('hotel.floor', domain="[('hotel_id','=',hotel_id)]")
    search_facilities_ids = fields.Many2many('hotel.facility')
    display_mode = fields.Selection([('all', 'All'), ('vacant_only', 'With Vacancy'), ('booked_only', 'Booked'), ], default="all")
    booking_screen = fields.Text()
    # booking_screen2 = fields.Text(compute="compute_booking_screen")
    booking_screen_color = fields.Char()
    view_type = fields.Selection([('view1', 'view1'), ('view2', 'view2')])

    # def compute_booking_screen(self):
    #     for dashboard in self:
    #         dashboard.booking_screen2 = dashboard.booking_screen

    def save_screen_color(self):
        if not self.booking_screen_color:
            raise UserError("Choose a colour !")

        self.env.user.write({
            'hotel_booking_screen_color': self.booking_screen_color
        })
        self.update_result()

    def check_dates(self):
        if self.date_from > self.date_to:
            raise UserError("Date From shouldn\'t before Date To !")
        # days = (self.date_to - self.date_from).days+1
        # if days > 31:
        #     raise UserError("Date range should be maximum 31 days ! !")

    @staticmethod
    def get_dates_between(date1, date2):
        my_list = []
        for n in range(int((date2 - date1).days) + 1):
            my_list.append(date1 + timedelta(n))
        return my_list

    def save_selected_hotel(self):
        self.env.user.write({'hotel_booking_dashboard_hotel_id': self.hotel_id})

    def save_selected_view(self):
        self.env.user.write({'hotel_booking_dashboard_view_type': self.view_type})

    def update_result(self):
        self.ensure_one()
        self.check_dates()
        self.save_selected_hotel()
        self.save_selected_view()
        data = self.dashboard_data(date_from=self.date_from, date_to=self.date_to)
        self.update(data)

    def button_search(self):
        self.update_result()

    def button_staying(self):
        self.ensure_one()
        action = self.env.ref('hotel_booking.action_hotel_booking').read()[0]
        booking_ids = self.env['hotel.room'].search([('booking_id', '!=', False)]).mapped('booking_id')
        if not booking_ids:
            raise UserError("Nothing Found.")
        action['domain'] = [('id', 'in', booking_ids.ids)]
        action['target'] = "new"
        action['help'] = "No records"
        return action

    def button_overdue(self):
        self.ensure_one()
        action = self.env.ref('hotel_booking.action_hotel_booking').read()[0]
        overdue_booking_ids = self.env['hotel.booking'].search([('state', '!=', 'cancelled')]).filtered(lambda x: x.amount_due > 0)
        if not overdue_booking_ids:
            raise UserError("Nothing Found.")
        action['domain'] = [('id', 'in', overdue_booking_ids.ids)]
        action['target'] = "new"
        action['help'] = "No records"
        return action

    @api.model
    def default_get(self, _fields):
        res = super(HotelBookingDashboard, self).default_get(_fields)
        data = self.dashboard_data()
        for field, val in data.items():
            res[field] = val
        return res

    def get_rooms_sorted(self, hotel_id=None):
        rooms = []
        for floor in self.env['hotel.floor'].search([('hotel_id', '=', hotel_id or -1)], order='sequence'):
            for room in floor.room_ids.sorted('sequence'):

                if self.search_room_ids:
                    if room.id not in self.search_room_ids.ids:
                        continue

                if self.search_room_type_ids:
                    if room.room_type_id.id not in self.search_room_type_ids.ids:
                        continue

                if self.search_floor_ids:
                    if room.floor_id.id not in self.search_floor_ids.ids:
                        continue

                if self.search_facilities_ids:
                    f1 = set(self.search_facilities_ids.ids)
                    f2 = set(room.facility_line_ids.filtered(lambda x: x.qty > 0).mapped('facility_id').ids)

                    if not f1.issubset(f2):
                        continue

                if room.booking_ok:
                    rooms.append(room)
        return rooms

    def dashboard_data(self, date_from=False, date_to=False):
        view_type = self.view_type or self.env.user.hotel_booking_dashboard_view_type or "view1"

        if view_type == "view1":
            return self.dashboard_data_view1(date_from=date_from, date_to=date_to)

        if view_type == "view2":
            return self.dashboard_data_view2(date_from=date_from, date_to=date_to)

        raise NotImplementedError

    def dashboard_data_view1(self, date_from=False, date_to=False):
        booking_obj = self.env['hotel.booking']
        booking_line_obj = self.env['hotel.booking.line']
        hotel_id = booking_obj.get_default_hotel_id()

        if not date_from:
            date_from = self.default_dates()['date_from']
        if not date_to:
            date_to = self.default_dates()['date_to']

        booking_data = booking_obj.sudo().get_booking_data(date_from=date_from, date_to=date_to)
        booking_data = booking_obj.booking_data_fill_blank_room(booking_data, room_ids=self.get_rooms_sorted(hotel_id))

        check_in_point_utc, check_out_point_utc = booking_line_obj.get_check_points_utc()

        data = {'hotel_id': hotel_id, 'view_type': 'view1'}
        screen = [[]]

        # Set Heading
        screen[0] += [{"class": "bsv-td-cell", "body": [{"type": "icon", "icon": 'fa-home', "class": "bsv-home-icon"}]}]
        for date in self.get_dates_between(date_from, date_to):
            screen[0] += [{"class": "bsv-td-cell", "body": [{"type": "text", "text": date.strftime('%d %b'), "class": "bsv-col-head"}]}]

        # Set Values
        room_ids = self.get_rooms_sorted(hotel_id=hotel_id)

        row = 0
        for room_id in room_ids:
            row += 1
            row_data = [{"class": "bsv-td-cell", "body": [{"type": "action", "text": room_id.name, "class": "bsv-row-head", "model": "hotel.room", "res_id": room_id.id, "flags": {'mode': 'readonly'}}]}]

            col = 0
            for date in self.get_dates_between(date_from, date_to):
                col += 1
                booking = self.env["hotel.booking"].get_booking(date=date, room_id=room_id, data=booking_data)

                # If customer left before end
                if booking and booking.get('actual_check_in') and booking.get('actual_check_out'):
                    if date not in self.get_dates_between(booking['actual_check_in'].date(), booking['actual_check_out'].date()):
                        booking = False

                text = booking and "BOOKED" or False
                if room_id.booking_line_id:
                    b = room_id.booking_line_id
                    if b.actual_check_in < fields.Datetime.now():
                        status = b.get_datetime_status(b.actual_check_in, fields.Datetime.now())
                        paid_date_list = b.get_paid_dates(status)
                        if date in paid_date_list:
                            text = "IN"

                if text == "BOOKED":
                    row_data += [{"class": "bsv-td-cell-booked", "body": [
                        {"type": "icon", "icon": 'fa-calendar-check-o', "class": "bsv-btn-hotel-booked-icon", "model": "hotel.booking", "res_id": booking['id']},
                        {"type": "action", "text": booking['name'], "class": "bsv-btn-hotel-booked", "model": "hotel.booking", "res_id": booking['id']},
                    ]}]
                elif text == "IN":
                    booking = booking or {"name": "---", "id": -1}
                    row_data += [
                        {"class": "bsv-td-cell-booked", "body": [{"type": "icon", "icon": 'fa-bed', "class": "bsv-btn-hotel-stay-icon", "model": "hotel.booking", "res_id": booking['id']},
                        {"type": "action", "text": booking['name'], "class": "bsv-btn-hotel-booked", "model": "hotel.booking", "res_id": booking['id']},
                    ]}]

                else:
                    booking_datetime = datetime(year=date.year, month=date.month, day=date.day, hour=0, minute=0, second=0) + timedelta(hours=check_in_point_utc)

                    ctx = {"default_line_ids": [
                        (0, 0, {
                            'check_in': str(booking_datetime),
                            'check_out': str(booking_datetime),
                            'room_id': room_id.id,
                            'room_type_id': room_id.room_type_id.id,
                            'pricelist_id': booking_line_obj.get_pricelist(hotel_id=hotel_id, room_type_id=room_id.room_type_id.id, room_id=room_id.id),
                            'number_of_days': booking_line_obj.get_number_of_days(booking_datetime, booking_datetime),
                        })
                    ]}

                    # ctx = {
                    #     'default_check_in': str(booking_datetime),
                    #     'default_check_out': str(booking_datetime),
                    #     'default_room_id': room_id.id,
                    #     'default_room_type_id': room_id.room_type_id.id,
                    # }

                    row_data += [{"class": "bsv-td-cell-schedule", "body": [
                            {"type": "action", "text": "SCHEDULE", "class": "bsv-btn-hotel-schedule", "model": "hotel.booking", "context": ctx}
                    ]}]
            screen.append(row_data)

        #####################################################################
        # screen[0].append({"type": "col_head", "icon": 'fa-home', "col_width": COL_WIDTH,})
        # for date in self.get_dates_between(date_from, date_to):
        #     screen[0].append({
        #         "type": "col_head",
        #         "col_width": COL_WIDTH,
        #         "name": date.strftime('%d %b')
        #     })
        #
        # # Set Values
        # room_ids = self.get_rooms_sorted(hotel_id=hotel_id)
        #
        # row = 0
        # for room_id in room_ids:
        #     row += 1
        #
        #     row_data = [
        #         {"type": "button_action", "name": room_id.name, "model": "hotel.room", "res_id": room_id.id},
        #     ]
        #
        #     col = 0
        #     for date in self.get_dates_between(date_from, date_to):
        #         col += 1
        #         booking = self.get_booking(date=date, room_id=room_id, data=booking_data)
        #
        #         text = booking and "BOOKED" or False
        #         if room_id.booking_id:
        #             b = room_id.booking_id
        #             if b.actual_check_in < fields.Datetime.now():
        #                 status = b.get_datetime_status(b.actual_check_in, fields.Datetime.now())
        #                 paid_date_list = b.get_paid_dates(status)
        #                 if date in paid_date_list:
        #                     text = "IN"
        #
        #         if text == "BOOKED":
        #             row_data += [
        #                 {"type": "button_action", "name": booking['name'], "model": "hotel.booking", "res_id": booking['id'], "icon": "fa-calendar-check-o", "class": "ik-btn-hotel-booked", "col_width": COL_WIDTH,},
        #             ]
        #
        #         elif text == "IN":
        #             booking = booking or {"name": "---", "id": -1}
        #             row_data += [
        #                 {"type": "button_action", "name": booking['name'], "model": "hotel.booking", "res_id": booking['id'], "icon": "fa-bed","class": "ik-btn-hotel-stay", "col_width": COL_WIDTH,},
        #             ]
        #         else:
        #
        #             booking_datetime = datetime(year=date.year, month=date.month, day=date.day, hour=0, minute=0, second=0) + timedelta(hours=check_in_point_utc)
        #
        #             ctx = {
        #                 'default_check_in': str(booking_datetime),
        #                 'default_check_out': str(booking_datetime),
        #                 'default_room_id': room_id.id,
        #                 'default_room_type_id': room_id.room_type_id.id,
        #             }
        #
        #             row_data += [
        #                 {"type": "button_action", "name": "SCHEDULE", "class": "ik-btn-hotel-schedule", "model": "hotel.booking", "context":ctx, "col_width": COL_WIDTH,},
        #             ]
        #
        #     screen.append(row_data)
        #
        data['booking_screen_color'] = self.env.user.hotel_booking_screen_color
        color1 = self.booking_screen_color or data['booking_screen_color'] or "#ff7373"
        bg_color = "#efefef"

        styles = """
            .bsv-col-head {white-space: nowrap; text-align: center; padding-left: 36px; padding-right: 36px; background: #afafaf; color: black; font-weight: bold; height: 49px; vertical-align: middle; display: table-cell; border: 1px solid white;}
            .bsv-home-icon { white-space: nowrap; text-align: center; padding-left: 20px; padding-right: 20px; background: #afafaf; color: black; font-weight: bold; height: 49px; vertical-align: middle; display: table-cell; border: 1px solid white; width:100%;}
            .bsv-row-head { white-space: nowrap; text-align: center; padding-left: 20px; padding-right: 20px; background: #efefef; font-weight: bold; height: 49px; vertical-align: middle; display: table-cell; border: 1px solid white; color: #7a4d9f; width:100%}
            .bsv-btn-hotel-booked { white-space: nowrap; text-align: center; padding-left: 20px; padding-right: 20px; vertical-align: middle; display: table-cell; border: 1px solid bg_color; width: 100%; color: color1; font-size: 10px; background: bg_color; outline: 0px !important;}
            .bsv-btn-hotel-booked-icon { white-space: nowrap; text-align: center; padding-left: 20px; padding-right: 20px; color: color1; font-weight: bold; height: 28px; vertical-align: middle; display: table-cell; border: 1px solid bg_color; width: 100%; background: bg_color;  outline: 0px !important;}
            .bsv-td-cell { background: bg_color; }
            .bsv-td-cell-booked { background: bg_color; border: 1px solid white;}
            .bsv-btn-hotel-stay-icon { white-space: nowrap; text-align: center; padding-left: 20px; padding-right: 20px; color: color1; font-weight: bold; height: 28px; vertical-align: middle; display: table-cell; border: 1px solid #efefef; width: 100%; background: #efefef; outline: 0px !important; }
            .bsv-btn-hotel-schedule { white-space: nowrap; text-align: center; padding-left: 20px; padding-right: 20px; background: color1!important; font-weight: bold; height: 50px; color: bg_color; vertical-align: middle; display: table-cell; border: 1px solid #efefef; width: 100%; background: #efefef; outline: 0px !important;}
            
        """.replace('color1', color1).replace('bg_color', bg_color)
        data['booking_screen'] = json.dumps({'data': screen, 'styles': styles.strip(), "model":self._name, "field_name": "booking_screen"})
        return data

    def get_calendar_data(self, date_from, date_to):
        months = set([(x.year, x.month) for x in self.get_dates_between(date_from, date_to)])
        data = {}
        for year, month in months:
            data[(year, month)] = calendar.monthcalendar(year, month)
        return data

    def booking_data_by_room_type(self, calendar_date, hotel_id):
        room_types = self.env['hotel.room.type'].search([('hotel_id', '=', hotel_id)])

        data = []
        for room_type in room_types:

            count = 0
            booked = 0
            for room_id in self.get_rooms_sorted(hotel_id=hotel_id):
                if room_id.room_type_id.id != room_type.id:
                    continue

                count += 1
                booking_data = self.sudo().env["hotel.booking"].get_booking_data(date_from=calendar_date,
                                                                                 date_to=calendar_date,
                                                                                 )
                if [b for b in booking_data if b['room_id'] == room_id.id]:
                    booked += 1

            vacant = count - booked
            # if vacant:
            data.append({'room_type_name': room_type.name, 'vacant': vacant, 'booked': booked})
        return data

    def dashboard_data_view2(self, date_from=False, date_to=False):
        booking_obj = self.env['hotel.booking']
        booking_line_obj = self.env['hotel.booking.line']

        check_in_point_utc, check_out_point_utc = booking_line_obj.get_check_points_utc()
        hotel_id = booking_obj.get_default_hotel_id()

        if not date_from:
            date_from = self.default_dates()['date_from']

        if not date_to:
            date_to = self.default_dates()['date_to']

        date_list = self.get_dates_between(date_from, date_to)

        data = {'hotel_id': hotel_id, 'view_type': 'view2'}

        calendar_data = self.get_calendar_data(date_from, date_to)

        screen = []
        for month in sorted(calendar_data):
            month_name = calendar.month_name[month[1]].upper()

            row_data = [{"class": "bsv-td-calendar-month-name", "colspan": 7, "body": [{"type": "text", "text": month_name + " " + str(month[0]), "class": "bsv-btn-calendar-month-name",}, ]}]
            screen.append(row_data)

            row_data = []
            for week in calendar.day_name:
                row_data += [{"class": "bsv-td-calendar-month-day-head", "body": [
                    {"type": "text", "text": week.upper(), "class": "bsv-btn-calendar-month-day-head",},
                ]}]
            screen.append(row_data)

            for row in calendar_data[month]:
                row_data = []
                for col in row:
                    calendar_date = col and date(month[0], month[1], col) or False

                    # if calendar_date and calendar_date.day == 23:
                    #     self.booking_data_by_room_type(calendar_date, hotel_id=hotel_id)

                    # if False:
                    if col and calendar_date in date_list:

                        booking_data = self.booking_data_by_room_type(calendar_date, hotel_id=hotel_id)
                        status_class = "bsv-btn-calendar-room-status"
                        text = "\n".join(["%s (%s)" % (x['room_type_name'], x['vacant']) for x in booking_data if x['vacant']])
                        if not text.strip():
                            text = len(booking_data) * "\nx"
                            status_class += "\t satus-hidden"

                        booking_datetime = datetime(year=month[0], month=month[1], day=col, hour=0, minute=0, second=0) + timedelta(hours=check_in_point_utc)

                        ctx = {"default_line_ids": [
                            (0, 0, {
                                'check_in': str(booking_datetime),
                                'check_out': str(booking_datetime),
                                'room_id': False,
                                'room_type_id': False,
                                'pricelist_id': False,
                                'number_of_days': booking_line_obj.get_number_of_days(booking_datetime, booking_datetime),
                            })
                        ]}
                        # ctx = {
                        #     'default_check_in': str(booking_datetime),
                        #     'default_check_out': str(booking_datetime),
                        #     'default_room_id': False,
                        #     'default_room_type_id': False,
                        # }

                        row_data += [{"class": "bsv-td-cell", "body": [
                                {"type": "action", "text": col, "class": "bsv-btn-calendar-day", "model": "hotel.booking", "context": ctx},
                                {"type": "action", "text": text.strip() or "", "class": status_class, "model": "hotel.booking", "context": ctx},
                            ]}]
                    elif col:

                        row_data += [{"class": "bsv-td-cell", "body": [{"type": "text", "text": col, "class": "bsv-btn-calendar-day-disabled", }]}]
                    else:
                        row_data += [{"class": "bsv-td-cell", "body": [{"type": "action", "text": "-1", "class": "bsv-btn-calendar-day-empty", }]}]

                screen.append(row_data)

        data['booking_screen_color'] = self.env.user.hotel_booking_screen_color
        color1 = self.booking_screen_color or data['booking_screen_color'] or "#ff7373"

        styles = """
           button.ik-button-text-table{height: 100%!important}
           .bsv-btn-calendar-month-name { background: #efefef!important; border: 1px solid #afa9a9!important; }
           .bsv-btn-calendar-month-day-head { background: #5c5b5b!important; border: 1px solid white!important; width: 160px; color: white; text-align: center; }
           .bsv-btn-calendar-day-disabled { font-size: 45px; background: #efefef; pointer-events: none; width: 100%; height: 90px!important; border: 1px solid white; text-align: center; color: #c3c3c3;}
           .bsv-btn-calendar-day { font-size: 45px; background: #efefef; width: 100%; border: 1px solid white; text-align: center; color: color1;     outline: 0px !important;}
           .bsv-btn-calendar-day-empty { font-size: 45px; background: #efefef; width: 100%; border: 0px; text-align: center; color: #5c5b5b;  pointer-events:none; color: transparent;}
           .bsv-btn-calendar-month-name { text-align: center; padding: 4px; font-size: 20px; background: color1!important; border: 1px solid white!important; color: white;}
           .bsv-btn-calendar-room-status { width: 100%; border: 1px solid white; border-top: 0px; margin-top: -2px; white-space: pre-line;    outline: 0px !important;color: #71639e;}
           .bsv-btn-calendar-room-status.satus-hidden { color: transparent; }
           td.bsv-td-cell { background: #efefef; }
            """.replace('color1', color1)


        data['booking_screen'] = json.dumps({'data': screen, 'styles': styles, "model":self._name, "field_name": "booking_screen"})

        return data


    def button_display_raw_data(self):
        raise UserError(str(self.booking_screen))

    def button_switch_view(self):
        self.view_type = self._context['view_type']
        self.update_result()

    # def foo(self):
    #     print(55)

        # dashboard_id = self.env["hotel.booking.dashboard2"].search([], order="id")
        # print(dashboard_id)