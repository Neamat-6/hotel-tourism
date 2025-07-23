# -*- coding: utf-8 -*-
import base64
import json
from collections import Counter
from datetime import datetime
from datetime import timedelta

import pytz
import requests
from dateutil.relativedelta import relativedelta
from hijri_converter import convert

from odoo import _
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from odoo.http import request
from odoo.tools import format_amount


class HotelBookingconact(models.Model):
    _inherit = "res.partner"

    check = fields.Boolean("Is Vendor")


class Hotelcontract(models.Model):
    _name = "hotel.contract"

    name = fields.Char(string="Contract #")
    hotel = fields.Many2one('hotel.hotel', string="Hotel")
    num_room = fields.Char('Room Count')
    vendor = fields.Many2one('res.partner', string="Supplier")
    contract_line = fields.One2many('hotel.contract.line', 'contract_id')
    log_line = fields.One2many('hotel.contract.log.line', 'log_id')
    total = fields.Float('Total', compute="_amoun_total")
    invoice_id_con = fields.Many2one('purchase.order', 'purchase')
    state = fields.Selection(
        [('draft', 'Draft'), ('confirmed', 'Confirmed'), ('purchase', 'Purchase'), ('cancel', 'Cancelled')], 'State',
        default='draft', required=True, tracking=True)

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('Cannot delete a record which is in state \'%s\'.') % (rec.state,))
        return super(Hotelcontract, self).unlink()

    def action_confirm(self):
        for rec in self:
            rec.state = 'confirmed'

    def action_cancel(self):
        for rec in self:
            rec.state = 'cancel'

    @api.depends('contract_line.total')
    def _amoun_total(self):

        for order in self:
            total = 0.0
            for line in order.contract_line:
                total += line.total

            order.update({
                'total': total,

            })

    def create_purchase_contract(self):

        invoice_obj = self.env['purchase.order']
        data = []
        for u in self.contract_line:
            data.append((0, 0, {
                'name': u.room_type.name,
                'product_id': u.room_type.product_id.id,
                'product_qty': u.count,
                'start_date': u.start_date,
                'end_date': u.end_date,
                'price_unit': u.price,
                'price_subtotal': u.total

            }))
        inv_create_obj = invoice_obj.create({
            'hotel': self.hotel.id,
            'partner_id': self.vendor.id,
            'tax_totals_json': self.total,
            'order_line': data
        })

        self.update({'invoice_id_con': inv_create_obj})

        self.state = 'purchase'

        return {
            'name': 'purchase.order.form',
            'res_model': 'purchase.order',
            'view_mode': 'form',
            'res_id': inv_create_obj.id,
            'target': 'current',
            'type': 'ir.actions.act_window'
        }


class HotelcontractLogline(models.Model):
    _name = "hotel.contract.log.line"
    room_id = fields.Many2one('hotel.room', string="Room Type")
    count = fields.Float('Room Count')
    date = fields.Date('Start Date')
    log_id = fields.Many2one('hotel.contract')
    user_id = fields.Many2one('res.users')


class Hotelcontractline(models.Model):
    _name = "hotel.contract.line"

    room_type = fields.Many2one('hotel.room', string="Room Type")
    count = fields.Float('Room Count')
    start_date = fields.Date('Start Date', default=fields.Date.context_today)
    end_date = fields.Date('End Date', default=fields.Date.context_today)
    contract_id = fields.Many2one('hotel.contract')
    price = fields.Float('Price')
    total = fields.Float('Total')
    date_difference = fields.Char(' Total Days')
    state = fields.Selection(
        [('draft', 'Draft'), ('confirmed', 'Confirmed'), ('purchase', 'Purchase'), ('cancel', 'Cancelled')],
        'State', related='contract_id.state', store=True)
    hotel_id = fields.Many2one('hotel.hotel', string='Hotel', related='contract_id.hotel', store=True)

    @api.onchange('date_difference')
    def compute_time(self):
        for rec in self:
            if rec.date_difference:
                rec.total = float(rec.date_difference) * float(rec.price)

    @api.onchange('room_type')
    def _get_price(self):
        if self.room_type:
            self.price = self.room_type.price

    @api.onchange('start_date', 'end_date')
    def time_function(self):
        for record in self:
            d1 = record.start_date
            d2 = record.end_date
            time_diff = (d2 - d1).days
            record.date_difference = time_diff


class Services(models.Model):
    _name = 'booking.services'

    line_id = fields.Many2one('hotel.booking.line')
    booking_id = fields.Many2one('hotel.booking')
    service_id = fields.Many2one('hotel.services', string='Service')
    price_type = fields.Selection([('fixed', 'Fixed'), ('multiply_with_guest', 'Multiply With No.of.Guests'), ],
                                  default="fixed", string="Price Type")
    type = fields.Selection([('every_day', 'Every Day'), ('every_day_checkin', 'Every Day Except Checkin'),
                             ('every_day_checkout', 'Every Day Except Checkout'), ('one_time', 'One Time'), ],
                            default="", string="Type")
    company_id = fields.Many2one('res.company', related='booking_id.company_id', store=True)


