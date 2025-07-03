# -*- coding: utf-8 -*-
from datetime import timedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta, date
import json
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
import pytz

STATUS_PAID = "PAID"
STATUS_NOT_PAID = "NOT_PAID"
STATUS_PAID_ADD_ONE_DAY = "PAID_WITH_EXTRA_ONE_DAY"


def get_timezone_offset(timezone):
    import pytz
    from datetime import datetime
    now_utc = datetime.utcnow()
    now_local = now_utc.astimezone(pytz.timezone(timezone))
    offset = now_local.utcoffset()
    return offset.seconds / 3600


class HotelBookingLine(models.Model):
    _name = 'hotel.booking.line'
    _description = 'Hotel Booking Lines'

    name = fields.Char(compute="_compute_name", store=True)
    vendor = fields.Many2one("res.partner", string='Vendor')
    room_aval = fields.Float('Room reserved')
    check_dir = fields.Boolean('Hotel contract', default=True)
    ro_co = fields.Float('Room avalible', related='room_id.room_vvv')
    total = fields.Float('Total')
    plan_tax_ids = fields.Many2many('account.tax', related='rate_plan.tax_ids', store=True,
                                    relation='booking_line_plan_tax_rel',
                                    column1='booking_line_id', column2='tax_id')
    tax_id = fields.Many2many('account.tax', string='Taxes', domain="[('id', 'in', plan_tax_ids)]")
    booking_id = fields.Many2one('hotel.booking', required=True, ondelete="cascade", copy=False)
    customer = fields.Many2one("res.partner", related='booking_id.partner_id', store=True, string='Customer')
    hotel_id = fields.Many2one('hotel.hotel', required=False, related='booking_id.hotel_id', store=True)
    room_type_id = fields.Many2one('hotel.room.type', string='Room Type', domain="[('hotel_id','=',hotel_id)]")
    available_room_ids = fields.Many2many('hotel.room', copy=False)
    room_id = fields.Many2one('hotel.room', domain="[('room_type', '=', room_type), ('id', 'in', available_room_ids)]",
                              copy=False)
    price = fields.Float('Price', compute='_compute_price', store=True)
    cost = fields.Float('Cost', compute='_compute_cost', store=True)
    m_price = fields.Float('Sales Price', store=True)
    m_cost = fields.Float(' Cost Price', store=True)
    check_price = fields.Boolean('Check Price', compute='get_check_price')
    check_cost = fields.Boolean('Check Cost', compute='get_check_cost')
    rooms_display = fields.Char("Room", compute='compute_rooms_display')
    number_of_adults = fields.Integer(string='Adults', default=lambda self:self.rate_plan.base_adult, readonly=False)
    max_number_of_adults = fields.Integer(string='Max Adults', related='rate_plan.max_adult', store=True)
    diff_number_of_adults = fields.Integer(string='Diff Adults', compute='compute_diff_number_of_adults', store=True)
    number_of_children = fields.Integer(string='Children', default=0, )
    pricelist_id = fields.Many2one('hotel.pricelist')
    check_in = fields.Datetime(string='Check In', related='booking_id.check_in', store=True)
    check_out = fields.Datetime(string='Check Out', related='booking_id.check_out', store=True)
    number_of_days = fields.Integer(string='Days')
    actual_check_in = fields.Datetime(string="Actual Check-In", compute="compute_actual_check_in_out")
    actual_check_out = fields.Datetime(string="Actual Check-Out", compute="compute_actual_check_in_out")
    actual_number_of_days = fields.Integer(string='Actual Days', compute="compute_actual_check_in_out")
    # time_summary_scheduled = fields.Text(compute="_compute_time_summary")
    # time_summary_actual = fields.Text(compute="_compute_time_summary")
    check_in_out_state = fields.Selection(
        [('draft', 'Draft'), ('checked_in', 'Checked In'), ('checked_out', 'Checked Out'), ], default="draft")
    invoice_id = fields.Many2one('purchase.order', 'purchase')
    date_diff = fields.Float(' Total Nights', default=1.0)
    total_f = fields.Float('Total', )  # compute="_compute_total_f")
    service_ids = fields.One2many('booking.services', 'line_id', related='booking_id.service_ids')
    count = fields.Float('Number Of Room', default=1.0)
    total_amount = fields.Float('Total')
    contract_id = fields.Many2one('hotel.contract', compute='get_contract')
    vendor_id = fields.Many2one('res.partner', related='contract_id.vendor')
    # ezee absolute cloning
    company_id = fields.Many2one('res.company', related='booking_id.company_id', store=True)
    room_type = fields.Many2one('room.type', domain="[('company_id', '=', company_id)]")
    # available_rooms = fields.Float(compute='compute_available_rooms', store=True)
    available_rooms = fields.Float()
    rate_plan = fields.Many2one('hotel.rate.plan', domain="[('room_type_id', '=', room_type)]")
    price_unit = fields.Float(string='Unit Price')
    price_subtotal = fields.Float(compute='compute_amount_total', store=True, string='Subtotal')
    price_total = fields.Float(compute='compute_amount_total', store=True, string='Total')
    price_tax = fields.Float(compute='compute_amount_total', store=True, string='Total Tax')
    discount = fields.Float()
    number_of_rooms = fields.Integer(string='No. of Rooms', default=1)
    state_selection = fields.Selection(related='room_id.state_selection', store=True,
                                       help='used in booking lines colors')
    price_include_tax = fields.Boolean(help='is tax included or excluded', default=True)
    booking_state = fields.Selection(related='booking_id.state', store=True)
    # buttons
    change_room = fields.Boolean(copy=False)
    assign_room = fields.Boolean(copy=False)
    # Book All Available Rooms
    room_ids = fields.Many2many('hotel.room', 'booking_line_room_rel', 'booking_line_id', 'room_id',
                                domain="[('room_type', '=', room_type), ('id', 'in', available_room_ids)]",
                                copy=False, string='Rooms', )
    edit_price = fields.Boolean(related='booking_id.edit_price')
    edit_price_include_tax = fields.Boolean(related='booking_id.edit_price_include_tax')
    quick_group_booking = fields.Boolean(related='booking_id.quick_group_booking', store=True, readonly=False)

    @api.onchange('rate_plan', 'number_of_adults')
    def onchange_rate_plan(self):
        if self.rate_plan:
            price_unit = self.rate_plan.rock_rate
            timezone = pytz.timezone(self.env.user.tz or 'UTC')
            check_in = pytz.utc.localize(self.check_in).astimezone(timezone).replace(tzinfo=None)
            price_line = self.rate_plan.day_price_ids.filtered(lambda d: d.date == check_in.date())
            if price_line:
                price_line = price_line[0]
                price_unit = price_line.price
            # extra adults
            if self.number_of_adults > self.rate_plan.base_adult:
                diff = self.number_of_adults - self.rate_plan.base_adult
                price_unit += diff * self.rate_plan.extra_adult
            self.price_unit = price_unit
            self.tax_id = self.rate_plan.tax_ids.ids

    # @api.onchange('price_include_tax')
    # def onchange_price_include_tax(self):
    #     if self.price_include_tax:
    #         self.tax_id = self.rate_plan.tax_ids.filtered(lambda t: t.price_include).ids or [(6, 0, [])]
    #     else:
    #         self.tax_id = self.rate_plan.tax_ids.filtered(lambda t: not t.price_include).ids

    # @api.onchange('rate_plan')
    # def onchange_rate_plan(self):
    #     if self.rate_plan:
    #         self.tax_id = self.rate_plan.tax_ids.ids

    # ezee functions
    @api.constrains('number_of_rooms', 'room_ids')
    def check_number_of_rooms(self):
        for line in self:
            if line.number_of_rooms > 0 and line.room_ids:
                if line.number_of_rooms != len(line.room_ids):
                    raise ValidationError("Number of Rooms doesn't match rooms count!")

    @api.onchange('number_of_rooms')
    def onchange_number_of_rooms(self):
        if self.number_of_rooms and self.available_rooms:
            if self.number_of_rooms > self.available_rooms:
                self.number_of_rooms = self.available_rooms

    @api.depends('rate_plan', 'booking_id.total_nights', 'tax_id', 'number_of_rooms', 'price_unit')
    def compute_amount_total(self):
        # todo handle rate plan
        for line in self:
            price = line.price_unit
            if line.number_of_rooms:
                taxes = line.tax_id.compute_all(price, line.booking_id.currency_id,
                                                line.booking_id.total_nights * line.number_of_rooms)
            else:
                taxes = line.tax_id.compute_all(price, line.booking_id.currency_id, line.booking_id.total_nights)
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })

    @api.depends('max_number_of_adults', 'number_of_adults')
    def compute_diff_number_of_adults(self):
        for rec in self:
            rec.diff_number_of_adults = rec.max_number_of_adults - rec.number_of_adults

    @api.onchange('number_of_children')
    def onchange_number_of_children(self):
        if self.room_type.mini_children:
            if self.number_of_children < 0:
                self.number_of_children = 0
            elif self.number_of_children > self.room_type.mini_children:
                self.number_of_children = self.room_type.mini_children

    def get_booked_room_qty(self, room_id, checkin, checkout, hotel):
        query = """SELECT count as qty FROM
                            hotel_booking_line WHERE check_dir = True AND  room_id=%s AND
                            (%s,%s) OVERLAPS (check_in, check_out)
                            AND hotel_id=%s """
        args = (room_id, checkin, checkout, hotel)
        self.env.cr.execute(query, args)
        data = self.env.cr.dictfetchall()
        room_qty = 0
        for line in data:
            room_qty += line['qty']
        if room_qty is None:
            room_qty = 0
        return room_qty

    @api.depends('room_id', 'hotel_id', 'check_in', 'check_out')
    def get_contract(self):
        for rec in self:
            contracts = self.env['hotel.contract.line'].search(
                [('room_type', '=', rec.room_id.id), ('hotel_id', '=', rec.hotel_id.id),
                 ('start_date', '<=', rec.check_in), ('end_date', '>=', rec.check_out)], limit=1)
            rec.contract_id = contracts.contract_id.id

    @api.depends('price')
    def get_check_price(self):
        for rec in self:
            if rec.price <= 1.0:
                rec.check_price = True
            else:
                rec.check_price = False

    @api.depends('cost')
    def get_check_cost(self):
        for rec in self:
            if rec.cost <= 1.0:
                rec.check_cost = True
            else:
                rec.check_cost = False

    @api.depends('price', 'm_price', 'count', 'tax_id')
    def get_total_amount(self):
        for rec in self:
            if rec.price > 1.0:
                if rec.tax_id:
                    rec.total_amount = (rec.price * rec.count * rec.date_diff) + (
                            (rec.price * rec.count * rec.tax_id.amount) / 100)
                else:
                    rec.total_amount = rec.price * rec.count
            else:
                if rec.tax_id:
                    rec.total_amount = (rec.m_price * rec.date_diff * rec.count) + (
                            (rec.m_price * rec.date_diff * rec.count * rec.tax_id.amount) / 100)
                else:
                    rec.total_amount = rec.m_price * rec.count * rec.date_diff

    @api.depends('check_in', 'check_out', 'date_diff')
    def _compute_price(self):
        for rec in self:
            if rec.check_dir == True:
                line_obj = self.env['room.availability.line']
                # purchase_obj = self.env['purchase.order.line']
                if rec.check_in and rec.hotel_id and rec.room_id and rec.check_out:
                    date_from = rec.check_in
                    date_list = [(date_from + timedelta(days=i)) for i in range(0, int(rec.date_diff))]
                    total = 0
                    # cost_total = 0
                    for i in date_list:
                        line_rec = line_obj.search([
                            ('date', '=', i.date()),
                            ('company_id', '=', rec.hotel_id.id),
                            ('room_category_id', '=', rec.room_id.id)], limit=1)
                        total += line_rec.room_cost_price
                    rec.price = total
                # rec.cost_price = cost_total
            else:
                rec.price = 0.0

    @api.depends('check_in', 'check_out', 'date_diff')
    def _compute_cost(self):
        for rec in self:
            if rec.check_dir == True:
                purchase_obj = self.env['purchase.order.line']
                if rec.check_in and rec.hotel_id and rec.room_id and rec.check_out:
                    date_from = rec.check_in
                    date_list = [(date_from + timedelta(days=i)) for i in range(0, int(rec.date_diff))]
                    total = 0
                    # cost_total = 0
                    for i in date_list:
                        purchase_rec = purchase_obj.search([
                            ('start_date', '<=', i.date()),
                            ('end_date', '>=', i.date()),
                            ('order_id.hotel', '=', rec.hotel_id.id),
                            ('product_id', '=', rec.room_id.product_id.id)], limit=1)
                        total += purchase_rec.price_unit
                    rec.cost = total
            else:
                rec.cost = 0.0

    tax_amount = fields.Float('Tax Amount', compute='get_tax_amount')

    @api.depends('price', 'm_price', 'count', 'tax_id')
    def get_tax_amount(self):
        for line in self:
            price = line.price or line.m_price
            taxes = line.tax_id.compute_all(price, line.booking_id.currency_id, 1, product=False,
                                            partner=line.booking_id.partner_id or line.booking_id.company_booking_source)
            line.update({
                'tax_amount': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
            })

    @api.onchange('date_diff')
    def _compute_total_f(self):
        for rec in self:
            if rec.date_diff:
                rec.total_f = float(rec.date_diff) * float(rec.price)

    @api.onchange('room_id')
    def _get_price(self):
        if self.room_id:
            self.price = self.room_id.price

    @api.onchange('check_in', 'check_out')
    def time_function_booking_line(self):
        for record in self:
            d1 = datetime.strptime(str(record.check_in), "%Y-%m-%d %H:%M:%S").date()
            d2 = datetime.strptime(str(record.check_out), "%Y-%m-%d %H:%M:%S").date()
            time_diff = (d2 - d1).days
            record.date_diff = time_diff

    def action_view_invoice(self):
        return {
            'name': _('Purchase'),
            'view_mode': 'tree,form',
            'res_model': 'purchase',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', '=', self.invoice_id.id)],

        }

    is_purchased = fields.Boolean(copy=False)

    def create_purchase_commission(self):

        invoice_obj = self.env['purchase.order']
        # # account = self.env.user.company_id.worksheet_account_id
        # if not account:
        #     raise ValidationError(
        #         _("Please Set Account Configuration under Commission -> Configuration -> Settings."))

        for u in self:
            inv_create_obj = invoice_obj.create({
                'partner_id': u.vendor.id,
                # 'move_type': 'in_invoice',
                # 'invoice_id': u.id,
                'order_line': [(0, 0, {
                    'name': u.room_id.name,
                    'product_id': u.room_id.id,
                    'price_unit': u.m_cost,
                    'product_qty': u.count * u.date_diff,
                    'source_booking_id': u.id,
                    # 'product_qty':u.room_aval,
                })]
            })
            inv_create_obj.button_confirm()

            u.update({'invoice_id': inv_create_obj.id})
            u.is_purchased = True

            # return {
            #     'name': 'purchase.order.form',
            #     'res_model': 'purchase.order',
            #     'view_mode': 'form',
            #     'res_id': inv_create_obj.id,
            #     'target': 'current',
            #     'type': 'ir.actions.act_window'
            # }

    @api.depends("booking_id", "room_id")
    def _compute_name(self):
        for line in self:
            line.name = "%s (#%s)" % (line.booking_id.name, line.rooms_display)

    def compute_rooms_display(self):
        for line in self:
            line.rooms_display = line.room_id.name or "Not Mentioned"

    # def name_get(self):
    #     result = []
    #     for line in self:
    #         # name = account.code + ' ' + account.name
    #         name = "%s (#%s)" % (line.booking_id.name, line.rooms_display)
    #         result.append((line.id, name))
    #     return result

    def get_number_of_days(self, datetime_from, datetime_to):
        data = self.get_datetime_status(datetime_from, datetime_to)
        days = len(self.get_paid_dates(data))
        return days

    @api.onchange('check_in', 'check_out')
    def _compute_total_days(self):
        # self.check_dates()
        for booking in self:
            if not booking.check_out:
                booking.number_of_days = 0
            else:
                booking.number_of_days = self.get_number_of_days(booking.check_in, booking.check_out)

    @api.onchange('hotel_id', 'number_of_days')
    def _compute_total_rommm(self):
        # self.check_dates()
        for room in self:
            if not room.room_id:
                room.room_id.room_vvv = 0
            else:
                room.room_id.room_vvv = room.room_id.room_c - room.room_aval

    @api.constrains('check_in', 'check_out', 'room_id.room_c')
    def _check_dates(self):

        for fy in self:
            # Starting date must be prior to the ending date
            check_in = fy.check_in
            check_out = fy.check_out
            if check_out < check_in:
                raise ValidationError(_('The ending date must not be prior to the starting date.'))
            # if fy.room_id.room_c<=0:
            #     raise ValidationError(_('There is no Rooms'))

            domain = [
                ('id', '!=', fy.id),
                '|',
                '&', ('check_in', '<=', fy.check_in), ('check_out', '>=', fy.check_in),
                '&', ('check_in', '<=', fy.check_in), ('check_out', '>=', fy.check_out),
                '&', ('check_in', '<=', fy.check_in), ('check_out', '>=', fy.check_out),
            ]

            if fy.search_count(domain) > 0 and fy.room_id.room_vvv > 0:
                self.room_id.room_vvv = fy.room_id.room_c - fy.room_aval

            else:
                fy.room_id.room_vvv = fy.room_id.room_c

    #

    # @api.depends('check_in', 'check_out', 'actual_check_in', 'actual_check_out', )
    # def _compute_time_summary(self):
    #
    #     lg = self.env['res.lang']._lang_get(self.env.user.lang)
    #
    #     date_format = "%s %s" % (lg.date_format, lg.time_format)
    #
    #     def format_dates(d1, d2, days):
    #         d1 = d1 and d1.strftime(date_format) or ""
    #         d2 = d2 and d2.strftime(date_format) or ""
    #
    #         if not d1 and not d2:
    #             return ""
    #
    #         text = """
    #         Check In: {check_in}\nCheck Out: {check_out}\n({days} days)
    #         """.format(check_in=d1, check_out=d2, days=days).strip()
    #         return text
    #
    #     for line in self:
    #         line.time_summary_scheduled = format_dates(line.check_in, line.check_out, line.number_of_days)
    #         line.time_summary_actual = format_dates(line.actual_check_in, line.actual_check_out, line.actual_number_of_days)

    def get_default_hotel_id(self):
        if self._context.get("default_room_id"):
            return self.env['hotel.room'].browse(self._context['default_room_id']).hotel_id.id
        hotel_id = self.env.user.hotel_booking_dashboard_hotel_id
        if not hotel_id:
            hotel_id = self.env['hotel.hotel'].search([], order="sequence", limit=1)
        if not hotel_id:
            return False
        return hotel_id.id

    def get_booked_date_list(self):
        self.ensure_one()

        d1 = self.check_in.date()
        d2 = self.check_out.date() or self.check_in.date()

        days = (d2 - d1).days

        data = []
        for each in range(0, days + 1):
            data.append(d1 + timedelta(each))

        return data

    def get_booked_date_list_actual(self):
        self.ensure_one()

        if not self.actual_check_in or not self.actual_check_out:
            return []

        d1 = self.actual_check_in.date()
        d2 = self.actual_check_out.date()

        days = (d2 - d1).days

        data = []
        for each in range(0, days + 1):
            data.append(d1 + timedelta(each))

        return data

    # def check_room_already_booked(self):
    #     self.ensure_one()
    #
    #     count = 0
    #
    #     for line in self.search([
    #         ('id', '!=', self.id),
    #         ('room_type_id', '=', self.room_type_id.id),
    #         ('booking_id.state', 'not in', ['cancelled']),
    #     ]):
    #         date_list_other = line.get_booked_date_list_actual() or line.get_booked_date_list()
    #         date_list_current = self.get_booked_date_list_actual() or self.get_booked_date_list()
    #
    #         for d in date_list_current:
    #             if d in date_list_other:
    #                 count += 1
    #
    #     no_of_rooms = len(self.env['hotel.room'].search([('booking_ok', '=', True), ('room_type_id', '=', self.room_type_id.id)]))
    #
    #     # if count >= no_of_rooms:
    #     #     raise UserError("Already booked")

    # count = 0
    #
    # for line in self.search([
    #     ('room_id', '=', self.room_id.id),
    #     ('room_id', '!=', False),
    #     ('id', '!=', self.id),
    #     ('booking_id.state', 'not in', ['cancelled']),
    # ]):
    #
    #     date_list_other = line.get_booked_date_list_actual() or line.get_booked_date_list()
    #     date_list_current = self.get_booked_date_list_actual() or self.get_booked_date_list()
    #
    #     for d in date_list_current:
    #         if d in date_list_other:
    #             raise UserError('Already booked for %s' % d.strftime("%d/%b/%Y"))
    #
    # # Room Not Mentioned
    # for line in self.search([
    #     ('room_id', '=', False),
    #     ('room_type_id', '=', self.room_type_id.id),
    #     ('id', '!=', self.id),
    #     ('booking_id.state', 'not in', ['cancelled']),
    # ]):
    #
    #     date_list_other = line.get_booked_date_list_actual() or line.get_booked_date_list()
    #     date_list_current = self.get_booked_date_list_actual() or self.get_booked_date_list()
    #
    #     for d in date_list_current:
    #         if d in date_list_other:
    #             count += 1
    #
    # no_of_rooms = len(self.env['hotel.room'].search([('booking_ok', '=', True), ('room_type_id', '=', self.room_type_id.id)]))
    #
    # print(count)
    # if count >= no_of_rooms:
    #     raise UserError("Already booked")

    # block

    @staticmethod
    def get_dates_between(date1, date2):
        my_list = []
        for n in range(int((date2 - date1).days) + 1):
            my_list.append(date1 + timedelta(n))
        return my_list

    def get_datetime_status(self, datetime_from, datetime_to):
        date_list = self.get_dates_between(datetime_from.date(), datetime_to.date())

        # Start
        data = {
            'start': {
                'date': datetime_from,
                'status': self.compare_with_point(datetime_from, 'CHECK_IN'),
            },
            'between': False,
            'end': False
        }

        date_list.remove(datetime_from.date())

        # End
        if date_list:
            data['end'] = {
                'date': datetime_to,
                'status': self.compare_with_point(datetime_to, 'CHECK_OUT'),
            }
            date_list.remove(datetime_to.date())

        # Between
        if date_list:
            data['between'] = {'date_list': date_list}

        # Modify Status
        start = data['start']
        between = data['between']
        end = data['end']

        # If checkout Same Day
        if start['status'] == "NOT_PAID" and not between and not end:
            start['status'] = STATUS_PAID

        # Re-arrange
        if start['status'] == STATUS_NOT_PAID and end and end['status'] == STATUS_PAID:
            start['status'] = STATUS_PAID
            end['status'] = STATUS_NOT_PAID

        if start['status'] == STATUS_NOT_PAID and end and end['status'] == STATUS_PAID_ADD_ONE_DAY:
            start['status'] = STATUS_PAID
            end['status'] = STATUS_PAID

        return data

    def compare_with_point(self, datetime_val, check_type):
        # self.check_configured_check_in_out_points()
        check_in_point_utc, check_out_point_utc = self.get_check_points_utc()

        if check_type == 'CHECK_IN':
            d = datetime_val.replace(hour=0, minute=0, second=0) + timedelta(hours=check_in_point_utc)
            return STATUS_PAID if datetime_val < d else STATUS_NOT_PAID

        if check_type == 'CHECK_OUT':
            d = datetime_val.replace(hour=0, minute=0, second=0) + timedelta(hours=check_out_point_utc)
            return STATUS_PAID_ADD_ONE_DAY if datetime_val > d else STATUS_PAID

        raise NotImplementedError

    def check_configured_check_in_out_points(self):
        company = self.env.company
        # if not company.hotel_check_in_point or not company.hotel_check_out_point:
        #     raise UserError("Please configure the Check-In/Check-Out Points (Please go to general settings and choose hotel section).")

        if not company.hotel_check_in_am_pm or not company.hotel_check_out_am_pm:
            raise UserError(
                "Please set AM/PM in the Check-In/Check-Out Points (Please go to general settings and choose hotel section).")
        if not company.hotel_timezone:
            raise UserError(
                "Please set Timezone for the Check-In/Check-Out Points (Please go to general settings and choose hotel section).")

    def get_check_points_utc(self):
        company = self.env.company

        check_in_point = company.hotel_check_in_point
        check_out_point = company.hotel_check_out_point
        timezone = company.hotel_timezone
        check_in_am_pm = company.hotel_check_in_am_pm
        check_out_am_pm = company.hotel_check_out_am_pm

        offset = get_timezone_offset(timezone or "UTC")

        check_in_point_utc = check_in_point - offset
        check_out_point_utc = check_out_point - offset

        if check_in_am_pm == "PM":
            check_in_point_utc += 12

        if check_out_am_pm == "PM":
            check_out_point_utc += 12

        return check_in_point_utc, check_out_point_utc

    def get_paid_dates(self, status):
        start = status['start']
        end = status['end']
        between = status['between']

        date_list = []
        if start and start['status'] == STATUS_PAID:
            date_list.append(start['date'].date())

        if between:
            date_list += between['date_list']

        if end and end['status'] == STATUS_PAID:
            date_list.append(end['date'].date())

        if end and end['status'] == STATUS_PAID_ADD_ONE_DAY:
            date_list.append(end['date'].date())
            date_list.append(end['date'].date() + timedelta(days=1))

        return list(set(date_list))

    @api.onchange('room_id', 'rate_plan')
    def onchange_room(self):
        self.number_of_adults = self.rate_plan.base_adult
        self.number_of_children = self.rate_plan.base_child

    def button_open_transfer_wizard(self):
        self.ensure_one()

        if self.booking_id.state != "confirmed":
            raise UserError("The booking is not confirmed.")

        ctx = {
            'default_type': self._context['type'],
            'default_booking_line_id': self.id,
            'default_transfer_time': fields.Datetime.now(),
        }

        return {
            'name': {"in": "Check In", "out": "Check Out"}[self._context['type']],
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'hotel.booking.transfer.wizard',
            'context': ctx,
            'target': 'new',
        }

    def compute_actual_check_in_out(self):
        for line in self:
            booking = line.booking_id

            in_transfers = booking.transfer_ids.filtered(lambda x: x.type == "in").filtered(
                lambda x: x.booking_line_id.id == line.id)
            in_transfers = in_transfers.sorted(key=lambda x: x.transfer_time)
            line.actual_check_in = in_transfers[0].transfer_time if in_transfers else False

            out_transfers = booking.transfer_ids.filtered(lambda x: x.type == "out").filtered(
                lambda x: x.booking_line_id.id == line.id)
            out_transfers = out_transfers.sorted(key=lambda x: x.transfer_time)
            line.actual_check_out = out_transfers[0].transfer_time if out_transfers else False

            if line.actual_check_in and line.actual_check_out:
                line.actual_number_of_days = self.get_number_of_days(booking.check_in, booking.check_out)
            else:
                line.actual_number_of_days = 0

    @api.onchange('room_type', 'check_in', 'check_out')
    def set_rooms_onchange_domain(self):
        if self.room_type and self.check_in and self.check_out:
            self.rate_plan = False
            booking_data = self.sudo().env["hotel.booking"].get_booking_data(
                date_from=self.check_in.date(), date_to=self.check_out.date()
            )
            available_rooms = []
            for room_id in self.env["hotel.room"].search([('room_type', '=', self.room_type.id)]):
                booking = self.env["hotel.booking"].get_booking(
                    date=self.check_in.date(), room_id=room_id, data=booking_data
                )
                if not booking:
                    available_rooms.append(room_id.id)

            self.available_room_ids = [(6, 0, available_rooms)]
            # self.available_rooms = len(available_rooms)
            return {
                'domain': {
                    'room_id': [('id', 'in', available_rooms)]
                }
            }

    def update_folio(self, number_of_rooms, price=False, room_type=False,check_in=False,check_out=False):
        date_list = self.get_dates_between(self.check_in, self.check_out)
        timezone = pytz.timezone(self.env.user.tz or 'UTC')
        check_in = pytz.utc.localize(self.check_in).astimezone(timezone)
        check_out = pytz.utc.localize(self.check_out).astimezone(timezone)
        folio = self.env['booking.folio'].create({
            'booking_id': self.booking_id.id,
            'booking_line_id': self.id,
        })
        amount_total = folio.booking_line_id.price_unit * number_of_rooms
        rate_plan = folio.booking_line_id.rate_plan
        rate_type = rate_plan.rate_type_id
        for day in date_list:
            if rate_type.is_package:
                for incl in rate_type.inclusion_ids:
                    if day.date() == check_in.date() and incl.posting_rule in ['everyday_no_check_in',
                                                                               'everyday_no_check_in_out']:
                        continue
                    if day.date() == check_out.date() and incl.posting_rule in ['everyday_no_check_out',
                                                                                'everyday_no_check_in_out']:
                        continue
                    if day.date() != check_in.date() and incl.posting_rule in ['check_in', 'check_in_out']:
                        continue
                    if day.date() != check_out.date() and incl.posting_rule in ['check_out', 'check_in_out']:
                        continue
                    # create line for service
                    service_amount = incl.rate * folio.booking_line_id.number_of_adults
                    self.env['booking.folio.line'].create({
                        'folio_id': folio.id,
                        'day': day,
                        'amount': service_amount,
                        'particulars': incl.service_id.name,
                        'type': incl.service_id.type,
                    })
                    amount_total -= incl.rate
                    # create line for service taxes
                    # TODO loop thru all taxes
                    taxes = folio.booking_line_id.tax_id.compute_all(service_amount,
                                                                     partner=self.env['res.partner'])
                    price_tax = sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))
                    if price_tax > 0:
                        self.env['booking.folio.line'].create({
                            'folio_id': folio.id,
                            'day': day,
                            'amount': price_tax,
                            'particulars': 'VAT',
                            'type': 'tax',
                        })
            # create line for room charge
            self.env['booking.folio.line'].create({
                'folio_id': folio.id,
                'day': day,
                'amount': amount_total,
                'particulars': 'Room Charge',
                'type': 'room_charge',
            })
            # create line for room charge taxes
            taxes = folio.booking_line_id.tax_id.compute_all(amount_total, partner=self.env['res.partner'])
            price_tax = sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))
            if price_tax > 0:
                self.env['booking.folio.line'].create({
                    'folio_id': folio.id,
                    'day': day,
                    'amount': price_tax,
                    'particulars': 'VAT',
                    'type': 'tax'
                })

    def write(self, vals):
        if not self.env.context.get('ignore_all_update', False):
            if vals.get('quick_group_booking') is None:
                quick_group_changed = False
            else:
                quick_group_changed = True
            if (vals.get('number_of_rooms', False) and not self.env.context.get('ignore_number_of_rooms_update',False)) or vals.get('room_type',False) or quick_group_changed:
                if vals.get('number_of_rooms', False):
                    number_of_rooms = vals['number_of_rooms'] if vals['number_of_rooms'] > 0 else 1
                else:
                    number_of_rooms = self.number_of_rooms
                if vals.get('price_unit', False):
                    price = vals['price_unit']
                else:
                    price = self.price_unit
                if vals.get('room_type', False):
                    room_type = vals['room_type']
                else:
                    room_type = self.room_type.id
                folio = self.env['booking.folio'].search([('booking_line_id', '=', self.id)])
                folio.line_ids.unlink()
                folio.unlink()
                self.update_folio(number_of_rooms, price=price, room_type=room_type)
            elif vals.get('price_unit', False):
                price = vals['price_unit']
                self.with_context(update_existing_folio=True).update_folio(self.number_of_rooms, price=price)

        res = super(HotelBookingLine, self).write(vals)
        return res

    def unlink(self):
        for rec in self:
            if rec.booking_id.state != 'draft':
                raise ValidationError("you cant delete folio from confirmed booking")
            folio = self.env['booking.folio'].search([('booking_line_id', '=', rec.id)])
            folio.line_ids.unlink()
            folio.unlink()
        return super().unlink()