from datetime import datetime, timedelta

import pytz
from dateutil.relativedelta import relativedelta

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, _logger
import logging
import traceback
logger = logging.getLogger(__name__)


class Folio(models.Model):
    _inherit = 'booking.folio'

    room_type_id = fields.Many2one('room.type')
    available_room_ids = fields.Many2many('hotel.room', copy=False)
    room_id = fields.Many2one('hotel.room',
                              domain="[('room_type', '=', room_type_id), ('id', 'in', available_room_ids)]", copy=False)
    cancel_reason_id = fields.Many2one('booking.cancel.reason')
    state = fields.Selection([
        ('draft', 'Unconfirmed'), ('confirmed', 'Confirmed'),
        ('part_checked_in', 'Partially Checked In'), ('checked_in', 'Checked In'),
        ('part_checked_out', 'Partially Checked Out'), ('checked_out', 'Checked Out'),
        ('cancelled', 'Cancelled')
    ], default='draft', required=True)
    # check in/out fields
    check_in = fields.Datetime()
    check_out = fields.Datetime()
    new_check_in = fields.Date(string='Check In')
    new_check_out = fields.Date(string='Check Out')
    total_nights = fields.Integer()
    check_in_date = fields.Date(compute='compute_check_in_date', store=True)
    check_out_date = fields.Date(compute='compute_check_out_date', store=True)
    amend_stay = fields.Boolean()
    today_is_checkout = fields.Boolean(compute='compute_today_is_checkout')
    today_is_checkin = fields.Boolean(compute='compute_today_is_checkin')

    # amount fields
    room_price_subtotal = fields.Monetary(compute='compute_amount_total', store=True, string='Room Charge Subtotal',
                                          )
    room_price_tax = fields.Monetary(compute='compute_amount_total', store=True, string='Room Charge Tax',
                                     )
    room_price_discount = fields.Monetary(compute='compute_amount_total', store=True, string='Room Charge Discount')
    room_price_total = fields.Monetary(compute='compute_amount_total', store=True, string='Room Charge Total',
                                       )
    price_municipality = fields.Monetary(compute='compute_amount_total', store=True, string='Room Charge Municipality',
                                         )
    price_vat = fields.Monetary(compute='compute_amount_total', store=True, string='Room Charge VAT', )

    service_price_municipality = fields.Monetary(compute='compute_amount_total', store=True,
                                                 string='Service Total Municipality')
    service_price_vat = fields.Monetary(compute='compute_amount_total', store=True, string='Service Total VAT')
    service_price_tax = fields.Monetary(compute='compute_amount_total', store=True, string='Service Total TAX')
    service_price_discount = fields.Monetary(compute='compute_amount_total', store=True,
                                             string='Service Total Discount')
    service_price_subtotal = fields.Monetary(compute='compute_amount_total', store=True, string='Services Subtotal')
    service_price_total = fields.Monetary(compute='compute_amount_total', store=True, string='Services Total')

    price_tax = fields.Monetary(compute='compute_amount_total', store=True, string='Total Tax')
    price_discount = fields.Monetary(compute='compute_amount_total', store=True, string='Total Discount')
    price_paid = fields.Monetary(compute='compute_amount_total', store=True, string='Total Paid')
    price_due = fields.Monetary(compute='compute_amount_total', store=True, string='Total Due')
    price_subtotal = fields.Monetary(compute='compute_amount_total', store=True, string='Subtotal')
    price_total = fields.Monetary(compute='compute_amount_total', store=True, string='Total')
    currency_id = fields.Many2one('res.currency', related='booking_id.currency_id', store=True)
    audit_date = fields.Date(string='Audit Date', default=lambda self: self.env.company.audit_date, readonly=True)
    partner_id = fields.Many2one('res.partner', string='Guest')
    change_room = fields.Boolean()
    filter_type = fields.Selection(selection=[
        ('today_arrival', 'Today Arrival'), ('today_check_out', "Today's Check Out"),
        ('inhouse', 'In-house'), ('none', 'None')
    ])
    next_folio = fields.Many2one('booking.folio', compute='compute_next_folio')
    service_ids = fields.One2many('booking.services', 'folio_id')
    # beds
    book_by_bed = fields.Boolean(related='booking_id.book_by_bed', store=True)
    total_beds = fields.Integer(related='room_type_id.max_adults', store=True, string='Total Beds')
    available_beds = fields.Integer()
    bed_ids = fields.One2many('booking.folio.bed', 'folio_id', string='Beds')
    state_selection = fields.Selection(related='room_id.state_selection', store=True,
                                       help='used in booking lines colors')
    rate_plan_id = fields.Many2one('hotel.rate.plan', related='booking_line_id.rate_plan')
    number_of_guests = fields.Integer()
    checkout_charge = fields.Boolean(related='company_id.checkout_charge', store=True)
    # hotel.booking fields for ninja dashboard
    hotel_id = fields.Many2one('hotel.hotel', related='booking_id.hotel_id', store=True)
    reservation_type = fields.Many2one('booking.type', related='booking_id.reservation_type', store=True)
    booking_source = fields.Selection(related='booking_id.booking_source', store=True)
    travel_agent_booking_source = fields.Many2one('res.partner', related='booking_id.travel_agent_booking_source',
                                                  store=True)
    online_travel_agent_source = fields.Many2one('res.partner', related='booking_id.online_travel_agent_source',
                                                 store=True)
    company_booking_source = fields.Many2one('res.partner', related='booking_id.company_booking_source', store=True)
    company_code = fields.Char(related='booking_id.company_code', store=True)
    ref = fields.Char(related='booking_id.ref', store=True)
    booking_source_id = fields.Many2one('booking.source', related='booking_id.booking_source_id', store=True)
    business_source_id = fields.Many2one('business.source', related='booking_id.business_source_id', store=True)
    payment_type = fields.Selection(related='booking_id.payment_type', store=True, string='Booking Payment Type')
    account_company_id = fields.Many2one('res.partner', related='booking_id.account_company_id', store=True)
    book_all_available_rooms = fields.Boolean(related='booking_id.book_all_available_rooms', store=True)
    quick_group_booking = fields.Boolean(related='booking_id.quick_group_booking', store=True)
    complimentary_room = fields.Boolean(related='booking_id.complimentary_room', store=True)
    house_use = fields.Boolean(related='booking_id.house_use', store=True)
    price_include_tax = fields.Boolean(related='booking_id.price_include_tax', store=True)
    booking_note = fields.Text(related='booking_id.note', store=True)
    booking_name = fields.Char(related='booking_id.name', string="Booking #", store=True)
    booking_partner_id = fields.Many2one(related='booking_id.partner_id', string="Guest Name", store=True)
    payment_number = fields.Char(related='booking_id.payment_number', store=True)
    is_master_folio = fields.Boolean(compute='compute_is_master_folio', store=True)
    unsettled_invoice = fields.Boolean()
    undo_check_in = fields.Boolean(compute='compute_undo_check_in')
    undo_check_out = fields.Boolean(compute='compute_undo_check_out')
    type_payment = fields.Selection(related='booking_id.payment_type_id')
    note = fields.Char("Note")
    price_ids = fields.One2many('booking.folio.line.price', 'folio_id')
    day_use = fields.Boolean(related='booking_id.day_use', store=True)
    folio_day_use = fields.Boolean(string='Day Use', help='used in amend stay')
    # used in manual assign
    floor_start = fields.Many2one('hotel.floor')
    floor_end = fields.Many2one('hotel.floor')
    group_action_wizard = fields.Integer()
    is_allotted = fields.Boolean(related='booking_id.is_allotted', store=True, string='Allotment')

    @api.depends('booking_id.master_folio_id')
    def compute_is_master_folio(self):
        for rec in self:
            rec.is_master_folio = False
            if rec.booking_id.master_folio_id.id == rec.id:
                rec.is_master_folio = True

    @api.model
    def create(self, vals):
        res = super(Folio, self).create(vals)
        if res.book_by_bed:
            count = res.room_type_id.mini_adults
            res.available_beds = count
            for i in range(count):
                self.env['booking.folio.bed'].create({'folio_id': res.id})
        if res.hotel_id.unsettled_invoice:
            res.unsettled_invoice = True
        return res

    def button_cancel_discount(self):
        for rec in self:
            if rec.line_ids:
                dates = rec.get_dates_between_exclude_checkout(rec.check_in, rec.check_out)
                for date in dates:
                    lines = rec.line_ids.filtered(lambda l: l.day == date.date() and (l.type == 'room_charge' or l.type == 'tax'))
                    discount_lines = rec.line_ids.filtered(lambda l:l.day == date.date() and l.type == 'discount')
                    total_amount = sum(lines.mapped('amount')) +  abs(sum(discount_lines.mapped('discount_amount')))
                    taxes = self.env['account.tax'].search([])
                    wizard = self.env['folio.room.charge'].sudo().create({
                        'folio_id': rec.id,
                        'amount': total_amount,
                        'folio_line_ids': lines.filtered(lambda l: l.type == 'room_charge' and l.day >= rec.audit_date).ids,
                        'all_folio_line_ids': rec.line_ids.filtered(lambda l: l.type == 'room_charge').ids,
                        'tax_ids': taxes.filtered(lambda t: t.price_include).ids
                    })
                    wizard.button_update_charge()
                    discount_lines.unlink()

    @api.onchange('line_ids')
    @api.depends('line_ids', 'line_ids.amount')
    def compute_amount_total(self):
        for folio in self:
            # room prices
            room_price_discount = sum(
                folio.line_ids.filtered(lambda l: l.type == 'discount' and not l.discount_related_line).mapped(
                    'discount_amount')) or 0
            price_municipality = sum(
                folio.line_ids.filtered(lambda l: l.tax_type == 'municipality' and not l.is_service_tax).mapped(
                    'amount')) or 0
            price_vat = sum(folio.line_ids.filtered(
                lambda l: l.type == 'tax' and l.tax_type == 'vat' and not l.is_service_tax).mapped('amount')) or 0
            room_price_tax = price_municipality + price_vat
            room_price_subtotal = (sum(folio.line_ids.filtered(lambda l: l.type == 'room_charge').mapped(
                'amount')) or 0)
            room_price_total = room_price_subtotal + room_price_tax
            # service prices
            service_price_discount = sum(
                folio.line_ids.filtered(lambda l: l.type == 'discount' and l.discount_related_line).mapped(
                    'discount_amount')) or 0
            service_price_municipality = sum(
                folio.line_ids.filtered(lambda l: l.tax_type == 'municipality' and l.is_service_tax).mapped(
                    'amount')) or 0
            service_price_vat = sum(
                folio.line_ids.filtered(lambda l: l.tax_type == 'vat' and l.is_service_tax).mapped(
                    'amount')) or 0
            service_price_tax = service_price_municipality + service_price_vat
            service_price_subtotal = (sum(folio.line_ids.filtered(
                lambda l: not l.is_service_tax and l.type in ['food', 'beverage', 'laundry', 'rent']).mapped(
                'amount')) or 0) + service_price_discount
            service_price_total = service_price_tax + service_price_subtotal
            # total
            price_discount = room_price_discount + service_price_discount
            price_tax = room_price_tax + service_price_tax
            price_subtotal = room_price_subtotal + service_price_subtotal
            price_total = price_tax + price_subtotal
            price_paid = -(sum(folio.line_ids.filtered(lambda l: l.payment_id or l.is_city_ledger).mapped('amount'))) or 0

            folio.update({
                'price_municipality': price_municipality,
                'price_vat': price_vat,
                'room_price_tax': room_price_tax,
                'room_price_discount': room_price_discount,
                'room_price_subtotal': room_price_subtotal,
                'room_price_total': room_price_total,
                'service_price_municipality': service_price_municipality,
                'service_price_vat': service_price_vat,
                'service_price_tax': service_price_tax,
                'service_price_discount': service_price_discount,
                'service_price_subtotal': service_price_subtotal,
                'service_price_total': service_price_total,
                'price_tax': price_tax,
                'price_discount': price_discount,
                'price_subtotal': price_subtotal,
                'price_total': price_total,
                'price_paid': price_paid,
                'price_due': price_total - price_paid,
            })

    def get_dates_between(self, date1, date2):
        my_list = []
        for n in range(int((date2 - date1).days) + 1):
            my_list.append(date1 + timedelta(n))
        return my_list

    def get_dates_between_exclude(self, date1, date2):
        if isinstance(date1, str):
            date1 = fields.Datetime.from_string(date1)
        if isinstance(date2, str):
            date2 = fields.Datetime.from_string(date2)
        my_list = []
        for n in range(1, int((date2 - date1).days)):
            my_list.append(date1 + timedelta(n))
        return my_list

    def get_dates_between_exclude_checkin(self, date1, date2):
        if isinstance(date1, str):
            date1 = fields.Datetime.from_string(date1)
        if isinstance(date2, str):
            date2 = fields.Datetime.from_string(date2)
        my_list = []
        for n in range(1, int((date2 - date1).days) + 1):
            my_list.append(date1 + timedelta(n))
        return my_list

    def get_dates_between_exclude_checkout(self, date1, date2):
        if isinstance(date1, str):
            date1 = fields.Datetime.from_string(date1)
        if isinstance(date2, str):
            date2 = fields.Datetime.from_string(date2)
        my_list = []
        for n in range(0, int((date2 - date1).days)):
            my_list.append(date1 + timedelta(n))
        return my_list

    def button_update_folio(self):
        timezone = pytz.timezone(self.env.user.tz or 'UTC')
        if self.folio_day_use:
            date_list = self.get_dates_between_exclude_checkout(self.check_in, self.check_out + relativedelta(days=1))
        else:
            date_list = self.get_dates_between_exclude_checkout(self.check_in, self.check_out)
        check_in = pytz.utc.localize(self.check_in).astimezone(timezone)
        check_out = pytz.utc.localize(self.check_out).astimezone(timezone)
        rate_plan = self.booking_line_id.rate_plan
        rate_type = rate_plan.rate_type_id
        self.line_ids.filtered(lambda l: not l.payment_id and not l.is_cancellation_fee and l.type not in ['food', 'beverage', 'laundry',
                                                                             'rent'] and not l.is_service_tax).unlink()
        if self.room_id:
            self.room_id.write({
                'stay_state': self.env.ref('hotel_booking.hotel_room_stay_status_vacant').id,
            })
        # self.room_id = False         #when change check in and out , room is not settled and remove it
        # recompute available rooms
        self.available_room_ids = [(6, 0, self.get_available_rooms())]
        if self.env.context.get('check_available', False):
            pass
            # self.check_room_type_availability(self.new_check_in, self.new_check_out)
        for day in date_list:
            prices = self.get_prices(self.booking_line_id, day.date())
            price_untaxed = prices['price_untaxed']
            price_vat = prices['price_vat']
            price_municipality = prices['price_municipality']
            if self.price_ids:
                price_ids = self.price_ids.filtered(lambda p: p.day == day.date())
                if price_ids:
                    # get the latest price from price history
                    price_untaxed = price_ids[0].amount
                    price_vat = price_ids[0].vat
                    price_municipality = price_ids[0].municipality
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
                    service_amount = incl.rate * self.booking_line_id.number_of_adults
                    self.env['booking.folio.line'].create({
                        'folio_id': self.id,
                        'day': day,
                        'amount': service_amount,
                        'particulars': incl.service_id.name,
                        'type': incl.service_id.type,
                    })
                    price_untaxed -= incl.rate
                    # create line for service taxes
                    # TODO loop thru all taxes
                    taxes = self.booking_line_id.tax_id.compute_all(service_amount, partner=self.env['res.partner'])
                    price_tax = sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))
                    if price_tax > 0:
                        self.env['booking.folio.line'].create({
                            'folio_id': self.id,
                            'day': day,
                            'amount': price_tax,
                            'particulars': 'VAT',
                            'type': 'tax',
                        })
            # create line for room charge
            self.env['booking.folio.line'].create({
                'folio_id': self.id,
                'day': day,
                'amount': price_untaxed,
                'particulars': 'Room Charge',
                'type': 'room_charge',
            })
            # create line for room charge taxes
            if prices['price_municipality'] > 0:
                self.env['booking.folio.line'].create({
                    'folio_id': self.id,
                    'day': day,
                    'amount': price_municipality,
                    'particulars': 'Municipality',
                    'type': 'tax',
                    'tax_type': 'municipality'
                })
            if prices['price_vat'] > 0:
                self.env['booking.folio.line'].create({
                    'folio_id': self.id,
                    'day': day,
                    'amount': price_vat,
                    'particulars': 'VAT',
                    'type': 'tax',
                    'tax_type': 'vat',
                })
            #  create price history
            self.env['booking.folio.line.price'].create({
                'folio_id': self.id,
                'day': day,
                'amount': price_untaxed,
                'vat': price_vat,
                'municipality': price_municipality,
            })
        return self.action_refresh()

    def check_room_type_availability(self, start, end):
        vals = []
        room_types = self.env['room.type'].search(
            [('company_id', '=', self.env.company.id), ('id', '=', self.room_type_id.id)])
        while start <= end:
            for room_type in room_types:
                hotel_id = self.env.company.related_hotel_id
                rooms = self.env['hotel.room'].search(
                    [('hotel_id', '=', hotel_id.id), ('room_type', '=', room_type.id)])
                total_rooms = len(rooms)
                # Filter out "out of order" rooms during the period
                out_of_order_rooms = self.env['hotel.room'].search([
                    ('id', 'in', rooms.ids),
                    '|',
                    '&', ('out_of_order_from', '<=', end),
                    ('out_of_order_to', '>=', start),
                    '&', ('out_of_order_from', '<=', start),
                    ('out_of_order_to', '>=', end)
                ])

                out_of_order_room_ids = out_of_order_rooms.ids

                booked_rooms = self.get_booked_inventory(room_type, rooms.ids, start)
                available_rooms = int(total_rooms - booked_rooms - len(out_of_order_room_ids))
                if not available_rooms or available_rooms < 0:
                    raise ValidationError(
                        f"No available rooms for room type '{room_type.name}', Please check availability.")
            start += relativedelta(days=1)
        return vals

    def get_booked_inventory(self, room_type, rooms, day):
        """
            get booked qty for a specific day
        """
        booked_folios = 0
        if day:
            company = self.env.company
            # arrival
            check_in_folios = self.env['booking.folio'].sudo().search([
                ('state', 'in', ['confirmed', 'draft']), ('company_id', '=', company.id),
                ('check_in', '!=', False), ('check_in_date', '=', day), ('room_type_id', '=', room_type.id)
            ])
            # departure
            check_out_folios = self.env['booking.folio'].sudo().search([
                ('room_id', '!=', False), ('company_id', '=', company.id),
                ('state', '=', 'checked_in'), ('check_in', '!=', False),
                ('check_out_date', '=', day), ('room_id', 'in', rooms), ('room_type_id', '=', room_type.id)
            ])
            exp_check_out_folios = self.env['booking.folio'].sudo().search([
                ('company_id', '=', company.id), ('state', '!=', 'cancelled'),
                ('check_in', '!=', False), ('check_out_date', '=', day), ('room_type_id', '=', room_type.id)
            ])
            exp_inhouse_folios = self.env['booking.folio'].sudo().search([
                ('check_in', '!=', False), ('company_id', '=', company.id), ('state', '!=', 'cancelled'),
                ('room_type_id', '=', room_type.id),
                ('id', 'not in', check_out_folios.ids), ('id', 'not in', exp_check_out_folios.ids),
                ('id', 'not in', check_in_folios.ids)
            ]).filtered(lambda f: f.check_in_date <= day <= f.check_out_date)

            booked_folios = len(check_in_folios) + len(exp_inhouse_folios)
        return booked_folios

    def button_amend_stay(self):
        return {
            'type': 'ir.actions.act_window',
            'name': "Amend Stay",
            'res_model': 'folio.amend.stay',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_folio_id': self.id,
                'default_check_in': self.check_in,
                'default_old_check_out': self.new_check_out,
            }
        }

    def button_update_room_charge(self):
        audit_date = self.env.company.audit_date
        if self.env.user.has_group('hotel_booking_folio.group_update_room_charge_before_audit'):
            folio_line_ids = self.line_ids.filtered(lambda l: l.type == 'room_charge')
        else:
            folio_line_ids = self.line_ids.filtered(lambda l: l.type == 'room_charge' and l.day >= audit_date)


        return {
            'type': 'ir.actions.act_window',
            'name': "Update Room Charge",
            'res_model': 'folio.room.charge',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_folio_id': self.id,
                'default_folio_line_ids': folio_line_ids.ids,
                'default_all_folio_line_ids': folio_line_ids.ids,
            }
        }

    @api.onchange('new_check_in')
    def onchange_new_check_in(self):
        if self.new_check_in:
            self.check_in = datetime.combine(self.new_check_in, datetime.min.time())
            if self.day_use:
                self.new_check_out = self.new_check_in

    @api.onchange('new_check_out')
    def onchange_new_check_out(self):
        if self.new_check_out:
            self.check_out = datetime.combine(self.new_check_out, datetime.min.time())

    @api.onchange('check_in', 'check_out')
    def onchange_check_in_out(self):
        self.total_nights = 0
        if self.check_in and self.check_out:
            check_in = datetime.combine(self.check_in.date(), datetime.min.time())
            check_out = datetime.combine(self.check_out.date(), datetime.min.time())
            delta = (check_out - check_in).days
            self.total_nights = delta if delta > 0 else 0
            # set available_room_ids
            folio = self.env['booking.folio'].browse(self.ids)
            self.available_room_ids = [(6, 0, folio.get_available_rooms(self.check_in_date, self.check_out_date))]

    @api.onchange('total_nights')
    def onchange_total_nights(self):
        if self.total_nights and self.check_in:
            check_in = datetime.combine(self.new_check_in, datetime.min.time())
            self.new_check_out = check_in + relativedelta(days=self.total_nights)

    def button_register_payment(self):
        amount = self.booking_id.amount_due if self.is_master_folio else self.price_due
        split = True if self.is_master_folio else False
        select_all = True if self.is_master_folio else False
        is_master_folio = True if self.is_master_folio else False
        if self.company_booking_source:
            booking_source = [(4, self.booking_id.company_booking_source.id)]
        elif self.online_travel_agent_source:
            booking_source = [(4, self.booking_id.online_travel_agent_source.id)]
        else:
            booking_source = False
        return {
            'name': _('Register Payment'),
            'res_model': 'booking.payment.register',
            'view_mode': 'form',
            'target': 'new',
            'type': 'ir.actions.act_window',
            'context': {
                'default_folio_id': self.id,
                'default_booking': self.booking_id.id,
                'default_partner_id':  self.booking_id.company_booking_source.id if self.booking_id.company_booking_source else self.booking_id.partner_id.id,
                'default_payment_type': 'inbound',
                'default_amount': amount,
                'default_partner_type': 'customer',
                'default_communication': self.name,
                'default_audit_date': self.company_id.audit_date,
                'default_split': split,
                'default_select_all': select_all,
                'default_is_master_folio': is_master_folio,
                'default_total_amount_booking': self.booking_id.amount_total,
                'default_booking_payment_type': self.booking_id.payment_type_id,
                'default_company_booking_source_ids': booking_source
            }
        }

    def button_confirm(self):
        if not self.line_ids:
            if self.state == 'cancelled':
                return True
            else:
                raise ValidationError("You have to add at least one line.")
        if not self.partner_id:
            raise ValidationError(f"Please select customer for folio {self.name}")
        vacant = self.env.ref('hotel_booking.hotel_room_stay_status_vacant')
        arrival = self.env.ref('hotel_booking.data_hotel_room_stay_status_arrival')
        if self.room_id:
            # make sure room is available
            if self.room_id.id in self.get_available_rooms():
                # room will be on arrival from night audit and if checkin is audit date
                if self.room_id.stay_state.id == vacant.id and self.check_in_date == self.company_id.audit_date:
                    self.room_id.stay_state = arrival.id
            else:
                raise ValidationError("room {} is not available for the moment.\n"
                                      "please select another room".format(self.room_id.name))
        self.state = "confirmed"
        return self.action_refresh()

    def validate_check_in(self, room):
        vacant = self.env.ref('hotel_booking.hotel_room_stay_status_vacant').id
        arrival = self.env.ref('hotel_booking.data_hotel_room_stay_status_arrival').id
        if not self.partner_id:
            raise ValidationError(f"Please choose customer for folio {self.name}.")
        if not room:
            raise ValidationError(f'please select room for folio {self.name}!')
        if room.id not in self.get_available_rooms():
            raise ValidationError("room {} is not available for the moment.\n"
                                  "please select another room".format(room.name))
        if room.state.state != 'clean':
            raise ValidationError('{} is not clean'.format(room.name))
        if room.stay_state.id not in [vacant, arrival]:
            raise ValidationError('{} is not vacant or on arrival'.format(room.name))
        if self.price_due > 0 and not self.env.user.has_group('hotel_booking.group_no_payment_check_in'):
            raise ValidationError("you are not allowed to check in without adding any reservation payment!")

    def js_validate_check_in(self, room):
        vacant = self.env.ref('hotel_booking.hotel_room_stay_status_vacant').id
        arrival = self.env.ref('hotel_booking.data_hotel_room_stay_status_arrival').id
        msg = ''
        if not self.today_is_checkin:
            msg = f"folio {self.name} check in is not today!"
        elif not self.partner_id:
            msg = f"Please choose customer for folio {self.name}."
        elif not room:
            msg = f'please select room for folio {self.name}!'
        elif room.id not in self.get_available_rooms():
            msg = "room {} is not available for the moment.\n please select another room".format(room.name)
        elif room.state.state != 'clean':
            msg = '{} is not clean'.format(room.name)
        elif room.stay_state.id not in [vacant, arrival]:
            msg = '{} is not vacant or on arrival'.format(room.name)
        elif self.price_due > 0 and not self.env.user.has_group('hotel_booking.group_no_payment_check_in'):
            msg = "you are not allowed to check in without adding any reservation payment!"
        return msg

    def button_check_in(self, book_by_bed=None, bed_partner=None):
        if self.price_paid == 0.0:
            if not self.complimentary_room or not self.house_use:
                if self.price_total != 0.0 and not self.env.user.has_group(
                        'hotel_booking_folio.group_check_without_settled'):
                    raise ValidationError("Please Settle Amount First Then Checked In")
        if not self.env.context.get('called_from_js', False):
            self.validate_check_in(self.room_id)
        self.room_id.write({
            'state': self.env.ref('hotel_booking.hotel_room_status_dirty').id,
            'stay_state': self.env.ref('hotel_booking.data_hotel_room_stay_status_arrived').id,
        })
        if self.partner_id and self.partner_id.balance < 0.0 and self.partner_id.is_city_ledger:
            if not self.env.user.has_group('hotel_booking_folio.group_check_in_exception'):
                raise ValidationError(
                    f"sorry,you cant checked in because {self.partner_id.name} have due amount {self.partner_id.customer_due_amount}")
        self.with_context(ignore_updates=True).state = 'part_checked_in' if book_by_bed else 'checked_in'
        partner = bed_partner if bed_partner else self.partner_id
        self.booking_id.send_by_whatsapp_direct('check_in', partner=partner)
        if not self.env.context.get('called_from_group_action', False):
            action = self.env.ref('hotel_booking.action_guest_register_form_report').report_action(self.booking_id)
        message = f'{self.name} is Checked in Successfully'
        return {
            'name': 'Message',
            'type': 'ir.actions.act_window',
            'res_model': 'warn.wizard',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': {'default_message': message, 'default_booking_id': self.booking_id.id}
        }

    def js_validate_check_out(self):
        msg = ''
        if self.price_due < 0:
            msg = f"{self.booking_id.user_id.name} still have money on Booking should be returned"
        if not self.booking_id.payment_type == 'postpaid':
            if self.price_due > 0:
                msg = f"There is Due amount for {self.name}.\n you have to settle it first."
        return msg

    def button_check_out(self):
        logger.info('folio check outttttttttttttttttttttttttttttttttttt')
        # Ensure checkout charge is processed
        self.button_check_out_charge()
        if self.checkout_charge:
            if not self.line_ids.mapped('move_line_ids') and not any(self.line_ids.mapped('is_invoiced')):
                raise ValidationError("You have to charge before checkout!")

        # Check if there are funds to be returned to the customer
        if self.price_due < 0 :
            raise ValidationError(f"{self.booking_id.user_id.name} still have money on Booking should be returned")

        # Ensure that due amounts are settled before checking out
        if not self.booking_id.payment_type == 'postpaid':
            if self.booking_id.master_group_room:
                if self.booking_id.amount_due > 0 and self.booking_id.master_folio_id.id == self.id:
                    raise ValidationError(
                        "There is a Due amount for {}.\nYou have to settle it first.".format(self.name))
            else:
                if self.price_due > 0 and not self.complimentary_room:
                    raise ValidationError(
                        "There is a Due amount for {}.\nYou have to settle it first.".format(self.name))

        # Send WhatsApp notification
        self.booking_id.send_by_whatsapp_direct('check_out', partner=self.partner_id)

        # Update room status
        self.room_id.write({
            'stay_state': self.env.ref('hotel_booking.hotel_room_stay_status_vacant').id,
            'state': self.env.ref('hotel_booking.hotel_room_status_dirty').id,
        })

        # Set folio state to checked_out
        self.state = 'checked_out'

        # Post invoice and reconcile payments if needed
        draft_states = ['draft', 'confirmed', 'checked_in']
        folio_states = self.booking_id.folio_ids.mapped('state')
        if not any(state in draft_states for state in folio_states):
            logger.info('here before post')
            booking = self.booking_id
            move_id = booking.move_id
            # Post the move
            try:
                move_id.post()
            except Exception as e:
                logger.info(f'error in post move {e}')
                logger.info(f'error in post move {traceback.format_exc()}')
            logger.info(f'moveeeeeeeeee state {move_id.state}')
            logger.info(f'moveeeeeeeeee state {move_id}')
            # Gather all relevant move lines
            move_lines = booking.folio_ids.mapped('line_ids').sudo().mapped('payment_id').mapped('invoice_line_ids').ids
            logger.info(f'move_lines {move_lines}')
            lines = self.env['account.move.line'].sudo().browse(move_lines).filtered(
                lambda line: line.account_id.user_type_id.type in ('receivable', 'payable') and not line.reconciled
            )
            # Include lines from the move that have not been reconciled
            if lines:
                lines += move_id.line_ids.sudo().filtered(
                    lambda line: line.account_id == lines[0].account_id and not line.reconciled
                )
                booking.state = 'checked_out'
                return lines.sudo().reconcile()

        # Show success message
        message = f'{self.name} is Checked Out Successfully'
        return {
            'name': 'Message',
            'type': 'ir.actions.act_window',
            'res_model': 'warn.wizard',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': {'default_message': message, 'default_booking_id': self.booking_id.id}
        }

    def button_cancel(self):
        cancellation_payments = abs(sum(self.line_ids.filtered(lambda l: l.payment_id and l.is_cancellation_fee).mapped('amount')))
        cancellation_fee = sum(self.line_ids.filtered(lambda l: not l.payment_id and l.is_cancellation_fee).mapped('amount'))
        if any(self.line_ids.filtered(lambda l: l.particulars == 'City Ledger')):
            raise ValidationError(f"Please remove City Ledger line from {self.name} before cancellation!")
        if self.price_paid > 0:
            if self.price_paid != cancellation_payments and not self.booking_id.payment_type_id == 'city_ledger':
                raise ValidationError(f"Please Refund paid amount for {self.name} before cancellation!")
        else:
            if cancellation_fee > cancellation_payments:
                raise ValidationError(f"Please register cancellation fee for {self.name} before cancellation!")
        if self.room_id:
            self.room_id.write({
                'stay_state': self.env.ref('hotel_booking.hotel_room_stay_status_vacant').id
            })
        # self.line_ids.filtered(lambda l: not l.payment_id).unlink()
        self.state = 'cancelled'

    def compute_today_is_checkin(self):
        for rec in self:
            rec.today_is_checkin = False
            if rec.check_in and rec.state in ['draft', 'confirmed'] and not rec.book_by_bed:
                if rec.company_id.audit_date == rec.check_in.date():
                    rec.today_is_checkin = True

    def compute_today_is_checkout(self):
        for rec in self:
            rec.today_is_checkout = False
            if rec.check_out and rec.state in ['checked_in', 'paid']:
                if rec.company_id.audit_date == rec.check_out.date():
                    rec.today_is_checkout = True

    @api.depends('check_in')
    def compute_check_in_date(self):
        for rec in self:
            if rec.check_in:
                timezone = pytz.timezone(self.env.user.tz or 'UTC')
                check_in = pytz.utc.localize(rec.check_in).astimezone(timezone)
                rec.check_in_date = check_in.date()
            else:
                rec.check_in_date = False

    @api.constrains('check_in_date')
    def validate_check_in_date(self):
        for rec in self:
            if rec.check_in_date and rec.check_in_date < rec.company_id.audit_date:
                raise ValidationError(f"{rec.booking_id.name} Folio {rec.name} check in date can't be in past!")

    @api.depends('check_out')
    def compute_check_out_date(self):
        for rec in self:
            if rec.check_out:
                timezone = pytz.timezone(self.env.user.tz or 'UTC')
                check_out = pytz.utc.localize(rec.check_out).astimezone(timezone)

                rec.check_out_date = check_out.date()
            else:
                rec.check_out_date = False

    @api.constrains('check_out_date')
    def validate_check_out_date(self):
        for rec in self:
            if rec.check_out_date and rec.check_out_date < rec.company_id.audit_date:
                raise ValidationError("check out date can't be in past!")

    def action_refresh(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Folio'),
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'booking.folio',
            'res_id': self.id,
            'target': 'new'
        }

    def button_open_lines(self):
        # in all cases user will click on display button to open folios then availability will be computed!
        self.available_room_ids = [(6, 0, self.get_available_rooms())]
        return {
            'type': 'ir.actions.act_window',
            'name': "Folio",
            'res_model': 'booking.folio',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    # todo check this again
    # @api.constrains('new_check_in', 'new_check_out')
    # def check_room_available(self):
    #     if self.new_check_in and self.new_check_out:
    #         available_rooms = self.get_available_rooms(self.new_check_in, self.new_check_out)
    #         # _logger.info(f"++++++++++ ROOMS : >> {available_rooms} ++++++")
    #         if self.env.context.get('check_available', False):
    #             if not available_rooms:
    #                 raise ValidationError(f"Please Check Room Type Again {self.room_type_id.name} For Availability")

    def get_available_rooms(self, check_in_date=False, check_out_date=False):
        '''
        There are 3 cases of overlapping to consider:

        s1   s2   e1   e2
        (    [----)----]
        s2   s1   e2   e1
        [----(----]    )
        s1   s2   e2   e1
        (    [----]    )
        '''
        print('calllllllllllllllllled')
        available_rooms = []
        check_in_date = check_in_date if check_in_date else self.check_in_date
        check_out_date = check_out_date if check_out_date else self.check_out_date
        _logger.info(f">>>>>>>>>>>>>>>> CHECK IN AND OUT {check_in_date} {check_out_date}")
        out_of_order_rooms = self.env["hotel.room"].search([
            ('room_type', '=', self.room_type_id.id),
            '|', '|',
            '&', ('out_of_order_from', '<=', check_in_date), ('out_of_order_to', '>', check_in_date),
            '&', ('out_of_order_from', '<=', check_out_date), ('out_of_order_to', '>', check_out_date),
            '&', ('out_of_order_from', '<=', check_in_date), ('out_of_order_to', '>', check_out_date),
        ])
        print('out_of_order_rooms', out_of_order_rooms)
        rooms = self.env["hotel.room"].search([
            ('room_type', '=', self.room_type_id.id), ('id', 'not in', out_of_order_rooms.ids)
        ])
        print('roooms', rooms)
        for room in rooms:
            # s1 = check_in_date # s2 = self.check_in_date
            # e1 = check_out_date # e2 = self.check_out_date
            domain = [
                ('id', '!=', self.id),
                ('company_id', '=', self.company_id.id),
                ('room_id', '=', room.id),
                ('state', 'in', ['part_checked_in', 'checked_in', 'confirmed', 'draft']),
                '|', '|',
                '&', ('check_in_date', '<=', check_in_date), ('check_out_date', '>', check_in_date),
                '&', ('check_in_date', '<=', check_out_date), ('check_out_date', '>', check_out_date),
                '&', ('check_in_date', '<=', check_in_date), ('check_out_date', '>', check_out_date),
            ]
            folio = self.env['booking.folio'].search(domain)
            print('folio', folio)
            if not folio:
                available_rooms.append(room.id)
        return available_rooms

    # todo created a booking folio and check if folio is updated or not
    @api.model
    def create(self, vals):
        res = super(Folio, self).create(vals)
        if res.hotel_id.unsettled_invoice:
            res.unsettled_invoice = True
        if not res['partner_id']:
            res.update({
                'partner_id': res['booking_id'].partner_id.id,
            })
        if res['booking_id'].is_hotel_room and res['booking_id'].hotel_room_id and not res['booking_id'].is_updated:
            res.update({'room_id': res['booking_id'].hotel_room_id.id})
            res['booking_id'].is_updated = True
        if res['booking_id'].state == 'draft':
            res.update({'state': 'draft'})
        else:
            res.update({'state': 'confirmed'})
        return res

    def unlink(self):
        for folio in self:
            if folio.room_id:
                folio.room_id.write({
                    'stay_state': self.env.ref('hotel_booking.hotel_room_stay_status_vacant').id,
                })
        return super(Folio, self).unlink()


    def write(self, vals):
        if vals.get('check_out', False) or vals.get('check_in', False) or vals.get('total_nights', False):
            self = self.with_context(ignore_updates=False)
        if not self.env.context.get('ignore_updates', False):
            if vals.get('room_id', False):
                room = self.env['hotel.room'].browse(vals['room_id'])
            else:
                room = self.room_id
            if room and room.id not in self.get_available_rooms() and not vals.get('state', False) and not vals.get(
                    'available_room_ids', False):
                raise ValidationError("room {} is not available for the moment.\n"
                                      "please select another room".format(room.name))
            # in case user change room after check in new room should be arrived & dirty, old room should be vacant clean
            if vals.get('room_id', False) and self.room_id and (self.change_room or vals.get('change_room', False)):
                # old room
                self.room_id.write({
                    'state': self.env.ref('hotel_booking.hotel_room_status_dirty').id,
                    'stay_state': self.env.ref('hotel_booking.hotel_room_stay_status_vacant').id,
                })
                # new room
                new_room = self.env['hotel.room'].browse(vals['room_id'])
                self.validate_check_in(new_room)
                new_room.write({
                    'state': self.env.ref('hotel_booking.hotel_room_status_dirty').id,
                    'stay_state': self.env.ref('hotel_booking.data_hotel_room_stay_status_arrived').id,
                })
            # in case user keep changing the room when folio still confirmed
            if vals.get('room_id', False) and self.state == 'confirmed':
                old_room = self.room_id
                new_room = self.env['hotel.room'].browse(vals['room_id'])

                old_room.write({
                    'stay_state': self.env.ref('hotel_booking.hotel_room_stay_status_vacant').id,
                })
                if self.check_in_date == self.company_id.audit_date:
                    new_room.write({
                        'stay_state': self.env.ref('hotel_booking.data_hotel_room_stay_status_arrival').id,
                    })

        if not self.env.context.get('ignore_updates', False) and self.check_in and not vals.get('check_in',
                                                                                                False) and 'check_in' in vals:
            raise ValidationError("You can't remove check in date from folio")
        if not self.env.context.get('ignore_updates', False) and self.check_out and not vals.get('check_out',
                                                                                                 False) and 'check_out' in vals:
            raise ValidationError("You can't remove check out date from folio")
        res = super(Folio, self).write(vals)
        state = False
        if not self.env.context.get('ignore_updates', False) and (
                vals.get('check_in', False) or vals.get('check_out', False)):
            self.with_context(check_available=True).button_update_folio()
        if vals.get('state', False):
            states = self.booking_id.folio_ids.mapped('state')
            active_states = [s for s in states if s != 'cancelled']
            identical = active_states and all(active_states[0] == elem for elem in active_states)
            if self.state == 'checked_in':
                state = 'checked_in' if identical else 'part_checked_in'
            elif self.state == 'checked_out':
                state = 'checked_out' if identical else 'part_checked_out'
            if state:
                self.booking_id.write({'state': state})
        return res

    def compute_next_folio(self):
        for rec in self:
            rec.next_folio = False
            folios = rec.booking_id.folio_ids.ids
            next_folio = rec.id + 1
            if next_folio in folios:
                rec.next_folio = next_folio

    def button_next_folio(self):
        self.next_folio.available_room_ids = [(6, 0, self.next_folio.get_available_rooms())]
        return {
            'type': 'ir.actions.act_window',
            'name': "Folio",
            'res_model': 'booking.folio',
            'res_id': self.next_folio.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def button_refund_payment(self):
        amount = sum(self.line_ids.filtered(lambda l: l.amount < 0.0).mapped('amount'))
        return {
            'type': 'ir.actions.act_window',
            'name': "Refunded / Transfer Amount",
            'res_model': 'booking.refund.payment',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_folio_id': self.id,
                'default_booking_id': self.booking_id.id,
                'default_total_amount': abs(self.price_paid),
            }
        }

    def button_add_service(self):
        taxes = self.booking_line_id.rate_plan.tax_ids.ids
        return {
            'type': 'ir.actions.act_window',
            'name': "Add Service",
            'res_model': 'folio.service',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_folio_id': self.id,
                'default_plan_tax_ids': taxes,
                'default_tax_ids': taxes,
            }
        }

    def button_change_room(self):
        available_room_ids = self.env['hotel.room'].browse(self.get_available_rooms()).filtered(
            lambda r: r.stay_state.id == self.env.ref('hotel_booking.hotel_room_stay_status_vacant').id
        ).ids
        charged_line_ids = self.line_ids.filtered(lambda l: l.type == 'room_charge').ids
        has_charge_access = True if self.env.user.has_group(
            'hotel_booking_folio.group_change_room_charge_user') else False
        return {
            'type': 'ir.actions.act_window',
            'name': "Change Room",
            'res_model': 'folio.change.room',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_folio_id': self.id,
                'default_room_type_id': self.room_type_id.id,
                'default_old_room_id': self.room_id.id,
                'default_check_in': self.check_in,
                'default_check_out': self.check_out,
                'default_available_room_ids': [(6, 0, available_room_ids)],
                'default_charged_line_ids': [(6, 0, charged_line_ids)],
                'default_has_charge_access': has_charge_access,
            }
        }

    def button_open_discount_wizard(self):
        return {
            'name': _('Discount'),
            'view_mode': 'form',
            'res_model': 'booking.apply.discount',
            'type': 'ir.actions.act_window',
            'context': {
                'default_folio_id': self.id
            },
            'target': 'new',
        }

    def prepare_invoice_lines(self, lines):
        invoice_line_vals = []
        municipality_price = 0
        default_account = self.room_id.product_id.categ_id.property_account_income_categ_id.id
        for line in lines:
            if self.booking_line_id.price_include_tax:
                price_unit = line.amount
                if line.type == 'room_charge':
                    vat_line = self.line_ids.filtered(
                        lambda l: l.day == line.day and l.type == 'tax' and l.tax_type == 'vat' and not l.is_service_tax
                    )
                    municipality_line = self.line_ids.filtered(
                        lambda
                            l: l.day == line.day and l.type == 'tax' and l.tax_type == 'municipality' and not l.is_service_tax
                    )
                else:
                    vat_line = self.line_ids.filtered(
                        lambda l: l.tax_type == 'vat' and l.is_service_tax and l.related_line_id.id == line.id
                    )
                    municipality_line = self.line_ids.filtered(
                        lambda
                            l: l.tax_type == 'municipality' and l.is_service_tax and l.related_line_id.id == line.id
                    )
                if vat_line:
                    price_unit += vat_line[0].amount
                if municipality_line:
                    municipality_price = municipality_line[0].amount
            else:
                price_unit = line.amount
            invoice_line_vals.append((0, 0, {
                'product_id': self.room_id.product_id.id,
                'name': line.particulars,
                'quantity': 1,
                'price_unit': price_unit,
                'source_booking_id': self.booking_line_id.id,
                'tax_ids': [(6, 0, self.booking_line_id.tax_id.filtered(lambda l: '15%' in (l.name or '').lower()).ids or [])],
                'account_id': line.get_account(line.type) or default_account,
                'folio_line_id': line.id,
                "pos_order_ref": line.pos_order_ref,
            }))
            if municipality_price:
                invoice_line_vals.append((0, 0, {
                    'name': f"Municipality Tax",
                    'quantity': 1,
                    'price_unit': municipality_price,
                    'source_booking_id': self.booking_line_id.id,
                    'tax_ids': [(6, 0, self.booking_line_id.tax_id.filtered(lambda l: '15%' in (l.name or '').lower()).ids or [])],
                    'account_id': line.get_account('tax') or default_account,
                    'folio_line_id': line.id,
                    "pos_order_ref": line.pos_order_ref,
                }))
        return invoice_line_vals

    def grouped_invoice_lines(self, invoice_lines):
        grouped = {}
        for command in invoice_lines:
            if command[0] != 0:
                continue
            vals = command[2]
            tax_ids = tuple(sorted(vals['tax_ids'][0][2])) if vals.get('tax_ids') else ()
            key = (
                vals['name'],
                vals['account_id'],
                tax_ids,  # extract tax IDs
                vals.get("pos_order_ref")
            )
            if key in grouped:
                grouped[key]['price_unit'] += vals['price_unit']
            else:
                grouped[key] = vals

        invoice_lines = [(0, 0, v) for v in grouped.values()]
        print('grouped invoice lines', invoice_lines)
        return invoice_lines

    def create_invoice(self, lines):
        """
        create draft invoice containing folio lines
        """
        self.ensure_one()
        booking = self.booking_id
        invoice_lines = self.prepare_invoice_lines(lines)
        invoice_lines = self.grouped_invoice_lines(invoice_lines)
        move_vals = {
            'move_type': 'out_invoice',
            'partner_id': booking.company_booking_source.id if booking.company_booking_source else booking.partner_id.id,
            'booking_id': booking.id,
            'guest_id': booking.partner_id.id,
            # 'narration': booking.conditions,
            'booking_folio_id': self.id,
            'invoice_user_id': self._uid,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': invoice_lines
        }
        move = self.env['account.move'].with_context({'line_ids': False}).create(move_vals)
        booking.move_id = move.id
        lines.write({'is_invoiced': True})


    def button_check_out_charge(self):
        move = self.booking_id.move_id
        lines = self.line_ids.filtered(
            lambda l: not l.payment_id and not l.is_city_ledger and l.type != 'tax' and l.folio_id.state == 'checked_in' and l.folio_id.room_id
        )
        move_line_ids = self.booking_id.folio_ids.mapped('line_ids').mapped('move_line_ids')
        invoiced_lines = any(self.booking_id.folio_ids.mapped('line_ids').mapped('is_invoiced'))
        if not self.booking_id.hotel_id.unsettled_invoice:
            if move:
                if not move_line_ids and not invoiced_lines:
                    move.unlink()
                    self.create_invoice(lines)
                else:
                    lines = lines.filtered(lambda l: not l.move_line_ids and not l.is_invoiced)
                    invoice_lines = self.prepare_invoice_lines(lines)
                    invoice_lines = self.grouped_invoice_lines(invoice_lines)
                    logger.info(f'herrrrr exist move---{move}')
                    for new_line in invoice_lines:
                        existing_lines = move.invoice_line_ids
                        print('new_line', new_line)
                        new_vals = new_line[2]
                        tax_ids = tuple(sorted(new_vals['tax_ids'][0][2])) if new_vals.get(
                            'tax_ids') else ()
                        key_new = (
                            new_vals['name'],
                            new_vals['account_id'],
                            tax_ids,
                            new_vals.get("pos_order_ref")
                        )
                        match = False
                        for line in existing_lines:
                            key_existing = (
                                line.name,
                                line.account_id.id,
                                tuple(sorted(line.tax_ids.ids)),
                                line.pos_order_ref
                            )
                            if key_existing == key_new:
                                logger.info(f'match {key_existing} {key_new}')
                                vals = {
                                    'price_unit': line.price_unit + new_vals['price_unit'],
                                    'product_id': line.product_id.id,
                                    'name': line.name,
                                    'quantity': line.quantity,
                                    'source_booking_id': line.source_booking_id,
                                    'tax_ids': line.tax_ids.ids,
                                    'account_id': line.account_id.id,
                                    'folio_line_id': line.folio_line_id.id,
                                    'pos_order_ref': line.pos_order_ref,
                                }
                                move.write({
                                    'invoice_line_ids': [
                                        (2, line.id),
                                        (0, 0, vals)
                                    ]
                                })
                                match = True
                                break
                        if not match:
                            move.write({
                                'invoice_line_ids': [new_line]
                            })
                    lines.write({'is_invoiced': True})
            else:
                lines = lines.filtered(lambda l: not l.move_line_ids and not l.is_invoiced)
                self.create_invoice(lines)

    def action_create_folio_invoice(self):
        folios = self.env['booking.folio'].browse(self.env.context.get('active_ids')).filtered(
            lambda f: f.unsettled_invoice)
        for folio in folios:
            booking = folio.booking_id
            move = booking.move_id
            lines = folio.line_ids.filtered(
                lambda
                    l: not l.payment_id and not l.is_city_ledger and l.type != 'tax' and l.folio_id.state == 'checked_out' and l.folio_id.room_id
            )
            move_line_ids = booking.folio_ids.mapped('line_ids').mapped('move_line_ids')
            invoiced_lines = any(self.booking_id.folio_ids.mapped('line_ids').mapped('is_invoiced'))
            if move:
                if not move_line_ids and not invoiced_lines:
                    move.unlink()
                    folio.create_invoice(lines)
                else:
                    lines = lines.filtered(lambda l: not l.move_line_ids and not l.is_invoiced)
                    invoice_lines = folio.prepare_invoice_lines(lines)
                    invoice_lines = self.grouped_invoice_lines(invoice_lines)
                    print('herrrrr exist move', move)
                    for new_line in invoice_lines:
                        existing_lines = move.invoice_line_ids
                        print('new_line', new_line)
                        new_vals = new_line[2]
                        tax_ids = tuple(sorted(new_vals['tax_ids'][0][2])) if new_vals.get(
                            'tax_ids') else ()
                        key_new = (
                            new_vals['name'],
                            new_vals['account_id'],
                            tax_ids,
                            new_vals.get("pos_order_ref")
                        )
                        match = False
                        for line in existing_lines:
                            key_existing = (
                                line.name,
                                line.account_id.id,
                                tuple(sorted(line.tax_ids.ids)),
                                line.pos_order_ref
                            )
                            if key_existing == key_new:
                                print('match', key_existing, key_new)
                                print('match', line)
                                vals = {
                                    'price_unit': line.price_unit + new_vals['price_unit'],
                                    'product_id': line.product_id.id,
                                    'name': line.name,
                                    'quantity': line.quantity,
                                    'source_booking_id': line.source_booking_id,
                                    'tax_ids': line.tax_ids.ids,
                                    'account_id': line.account_id.id,
                                    'folio_line_id': line.folio_line_id.id,
                                    'pos_order_ref': line.pos_order_ref,
                                }
                                move.write({
                                    'invoice_line_ids': [
                                        (2, line.id),
                                        (0, 0, vals)
                                    ]
                                })
                                match = True
                                break
                        if not match:
                            move.write({
                                'invoice_line_ids': [new_line]
                            })
                    lines.write({'is_invoiced': True})
            else:
                lines = lines.filtered(lambda l: not l.move_line_ids and not l.is_invoiced)
                folio.create_invoice(lines)
            folio.unsettled_invoice = False
            # check current folio is the last booking folio
            if not [f.unsettled_invoice for f in booking.folio_ids if f.unsettled_invoice]:
                booking.move_id.post()
                move_lines = booking.folio_ids.mapped('line_ids').mapped('payment_id').mapped('invoice_line_ids').ids
                lines_ids = self.env['account.move.line'].browse(move_lines).filtered(
                    lambda line: line.account_id.user_type_id.type in (
                        'receivable', 'payable') and not line.reconciled).ids
                if lines_ids:
                    lines = self.env['account.move.line'].browse(lines_ids)
                    lines += booking.move_id.line_ids.filtered(
                        lambda line: line.account_id == lines[0].account_id and not line.reconciled)
                    booking.state = 'checked_out'
                    lines.reconcile()

    def get_daily_price(self, plan, day):
        return self.env['rate.plan.day.price'].search([('plan_id', '=', plan.id), ('date', '=', day)], limit=1)

    def get_price_unit(self, booking_line, day):
        if booking_line.booking_id.apply_daily_price:
            price_id = self.get_daily_price(booking_line.rate_plan, day)
            price_unit = price_id.price
        else:
            price_unit = booking_line.price_unit
        return price_unit

    def get_prices(self, booking_line, day):
        price_unit = self.get_price_unit(booking_line, day)
        price_vat = 0
        price_municipality = 0
        price_untaxed = 0
        if booking_line.price_include_tax:
            vat = booking_line.tax_id.filtered(lambda t: t.type == 'vat')
            if vat:
                vat = vat[0]
                price_untaxed = (price_unit / (100 + vat.amount)) * 100
                price_vat = price_unit - price_untaxed
            municipality = booking_line.tax_id.filtered(lambda t: t.type == 'municipality')
            if municipality:
                price_before_municipality = price_untaxed
                municipality = municipality[0]
                price_untaxed = (price_before_municipality / (100 + municipality.amount)) * 100
                price_municipality = price_before_municipality - price_untaxed
        else:
            price_untaxed = price_unit
            price_total = price_unit
            municipality = booking_line.tax_id.filtered(lambda t: t.type == 'municipality')
            if municipality:
                municipality = municipality[0]
                price_total = price_unit * (municipality.amount / 100 + 1)
                price_municipality = price_total - price_unit

            vat = booking_line.tax_id.filtered(lambda t: t.type == 'vat')
            if vat:
                price_before_vat = price_total
                vat = vat[0]
                price_total = price_before_vat * (vat.amount / 100 + 1)
                price_vat = price_total - price_before_vat

        return {
            'price_untaxed': price_untaxed,
            'price_vat': price_vat,
            'price_municipality': price_municipality
        }

    def compute_undo_check_in(self):
        # check applicability of option undo check in
        for rec in self:
            rec.undo_check_in = False
            if rec.check_in_date and rec.state == 'checked_in':
                if rec.company_id.audit_date == rec.check_in_date:
                    rec.undo_check_in = True

    def compute_undo_check_out(self):
        # check applicability of option undo check out
        for rec in self:
            rec.undo_check_out = False
            # can't undo if user already called action_create_folio_invoice and folio is settled
            # if rec.hotel_id.unsettled_invoice and rec.unsettled_invoice:
            if rec.check_out_date and rec.state == 'checked_out':
                if rec.company_id.audit_date == rec.check_out_date:
                    rec.undo_check_out = True

    def button_undo_check_in(self):
        self.room_id.write({
            'state': self.env.ref('hotel_booking.hotel_room_status_clean').id,
            'stay_state': self.env.ref('hotel_booking.data_hotel_room_stay_status_arrival').id,
        })
        self.state = 'confirmed'
        self.booking_id.state = 'confirmed'
        self.action_refresh()

    def button_undo_check_out(self):
        self.room_id.write({
            'stay_state': self.env.ref('hotel_booking.data_hotel_room_stay_status_duo_out').id,
            'state': self.env.ref('hotel_booking.hotel_room_status_dirty').id,
        })
        self.state = 'checked_in'
        self.action_refresh()

    def button_manual_assign(self):
        pass

    def button_open_room_charge_wizard(self):
        taxes = self.booking_line_id.rate_plan.tax_ids.ids
        return {
            'name': _('Manual Chrage'),
            'view_mode': 'form',
            'res_model': 'room.charge.wizard',
            'type': 'ir.actions.act_window',
            'context': {
                'default_folio_id': self.id,
                'default_tax_ids': [(6, 0, taxes)],
            },
            'target': 'new',
        }