class HotelBooking(models.Model):
    _name = 'hotel.booking'
    _inherit = ["mail.thread", 'portal.mixin']
    _description = 'Hotel Booking'

    STATES = [
        ('draft', 'Unconfirmed Booking'),
        ('confirmed', 'Confirmed Booking'),
        ('part_checked_in', 'Partially Checked In'),
        ('checked_in', 'Checked In'),
        ('part_checked_out', 'Partially Checked Out'),
        ('checked_out', 'Checked Out'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ]

    your_date_field = fields.Date(string="Your Date Field", default=fields.Date.today())

    hijri_date = fields.Char(string="Hijri Year", compute="compute_hijri_date", store=True)
    check_out_hijri = fields.Char(string="Check out Hijri Year", compute="compute_check_out_hijri", store=True)
    automatic_send_confirmation_email_and_folio_invoice = fields.Boolean()
    booking_type = fields.Selection(string="Booking Type",
                                    selection=[('transportation', 'Transportation'), ('visa', 'Visa'),
                                               ('full_package', 'Full Package')])

    def get_invoice_issue_date(self):
        return self.check_out

    def get_invoice_issue_date_hijri(self):
        return self.check_out_hijri

    def get_total_exclude_vat_municipality(self):
        return 0

    def get_total_municipality(self):
        return 0

    def get_total_exclude_vat(self):
        return 0

    def get_total_vat(self):
        return 0

    @api.model
    def get_qr_code(self):
        def get_qr_encoding(tag, field):
            company_name_byte_array = field.encode('UTF-8')
            company_name_tag_encoding = tag.to_bytes(length=1, byteorder='big')
            company_name_length_encoding = len(company_name_byte_array).to_bytes(length=1, byteorder='big')
            return company_name_tag_encoding + company_name_length_encoding + company_name_byte_array

        for record in self:
            qr_code_str = ''
            seller_name_enc = get_qr_encoding(1, record.company_id.display_name)
            company_vat_enc = get_qr_encoding(2, record.company_id.vat or '')
            # date_order = fields.Datetime.from_string(record.create_date)
            if record.check_in:
                time_sa = fields.Datetime.context_timestamp(self.with_context(tz='Asia/Riyadh'), record.check_in)
            else:
                time_sa = fields.Datetime.context_timestamp(self.with_context(tz='Asia/Riyadh'), record.create_date)
            timestamp_enc = get_qr_encoding(3, time_sa.isoformat())
            invoice_total_enc = get_qr_encoding(4, str(record.amount_total))
            total_vat_enc = get_qr_encoding(5,
                                            str(record.currency_id.round(record.amount_total - record.amount_untaxed)))

            str_to_encode = seller_name_enc + company_vat_enc + timestamp_enc + invoice_total_enc + total_vat_enc
            qr_code_str = base64.b64encode(str_to_encode).decode('UTF-8')
            return qr_code_str

    @api.depends('check_out')
    def compute_check_out_hijri(self):
        for record in self:
            if record.check_out:
                hijri_date = convert.Gregorian(record.check_out.year, record.check_out.month,
                                               record.check_out.day).to_hijri()
                record.check_out_hijri = str(hijri_date)
            else:
                record.check_out_hijri = ''

    @api.depends('your_date_field')
    def compute_hijri_date(self):
        for record in self:
            if record.your_date_field:
                hijri_date = convert.Gregorian(record.your_date_field.year, record.your_date_field.month,
                                               record.your_date_field.day).to_hijri()
                record.hijri_date = str(hijri_date)
            else:
                record.check_out_hijri = ''

    def get_default_sequence(self):
        return self.env['ir.sequence'].sudo().next_by_code('hotel.booking.ref')

    vendor_id = fields.Many2one('res.partner', compute='get_vendor_id')

    def unlink(self):
        for rec in self:
            if not self.env.user.has_group('hotel_booking.group_delete_booking_user'):
                raise UserError("You are not allowed to delete booking!")
            if rec.state != 'draft':
                raise UserError(_('Cannot delete a record which is in state \'%s\'.') % (rec.state,))
        return super(HotelBooking, self).unlink()

    def get_vendor_id(self):
        for rec in self:
            vendor = 0
            for line in rec.line_ids:
                vendor = line.vendor.id or line.vendor_id.id
            rec.vendor_id = vendor

    def action_payment(self):
        self.state = 'paid'
        return {
            'type': 'ir.actions.act_window',
            'name': 'Payment',
            'view_mode': 'form',
            'view_type': 'form',
            'view_id': self.env.ref('account.view_move_form').id,
            'res_model': "account.move",
            'domain': [('move_type', '=', 'out_invoice'), ('id', '=', self.move_id.id)],
            'target': 'new',
            'res_id': self.move_id.id,
        }

    def prepare_attachments(self):
        report_template_id = self.env.ref('hotel_booking.customer_hotel_booking_report')._render_qweb_pdf(self.id)
        data_record = base64.b64encode(report_template_id[0])
        attachment_values = {
            'name': "Confirmation Customer Booking",
            'type': 'binary',
            'datas': data_record,
            'store_fname': data_record,
            'mimetype': 'application/pdf',
        }
        return self.env['ir.attachment'].create(attachment_values)

    def prepare_attachments_folio_invoice(self):
        report_template_id = self.env.ref('hotel_booking.action_folio_invoice_form_report')._render_qweb_pdf(self.id)
        data_record = base64.b64encode(report_template_id[0])
        attachment_values = {
            'name': "Folio Invoice",
            'type': 'binary',
            'datas': data_record,
            'store_fname': data_record,
            'mimetype': 'application/pdf',
        }
        return self.env['ir.attachment'].create(attachment_values)

    def action_confirmation_send(self):
        """opens a window to compose an email,
        with template message loaded by default"""
        active_model = self.env.context.get('active_model')
        active_id = self.env.context.get('active_id')
        self = self.env[active_model].browse(active_id)
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = \
                ir_model_data._xmlid_lookup('hotel_booking.confirmation_customer_mail_booking')[2]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data._xmlid_lookup('mail.email_compose_message_wizard_form')[2]
        except ValueError:
            compose_form_id = False

        attachment = self.prepare_attachments()
        attachment_folio_invoice = self.prepare_attachments_folio_invoice()
        ctx = {
            'default_model': 'hotel.booking',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'default_attachment_ids': [(6, 0, [attachment.id, attachment_folio_invoice.id])],
        }
        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

    def send_confirmation_and_folio_invoice(self):
        partner_id = self.partner_id if self.booking_source == 'direct' else self.company_booking_source if self.booking_source == 'company' else self.online_travel_agent_source

        attachment_confirmation = self.prepare_attachments()
        attachment_folio_invoice = self.prepare_attachments_folio_invoice()
        ctx = {
            'model': 'hotel.booking',
            'res_id': self.ids[0],
            # 'use_template': False,
            # 'template_id': template_id,
            'composition_mode': 'comment',
            'attachment_ids': [(6, 0, [attachment_confirmation.id, attachment_folio_invoice.id])],
            'subject': 'Booking Confirmation',
            'partner_ids': [(4, partner_id.id)],
        }
        composer = self.env['mail.compose.message'].create(ctx)
        composer._action_send_mail()

    def action_vendor_booking_send_email(self):
        if not self:
            active_model = self.env.context.get('active_model')
            active_id = self.env.context.get('active_id')
            self = self.env[active_model].browse(active_id)
        for rec in self:
            template_vend = self.env.ref('hotel_booking.vendor_mail_booking_details_notification')
            self.env['mail.template'].browse(template_vend.id).send_mail(rec.id, force_send=True)

    def action_customer_booking_send_email(self):
        if not self:
            active_model = self.env.context.get('active_model')
            active_id = self.env.context.get('active_id')
            self = self.env[active_model].browse(active_id)
        for rec in self:
            template_vend = self.env.ref('hotel_booking.customer_mail_booking_details_notification')
            self.env['mail.template'].browse(template_vend.id).send_mail(rec.id, force_send=True)

    booking_number = fields.Char('Booking Number')

    name = fields.Char(string='Booking #', copy=False)
    company_id = fields.Many2one('res.company', 'Company', index=True, default=lambda self: self.env.company,
                                 required=True,
                                 store=True)
    state = fields.Selection(STATES, default='draft', track_visibility="onchange", string='booking state')
    email = fields.Char('Email', related='partner_id.email')
    partner_id = fields.Many2one('res.partner', string='Customer', required=True, domain="[('parent_id','=',company_booking_source)]")
    note = fields.Text()
    payment_number = fields.Char()
    user_id = fields.Many2one('res.users', 'Booked By', default=lambda self: self.env.user)
    amount_invoiced = fields.Monetary("Invoiced")
    amount_paid = fields.Monetary("Paid", compute='_compute_amount_paid')
    amount_due = fields.Monetary("Amount Due", compute='_compute_amount_paid', store=True)
    currency_id = fields.Many2one('res.currency', readonly=True, default=lambda self: self.env.company.currency_id)
    invoice_ids = fields.One2many('account.move', 'booking_id')
    check_in_done = fields.Boolean(default=False)
    check_out_done = fields.Boolean(default=False)
    transfer_ids = fields.One2many('hotel.transfer', 'booking_id')
    transfer_count = fields.Integer(compute='_compute_transfer_count')
    invoice_total = fields.Float(compute="_compute_invoice_total")
    line_ids = fields.One2many('hotel.booking.line', 'booking_id', copy=True)
    rooms = fields.Char(compute="_compute_room_names")
    service_ids = fields.One2many('booking.services', 'booking_id', copy=True)

    # ARCHIVED FIELDS
    hotel_id = fields.Many2one('hotel.hotel', related='company_id.related_hotel_id', store=True, readonly=False)
    pricelist_id = fields.Many2one('hotel.pricelist')
    number_of_adults = fields.Integer(string='Adults', default=1, track_visibility="onchange")
    number_of_children = fields.Integer(string='Children', default=0, track_visibility="onchange")
    check_in = fields.Datetime(string='old Check In', default=lambda self: self.env.company.audit_date, required=True)
    check_out = fields.Datetime(string='old Check Out', default=lambda self: self.env.company.audit_date, required=True)
    new_check_in = fields.Date(string='Check In', default=lambda self: self.env.company.audit_date, required=True)
    new_check_out = fields.Date(string='Check Out', default=lambda self: self.env.company.audit_date, required=True)
    audit_date = fields.Date(string='Audit Date', default=lambda self: self.env.company.audit_date, readonly=True)
    check_in_date = fields.Date(compute='compute_check_in_date', store=True)
    check_out_date = fields.Date(compute='compute_check_out_date', store=True)
    room_type_id = fields.Many2one('hotel.room.type', string='Room Type', domain="[('hotel_id','=',hotel_id)]")
    room_id = fields.Many2one('hotel.room', string='Room',
                              domain="[('room_type_id', '=', room_type_id),('hotel_id','=',hotel_id)]",
                              track_visibility="onchange")
    # actual_check_in = fields.Datetime(string="Actual Check-In", compute="compute_actual_check_in_out")
    # actual_check_out = fields.Datetime(string="Actual Check-Out", compute="compute_actual_check_in_out")
    number_of_days = fields.Integer(string='Total Days')
    number_of_room = fields.Integer(compute='calc_number_rooms', string='Number Of Rooms')
    customer_name = fields.Char(string='Customer Name')
    # customer_name_display = fields.Char(string='Customer', compute='_compute_customer_name_display')
    street = fields.Char('Street')
    street2 = fields.Char('Street2')
    zip = fields.Char('Zip')
    city = fields.Char('City')
    state_id = fields.Many2one("res.country.state", string='State')
    country_id = fields.Many2one('res.country', string='Country')
    national_id = fields.Char(string='National ID')
    passport_no = fields.Char(string='Passport ID')
    condition_id = fields.Many2one('conditions.terms', copy=True, store=True)
    conditions = fields.Html('Conditions', related='condition_id.terms', readonly=False, copy=True, store=True)
    customer_type = fields.Selection([('new', 'New Customer'), ('existing', 'Existing Customer')],
                                     string='Customer Type', default='new')
    is_contract = fields.Boolean(compute='check_exist_contract_or_not')
    signature = fields.Binary()
    signed_by = fields.Char()
    signed_on = fields.Datetime()
    type = fields.Selection([('every_day', 'Every Day'), ('every_day_checkin', 'Every Day Except Checkin'),
                             ('every_day_checkout', 'Every Day Except Checkout'), ('one_time', 'One Time'), ],
                            default="", string="Type")
    # ezee absolute cloning
    total_nights = fields.Integer()
    reservation_type = fields.Many2one('booking.type')
    rooms_count = fields.Integer(compute='get_rooms_count')
    booking_source = fields.Selection(selection='_get_booking_source', required=True, default='direct')
    travel_agent_booking_source = fields.Many2one('res.partner', domain="[('travel_type', '=', 'agent')]")
    online_travel_agent_source = fields.Many2one('res.partner', domain="[('online_travel_agent', '=', True)]")
    company_booking_source = fields.Many2one('res.partner', domain="[('is_company', '=',True)]")
    company_code = fields.Char(related='company_booking_source.company_code', string="Company Code")
    ref = fields.Char(string='Reference')
    apply_ntmp = fields.Boolean(compute='get_ntmp_state')
    # used only in case of others booking source
    booking_source_id = fields.Many2one('booking.source', string="Other Sources")
    business_source_id = fields.Many2one('business.source')
    # guest information
    guest_option = fields.Selection(selection=[
        ('create', 'Create New Guest'),
        ('exist', 'Select Existing Guest'),
    ], default='exist', required=True)
    guest_title = fields.Selection(selection=[
        ('dr', 'Dr.'), ('jn', 'Jn.'), ('mam', 'Mam.'), ('mr', 'Mr.'),
        ('mrs', 'Mrs.'), ('ms', 'Ms.'), ('sir', 'Sir'), ('sr', 'Sr.'),
    ], default='mr', required=True)
    guest_name = fields.Char()
    guest_mobile = fields.Char(string='Mobile')
    guest_email = fields.Char(string='Guest Email')
    guest_address = fields.Char(string='Address')
    guest_country_id = fields.Many2one('res.country', string='Guest Country')
    guest_state_id = fields.Many2one('res.country.state', string='Guest State')
    guest_city = fields.Char(string='Guest City')
    guest_zip_code = fields.Char(string='Guest Zip')
    guest_list = fields.Boolean()
    guest_ids = fields.One2many('booking.guest', 'booking_id')
    folio_ids = fields.One2many('booking.folio', 'booking_id')
    cancel_reason_id = fields.Many2one('booking.cancel.reason')
    payment_type = fields.Selection(selection=[('postpaid', 'PostPaid'), ('cash', 'Cash')], string='Payment Type State')
    account_company_id = fields.Many2one('res.partner', domain="[('is_company', '=', True)]")
    # checkboxes
    book_all_available_rooms = fields.Boolean()
    quick_group_booking = fields.Boolean()
    book_by_bed = fields.Boolean()
    complimentary_room = fields.Boolean()
    house_use = fields.Boolean()
    price_include_tax = fields.Boolean()
    reservation_confirmed = fields.Boolean(compute='onchange_reservation_confirmed')
    today_is_checkout = fields.Boolean(compute='compute_today_is_checkout')
    today_is_checkin = fields.Boolean(compute='compute_today_is_checkin')
    # amount fields
    amount_untaxed = fields.Monetary(string='Untaxed Amount', store=True, compute='_amount_all', tracking=5)
    amount_tax = fields.Monetary(string='Taxes', store=True, compute='_amount_all')
    amount_total = fields.Monetary(string='Total', store=True, compute='_amount_all', tracking=4)
    text_message_chat_api = fields.Text("Message")
    # buttons
    add_package = fields.Boolean()
    amend_stay = fields.Boolean()
    # filters
    filter_type = fields.Selection(selection=[
        ('today_arrival', 'Today Arrival'), ('tomorrow_check_in', 'Tomorrow Check In'),
        ('next7_check_in', 'Next 7 Days Arrival'), ('today_check_out', "Today's Check Out"),
        ('today_departure', 'Today Duo Out'), ('tomorrow_departure', 'Tomorrow Duo Out'), ('none', 'None')
    ])
    has_one_line = fields.Boolean(compute='compute_has_one_line', store=True)
    edit_price = fields.Boolean(compute='price_unit_group')
    edit_price_include_tax = fields.Boolean(compute='price_tax_group')
    payment_type_id = fields.Selection(string="Payment Type",
                                       selection=[('cash', 'Cash'), ('city_ledger', 'City Ledger'),
                                                  ('charge_city_ledger',
                                                   'Room Charge - City Ledger, Extra Charge - Cash')], default='cash',
                                       required=False, )
    balance = fields.Monetary(related='company_booking_source.balance', string='CL Balance')
    total_advance_payment = fields.Monetary(related='partner_id.total_advanced_payment')
    check_partner_advance = fields.Boolean(compute='check_advance')
    validation_error = fields.Char()
    settled_by_city_ledger = fields.Boolean()
    company_paid = fields.Float("Actual Paid City Ledger", copy=False, readonly=True)
    paid_amount_city_ledger = fields.Float("Transferred To City Ledger", copy=False, readonly=True,
                                           compute='calc_paid_amount_city_ledger')
    memo = fields.Text("Memo")
    settled_by_company = fields.Boolean()
    is_selected = fields.Boolean("#")
    season_id = fields.Many2one('season.duration', string='Season', compute='_compute_season', store=True)
    ignore_record_rule = fields.Boolean()
    amount_in_words = fields.Char()
    printed_by = fields.Char(string="Printed By", compute="_compute_printed_by")
    city_ledger_balance = fields.Float("City Ledger Balance", compute='calc_balance')
    cash_paid = fields.Monetary("Cash Paid", compute='calc_paid_amount_cash')
    bank_paid = fields.Monetary("Bank Paid", compute='calc_paid_amount_cash')
    front_id = fields.Binary(related='partner_id.front_id')
    day_use = fields.Boolean()
    actual_no_room = fields.Integer("Actual Rooms", compute='_compute_no_rooms')
    actual_no_night = fields.Integer("Actual Room Nights", compute='_compute_no_rooms')
    room_charge_mun = fields.Float('Room Charge Municipality', compute='get_charges_total')
    room_charge_vat = fields.Float('Room Charge VAT', compute='get_charges_total')
    room_charge_tax = fields.Float('Room Charge Tax', compute='get_charges_total')
    room_charge_subtotal = fields.Float('Room Charge Subtotal', compute='get_charges_total')
    room_charge_total = fields.Float('Room Charge Total', compute='get_charges_total')
    service_total_mun = fields.Float("Service Total Municipality", compute='get_charges_total')
    service_total_vat = fields.Float("Service Total VAT", compute='get_charges_total')
    service_total_tax = fields.Float("Service Total Tax", compute='get_charges_total')
    service_total_subtotal = fields.Float("Service Total Subtotal", compute='get_charges_total')
    service_total_total = fields.Float("Service Total Total", compute='get_charges_total')
    room_price_discount = fields.Float("Room Charge Discount", compute='get_charges_total')
    service_price_discount = fields.Float("Service Total Discount", compute='get_charges_total')
    price_discount = fields.Float("Total Discount", compute='get_charges_total')

    account_account_id = fields.Many2one('account.account', string='Account',compute='_compute_account_account_id',store=True)

    @api.depends('booking_source')
    def _compute_account_account_id(self):
      # assign account
      for booking in self:
          account_account_id = self.env['booking.source'].search([('name', '=', booking.booking_source)], limit=1).account_account_id
          booking.account_account_id = account_account_id.id

    @api.model
    def update_booking_account(self):
        self.env.cr.execute("update hotel_booking set account_account_id = (select account_account_id from booking_source where name = hotel_booking.booking_source) where account_account_id is null")
        self.env.cr.commit()

    @api.onchange('folio_ids')
    def get_charges_total(self):
        for rec in self:
            if rec.folio_ids:
                rec.room_charge_mun = sum(rec.folio_ids.mapped('price_municipality'))
                rec.room_charge_vat = sum(rec.folio_ids.mapped('price_vat'))
                rec.room_charge_tax = sum(rec.folio_ids.mapped('room_price_tax'))
                rec.room_charge_subtotal = sum(rec.folio_ids.mapped('room_price_subtotal'))
                rec.room_charge_total = sum(rec.folio_ids.mapped('room_price_total'))
                rec.service_total_mun = sum(rec.folio_ids.mapped('service_price_municipality'))
                rec.service_total_vat = sum(rec.folio_ids.mapped('service_price_vat'))
                rec.service_total_tax = sum(rec.folio_ids.mapped('service_price_tax'))
                rec.service_total_subtotal = sum(rec.folio_ids.mapped('service_price_subtotal'))
                rec.service_total_total = sum(rec.folio_ids.mapped('service_price_total'))
                rec.room_price_discount = sum(rec.folio_ids.mapped('room_price_discount'))
                rec.service_price_discount = sum(rec.folio_ids.mapped('service_price_discount'))
                rec.price_discount = sum(rec.folio_ids.mapped('price_discount'))
            else:
                rec.room_charge_mun = False
                rec.room_charge_vat = False
                rec.room_charge_tax = False
                rec.room_charge_subtotal = False
                rec.room_charge_total = False
                rec.service_total_mun = False
                rec.service_total_vat = False
                rec.service_total_tax = False
                rec.service_total_subtotal = False
                rec.service_total_total = False
                rec.room_price_discount = False
                rec.service_price_discount = False
                rec.price_discount = False

    @api.onchange('booking_source')
    def reset_booking_source(self):
        for rec in self:
            rec.online_travel_agent_source = False
            rec.company_booking_source = False

    @api.onchange('company_booking_source')
    def reset_partner(self):
        for rec in self:
            rec.partner_id = False

    @api.constrains('line_ids')
    def check_booking_line(self):
        if not self.line_ids:
            raise ValidationError("Please Set a Line For Booking 0r Discard Booking")

    @api.constrains('line_ids')
    def _compute_no_rooms(self):
        for rec in self:
            if rec.folio_ids:
                rec.actual_no_room = len(rec.folio_ids.filtered(lambda l: l.state != 'cancelled'))
                rec.actual_no_night = len(rec.folio_ids.line_ids.filtered(
                    lambda l: l.state != 'cancelled' and l.particulars == 'Room Charge'))
            else:
                rec.actual_no_room = 0
                rec.actual_no_night = 0

    @api.constrains('line_ids')
    def check_act_no_nights(self):
        for rec in self:
            if rec.actual_no_night > 10000:
                raise ValidationError(f"Your Max Night For Booking Is 10000 Night not {rec.actual_no_night}")

    def calc_paid_amount_cash(self):
        self.paid_amount_city_ledger = False
        self.cash_paid = 0
        self.bank_paid = 0
        for line in self:
            if line.folio_ids:
                cash_payment = line.folio_ids.line_ids.filtered(lambda
                                                                    l: l.payment_id and l.payment_id.journal_id.type == 'cash' and l.particulars == 'Cash').mapped(
                    'amount')
                bank_payment = line.folio_ids.line_ids.filtered(lambda
                                                                    l: l.payment_id and l.payment_id.journal_id.type == 'bank' and l.particulars == 'Bank').mapped(
                    'amount')
                if cash_payment or bank_payment:
                    line.cash_paid = abs(sum(cash_payment))
                    line.bank_paid = abs(sum(bank_payment))
                else:
                    line.cash_paid = 0.0
                    line.bank_paid = 0.0

    def calc_balance(self):
        for rec in self:
            if rec.paid_amount_city_ledger or rec.company_paid:
                rec.city_ledger_balance = rec.paid_amount_city_ledger - rec.company_paid
            else:
                rec.city_ledger_balance = 0.0

    @api.depends('printed_by')
    def _compute_printed_by(self):
        self.printed_by = False
        for record in self:
            record.printed_by = self.env.user.name

    def print_booking_payments(self):
        payment_ids = self.env['account.payment'].sudo().search([('booking_id', '=', self.id)]).ids
        booking_amount = sum(self.env['account.payment'].sudo().search([('booking_id', '=', self.id)]).mapped('amount'))
        self.amount_in_words = self.currency_id.with_context(lang=self.user_id.lang or 'es_ES').amount_to_text(booking_amount)
        if self.company_paid == 0.0 and self.payment_type_id == 'city_ledger':
            raise ValidationError("Nothing To Print")
        else:
            return self.env.ref('hotel_booking.action_report_payment_document').report_action(payment_ids)

    def print_booking_invoices(self):
        invoice_ids = self.env['account.move'].sudo().search([('booking_id', '=', self.id),('move_type','=','out_invoice')]).ids
        if not invoice_ids:
            raise ValidationError("Nothing To Print")
        return self.env.ref('einv_sa.action_tax_invoice_report').report_action(invoice_ids)

    def settled_booking_amount(self):
        partner_id = self.partner_id if self.payment_type_id == 'cash' else self.company_booking_source
        for rec in self.folio_ids:
            if self.payment_type_id == 'cash':
                folio_payments = rec.line_ids.filtered(lambda l: l.payment_id)
                if folio_payments and rec.price_due < 0.0:
                    if self.booking_source == 'company':
                        self.company_booking_source.total_advanced_payment += abs(rec.price_due)
                    elif self.booking_source == 'direct':
                        self.partner_id.total_advanced_payment += abs(rec.price_due)
                vals = {
                    'folio_id': rec.id,
                    'day': fields.Date.today(),
                    'amount': abs(rec.price_due),
                    'description': f"Advance Payment for {partner_id.name}",
                    'payment_id': folio_payments[0].payment_id.id if len(
                        folio_payments) > 1 else folio_payments.payment_id.id,
                    'particulars': "Advance Payment",
                }
                self.env['booking.folio.line'].sudo().create(vals)
            else:
                if self.payment_type_id == 'city_ledger' and self.company_booking_source.is_city_ledger and rec.price_due < 0.0:
                    if self.company_booking_source.is_credit_limit and self.company_booking_source.customer_credit_limit > rec.price_total:
                        # self.partner_id.company_booking_source += abs(rec.price_due)
                        folio_payments = rec.line_ids.filtered(lambda l: l.payment_id)[0]
                        for payment_line in folio_payments:
                            payment_line.payment_id.action_draft()
                            payment_line.payment_id.update({'amount': rec.price_total, 'is_payment': True})
                            payment_line.update({'amount': -rec.price_total})
                            payment_line.payment_id.action_post()
                        if self.company_paid:
                            if self.company_paid != self.amount_total:
                                advanced_payment = abs(self.amount_due)
                                self.company_booking_source.total_advanced_payment += advanced_payment
                                self.update({'company_paid': self.amount_total})

    def create_advance_payment(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Apply Advance Payments',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': "advance.payment",
            'target': 'new',
            'binding_model_id': self.id,
            'context': {
                'default_company_id': self.company_id.id,
                'default_currency_id': self.currency_id.id,
                'default_partner_id': self.company_booking_source.id if self.company_booking_source else self.partner_id.id,
                'default_partner_type': 'customer',
                'default_booking_id': self.id,
                'default_amount': abs(self.amount_due)
            }
        }

    def calc_paid_amount_city_ledger(self):
        self.paid_amount_city_ledger = False
        for line in self:
            if line.folio_ids:
                city_ledger_payment = line.folio_ids.line_ids.filtered(lambda l: l.particulars == 'City Ledger').mapped(
                    'amount')
                refund_payment = line.folio_ids.line_ids.filtered(lambda l: l.particulars == 'Refund').mapped('amount')
                if city_ledger_payment:
                    if refund_payment:
                        line.paid_amount_city_ledger = abs(sum(city_ledger_payment)) - sum(refund_payment)
                    else:
                        line.paid_amount_city_ledger = abs(sum(city_ledger_payment))
                else:
                    line.paid_amount_city_ledger = 0.0

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        domain = args
        if self.env.context.get('ignore_record_rule'):
            company_ids = self.env['res.company'].sudo().search([]).ids
            domain = ['|', ('company_id', '=', False), ('company_id', 'in', company_ids)] + args
            return super(HotelBooking, self.sudo()).search(domain, offset=offset, limit=limit, order=order, count=count)
        return super(HotelBooking, self).search(domain, offset=offset, limit=limit, order=order, count=count)

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        if self.env.context.get('ignore_record_rule'):
            company_ids = self.env['res.company'].sudo().search([]).ids
            self = self.with_context(allowed_company_ids=company_ids)
            return super(HotelBooking, self.sudo()).search_read(domain=domain, fields=fields, offset=offset,
                                                                limit=limit, order=order)
        return super(HotelBooking, self).search_read(domain=domain, fields=fields, offset=offset, limit=limit,
                                                     order=order)

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        if self.env.context.get('ignore_record_rule'):
            company_ids = self.env['res.company'].sudo().search([]).ids
            args = ['|', ('company_id', '=', False), ('company_id', 'in', company_ids)] + args
            return super(HotelBooking, self.sudo()).name_search(name, args=args, operator=operator, limit=limit)
        return super(HotelBooking, self).name_search(name, args=args, operator=operator, limit=limit)

    @api.onchange('folio_ids')
    def get_rooms_count(self):
        for rec in self:
            if rec.folio_ids:
                rec.rooms_count = len(rec.folio_ids)
            else:
                rec.rooms_count = 0

    @api.depends('create_date')
    def _compute_season(self):
        for record in self:
            if record.create_date:
                season = self.env['season.duration'].search(
                    [('date_from', '<=', record.create_date), ('date_to', '>=', record.create_date)], limit=1)
                record.season_id = season.id if season else False

    @api.depends('total_advance_payment')
    @api.onchange('booking_source', 'company_booking_source', 'payment_type_id')
    def check_advance(self):
        for rec in self:
            if rec.booking_source == 'company':
                partner = rec.company_booking_source
            else:
                partner = rec.partner_id

            total_advance_payment = partner.total_advanced_payment

            if total_advance_payment > 0.0 and rec.amount_paid == 0.0:
                rec.check_partner_advance = True
                validation_error = (
                    f"Attention Please, Guest {partner.name} "
                    f"has an Advance Payment of {total_advance_payment}"
                )
            else:
                rec.check_partner_advance = False
                validation_error = ""

            rec.validation_error = validation_error

    def apply_advance_payment(self):
        for rec in self:
            if rec.payment_type_id == 'city_ledger' and rec.booking_source == 'company':
                payment_amount = rec.amount_total if rec.company_booking_source.total_advanced_payment >= rec.amount_total else rec.company_booking_source.total_advanced_payment
                account_payment_obj = self.env['account.payment'].search(
                    [('partner_id', '=', rec.company_booking_source.id), ('state', '=', 'posted'),
                     ('is_advance_payment', '=', True)], order='create_date desc', limit=1)
            else:
                payment_amount = rec.amount_total if rec.total_advance_payment >= rec.amount_total else rec.total_advance_payment
                account_payment_obj = self.env['account.payment'].search(
                    [('partner_id', '=', rec.partner_id.id), ('state', '=', 'posted'),
                     ('is_advance_payment', '=', True)],
                    order='create_date desc', limit=1)

            if account_payment_obj:
                if len(rec.folio_ids) == 1:
                    vals = {
                        'folio_id': rec.folio_ids[0].id,
                        'day': fields.Date.today(),
                        'amount': -payment_amount,
                        'description': "Paid From Advance Payment",
                        'payment_id': account_payment_obj[0].id,
                        'particulars': "Advance Payment",
                    }
                    self.env['booking.folio.line'].sudo().create(vals)
                else:
                    for folio in rec.folio_ids:
                        vals = {
                            'folio_id': folio.id,
                            'day': fields.Date.today(),
                            'amount': -folio.price_total,
                            'description': "Paid From Advance Payment",
                            'payment_id': account_payment_obj[0].id,
                            'particulars': "Advance Payment",
                        }
                        self.env['booking.folio.line'].sudo().create(vals)

                if account_payment_obj.extra_amount - payment_amount < 0.0:
                    account_payment_obj.extra_amount = 0.0
                else:
                    account_payment_obj.extra_amount -= payment_amount

                # todo check booking source if city or cash
                if rec.payment_type_id == 'city_ledger' and rec.booking_source == 'company':
                    rec.company_booking_source.total_advanced_payment -= payment_amount
                else:
                    rec.partner_id.total_advanced_payment -= payment_amount

    @api.onchange('partner_id', 'booking_source')
    def onchange_guest(self):
        for rec in self:
            if rec.booking_source:
                if rec.booking_source == 'company':
                    rec.payment_type_id = 'city_ledger'
                else:
                    rec.payment_type_id = 'cash'


    def update_guest_name(self):
        for record in self:
            if record.partner_id:
                for line in record.folio_ids:
                    line.update({'partner_id': record.partner_id.id})

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

    @api.onchange('day_use')
    def onchange_day_use(self):
        if self.day_use and self.new_check_in:
            self.new_check_out = self.new_check_in

    @api.depends('line_ids')
    def price_tax_group(self):
        if self.env.user.has_group('hotel_booking.edit_price_tax_group'):
            self.edit_price_include_tax = True
        else:
            self.edit_price_include_tax = False

    def get_ntmp_state(self):
        for rec in self:
            if rec.company_id.apply_ntmp:
                rec.apply_ntmp = True
            else:
                rec.apply_ntmp = False

    def ntmp_state(self):
        pass

    def calc_number_rooms(self):
        for rec in self:
            if rec.folio_ids:
                rec.number_of_room = len(rec.folio_ids)
            else:
                rec.number_of_room = 0

    @api.depends('line_ids')
    def price_unit_group(self):
        if self.env.user.has_group('hotel_booking.edit_price_unit_group'):
            self.edit_price = True
        else:
            self.edit_price = False

    # @api.onchange('company_booking_source')
    # def get_company_booking_source(self):
    #     if self.company_booking_source:
    #         company_booking_code = self.env['res.partner'].search([('name', '=', self.company_booking_source.name)],limit=1)
    #         self.company_code = company_booking_code.company_code

    # @api.onchange('company_code')
    # def get_company_code(self):
    #     if self.company_code:
    #         company_booking = self.env['res.partner'].search([('company_code', '=', self.company_code)], limit=1)
    #         self.company_booking_source = company_booking.id

    def _get_booking_source(self):
        if self.env.user.has_group("hotel_booking.booking_source_company_group"):
            return [
                ('online_agent', 'Online Travel Agent'),
                ('company', 'Company'),
                ('direct', 'Direct'),
                ('government_booking', 'Government Booking'),
                ('contract_booking', 'Contract Booking'),
                ('allotment_booking', 'Allotment Booking'),
            ]
        else:
            return [('online_agent', 'Online Travel Agent'), ('direct', 'Direct'), ('travel_agent', 'Travel Agent')]

    def _get_confirm_report_base_filename(self):
        self.ensure_one()
        if self.partner_id and self.company_booking_source:
            text = '%s-%s-%s' % (
                self.partner_id.name, self.company_booking_source.name, self.company_booking_source.company_code)
        elif not self.partner_id and self.company_booking_source:
            text = '%s-%s' % (self.company_booking_source.name, self.company_booking_source.company_code)
        elif self.partner_id and not self.company_booking_source:
            text = '%s' % self.partner_id.name
        else:
            text = 'Confirmation Booking'
        return text

    @api.depends('line_ids')
    def compute_has_one_line(self):
        for booking in self:
            booking.has_one_line = True if len(booking.line_ids) > 0 else False

    # TODO include service lines
    @api.depends('line_ids.price_total')
    def _amount_all(self):
        for booking in self:
            amount_untaxed = amount_tax = 0.0
            for line in booking.line_ids:
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax
            booking.update({
                'amount_untaxed': amount_untaxed,
                'amount_tax': amount_tax,
                'amount_total': amount_untaxed + amount_tax,
            })

    @api.depends('folio_ids.line_ids')
    def _compute_amount_paid(self):
        for rec in self:
            rec.amount_paid = 0
            amount_paid = 0
            if rec.folio_ids:
                for folio in rec.folio_ids:
                    for line in folio.line_ids:
                        if line.payment_id:
                            amount_paid += abs(line.amount)
                # rec.amount_paid = amount_paid
                rec.amount_paid = sum(rec.folio_ids.mapped('price_paid'))
                rec.amount_due = sum(rec.folio_ids.mapped('price_due'))
                rec.amount_total = sum(rec.folio_ids.mapped('price_total'))

    # @api.onchange('amount_paid', 'amount_total')
    # def _compute_amount_due(self):
    #     for rec in self:
    #         rec.amount_due = sum(rec.folio_ids.mapped('price_due'))

    @api.onchange('line_ids')
    def get_available_rooms(self):
        for booking in self:
            room_type_lst = [line.room_type for line in booking.line_ids]
            c = Counter(room_type_lst)
            for rec in booking.line_ids:
                if rec.check_in and rec.check_out and rec.room_type:
                    booking_data = self.sudo().env["hotel.booking"].get_booking_data(
                        date_from=rec.check_in.date(), date_to=rec.check_out.date()
                    )
                    available_rooms = []
                    for room_id in self.env["hotel.room"].search([('room_type', '=', rec.room_type.id)]):
                        booking = self.env["hotel.booking"].get_booking(
                            date=self.check_in.date(), room_id=room_id, data=booking_data
                        )
                        if not booking:
                            available_rooms.append(room_id.id)
                    selected_room_type = [v - 1 for k, v in c.items() if k == rec.room_type]
                    if selected_room_type:
                        rec.available_rooms = len(available_rooms) - selected_room_type[0]
                    else:
                        rec.available_rooms = len(available_rooms)

    def get_message_detail_chat(self, hotel_id, company_id, partner_id, type):
        for rec in self:
            txt_message = ''
            if type == 'check_in':
                txt_message = """
                ضيفنا الكريم،
                اهلا وسهلا بك في فندق {}
                انه من دوعي سرورنا ان تقيم معنا
                ونسعي لتوفير غرفة نظيفة ومريحة لاجل اقامة رائعة وذكريات جميلة معنا
                ينتظر موظفونا المدربون جيدًا بشغف لخدمتك وتزويدك بإقامة لا تُنسى حقًا في فندقنا.
                ومن ثم ، إذا احتجت إلى أي مساعدة ، فلا تتردد في السؤال ،
                حيث سيكون من دواعي سرورنا دائمًا أن نكون خدمتك

                Dear Guest,
                Welcome to {}
                It is our pleasure to have you stay with us,
                and we strive to provide a clean and comfortable room
                for a wonderful stay and beautiful memories with us
                Our well-trained staff is eagerly waiting to serve you
                and provide you with a truly memorable stay at our hotel.
                Hence, if you need any assistance, feel free to ask,
                as it will always be our pleasure to be of service to you.
                """.format(hotel_id.name, company_id.english_name or hotel_id.name)
            elif type == 'check_out':
                txt_message = """
                ضيفنا الكريم
                شكرا لزيارتنا في {}.
                نأمل أن تكون إقامتك ممتعة وأن تكون إقامتنا وخدماتنا مقبولة.
                يرجي مساعدتنا من خلال الاستبيان المرفق لتقييم خدماتنا ومساعدتنا علي التطوير
                واخبرنا إذا كان هناك أي طريقة يمكننا من خلالها إجراء تحسينات في أماكن الإقامة
                والخدمات الخاصة بنا للزيارات المستقبلية.
                نتطلع إلى عودتك.

                Dear Guest,
                Thanks for visiting us at {}.
                We hope that you are a new topic and that you are acceptable to us and our services.
                Please help us through the questionnaire dedicated to our services and help us improve
                and tell us, we can make improvements in the accommodation specializing in accommodation.
                We look forward to your return
                """.format(hotel_id.name, company_id.english_name or hotel_id.name)
            elif type == 'confirm':
                txt_message = """
                ضيفنا الكريم شكرا لاختيارك فندق {} لاقامتك
                يسعدنا إبلاغك بأن طلب الحجز الخاص بك مؤكد وأن تفاصيل الحجز الخاصة بك هي كما يلي.

                Dear guest, thank you for choosing {} For your stay
                We are pleased to inform you that your reservation request is CONFIRMED
                and your reservation details are as follows.
                """.format(hotel_id.name, company_id.english_name or hotel_id.name)
            if txt_message:
                return txt_message.replace('&', '%26')
            else:
                return

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
                raise ValidationError(f"{rec.name} check in date can't be in past!")

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

    def compute_today_is_checkin(self):
        for rec in self:
            rec.today_is_checkin = False
            if rec.check_in and rec.state in ['draft', 'confirmed']:
                if rec.company_id.audit_date == rec.check_in.date():
                    rec.today_is_checkin = True

    def compute_today_is_checkout(self):
        for rec in self:
            rec.today_is_checkout = False
            if rec.check_out and rec.state in ['checked_in', 'paid']:
                if rec.company_id.audit_date == rec.check_out.date():
                    rec.today_is_checkout = True

    def button_check_in(self):
        for rec in self:
            if rec.amount_paid == 0.0:
                pass
                # raise ValidationError("Please Settled Booking Amount First Then Checked in")
            if not rec.folio_ids.mapped('line_ids').mapped('payment_id') \
                    and not self.env.user.has_group('hotel_booking.group_no_payment_check_in'):
                raise UserError("you are not allowed to check in without adding any reservation payment!")
            for line in rec.line_ids:
                if line.room_id:
                    line.room_id.write({
                        'state': self.env.ref('hotel_booking.hotel_room_status_dirty').id,
                        'stay_state': self.env.ref('hotel_booking.data_hotel_room_stay_status_arrived').id,
                    })
            rec.state = 'checked_in'
            rec.send_by_whatsapp_direct('check_in')
            self.env.ref('hotel_booking.action_guest_register_form_report').report_action(self)
        message = f'{self.name} is Checked in Successfully'
        return {
            'name': 'Message',
            'type': 'ir.actions.act_window',
            'res_model': 'warn.wizard',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': {'default_message': message, 'default_booking_id': self.id}
        }

    def generate_report(self, type, config=False):
        report_sudo = False
        if type == 'confirm':
            report_sudo = request.env.ref('hotel_booking.customer_hotel_booking_report').sudo()
        elif type == 'check_in':
            report_sudo = request.env.ref('hotel_booking.action_guest_register_form_report').sudo()
        if report_sudo:
            method_name = '_render_qweb_pdf'
            report = getattr(report_sudo, method_name)(
                [self.id], data={'report_type': 'pdf'})[0]
            encoded = base64.b64encode(report)
            encoded = encoded.decode("utf-8")
            base64_file = 'data:application/pdf;base64,{}'.format(encoded)
            return (base64_file)
        else:
            return

    def get_register_form_terms(self):
        return self.env['conditions.terms'].search([('type', '=', 'registration_form')], limit=1).terms

    def get_booking_confirm_terms(self):
        return self.env['conditions.terms'].search([('type', '=', 'confirm')], limit=1).terms

    def send_by_whatsapp_direct(self, type, partner=False):
        if self and self.company_id.use_whatsapp:
            base64_file = self.generate_report(type=type)
            find_default = self.env['sh.configuration.manager'].search([('default_send', '=', 'True')], limit=1)
            if partner:
                user = partner
            else:
                user = self.partner_id or self.company_booking_source
            headers = {"Content-Type": "application/json"}
            if find_default:
                if user.mobile:
                    for rec in self:
                        rec.text_message_chat_api = rec.get_message_detail_chat(
                            hotel_id=rec.hotel_id, company_id=rec.company_id, partner_id=user, type=type
                        )
                        if rec.company_id.display_in_message:
                            message = ''
                            if rec.text_message_chat_api:
                                message = str(self.text_message_chat_api).replace(
                                    '*', '').replace('_', '').replace('%0A', '<br/>').replace('%20', ' ').replace('%26',
                                                                                                                  '&')
                            if find_default.config_type == 'api_chat':
                                url = "https://api.apichat.io/v1/sendText"
                                headers['client-id'] = find_default.instance_id
                                headers['token'] = find_default.token
                                payload = {
                                    "text": rec.text_message_chat_api,
                                    "number": user.mobile,
                                }
                                send_message = requests.post(url=url, headers=headers, data=json.dumps(payload))
                                if send_message.status_code == 200:
                                    send_message_json = send_message.json()
                                    if 'message' in send_message_json.keys():
                                        e = send_message_json['message']
                                        raise UserError(_(e))
                                # send report
                                if base64_file:
                                    url = "https://api.apichat.io/v1/sendFile"
                                    payload = {
                                        "number": user.mobile,
                                        "url": '%s' % base64_file,
                                    }
                                    sendfile = requests.post(
                                        url=url, headers=headers, data=json.dumps(payload))
                                    if sendfile.status_code != 200:
                                        raise UserError(_(sendfile.text))

                            self.env['mail.message'].create({
                                'partner_ids': [(6, 0, user.ids)],
                                'model': 'hotel.booking',
                                'res_id': rec.id,
                                'author_id': self.env.user.partner_id.id,
                                'body': message or False,
                                'message_type': 'comment',
                            })
                else:
                    raise UserError(_("Partner Mobile Number Not Exist"))
            else:
                pass
                # raise UserError(_("No Default Configuration is selected"))

    def button_check_out(self):
        if self.amount_due < 0:
            title = _("Warning for %s", self.user_id.name)
            message = _(
                "This Customer still have money on Booking should be returned")
            warning = {
                'title': title,
                'message': message
            }
            return {'warning': warning}
        amount_paid = 0
        for folio in self.folio_ids:
            for line in folio.line_ids:
                if line.payment_id or line.is_city_ledger:
                    amount_paid += abs(line.amount)
        balance = self.amount_total - amount_paid
        if not self.payment_type == 'postpaid':
            if balance > 0:
                raise UserError("There is Due amount for {}.\n"
                                "you have to settle it first.".format(self.name))
        self.send_by_whatsapp_direct('check_out')
        for line in self.line_ids:
            if line.room_id:
                line.room_id.write({
                    'stay_state': self.env.ref('hotel_booking.hotel_room_stay_status_vacant').id,
                })
            elif line.room_ids:
                for room in line.room_ids:
                    room.write({
                        'stay_state': self.env.ref('hotel_booking.hotel_room_stay_status_vacant').id,
                    })

        self.state = 'checked_out'
        self.move_id.post()
        move_lines = self.folio_ids.mapped('line_ids').mapped('payment_id').mapped('invoice_line_ids').ids
        lines_ids = self.env['account.move.line'].browse(move_lines).filtered(
            lambda line: line.account_id.user_type_id.type in ('receivable', 'payable') and not line.reconciled).ids
        if lines_ids:
            lines = self.env['account.move.line'].browse(lines_ids)
            lines += self.move_id.line_ids.filtered(
                lambda line: line.account_id == lines[0].account_id and not line.reconciled)
            lines.reconcile()
        message = f'{self.name} is Checked Out Successfully'
        return {
            'name': 'Message',
            'type': 'ir.actions.act_window',
            'res_model': 'warn.wizard',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': {'default_message': message, 'default_booking_id': self.id}
        }

    def action_register_payment(self):
        if self.company_booking_source:
            booking_source = [(4, self.company_booking_source.id)]
        elif self.online_travel_agent_source:
            booking_source = [(4, self.online_travel_agent_source.id)]
        else:
            booking_source = False
        return {
            'name': _('Register Payment'),
            'res_model': 'booking.payment.register',
            'view_mode': 'form',
            'target': 'new',
            'type': 'ir.actions.act_window',
            'context': {
                'default_booking': self.id,
                'default_partner_id': self.company_booking_source.id if self.company_booking_source else self.partner_id.id,
                'default_payment_type': 'inbound',
                'default_amount': self.amount_due,
                'default_partner_type': 'customer',
                'default_communication': self.name.replace('BK', 'FO'),
                'default_audit_date': self.company_id.audit_date,
                'default_total_amount_booking': self.amount_total,
                'default_booking_payment_type': self.payment_type_id,
                'default_company_booking_source_ids': booking_source
            }
        }

    def action_refund_payment(self):
        return {
            'name': _('Refunded / Transfer Payment'),
            'res_model': 'booking.refund.payment',
            'view_mode': 'form',
            'target': 'new',
            'type': 'ir.actions.act_window',
            'context': {
                'default_booking_id': self.id,
                'default_is_group_refunded': True,
                'default_partner_id': self.company_booking_source.id if self.company_booking_source else self.partner_id.id,
                'default_payment_type': 'outbound',
                'default_total_amount': abs(self.amount_paid),
                'default_state': 'refund'
            }
        }

    # ezee functions
    @api.onchange('book_all_available_rooms')
    def onchange_book_all_available_rooms(self):
        self.line_ids = [(5, 0, 0)]
        if self.book_all_available_rooms:
            self.quick_group_booking = False
            rooms_count = 0
            for room_type in self.env['room.type'].search([]):
                all_rooms = self.env['hotel.room'].search([('room_type', '=', room_type.id)]).ids
                query = """SELECT room_id  FROM
                    hotel_booking_line WHERE room_type=%s AND
                    (%s,%s) OVERLAPS (check_in, check_out)
                    """
                args = (room_type.id, self.check_in, self.check_out)
                self.env.cr.execute(query, args)
                data = self.env.cr.dictfetchall()
                booked_room_ids = []
                for room in data:
                    if room['room_id']:
                        booked_room_ids.append(room['room_id'])
                available_rooms = list(set(all_rooms) - set(booked_room_ids))
                if len(available_rooms) > 0:
                    rooms_count += len(available_rooms)
                    vals = {
                        'room_type': room_type.id,
                        'available_room_ids': [(6, 0, available_rooms)],
                        'available_rooms': len(available_rooms),
                        'number_of_rooms': len(available_rooms),
                        'number_of_adults': room_type.mini_adults,
                        'number_of_children': room_type.mini_children,
                    }
                    new_booking_line = self.line_ids.new(vals)
                    self.line_ids += new_booking_line
            self.update({
                'rooms_count': rooms_count
            })

    @api.onchange('quick_group_booking')
    def onchange_quick_group_booking(self):
        if self.quick_group_booking:
            self.book_all_available_rooms = False

    @api.onchange('rooms_count')
    def onchange_rooms_count(self):
        self.line_ids = [(5, 0, 0)]
        if self.rooms_count:
            default_type = self.env['room.type'].search([('company_id', '=', self.company_id.id)], limit=1)
            if not default_type:
                raise ValidationError("Active Company has no room types!")
            count = self.rooms_count
            while count > len(self.line_ids):
                vals = {
                    'room_type': default_type.id,
                }
                new_booking_line = self.line_ids.new(vals)
                self.line_ids += new_booking_line

    @api.onchange('state')
    def onchange_reservation_confirmed(self):
        for record in self:
            if record.state == 'confirmed':
                record.reservation_confirmed = True
            else:
                record.reservation_confirmed = False

    @api.onchange('complimentary_room')
    def onchange_complimentary_room(self):
        if self.complimentary_room or self.house_use:
            for line in self.line_ids:
                line.price_unit = 0
        else:
            for line in self.line_ids:
                line.onchange_rate_plan()

    @api.onchange('hotel_id')
    def onchange_hotel_id(self):
        if self.hotel_id:
            self.company_id = self.env['res.company'].search([('related_hotel_id', '=', self.hotel_id.id)])

    def button_open_reservation_card(self):
        return {
            'name': _('Reservation Form'),
            'view_mode': 'form',
            'res_model': 'hotel.booking',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'res_id': self.id,
            'target': 'new',
            'context': {'create': False},
        }

    def button_open_discount_wizard(self):
        return {
            'name': _('Discount'),
            'view_mode': 'form',
            'res_model': 'booking.apply.discount',
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    @api.onchange('guest_list')
    def onchange_guest_list(self):
        if self.guest_list:
            self.guest_ids = [(5, 0, 0)]
            if not self.guest_ids:
                vals = {
                    'guest_title': self.guest_title,
                    'guest_name': self.guest_name,
                    'guest_mobile': self.guest_mobile,
                    'guest_email': self.guest_email,
                    'guest_address': self.guest_address,
                    'guest_country_id': self.guest_country_id.id,
                    'guest_state_id': self.guest_state_id.id,
                    'guest_city': self.guest_city,
                    'guest_zip_code': self.guest_zip_code,
                }
                new_guest_line = self.guest_ids.new(vals)
                self.guest_ids += new_guest_line

    # @api.onchange('rooms_count')
    # def onchange_rooms_count(self):
    #     if not self.env.context.get('book_all_available', False):
    #         old_count = len(self.line_ids)
    #         if self.rooms_count < 1:
    #             self.rooms_count = 1
    #         new_count = self.rooms_count
    #         diff_count = new_count - old_count
    #         if diff_count > 0:
    #             for _ in range(diff_count):
    #                 new_booking_line = self.line_ids.new()
    #                 self.line_ids += new_booking_line
    #         else:
    #             x = self.line_ids[diff_count:]
    #             for i in x:
    #                 self.line_ids = [(3, i.id, 0)]

    @api.onchange('check_in', 'check_out')
    def _compute_total_nights(self):
        for booking in self:
            if booking.check_in and booking.check_out:
                check_in = datetime.combine(booking.check_in.date(), datetime.min.time())
                check_out = datetime.combine(booking.check_out.date(), datetime.min.time())
                delta = (check_out - check_in).days
                booking.total_nights = delta if delta > 0 else 0

    @api.onchange('total_nights')
    def onchange_total_nights(self):
        if self.total_nights and self.check_in:
            check_in = datetime.combine(self.new_check_in, datetime.min.time())
            self.new_check_out = check_in + relativedelta(days=self.total_nights)

    # def get_portal_url(self, suffix='', query_string=''):
    #     return f'/my/bookings/{self.id}{suffix}{query_string}'

    def preview_booking(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'target': 'self',
            'url': self.get_portal_url(),
        }

    def _compute_access_url(self):
        super(HotelBooking, self)._compute_access_url()
        for booking in self:
            booking.access_url = '/my/booking/%s' % (booking.id)

    def has_to_be_signed(self, include_draft=False):
        return self.state != 'cancelled' and not self.signature

    def check_exist_contract_or_not(self):
        for rec in self:
            if rec.line_ids:
                for line in rec.line_ids:
                    if line.check_dir == False and line.is_purchased == False:
                        rec.is_contract = False
                    else:
                        rec.is_contract = True
            else:
                rec.is_contract = True

    def _compute_room_names(self):
        for booking in self:
            booking.rooms = ",".join(booking.line_ids.mapped('room_id').mapped('name'))

    @api.onchange('hotel_id')
    def onchange_hotel(self):
        if self.hotel_id:
            if "default_room_id" in self._context:
                return
            self.room_type_id = self.hotel_id and self.hotel_id.default_room_type_id
            self.room_id = False
        else:
            self.room_type_id = False
            self.room_id = False

    def get_default_hotel_id(self):
        for rec in self:
            if rec.line_ids:
                hotel_id = 0
                for line in rec.line_ids:
                    hotel_id = line.hotel_id.id
                    break
                rec.hotel_id = hotel_id
            else:
                rec.hotel_id = False

    def _compute_invoice_total(self):
        account_payment_obj = self.env['account.payment'].search([('booking_id', '=', self.id)])
        for line in self:
            if account_payment_obj:
                line.invoice_total = sum(account_payment_obj.sudo().mapped('amount_company_currency_signed'))
            else:
                line.invoice_total = 0.0

    def _compute_transfer_count(self):
        for booking in self:
            booking.transfer_count = len(booking.transfer_ids)

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'reference must be unique !'),
    ]

    def create_invoice(self):
        self.ensure_one()
        tax_ids = self.env.company.hotel_default_tax_ids.ids
        invoice_line_vals = []

        for line in self.line_ids:
            for prod in line.service_ids:
                price = prod.service_id.price
                if prod.price_type == "multiply_with_guest":
                    price = line.number_of_adults * price
                qty = line.number_of_days
                if prod.type == "every_day":
                    qty = line.number_of_days
                if prod.type == "every_day_checkin" or prod.type == "every_day_checkout":
                    qty = line.number_of_days - 1
                if prod.type == "one_time":
                    qty = 1.0

                invoice_line_vals += [(0, 0, {
                    'product_id': prod.service_id.product_id.id,
                    'name': 'Extra Charge',
                    'account_id': line.booking_id.account_account_id.id,
                    'quantity': qty,
                    'price_unit': line.price_total if line.price_include_tax else line.price_subtotal,
                    'tax_ids': [(6, 0, line.tax_id.ids or [])],
                })]
            tot_qty = 1.0
            if line.check_dir:
                tot_qty = line.count
            else:
                tot_qty = line.count * line.date_diff
            invoice_line_vals += [(0, 0, {
                'product_id': line.room_id.product_id.id,
                'account_id': line.booking_id.account_account_id.id,
                'name': ' Room Charge ',
                'quantity': tot_qty,
                'price_unit': line.price_total if line.price_include_tax else line.price_subtotal,
                'source_booking_id': line.id,
                'tax_ids': [(6, 0, line.tax_id.ids or [])],
            })]
        if self.booking_source == 'company' and self.payment_type == 'postpaid':
            partner_obj = self.account_company_id.id
        else:
            partner_obj = self.company_booking_source.id if self.company_booking_source else self.partner_id.id
        move_vals = {
            'move_type': 'out_invoice',
            'partner_id': partner_obj,
            'guest_id': self.partner_id.id,
            'booking_id': self.id,
            'narration': self.conditions,
            'invoice_user_id': self._uid,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': invoice_line_vals
        }

        move = self.env['account.move'].with_context({'line_ids': False}).create(move_vals)

        move.action_post()
        self.move_id = move.id

    move_id = fields.Many2one('account.move')

    def button_confirm(self):
        if not self.line_ids:
            raise UserError("You have to add at least one line.")
        for line in self.line_ids:
            vacant = self.env.ref('hotel_booking.hotel_room_stay_status_vacant')
            arrival = self.env.ref('hotel_booking.data_hotel_room_stay_status_arrival')
            if line.room_id:
                if line.room_id.stay_state.id == vacant.id:
                    line.room_id.stay_state = arrival.id
            elif line.room_ids:
                for room in line.room_ids:
                    if room.stay_state.id == vacant.id:
                        room.stay_state = arrival.id

        self.state = "confirmed"
        # self.name = self.get_default_sequence()
        self.action_vendor_booking_send_email()
        self.action_customer_booking_send_email()
        self.send_by_whatsapp_direct('confirm')

    def action_reset_to_draft(self):
        for rec in self:
            rec.state = 'draft'

    @api.onchange('price_include_tax')
    def onchange_price_include_tax(self):

        currency = self.currency_id
        for line in self.line_ids:
            res = line.tax_id.compute_all(line.price_subtotal, partner=self.env['res.partner'])
            joined = []
            included = res['total_included']
            if currency.compare_amounts(included, line.price_subtotal):
                joined.append(_('%s Incl. Taxes', format_amount(self.env, included, currency)))
            excluded = res['total_excluded']
            if currency.compare_amounts(excluded, line.price_subtotal):
                joined.append(_('%s Excl. Taxes', format_amount(self.env, excluded, currency)))
            if joined:
                tax_string = f"(= {', '.join(joined)})"
            else:
                tax_string = " "
            line.tax_string = tax_string

    def button_cancel(self):
        for rec in self:
            for line in rec.line_ids:
                if line.room_id.booking_line_id:
                    raise UserError("Sorry customer is still living in this room. You have to check out before cancel.")
            # for inv in rec.invoice_ids:
            #     inv.button_cancel()
            rec.state = 'cancelled'

    def button_assign_room(self):
        for line in self.line_ids:
            line.change_room = True
            line.assign_room = True

    def button_change_room(self):
        for line in self.line_ids:
            line.room_id.state = self.env.ref('hotel_booking.hotel_room_stay_status_vacant').id
            line.change_room = True
            line.assign_room = True

    def button_add_package(self):
        self.add_package = True

    def button_pass(self):
        pass

    def _get_report_base_filename(self):
        self.ensure_one()
        return self.name

    @api.model
    def create(self, vals):
        if vals.get('guest_name', False):
            partner = self.env['res.partner'].search([('name', '=', vals['guest_name'])])
            if not partner:
                partner = self.env['res.partner'].create({
                    'name': vals['guest_name'],
                    'zip': vals.get('guest_zip_code', False),
                    'city': vals.get('guest_city', False),
                    'state_id': vals.get('guest_state_id', False),
                    'country_id': vals.get('guest_country_id', False),
                    'mobile': vals.get('guest_mobile', False),
                    'email': vals.get('guest_email', False),
                    'customer_rank': 1,
                })
            vals['partner_id'] = partner.id
        res = super(HotelBooking, self).create(vals)
        # for booking in res:
        #     booking.name = "Draft"
        res.name = self.get_default_sequence()
        # Dashboard Instant Update
        dashboard_id = self.env["hotel.booking.dashboard2"].search([], order="id")
        if dashboard_id:
            dashboard_id[-1].update_result()
        return res

    def update_folio(self, check_in, check_out):
        for folio in self.folio_ids:
            date_list = self.get_dates_between(check_in, check_out)
            folio.line_ids.filtered(lambda f: not f.payment_id).unlink()
            for day in date_list:
                number_of_rooms = folio.booking_line_id.number_of_rooms if folio.booking_line_id.number_of_rooms > 0 else 1
                amount_total = folio.booking_line_id.price_unit * number_of_rooms
                rate_plan = folio.booking_line_id.rate_plan
                rate_type = rate_plan.rate_type_id
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
                        amount_total -= service_amount
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
        result = super(HotelBooking, self).write(vals)
        if vals.get('check_in', False) or vals.get('check_out', False):
            print('hhhhhhhhhhhhhhh')
            timezone = pytz.timezone(self.env.user.tz or 'UTC')
            if vals.get('check_in', False):
                check_in = fields.Datetime.from_string(vals['check_in'])
            else:
                check_in = self.check_in
            if vals.get('check_out', False):
                check_out = fields.Datetime.from_string(vals['check_out'])
            else:
                check_out = self.check_out
            check_in = pytz.utc.localize(check_in).astimezone(timezone)
            check_out = pytz.utc.localize(check_out).astimezone(timezone)
            self.update_folio(check_in, check_out)
        # Dashboard Instant Update
        dashboard_id = self.env["hotel.booking.dashboard2"].search([], order="id")
        if dashboard_id:
            dashboard_id[-1].update_result()

        return result

    def action_open_transfers(self):
        action = self.env.ref('hotel_booking.action_hotel_transfer').read()[0]
        action['domain'] = [('id', 'in', self.transfer_ids.ids)]
        return action

    def action_open_invoices(self):
        action = self.env.ref('account.action_account_payments').read()[0]
        action['domain'] = [('booking_id', '=', self.id)]

        action['context'] = {
            'default_booking_id': self.id,
            'default_partner_id':  self.company_booking_source.id if self.company_booking_source else self.partner_id.id,
            'default_guest_id': self.partner_id.id,
        }

        return action

    def get_booking_data(self, date_from, date_to):
        date_list = self.get_dates_between(date_from, date_to)
        data = []

        domain = [
            ('booking_id.state', 'not in', ['cancelled']),
            ('check_in', '<=', date_to),
            ('check_out', '>=', date_from)
        ]

        booking_lines = self.env['hotel.booking.line'].search(domain)

        for booking_line in booking_lines:
            booking = booking_line.booking_id
            booked_dates = booking_line.get_booked_date_list()

            for date in date_list:
                if date in booked_dates:
                    payment_status = "NOT PAID"
                    if booking.amount_paid > 0 and booking.amount_paid == booking.amount_total:
                        payment_status = "PAID"

                    data.append({
                        'check_in': booking_line.check_in,
                        'check_out': booking_line.check_out,
                        'actual_check_in': booking_line.actual_check_in,
                        'actual_check_out': booking_line.actual_check_out,
                        'id': booking.id,
                        'name': booking.name,
                        'room_id': booking_line.room_id.id,
                        'room_ids': booking_line.room_ids.ids,
                        'payment_status': payment_status,
                    })
        return data

    def booking_data_fill_blank_room(self, booking_data, room_ids):
        room_ids = [r.id for r in room_ids]
        booked_room_ids = [d['room_id'] for d in booking_data if d['room_id']]
        vacant_room_ids = [r for r in room_ids if r not in booked_room_ids]

        for each in booking_data:
            if not each['room_id'] and vacant_room_ids:
                each['room_id'] = vacant_room_ids[0]
                vacant_room_ids.pop(0)

        return booking_data

    def get_booking(self, date, room_id, data):
        booking_line_obj = self.env['hotel.booking.line']

        if type(room_id) != int:
            room_id = room_id.id

        for each in data:
            if each['room_id'] == room_id or room_id in each['room_ids']:
                status = booking_line_obj.get_datetime_status(each['check_in'], each['check_out'])
                paid_date_list = booking_line_obj.get_paid_dates(status)
                if date in paid_date_list:
                    return each
        return False

    @staticmethod
    def get_dates_between(date1, date2):
        if isinstance(date1, str):
            date1 = fields.Datetime.from_string(date1)
        if isinstance(date2, str):
            date2 = fields.Datetime.from_string(date2)
        my_list = []
        for n in range(int((date2 - date1).days) + 1):
            my_list.append(date1 + timedelta(n))
        return my_list

    @api.model
    def get_dates_between_exclude(self, date1, date2):
        if isinstance(date1, str):
            date1 = fields.Datetime.from_string(date1)
        if isinstance(date2, str):
            date2 = fields.Datetime.from_string(date2)
        my_list = []
        for n in range(1, int((date2 - date1).days)):
            my_list.append(date1 + timedelta(n))
        return my_list

    @api.model
    def get_room_stay_status(self):
        stay_over = self.env.ref('hotel_booking.data_hotel_room_stay_status').id
        arrived = self.env.ref('hotel_booking.data_hotel_room_stay_status_arrived').id
        return [stay_over, arrived]

    @api.model
    def default_get(self, fields):
        res = super(HotelBooking, self).default_get(fields)
        conditions = self.env['conditions.terms'].search([])
        if conditions and len(conditions) == 1:
            res['condition_id'] = conditions[0].id
        return res


class HotelBookingTransferWizard(models.TransientModel):
    _name = 'hotel.booking.transfer.wizard'
    _description = 'Booking Transfer Wizard'

    type = fields.Selection([('in', 'Check In'), ('out', 'Check Out')], string='Type', required=True)
    transfer_time = fields.Datetime(string="Time", required=True)
    # booking_id = fields.Many2one('hotel.booking', string="Booking #", required=True)
    booking_line_id = fields.Many2one('hotel.booking.line', required=True)

    def action_apply(self):
        self.ensure_one()
        transfer = self.env['hotel.transfer'].create({
            'room_id': self.booking_line_id.room_id.id,
            'type': self.type,
            'transfer_time': self.transfer_time,
            'booking_line_id': self.booking_line_id.id,
        })
        transfer.action_validate()
        if self.type == "in":
            self.booking_line_id.write({'check_in_out_state': 'checked_in'})
        elif self.type == "out":
            self.booking_line_id.write({'check_in_out_state': 'checked_out'})
        else:
            raise IndentationError


class BookingCancelReason(models.Model):
    _name = 'booking.cancel.reason'
    _description = 'Booking Cancel Reason'

    name = fields.Char()
