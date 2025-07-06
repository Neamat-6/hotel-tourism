# -*- coding: utf-8 -*-
from datetime import timedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta, date
import json
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT

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
    _name = 'tourism.hotel.booking.line'
    _description = 'Tourism Hotel Booking Lines'

    name = fields.Char(compute="_compute_name", store=True)
    vendor = fields.Many2one("res.partner", string='Vendor')
    room_aval = fields.Float('Room reserved')
    check_dir = fields.Boolean('Hotel contract', default=True)
    ro_co = fields.Float('Room avalible', related='room_id.room_vvv')
    total = fields.Float('Total')
    tax_id = fields.Many2one('account.tax', string='Tax')
    purchase_tax_id = fields.Many2one('account.tax', string='Purchase Tax')
    booking_id = fields.Many2one('tourism.hotel.booking', required=True, ondelete="cascade")
    hotel_id = fields.Many2one('tourism.hotel.hotel', required=True)
    room_type_id = fields.Many2one('tourism.hotel.room.type', string='Room Type', domain="[('hotel_id','=',hotel_id)]")
    room_id_domain = fields.Char(
        compute="_compute_room_id_domain",
        readonly=True,
        store=False,
    )
    room_id = fields.Many2one('tourism.hotel.room', string='Room', required=True)
    room_view_id = fields.Many2one('hotel.room.view', string="Room View")
    meal_id = fields.Many2many('hotel.meal', string="Meal")
    # cost_price = fields.Float('Price', compute='_compute_price', store=True, readonly=False)
    price = fields.Float('Price')
    cost = fields.Float('Cost', compute='_compute_cost', store=True)
    m_price = fields.Float('Sales Price', store=True)
    m_cost = fields.Float(' Cost Price', store=True)
    check_price = fields.Boolean('Check Price', compute='get_check_price')
    check_cost = fields.Boolean('Check Cost', compute='get_check_cost')
    rooms_display = fields.Char("Room", compute='compute_rooms_display')
    number_of_adults = fields.Integer(string='Adults', default=1, )
    number_of_children = fields.Integer(string='Children', default=0, )
    pricelist_id = fields.Many2one('tourism.hotel.pricelist')
    check_in = fields.Datetime(string='Check In', default=fields.Datetime.now(), required=True)
    check_out = fields.Datetime(string='Check Out', default=fields.Datetime.now(), required=True)
    number_of_days = fields.Integer(string='Days', compute='_compute_total_days', store=True)
    actual_check_in = fields.Datetime(string="Actual Check-In", compute="compute_actual_check_in_out")
    actual_check_out = fields.Datetime(string="Actual Check-Out", compute="compute_actual_check_in_out")
    actual_number_of_days = fields.Integer(string='Actual Days', compute="compute_actual_check_in_out")
    # time_summary_scheduled = fields.Text(compute="_compute_time_summary")
    # time_summary_actual = fields.Text(compute="_compute_time_summary")
    check_in_out_state = fields.Selection(
        [('draft', 'Draft'), ('checked_in', 'Checked In'), ('checked_out', 'Checked Out'), ], default="draft")
    invoice_id = fields.Many2one('purchase.order', 'purchase')
    account_move_id = fields.Many2one('account.move', 'Bill')
    date_diff = fields.Float(' Total Nights', default=1.0, compute='_compute_total_days', store=True)
    total_f = fields.Float('Total', )  # compute="_compute_total_f")
    service_ids = fields.One2many('tourism.booking.services', 'line_id')
    count = fields.Float('Number Of Room', default=1.0)
    total_amount = fields.Float('Total', compute='get_total_amount', store=True)
    contract_id = fields.Many2one('tourism.hotel.contract', compute='get_contract')
    vendor_id = fields.Many2one('res.partner')
    state_id = fields.Many2one('res.country.state', string='City', domain="[('country_id.code', '=', 'SA')]")
    hotel_rate = fields.Selection([
        ('1', 'One'),
        ('2', 'Two'),
        ('3', 'Tree'),
        ('4', 'Four'),
        ('5', 'Five'),
        ('6', 'Six'),
        ('7', 'Seven'),
    ])

    @api.onchange('state_id', 'hotel_rate')
    def onchange_state_rate(self):
        if self.state_id and not self.hotel_rate:
            return {'domain': {'hotel_id': [('state_id', '=', self.state_id.id)]}}
        elif not self.state_id and self.hotel_rate:
            return {'domain': {'hotel_id': [('hotel_rate', '=', self.hotel_rate)]}}
        elif self.state_id and self.hotel_rate:
            return {'domain': {'hotel_id': [('hotel_rate', '=', self.hotel_rate), ('state_id', '=', self.state_id.id)]}}
        else:
            return {'domain': {'hotel_id': []}}

    def get_account(self):
        hotel = self.hotel_id
        if hotel:
            return hotel.account_journal.id
        else:
            return False

    @api.model
    def create(self, vals):
        res = super(HotelBookingLine, self).create(vals)
        if vals.get('check_in') and vals.get('check_out'):
            if vals.get('check_in') > vals.get('check_out'):
                raise UserError("Check Out shouldn\'t before Check In !")
        return res

    def write(self, vals):
        res = super(HotelBookingLine, self).write(vals)
        if vals.get('check_in'):
            check_in = fields.Date.from_string(vals['check_in'])
        else:
            check_in = self.check_in.date()
        if vals.get('check_out'):
            check_out = fields.Date.from_string(vals['check_out'])
        else:
            check_out = self.check_out.date()
        if check_in and check_out:
            if check_in > check_out:
                raise UserError("Check Out shouldn\'t before Check In !")
        if self.account_move_id:
            if vals.get('room_id', False):
                if self.account_move_id.invoice_line_ids:
                    room_id = self.env['tourism.hotel.room'].browse(vals['room_id'])
                    self.account_move_id.invoice_line_ids[0].write({
                        'name': room_id.name,
                        'product_id': room_id.product_id.id,
                    })
            if vals.get('m_cost', False) or vals.get('count', False) or vals.get('date_diff', False) or vals.get(
                    'tax_id', False) or vals.get('purchase_tax_id'):
                if self.account_move_id.state != 'posted':
                    self.account_move_id.unlink()
                    m_cost = vals.get('m_cost', self.m_cost)
                    count = vals.get('count', self.count)
                    date_diff = vals.get('date_diff', self.date_diff)
                    move_id = self.env['account.move'].create({
                        'move_type': 'in_invoice',
                        'partner_id': self.booking_id.vendor_id.id,
                        'ref': self.booking_id.name,
                        'tourism_booking_id': self.booking_id.id,
                        'date': self.create_date,
                        'invoice_date': self.create_date,
                        'invoice_line_ids': [(0, 0, {
                            'name': self.room_id.name,
                            'product_id': self.room_id.product_id.id,
                            'price_unit': m_cost,
                            'tax_ids': self.purchase_tax_id,
                            'quantity': count * date_diff,
                            'tourism_source_booking_id': self.id,
                        })]
                    })
                    self.update({'account_move_id': move_id.id})
                    self.is_invoiced = True
        if self.booking_id.move_id:
            if vals.get('room_id', False):
                if self.booking_id.move_id.invoice_line_ids:
                    room_id = self.env['tourism.hotel.room'].browse(vals['room_id'])
                    self.booking_id.move_id.invoice_line_ids[0].write({
                        'name': room_id.name,
                        'product_id': room_id.product_id.id,
                    })
            if vals.get('m_price', False) or vals.get('price', False) or vals.get('count', False) or vals.get(
                    'date_diff', False):
                if self.booking_id.move_id.state != 'posted':
                    self.booking_id.move_id.unlink()
                    self.booking_id.create_invoice()
        return res

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

    @api.depends('hotel_id', 'check_in', 'check_out', 'date_diff', 'count')
    def _compute_room_id_domain(self):
        for rec in self:
            if rec.check_in and rec.check_out and rec.hotel_id:
                line_obj = self.env['room.availability.line']
                domain = [('hotel_id', '=', rec.hotel_id.id)]
                date_from = rec.check_in + timedelta(hours=3)

                date_list = [(date_from + timedelta(days=i)) for i in range(0, int(rec.date_diff))]
                remove_ids = []
                for i in date_list:
                    for room in self.env['tourism.hotel.room'].search(domain):
                        line_rec = line_obj.search([
                            ('date', '=', i.date()),
                            ('company_id', '=', rec.hotel_id.id),
                            ('room_category_id', '=', room.id)], limit=1)
                        print(i.date())
                        print(room.name)
                        # print(line_rec.close)
                        if line_rec:
                            if line_rec.close:
                                remove_ids.append(room.id)
                            else:
                                booked_qty = self.get_booked_room_qty(room.id, i.date(), i.date(),
                                                                      rec.hotel_id.id)
                                booked_qty = booked_qty or 0
                                qty = line_rec.contract_qty + line_rec.room_qty - booked_qty
                                if qty <= 0:
                                    remove_ids.append(room.id)
                            # print(booked_qty)
                            print(line_rec.contract_qty)
                            print(line_rec.room_qty)
                            # print(qty)
                print(remove_ids)
                domain.append(('id', 'not in', []))
                rec.room_id_domain = json.dumps(domain)
            else:
                rec.room_id_domain = json.dumps([('id', '=', 0)])

    @api.depends('room_id', 'hotel_id', 'check_in', 'check_out')
    def get_contract(self):
        for rec in self:
            contracts = self.env['tourism.hotel.contract.line'].search(
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

    @api.depends('check_dir', 'price', 'm_price', 'count', 'tax_id', 'date_diff', 'purchase_tax_id')
    def get_total_amount(self):
        for rec in self:
            if rec.check_dir:
                # if rec.tax_id:
                #     rec.total_amount = (rec.price * rec.count * rec.date_diff) + (
                #             (rec.price * rec.count * rec.tax_id.amount) / 100)
                # else:
                rec.total_amount = rec.price * rec.count * rec.date_diff
            else:
                # if rec.purchase_tax_id:
                #     rec.total_amount = (rec.m_price * rec.date_diff * rec.count) + (
                #             (rec.m_price * rec.date_diff * rec.count * rec.purchase_tax_id.amount) / 100)
                # else:
                rec.total_amount = rec.m_price * rec.count * rec.date_diff

    # @api.depends('check_in', 'check_out', 'date_diff')
    # def _compute_price(self):
    #     for rec in self:
    #         if rec.check_dir:
    #             line_obj = self.env['room.availability.line']
    #             # purchase_obj = self.env['purchase.order.line']
    #             if rec.check_in and rec.hotel_id and rec.room_id and rec.check_out:
    #                 date_from = rec.check_in
    #                 date_list = [(date_from + timedelta(days=i)) for i in range(0, int(rec.date_diff))]
    #                 total = 0
    #                 # cost_total = 0
    #                 for i in date_list:
    #                     line_rec = line_obj.search([
    #                         ('date', '=', i.date()),
    #                         ('company_id', '=', rec.hotel_id.id),
    #                         ('room_category_id', '=', rec.room_id.id)], limit=1)
    #                     # purchase_rec = purchase_obj.search([
    #                     #     ('start_date', '<=', i.date()),
    #                     #     ('end_date', '>=', i.date()),
    #                     #     ('order_id.hotel', '=', rec.hotel_id.id),
    #                     #     ('product_id', '=', rec.room_id.product_id.id)],limit=1)
    #                     # cost_total += purchase_rec.price_subtotal
    #                     total += line_rec.room_cost_price
    #                 rec.price = total
    #             # rec.cost_price = cost_total
    #         else:
    #             rec.price = 0.0

    @api.depends('check_in', 'check_out', 'date_diff')
    def _compute_cost(self):
        for rec in self:
            if rec.check_dir:
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
                            ('order_id.tourism_hotel', '=', rec.hotel_id.id),
                            ('product_id', '=', rec.room_id.product_id.id)], limit=1)
                        total += purchase_rec.price_unit
                    rec.cost = total
            else:
                rec.cost = 0.0

    tax_amount = fields.Float('Tax Amount', compute='get_tax_amount')

    @api.depends('price', 'm_price', 'count', 'tax_id', 'purchase_tax_id')
    def get_tax_amount(self):
        self.tax_amount = 0.0
        for rec in self:
            if rec.check_dir:
                price = rec.price
                total_amount = 0.0
                tax_only = 0.0
                if rec.tax_id:
                    for tax in rec.tax_id:
                        # Calculate the tax amount for the current tax
                        tax_only += price * (tax.amount / 100)
                        taxes = rec.tax_id.compute_all(rec.total_amount, partner=self.env['res.partner'])
                        tax_only += sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))
                        total_amount += taxes['total_included']
                        # total_amount += taxes['total_included']
                        # rec.tax_amount_line += (rec.price_unit * tax.amount) / 100
                        # Add the tax amount to the total_amount
                        # total_amount += tax_amount
                        rec.tax_amount = tax_only
            else:
                price = rec.m_price
                tax_amount = 0.0
                for tax in rec.purchase_tax_id:
                    tax_amount += tax.amount / 100 * (price * rec.date_diff)
                rec.tax_amount = tax_amount

    # @api.depends('price', 'm_price', 'count', 'tax_id', 'purchase_tax_id')
    # def get_tax_amount(self):
    #     for rec in self:
    #         if rec.tax_id and rec.price:
    #             total = 0
    #             for t in rec.tax_id:
    #                 total += rec.price * (t.amount / 100)
    #             rec.tax_amount = rec.price + total
    #         else:
    #             rec.tax_amount = 0

    @api.onchange('date_diff')
    def _compute_total_f(self):
        for rec in self:
            if rec.date_diff:
                rec.total_f = float(rec.date_diff) * float(rec.price)

    @api.onchange('room_id')
    def _get_price(self):
        if self.room_id:
            self.price = self.room_id.price

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
    is_invoiced = fields.Boolean(copy=False)

    def create_purchase_commission(self):

        invoice_obj = self.env['purchase.order']

        for u in self:
            inv_create_obj = invoice_obj.create({
                'partner_id': u.vendor_id.id,
                'tourism_booking_id': u.booking_id.id,
                'order_line': [(0, 0, {
                    'name': u.room_id.name,
                    'product_id': u.room_id.id,
                    'price_unit': u.m_cost,
                    'product_qty': u.count * u.date_diff,
                    'tourism_source_booking_id': u.id,
                })]
            })
            inv_create_obj.button_confirm()

            u.update({'invoice_id': inv_create_obj.id})
            u.is_purchased = True

    def create_bill_commission(self):
        account_move_obj = self.env['account.move']
        for line in self:
            if line.check_dir:
                bill_create_obj = account_move_obj.create({
                    'move_type': 'in_invoice',
                    'partner_id': line.vendor_id.id,
                    'ref': line.booking_id.name,
                    'tourism_booking_id': line.booking_id.id,
                    'date': line.create_date,
                    'invoice_date': line.create_date,
                    'journal_id': line.hotel_id.journal_id.id,
                    'invoice_line_ids': [(0, 0, {
                        'name': line.room_id.name,
                        'product_id': line.room_id.product_id.id,
                        'price_unit': line.m_cost,
                        'quantity': line.count * line.date_diff,
                        'tax_ids': line.purchase_tax_id,
                        'tourism_source_booking_id': line.id,
                        'account_id': line.hotel_id.journal_id.default_account_id.id
                    })]
                })
                # bill_create_obj.action_post()
                line.update({'account_move_id': bill_create_obj.id})
                line.is_invoiced = True
            else:
                bill_create_obj = account_move_obj.create({
                    'move_type': 'in_invoice',
                    'partner_id': line.vendor_id.id,
                    'ref': line.booking_id.name,
                    'tourism_booking_id': line.booking_id.id,
                    'date': line.create_date,
                    'invoice_date': line.create_date,
                    'invoice_line_ids': [(0, 0, {
                        'name': line.room_id.name,
                        'product_id': line.room_id.product_id.id,
                        'price_unit': line.m_cost,
                        'tax_ids': line.purchase_tax_id,
                        'quantity': line.count * line.date_diff,
                        'tourism_source_booking_id': line.id,
                    })]
                })
                # bill_create_obj.action_post()
                line.update({'account_move_id': bill_create_obj.id})
                line.is_invoiced = True

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

    @api.depends('check_in', 'check_out')
    def _compute_total_days(self):
        for booking in self:
            if not booking.check_out:
                booking.number_of_days = 0
            else:
                # booking.number_of_days = self.get_number_of_days(booking.check_in, booking.check_out)
                check_in = datetime.combine(booking.check_in.date(), datetime.min.time())
                check_out = datetime.combine(booking.check_out.date(), datetime.min.time())
                delta = (check_out - check_in).days
                booking.number_of_days = delta if delta > 0 else 0
                booking.date_diff = delta if delta > 0 else 0

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
            return self.env['tourism.hotel.room'].browse(self._context['default_room_id']).hotel_id.id
        hotel_id = self.env.user.hotel_booking_dashboard_hotel_id
        if not hotel_id:
            hotel_id = self.env['tourism.hotel.hotel'].search([], order="sequence", limit=1)
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
    #     no_of_rooms = len(self.env['tourism.hotel.room'].search([('booking_ok', '=', True), ('room_type_id', '=', self.room_type_id.id)]))
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
    # no_of_rooms = len(self.env['tourism.hotel.room'].search([('booking_ok', '=', True), ('room_type_id', '=', self.room_type_id.id)]))
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

        # Fixme
        # if not date_list:
        #     print(datetime_from)
        #     print(datetime_to)
        #     print(date_list)
        # print([datetime_from.date()])
        # print()

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

    @api.onchange('room_id', 'room_type_id')
    def onchange_room(self):
        self.pricelist_id = self.get_pricelist()
        self.number_of_adults = self.room_type_id.default_number_of_guest or 1

    def get_pricelist(self, hotel_id=None, room_type_id=None, room_id=None):

        hotel_id = hotel_id or self.hotel_id.id
        room_type_id = room_type_id or self.room_type_id.id
        room_id = room_id or self.room_id.id

        for pricelist in self.env['tourism.hotel.pricelist'].search([('hotel_id', '=', hotel_id)], order="sequence"):

            if pricelist.type == "room_type":
                if room_type_id in pricelist.room_type_ids.ids:
                    return pricelist.id

            if pricelist.type == "room":
                if room_id in pricelist.room_ids.ids:
                    return pricelist.id

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

    # @api.model
    # def create(self, vals):
    # if not vals.get('room_id'):
    #     raise UserError("Please select room.")
    # res = super(HotelBookingLine, self).create(vals)
    # return res

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

    @api.onchange('room_type_id', 'check_in', 'check_out')
    def set_rooms_onchange_domain(self):
        display_only_available = self.env.company.hotel_booking_display_only_available
        if not display_only_available:
            return False

        booking_data = self.sudo().env["hotel.booking"].get_booking_data(date_from=self.check_in.date(),
                                                                         date_to=self.check_out.date(),
                                                                         )

        available_rooms = []
        for room_id in self.env["tourism.hotel.room"].search([]):
            booking = self.env["tourism.hotel.booking"].get_booking(date=self.check_in.date(), room_id=room_id,
                                                            data=booking_data)
            if not booking:
                available_rooms.append(room_id.id)

        return {
            'domain': {
                'room_id': [('id', 'in', available_rooms)]
            }
        }

    # def create_purchase_room(self):
    #
    #     pur_obj = self.env['purchase.order']
    #     invoice_line_obj = self.env['purchase.order.line']
    #
    #     for u in self:
    #         inv_create_obj = pur_obj.create({
    #             'partner_id': u.vendor.id,
    #             # 'booking_id':u.id,
    #
    #             'order_line': [(0, 0, {
    #
    #                 'product_id': u.room_id.id,
    #
    #             })],
    #
    #         })
    #
    #         u.update({'order_id': inv_create_obj.id})
    #
    #         return {
    #             # 'name':'purchase.order.line',
    #             'res_model': 'purchase.order',
    #             'type': 'ir.actions.act_window',
    #             'view_mode': 'form',
    #             'res_id': inv_create_obj.id,
    #             'target': 'current',
    #         }
    #
    #