class FolioLine(models.Model):
    _inherit = 'booking.folio.line'

    is_service_tax = fields.Boolean()
    related_line_id = fields.Many2one('booking.folio.line')
    tax_type = fields.Selection(selection=[
        ('vat', 'VAT'), ('municipality', 'Municipality'),
    ])
    type = fields.Selection(selection_add=[("discount", "Discount")])
    discount_related_line = fields.Many2one('booking.folio.line')
    discount_amount = fields.Float()
    move_line_ids = fields.One2many('account.move.line', 'folio_line_id')
    is_invoiced = fields.Boolean(default=False)
    room_id = fields.Many2one('hotel.room', related='folio_id.room_id', store=True)
    folio_state = fields.Selection(related='folio_id.state', string='Folio State', store=True)
    is_cancellation_fee = fields.Boolean(help='any manadatory room charge can not removed')
    number_of_adults = fields.Integer( string='Number of Adults', readonly=True, default=1)
    room_charge_type = fields.Selection([
        ('manual', 'Manual'), ('cancellation', 'Cancellation'),
        ('no_show', 'No Show'), ('early', 'Early'), ('late', 'Late'),
    ])
    show_delete = fields.Boolean()
    delete_group = fields.Boolean(compute='_compute_delete_group')
    pos_order_ref = fields.Char(string='POS Order Reference')
    booking_service_id = fields.Many2one('booking.services')

    def _compute_delete_group(self):
        self.delete_group = self.env.user.has_group('hotel_booking_folio.group_delete_folio_line')

    def action_button_delete(self):
        child_lines = self.env['booking.folio.line'].search([('related_line_id', '=', self.id)])
        if child_lines:
            child_lines.unlink()
        self.unlink()


class FolioLinePrice(models.Model):
    _name = 'booking.folio.line.price'
    _description = 'Folio Line Price'
    _order = 'id desc'

    folio_id = fields.Many2one('booking.folio')
    day = fields.Date()
    amount = fields.Float()
    vat = fields.Float()
    municipality = fields.Float()
