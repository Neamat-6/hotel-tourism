# -*- coding: utf-8 -*-
import ast

import pytz

from odoo.exceptions import UserError
from odoo import api, fields, models, _
from datetime import datetime, timedelta, date
import base64
import uuid
from dateutil.relativedelta import relativedelta


class HotelBookingContact(models.Model):
    _inherit = "res.partner"

    is_plane_company = fields.Boolean("Is Plane Company")
    is_transportation_company = fields.Boolean("Is Transportation Company")


class ServiceVoucher(models.Model):
    _name = 'service.voucher'
    _description = 'service voucher'

    name = fields.Char(string='Barcode')
    service_id = fields.Many2one('tourism.booking.services')
    date_from = fields.Date()
    date_to = fields.Date()
    meal_number = fields.Selection(selection=[
        ('1', 'Breakfast'), ('2', 'Lunch'), ('3', 'Dinner'),
    ], default='1')
    state = fields.Selection(selection=[
        ('available', 'Available'),
        ('expired', 'Expired'),
        ('redeemed', 'Redeemed'),
    ], default='available')

    _sql_constraints = [
        ('name_uniq', 'CHECK(1=1)', """Barcode must be unique!"""),
    ]


class Services(models.Model):
    _name = 'tourism.booking.services'

    booking_id = fields.Many2one('tourism.hotel.booking')
    line_id = fields.Many2one('tourism.hotel.booking.line')
    service_id = fields.Many2one('hotel.services', string='Service')
    price_type = fields.Selection([('fixed', 'Fixed'), ('multiply_with_guest', 'Multiply With No.of.Guests'), ],
                                  default="fixed", string="Price Type")
    type = fields.Selection([('every_day', 'Every Day'), ('every_day_checkin', 'Every Day Except Checkin'),
                             ('every_day_checkout', 'Every Day Except Checkout'), ('one_time', 'One Time'), ],
                            default="", string="Type")
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    amount = fields.Monetary(compute='_compute_amount', store=True)
    voucher_ids = fields.One2many('service.voucher', 'service_id')
    is_voucher = fields.Boolean()
    general_barcode = fields.Char()
    meal_number = fields.Selection(selection=[
        ('1', 'One Meal'), ('2', 'Two Meals'), ('3', 'Three Meals'),
    ], default='1')

    def button_display_barcode(self):
        if not self.price_type == "multiply_with_guest":
            raise UserError('Price type should be multiply with no. of guests!')
        return {
            'name': _("Barcode"),
            'res_model': 'tourism.booking.services',
            'view_mode': 'form',
            'view_id': self.env.ref('hotel_booking.service_voucher_view_form').id,
            'type': 'ir.actions.act_window',
            'res_id': self.id,
            'target': 'new',
        }

    def button_generate_barcode(self):
        self.voucher_ids = [(5, 0, 0)]
        line_id = self.booking_id.line_ids[0] if self.booking_id.line_ids else False
        # self.general_barcode = str(int(datetime.now().timestamp()))
        if self.type == "every_day":
            days_between = (line_id.check_out - line_id.check_in).days + 1
            date_list = [(line_id.check_in + timedelta(days=i))
                         for i in range(0, days_between + 1)]

        elif self.type == "every_day_checkin":
            days_between = (line_id.check_out - line_id.check_in).days
            start = line_id.check_in + relativedelta(days=1)
            date_list = [(start + timedelta(days=i))
                         for i in range(0, days_between + 1)]

        elif self.type == "every_day_checkout":
            days_between = (line_id.check_out - line_id.check_in).days
            date_list = [(line_id.check_in + timedelta(days=i))
                         for i in range(0, days_between + 1)]
        else:
            days_between = 1
            date_list = [line_id.check_in for i in range(0, days_between)]
        general_barcodes = []
        for index in range((line_id.number_of_adults or 1) * int(line_id.count)):
            general_barcodes.append(str(int(datetime.now().timestamp())) + uuid.uuid4().hex[:3].upper())
        for i in range(len(date_list)):
            for index in range((line_id.number_of_adults or 1) * int(line_id.count)):
                if self.meal_number == '2':
                    self.write({
                        'voucher_ids': [
                            (0, 0,
                             {'name': general_barcodes[index], 'date_from': date_list[i], 'date_to': date_list[i],
                              'meal_number': '1'}),
                            (0, 0,
                             {'name': general_barcodes[index], 'date_from': date_list[i], 'date_to': date_list[i],
                              'meal_number': '2'}),
                        ]
                    })
                elif self.meal_number == '3':
                    self.write({
                        'voucher_ids': [
                            (0, 0,
                             {'name': general_barcodes[index], 'date_from': date_list[i], 'date_to': date_list[i],
                              'meal_number': '1'}),
                            (0, 0,
                             {'name': general_barcodes[index], 'date_from': date_list[i], 'date_to': date_list[i],
                              'meal_number': '2'}),
                            (0, 0,
                             {'name': general_barcodes[index], 'date_from': date_list[i], 'date_to': date_list[i],
                              'meal_number': '3'}),
                        ]
                    })
                else:
                    self.write({
                        'voucher_ids': [
                            (0, 0,
                             {'name': general_barcodes[index], 'date_from': date_list[i], 'date_to': date_list[i],
                              'meal_number': '1'}),
                        ]
                    })

        return {
            'name': "Barcode",
            'res_model': 'tourism.booking.services',
            'view_mode': 'form',
            'view_id': self.env.ref('hotel_booking.service_voucher_view_form').id,
            'type': 'ir.actions.act_window',
            'res_id': self.id,
            'target': 'new',
        }

    def print_vouchers(self):
        return self.env.ref('hotel_booking.service_voucher_report').report_action(self)

    @api.depends('line_id', 'service_id', 'price_type', 'type')
    def _compute_amount(self):
        qty = 0.0
        for prod in self:
            line = prod.booking_id.line_ids[0] if prod.booking_id.line_ids else False
            if line:
                price = prod.service_id.price
                if prod.price_type == "multiply_with_guest":
                    price = (line.number_of_adults or 1) * price
                if line.number_of_days:
                    qty = line.number_of_days
                if prod.type == "every_day":
                    qty = line.number_of_days
                if prod.type == "every_day_checkin" or prod.type == "every_day_checkout":
                    qty = line.number_of_days - 1
                if prod.type == "one_time":
                    qty = 1.0

                prod.amount = qty * price


class TourismHotelBooking(models.Model):
    _name = 'tourism.hotel.booking'
    _inherit = ["mail.thread", 'portal.mixin']
    _description = 'Tourism Hotel Booking'

    STATES = [
        ('draft', 'Tentative Confirmation'),
        ('waiting_hotel', 'Waiting the Hotel'),
        ('hotel_confirm', 'Confirmed from Hotel'),
        ('waiting_customer', 'Waiting the Customer'),
        ('customer_confirm', 'Confirmed from Customer'),
        ('confirmed', 'Confirmed'),
        ('stay_over', 'Stay Over'),
        ('customer_checkout', 'Checkout'),
        ('cancelled', 'Cancelled'),
    ]

    def get_default_sequence(self):
        return self.env['ir.sequence'].next_by_code('tourism.hotel.booking.ref')

    # def action_booking_send_email(self):
    #     """This method used to send booking  to customer."""
    #     email_template = self.env.ref('tourism_hotel_bookingmail_booking_details_notification', False)
    #     mail_mail = email_template.send_mail(self.id) if email_template else False
    #     if mail_mail:
    #         self.env['mail.mail'].browse(mail_mail).send()

    vendor_id = fields.Many2one('res.partner')

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('Cannot delete a record which is in state \'%s\'.') % (rec.state,))
        return super(TourismHotelBooking, self).unlink()

    def action_payment(self):
        return {
            'name': _('Register Payment'),
            'res_model': 'account.payment.register',
            'view_mode': 'form',
            'context': {
                'active_model': 'account.move',
                'active_ids': self.invoice_ids.ids,
                'default_tourism_booking_id': self.id
            },
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    def prepare_attachments(self):
        report_template_id = self.env.ref('tourism_hotel_booking.customer_hotel_booking')._render_qweb_pdf(self.id)
        data_record = base64.b64encode(report_template_id[0])
        attachment_values = {
            'name': "Confirmation Customer Booking",
            'type': 'binary',
            'datas': data_record,
            'store_fname': data_record,
            'mimetype': 'application/pdf',
        }
        return self.env['ir.attachment'].create(attachment_values)

    def action_confirmation_send(self):
        """opens a window to compose an email,
        with template message loaded by default"""
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = \
                ir_model_data._xmlid_lookup('tourism_hotel_booking.confirmation_customer_mail_booking')[2]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data._xmlid_lookup('mail.email_compose_message_wizard_form')[2]
        except ValueError:
            compose_form_id = False

        attachment = self.prepare_attachments()
        ctx = {
            'default_model': 'tourism.hotel.booking',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'default_attachment_ids': [(6, 0, [attachment.id])],
            'default_is_wp': True,
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

    def action_cancellation_mail_send(self):
        """opens a window to compose an email,
        with template message loaded by default"""
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = \
                ir_model_data._xmlid_lookup('tourism_hotel_booking.cancellation_mail_booking')[2]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data._xmlid_lookup('mail.email_compose_message_wizard_form')[2]
        except ValueError:
            compose_form_id = False

        # attachment = self.prepare_attachments()
        ctx = {
            'default_model': 'tourism.hotel.booking',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'default_is_wp': True,
            # 'default_attachment_ids': [(6, 0, [attachment.id])],
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

    def action_reset_draft(self):
        for rec in self:
            rec.state = 'draft'
            for invoice in rec.invoice_ids:
                invoice.button_draft()

    def _find_mail_template(self, partner_type):
        if partner_type == 'hotel':
            return self.env.ref('tourism_hotel_booking.vendor_mail_booking_details_notification').id
        return self.env.ref('tourism_hotel_booking.customer_mail_booking_details_notification').id

    def action_booking_send_email(self, partner_type):
        self.ensure_one()
        template_id = self._find_mail_template(partner_type)
        lang = self.env.context.get('lang')
        template = self.env['mail.template'].browse(template_id)
        if template.lang:
            lang = template._render_lang(self.ids)[self.id]
        ctx = {
            'default_model': 'tourism.hotel.booking',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'custom_layout': "mail.mail_notification_paynow",
            'force_email': True,
            'default_is_wp': True,
            'model_description': self.with_context(lang=lang).name,
        }
        if partner_type == 'hotel' and self.state == 'draft':
            ctx['mark_hotel_sent'] = True
        else:
            ctx['mark_customer_sent'] = True
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }

    def action_vendor_booking_send_email(self):
        return self.action_booking_send_email('hotel')

    # def action_customer_booking_send_email(self):
    #     if not self.hotel_booking_reference:
    #         raise UserError("Please enter the booking reference before send to customer")
    #     return self.action_booking_send_email('customer')

    # Manual confirm by hotel
    def manual_hotel_confirm(self):
        for rec in self:
            rec.state = "hotel_confirm"

    # Manual confirm by customer
    def manual_customer_confirm(self):
        for rec in self:
            rec.state = "customer_confirm"

    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, **kwargs):
        if self.env.context.get('mark_hotel_sent'):
            self.filtered(lambda o: o.state == 'draft').with_context(tracking_disable=True).write(
                {'state': 'waiting_hotel'})
        elif self.env.context.get('mark_customer_sent'):
            self.filtered(lambda o: o.state == 'hotel_confirm').with_context(tracking_disable=True).write(
                {'state': 'waiting_customer'})

        return super(TourismHotelBooking, self.with_context(
            mail_post_autofollow=self.env.context.get('mail_post_autofollow', True))).message_post(**kwargs)

    booking_number = fields.Char('Booking Number', related='')

    name = fields.Char(string='Booking #', copy=False)
    company_id = fields.Many2one(
        'res.company', 'Company', index=True,
        default=lambda self: self.env.company)
    state = fields.Selection(STATES, default='draft', track_visibility="onchange")
    payment_state = fields.Selection(related='move_id.payment_state')
    email = fields.Char('Email', related='partner_id.email')
    mobile = fields.Char('Mobile', related='partner_id.mobile')
    email_vendor = fields.Char('Email', related='vendor_id.email')
    mobile_vendor = fields.Char('Mobile', related='vendor_id.mobile')
    partner_id = fields.Many2one('res.partner', string='Customer', required=True,
                                 default=lambda x: x.env.company.hotel_default_customer_id.id)
    guest_name = fields.Char()
    note = fields.Text()
    user_id = fields.Many2one('res.users', 'Booked By', default=lambda self: self.env.user)
    amount_subtotal = fields.Monetary(string="Subtotal", compute='_compute_totals', store=True)
    amount_tax = fields.Monetary(string="Taxes", compute='_compute_totals', store=True)
    amount_total = fields.Monetary(string="Total", compute='_compute_totals', store=True)
    amount_invoiced = fields.Monetary("Invoiced", compute='_compute_amount', store=True)
    amount_paid = fields.Monetary("Paid", compute='_compute_amount', store=True)
    amount_due = fields.Monetary("Amount Due", compute='_compute_amount', store=True)
    total_cost = fields.Monetary(string="Total Cost", compute='_compute_total_cost', store=True)
    currency_id = fields.Many2one('res.currency', readonly=True, default=lambda self: self.env.company.currency_id,
                                  compute='_compute_amount')
    invoice_ids = fields.One2many('account.move', 'tourism_booking_id')
    check_in_done = fields.Boolean(default=False)
    check_out_done = fields.Boolean(default=False)
    transfer_ids = fields.One2many('tourism.hotel.transfer', 'booking_id')
    transfer_count = fields.Integer(compute='_compute_transfer_count')
    invoice_total = fields.Float(compute="_compute_invoice_total")
    bill_total = fields.Float(compute="_compute_bill_total")
    reconcile_total = fields.Float(compute="_compute_reconciled_total")
    payment_total = fields.Float(compute="_compute_payment_total")
    line_ids = fields.One2many('tourism.hotel.booking.line', 'booking_id', copy=True)
    rooms = fields.Char(compute="_compute_room_names")
    service_ids = fields.One2many('tourism.booking.services', 'booking_id', copy=True)

    # BOOKING TYPE FIELDS
    booking_type = fields.Selection(string="Booking Type",
                                    selection=[('transportation', 'Transportation'), ('visa', 'Visa'),
                                               ('full_package', 'Full Package')])
    travel_agent_name = fields.Many2one('res.partner', string='Travel Agent Name', required=True)
    group_name = fields.Char(string='Group Name')

    departure_date = fields.Date(string='Departure')
    return_date = fields.Date(string='Return')
    journey_expire_date = fields.Date(string='Journey Expire Date')

    visa_start_date = fields.Date(string='Visa Start Date')
    visa_end_date = fields.Date(string='Visa End Date')

    total_cost_tax = fields.Float(compute='calc_cost_totals', string='Total Cost With Tax')
    total_income = fields.Float(compute='calc_cost_totals', string='Total Income With Tax')
    difference = fields.Float(compute='calc_cost_totals')
    total_purchase_taxes = fields.Float(compute='calc_cost_totals')
    total_sales_taxes = fields.Float(compute='calc_cost_totals')

    gross_total = fields.Float(compute='calc_total_visa')
    refund_amount = fields.Float(compute='calc_total_visa')
    net_amount = fields.Float(compute='calc_total_visa')

    # transportation_booking_ids = fields.One2many('transportation.booking', 'booking_id')
    visa_booking_ids = fields.One2many('visa.booking', 'booking_id')

    # ARCHIVED FIELDS
    hotel_id = fields.Many2one('hotel.hotel', compute='get_default_hotel_id')
    pricelist_id = fields.Many2one('hotel.pricelist')
    number_of_adults = fields.Integer(string='Adults', default=1, track_visibility="onchange")
    number_of_children = fields.Integer(string='Children', default=0, track_visibility="onchange")
    check_in = fields.Date(string='Check In')
    check_out = fields.Date(string='Check Out')
    room_type_id = fields.Many2one('hotel.room.type', string='Room Type', domain="[('hotel_id','=',hotel_id)]")
    room_id = fields.Many2one('hotel.room', string='Room',
                              domain="[('room_type_id', '=', room_type_id),('hotel_id','=',hotel_id)]",
                              track_visibility="onchange")
    terms_id = fields.Many2one('conditions.terms', string="Terms & Conditions",
                               default=lambda self: self.env['conditions.terms'].search([], limit=1))

    # actual_check_in = fields.Datetime(string="Actual Check-In", compute="compute_actual_check_in_out")
    # actual_check_out = fields.Datetime(string="Actual Check-Out", compute="compute_actual_check_in_out")
    number_of_days = fields.Integer(string='Total Days')
    customer_name = fields.Char(string='Customer Name')
    expiry_date = fields.Date(string='Booking Expiry Date', track=True)
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
    conditions = fields.Html('Conditions', readonly=False, copy=True, store=True)
    customer_type = fields.Selection([('new', 'New Customer'), ('existing', 'Existing Customer')],
                                     string='Customer Type', default='new')
    is_contract = fields.Boolean(compute='check_exist_contract_or_not')
    is_invoiced = fields.Boolean(default=False, copy=False)
    signature = fields.Binary(copy=False)
    signed_by = fields.Char(copy=False)
    signed_on = fields.Datetime(copy=False)
    check_in_tomorrow = fields.Date()
    check_out_tomorrow = fields.Date()

    hotel_signature = fields.Binary(copy=False)
    hotel_signed_by = fields.Char(copy=False)
    hotel_signed_on = fields.Datetime(copy=False)
    hotel_booking_reference = fields.Char(copy=False)

    room_count = fields.Float(compute='_compute_room_total')
    
    
    

    @api.onchange('terms_id')
    def _onchange_conditions(self):
        for booking in self:
            booking.conditions = booking.terms_id.terms

    @api.depends('line_ids.cost')
    def _compute_total_cost(self):
        for booking in self:
            booking.total_cost = sum(booking.line_ids.mapped('cost'))

    # @api.onchange('transportation_booking_ids')
    # def calc_cost_totals(self):
    #     total_cost_tax = total_income = purchase_tax_ids = sales_tax = 0.0
    #     total_days = total_taxes = purchase_tax = total_buses = total_sales_taxes = 0.0
    #     if self.booking_type == 'transportation':
    #         self.visa_booking_ids.unlink()
    #     for rec in self:
    #         if rec.transportation_booking_ids:
    #             total_cost_tax = sum(rec.transportation_booking_ids.mapped('cost_price'))
    #             total_income = sum(rec.transportation_booking_ids.mapped('sell_price'))
    #             # total_days = sum(rec.transportation_booking_ids.mapped('days'))
    #             purchase_tax_ids = rec.transportation_booking_ids.purchase_tax_ids.compute_all(
    #                 total_cost_tax * total_buses,
    #                 product=False, partner=rec.partner_id)
    #             purchase_tax += sum(t.get('amount', 0.0) for t in purchase_tax_ids.get('taxes', []))
    #             total_sales_taxes = rec.transportation_booking_ids.sales_tax_ids.compute_all(
    #                 total_income * total_buses,
    #                 product=False,
    #                 partner=rec.partner_id)
    #             sales_tax += sum(t.get('amount', 0.0) for t in total_sales_taxes.get('taxes', []))
    #             total_buses = sum(rec.transportation_booking_ids.mapped('no_of_bus'))
    #     self.total_cost_tax = total_cost_tax * total_buses
    #     self.total_income = total_income * total_buses
    #     self.difference = self.total_income - self.total_cost_tax
    #     self.total_purchase_taxes = purchase_tax
    #     self.total_sales_taxes = sales_tax

    @api.onchange('visa_booking_ids')
    def calc_total_visa(self):
        gross_total = refund_amount = net_amount = 0.0
        for line in self:
            if line.visa_booking_ids:
                gross_total = sum(line.visa_booking_ids.mapped('total_price'))
                refund_amount = sum(line.visa_booking_ids.mapped('refund_price'))
                net_amount = sum(line.visa_booking_ids.mapped('net_amount_price'))
        self.gross_total = gross_total
        self.refund_amount = refund_amount
        self.net_amount = net_amount

    @api.onchange('booking_type')
    def onchange_booking_type(self):
        # if self.booking_type == 'visa':
        #     self.transportation_booking_ids.unlink()
        #     self.service_ids.unlink()
        if self.booking_type == 'transportation':
            self.visa_booking_ids.unlink()
            self.service_ids.unlink()

    @api.depends('line_ids.total_amount', 'service_ids.service_id', 'service_ids.price_type', 'service_ids.type')
    def _compute_totals(self):
        tax_ids = self.env.company.hotel_default_tax_ids
        for booking in self:
            amount_total = amount_tax = amount_subtotal = 0
            for line in booking.line_ids:
                tax_ids = line.tax_id
                taxes = tax_ids.compute_all(line.total_amount, booking.currency_id, 1,
                                            product=False, partner=booking.partner_id)
                amount_tax += sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))
                amount_total += taxes['total_included']
                amount_subtotal += taxes['total_included']
            for line in booking.service_ids:
                taxes = tax_ids.compute_all(line.amount, booking.currency_id, 1,
                                            product=line.service_id.product_id, partner=booking.partner_id)
                amount_tax += sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))
                amount_total += taxes['total_included']
                amount_subtotal += taxes['total_excluded']
            booking.update({
                'amount_subtotal': amount_subtotal - amount_tax,
                'amount_tax': amount_tax,
                'amount_total': amount_subtotal,
            })

    def get_portal_url(self, suffix='', query_string=''):
        return f'/my/bookings/{self.id}{suffix}{query_string}'

    def preview_booking(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'target': 'self',
            'url': self.get_portal_url(),
        }

    @api.onchange('line_ids')
    def onchange_lines_ids(self):
        if self.line_ids:
            check_in_line = self.line_ids.mapped('check_in')[0]
            check_in_date = check_in_line
            user_timezone = pytz.timezone(self.env.user.tz or 'UTC')
            check_in = pytz.utc.localize(check_in_date).astimezone(user_timezone)
            self.check_in = check_in.date()
            vendor_id = self.line_ids.mapped('vendor_id')[0]
            self.vendor_id = vendor_id
            check_out_line = self.line_ids.mapped('check_out')[-1]
            check_out_date = check_out_line
            check_out = pytz.utc.localize(check_out_date).astimezone(user_timezone)
            self.check_out = check_out
            self.check_in_tomorrow = check_in_line + timedelta(days=1)
            self.check_out_tomorrow = check_out_line + timedelta(days=1)

    def compute_state(self):
        hotel_booking_obj = self.search([('booking_type', '=', 'full_package')])
        for record in hotel_booking_obj:
            if record.check_in and record.check_out:
                if record.check_in <= fields.Date.today() < record.check_out:
                    record.state = 'stay_over'
                elif record.check_out == fields.Date.today() or fields.Date.today() > record.check_out:
                    record.state = 'customer_checkout'

    def _compute_access_url(self):
        super(TourismHotelBooking, self)._compute_access_url()
        for booking in self:
            booking.access_url = f'/my/bookings/{booking.id}'

    def has_to_be_signed(self, logged_in_partner=False):
        if (logged_in_partner == self.vendor_id and self.state == 'waiting_hotel') or \
                (logged_in_partner == self.partner_id and self.state == 'waiting_customer'):
            return True
        return False

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
        for booking in self:
            booking.invoice_total = sum(
                booking.invoice_ids.filtered(lambda d: d.move_type == 'out_invoice').mapped('amount_total'))

    def _compute_room_total(self):
        for rec in self:
            rec.room_count = sum(rec.line_ids.mapped('count'))

    def _compute_reconciled_total(self):
        reconcile_total = self.reconcile_total = 0.0
        for invoice in self:
            account_payment_obj = self.env['account.payment'].search(
                [('tourism_booking_id', '=', invoice.id), ('state', '=', 'posted')]).mapped("amount_total")
            if account_payment_obj:
                reconcile_total = sum(account_payment_obj) - (invoice.invoice_total + invoice.bill_total)
                invoice.reconcile_total = - reconcile_total
            else:
                invoice.reconcile_total = 0.0

    def _compute_payment_total(self):
        payment_total = self.payment_total = 0.0
        for booking in self:
            account_payment_obj = self.env['account.payment'].search(
                [('tourism_booking_id', '=', booking.id), ('state', '=', 'posted')]).mapped("amount")
            if account_payment_obj:
                booking.payment_total = sum(account_payment_obj)
            else:
                booking.payment_total = 0.0

    def _compute_bill_total(self):
        for booking in self:
            booking.bill_total = sum(
                booking.invoice_ids.filtered(lambda d: d.move_type == 'in_invoice').mapped('amount_total'))

    def _compute_transfer_count(self):
        for booking in self:
            booking.transfer_count = len(booking.transfer_ids)
            
            

    # @api.onchange('check_in', 'check_out')
    # def _compute_total_days(self):
    #     self.check_dates()
    #
    #     for booking in self:
    #         if not booking.check_out:
    #             booking.number_of_days = 0
    #         else:
    #             booking.number_of_days = self.get_number_of_days(booking.check_in, booking.check_out)

    # def compute_actual_check_in_out(self):
    #     for booking in self:
    #         in_transfers = booking.transfer_ids.filtered(lambda x: x.type == "in").sorted(key=lambda x: x.transfer_time)
    #         booking.actual_check_in = in_transfers[0].transfer_time if in_transfers else False
    #         out_transfers = booking.transfer_ids.filtered(lambda x: x.type == "out").sorted(key=lambda x: x.transfer_time)
    #         booking.actual_check_out = out_transfers[-1].transfer_time if out_transfers else False

    # def _compute_customer_name_display(self):
    #     for booking in self:
    #         booking.customer_name_display = booking.get_customer_name()

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'reference must be unique !'),
    ]

    # def get_customer_name(self):
    #     self.ensure_one()
    #     return self.partner_id and self.partner_id.name or self.customer_name

    # def get_booked_date_list(self):
    #     self.ensure_one()
    #     d1 = self.check_in.date()
    #     d2 = self.check_out.date() or self.check_in.date()
    #
    #     days = (d2 - d1).days
    #
    #     data = []
    #     for each in range(0, days + 1):
    #         data.append(d1 + timedelta(each))
    #
    #     return data

    # def check_room_already_booked(self):
    #     self.ensure_one()
    #
    #     for booking in self.search([
    #         ('room_id', '=', self.room_id.id),
    #         ('id', '!=', self.id),
    #         ('state', 'not in', ['cancelled']),
    #     ]):
    #         date_list_other = booking.get_booked_date_list()
    #         date_list_current = self.get_booked_date_list()
    #
    #         for d in date_list_current:
    #             if d in date_list_other:
    #                 raise UserError('Already booked for %s' % d.strftime("%d/%b/%Y"))

    # def create_customer(self):
    #
    #     if self.customer_type == "new":
    #
    #         if not self.customer_name:
    #             raise UserError("Please enter customer name.")
    #
    #         vals = {
    #             'name': self.customer_name,
    #             'street': self.street,
    #             'street2': self.street2,
    #             'zip': self.zip,
    #             'city': self.city,
    #             'state_id': self.state_id.id,
    #             'country_id': self.country_id.id,
    #             'national_id': self.national_id,
    #             'passport_no': self.passport_no,
    #             'customer_rank': 1,
    #         }
    #
    #         partner_id = self.env['res.partner'].create(vals)
    #         self.partner_id = partner_id.id

    type = fields.Selection([('every_day', 'Every Day'), ('every_day_checkin', 'Every Day Except Checkin'),
                             ('every_day_checkout', 'Every Day Except Checkout'), ('one_time', 'One Time'), ],
                            default="", string="Type")

    def create_invoice(self):
        self.ensure_one()
        tax_ids = self.env.company.hotel_default_tax_ids.ids
        invoice_line_vals = []
        for line in self.line_ids:
            hotel_hotel_obj = self.env['hotel.hotel'].sudo().search([('partner_id', '=', line.vendor_id.id)],
                                                                    limit=1)
            services = line.service_ids or self.service_ids
            for prod in services:
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
                if line.check_dir:
                    invoice_line_vals += [(0, 0, {
                        'product_id': prod.service_id.product_id.id,
                        'name': 'Extra Charge',
                        'quantity': qty,
                        'price_unit': price,
                        'tax_ids': line.tax_id,
                        'account_id': hotel_hotel_obj.account_journal_id.default_account_id.id
                    })]
                else:
                    invoice_line_vals += [(0, 0, {
                        'product_id': prod.service_id.product_id.id,
                        'name': 'Extra Charge',
                        'quantity': qty,
                        'price_unit': price,
                        'tax_ids': line.tax_id,
                    })]

            tot_qty = line.count * line.date_diff
            if line.check_dir:
                invoice_line_vals += [(0, 0, {
                    'product_id': line.room_id.product_id.id,
                    'name': ' Room Charge ',
                    'quantity': tot_qty,
                    'price_unit': line.price,
                    'source_booking_id': line.id,
                    'tax_ids': line.tax_id,
                    'account_id': hotel_hotel_obj.account_journal_id.default_account_id.id
                })]
            else:
                invoice_line_vals += [(0, 0, {
                    'product_id': line.room_id.product_id.id,
                    'name': ' Room Charge ',
                    'quantity': tot_qty,
                    'price_unit': line.m_price,
                    'source_booking_id': line.id,
                    'tax_ids': line.tax_id,
                })]
        for rec in self.line_ids:
            if rec.check_dir:
                journal_id = self.env['hotel.hotel'].sudo().search([('partner_id', '=', rec.vendor_id.id)],
                                                                   limit=1).account_journal_id.id
                move_vals = {
                    'move_type': 'out_invoice',
                    'partner_id': self.partner_id.id,
                    'booking_id': self.id,
                    'narration': self.conditions,
                    # 'journal_id': journal_id,
                    'invoice_user_id': self._uid,
                    'invoice_date': fields.Date.today(),
                    'invoice_line_ids': invoice_line_vals
                }
            else:
                move_vals = {
                    'move_type': 'out_invoice',
                    'partner_id': self.partner_id.id,
                    'booking_id': self.id,
                    'narration': self.conditions,
                    'invoice_user_id': self._uid,
                    'invoice_date': fields.Date.today(),
                    'invoice_line_ids': invoice_line_vals
                }
        move = self.env['account.move'].with_context({'line_ids': False}).create(move_vals)
        # move.action_post()
        self.move_id = move.id

    move_id = fields.Many2one('account.move', copy=False)

    def button_confirm(self):
        # if not self.hotel_booking_reference:
        #     raise UserError("Please Enter the Booking reference before confirm ")
        # if not self.line_ids:
        #     raise UserError("You have to add at least one line.")
        if self.is_contract:
            self.ensure_one()
            if self.booking_type == 'full_package':
                if not self.line_ids:
                    raise UserError("You have to add at least one line.")
                if not all([x.room_id.id for x in self.line_ids]):
                    raise UserError("You have to select room.")
                for line in self.line_ids:
                    if not line.check_out:
                        line.check_out = line.check_in
                    # line.check_room_already_booked()
                if not self.is_invoiced or not self.move_id:
                    self.create_invoice()
                    self.is_invoiced = True
            self.state = "confirmed"
        else:
            if not self.partner_id:
                raise UserError("Please choose customer.")
            # for rec in self.line_ids:
            #     if not rec.account_move_id:
            #         raise UserError("Please Create All Bills First")
            if not self.is_invoiced:
                self.create_invoice()
                self.is_invoiced = True
            self.state = "confirmed"

    # def button_open_invoice(self):
    #     self.ensure_one()
    #     # self.update_vals()
    #
    #     invoice_ids = self.sudo().get_invoice_ids()
    #
    #     if not invoice_ids:
    #         raise UserError('No Invoices Found!')
    #
    #     action = {
    #         'name': 'Invoice',
    #         'type': 'ir.actions.act_window',
    #         'view_mode': 'tree,form',
    #         'res_model': 'account.move',
    #         'context': {},
    #         'domain': [('id', 'in', invoice_ids.ids)],
    #         'views': [
    #             (self.env.ref('account.view_out_invoice_tree').id, 'tree'),
    #             (self.env.ref('account.view_move_form').id, 'form'),
    #         ],
    #     }
    #
    #     if len(invoice_ids) == 1:
    #         action['view_mode'] = 'form'
    #         action['res_id'] = invoice_ids.id
    #         action['views'] = [(self.env.ref('account.view_move_form').id, 'form')]
    #
    #     return action

    # def get_invoice_ids(self):
    #     return self.env['account.move'].search([
    #         ('booking_id', '=', self.id)
    #     ])

    def button_cancel(self):
        for rec in self:
            for line in rec.line_ids:
                if line.room_id.tourism_booking_line_id:
                    raise UserError(
                        "Sorry customer is still living in this room. You have to check out before cancel.")
            for inv in rec.invoice_ids:
                inv.button_cancel()

            rec.state = 'cancelled'
        return self.action_cancellation_mail_send()

    def _get_report_base_filename(self):
        self.ensure_one()
        return self.name

    @api.model
    def create(self, vals):
        res = super(TourismHotelBooking, self).create(vals)

        for booking in res:
            # for line in booking.line_ids:
            #     # Check Already Booked
            #     line.check_room_already_booked()

            # Generate Sequence
            booking.name = self.get_default_sequence()

        # Dashboard Instant Update
        dashboard_id = self.env["tourism.hotel.booking.dashboard2"].search([], order="id")
        if dashboard_id:
            dashboard_id[-1].update_result()

        # if self._context.get('active_model') == "hotel.booking.dashboard2":
        #     dashboard = self.env["hotel.booking.dashboard2"].browse(self._context['active_id'])
        #     dashboard.update_result()
        #     print(111)
        return res

    def write(self, vals):
        result = super(TourismHotelBooking, self).write(vals)
        if vals.get('vendor_id', False):
            for line in self.line_ids.filtered(lambda l: l.account_move_id):
                line.account_move_id.write({
                    'partner_id': self.env['res.partner'].browse(vals['vendor_id']).id
                })
        if vals.get('partner_id', False):
            self.move_id.write({
                'partner_id': self.env['res.partner'].browse(vals['partner_id']).id
            })
        # Dashboard Instant Update
        dashboard_id = self.env["tourism.hotel.booking.dashboard2"].search([], order="id")
        if dashboard_id:
            dashboard_id[-1].update_result()

        return result

    def _compute_amount(self):
        company_currency = self.env.user.company_id.currency_id
        for booking in self:
            amount_total = 0
            amount_due = 0
            for invoice in booking.invoice_ids:
                if invoice.move_type == 'out_invoice' or invoice.move_type == 'in_invoice':
                    amount_total += invoice.amount_total
                    amount_due += invoice.amount_residual
            booking.amount_invoiced = amount_total
            booking.amount_paid = amount_total - amount_due
            booking.amount_due = amount_due
            booking.currency_id = company_currency.id

    # def update_vals(self):
    #     for booking in self:
    #         amount_total = 0
    #         amount_due = 0
    #         currency_ids = []
    #         for invoice in booking.get_invoice_ids():
    #             amount_total += invoice.amount_total
    #             amount_due += invoice.amount_residual
    #             currency_ids.append(invoice.currency_id.id)
    #
    #         booking.amount_invoiced = amount_total
    #         booking.amount_paid = amount_total - amount_due
    #         booking.amount_due = amount_due
    #
    #         if len(set(currency_ids)) == 1:
    #             booking.currency_id = currency_ids[0]
    #         else:
    #             booking.currency_id = False

    # def button_print_invoice(self):
    #     self.ensure_one()
    #     invoice_ids = self.invoice_ids
    #     if not invoice_ids:
    #         raise UserError('No Invoice Found !')
    #
    #     if len(invoice_ids) > 1:
    #         raise UserError('Multiple Invoice Found !')
    #
    #     return self.env.ref('account.account_invoices').report_action(self)

    def action_open_transfers(self):
        action = self.env.ref('tourism_hotel_booking.action_hotel_transfer').read()[0]
        action['domain'] = [('id', 'in', self.transfer_ids.ids)]
        return action

    def action_open_invoices(self):
        action = self.env.ref('account.action_move_out_invoice_type').read()[0]
        action['domain'] = [('id', 'in', self.invoice_ids.ids)]
        action['context'] = {
            'default_move_type': 'out_invoice',
            'default_booking_id': self.id,
            'partner_id': self.partner_id.id,
        }
        return action

    def action_open_purchases(self):
        action = self.env.ref('purchase.purchase_rfq').read()[0]
        action['domain'] = [('booking_id', '=', self.id)]
        return action

    def action_open_bills(self):
        action = self.env.ref('account.action_move_in_invoice_type').read()[0]
        action['domain'] = [('booking_id', '=', self.id), ('move_type', '=', 'in_invoice')]
        return action

    def action_open_invoice(self):
        action = self.env.ref('account.action_move_out_invoice_type').read()[0]
        action['display_name'] = _('Invoices')
        action['domain'] = [('booking_id', '=', self.id), ('move_type', '=', 'out_invoice')]
        return action

    def get_booking_data(self, date_from, date_to):
        date_list = self.get_dates_between(date_from, date_to)
        data = []
        domain = [('booking_id.state', 'not in', ['cancelled'])]
        for booking_line in self.env['tourism.hotel.booking.line'].search(domain):
            booking = booking_line.booking_id

            for date in date_list:

                if date in booking_line.get_booked_date_list():

                    payment_status = "NOT PAID"
                    if booking.amount_paid > 0 and booking.amount_paid == booking.amount_invoiced:
                        payment_status = "PAID"

                    data.append({
                        'check_in': booking_line.check_in,
                        'check_out': booking_line.check_out,
                        'actual_check_in': booking_line.actual_check_in,
                        'actual_check_out': booking_line.actual_check_out,
                        'id': booking.id,
                        'name': booking.name,
                        'room_id': booking_line.room_id.id,
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
        booking_line_obj = self.env['tourism.hotel.booking.line']

        if type(room_id) != int:
            room_id = room_id.id

        for each in data:
            if each['room_id'] == room_id:
                status = booking_line_obj.get_datetime_status(each['check_in'], each['check_out'])
                paid_date_list = booking_line_obj.get_paid_dates(status)
                if date in paid_date_list:
                    return each
        return False

    @staticmethod
    def get_dates_between(date1, date2):
        my_list = []
        for n in range(int((date2 - date1).days) + 1):
            my_list.append(date1 + timedelta(n))
        return my_list

    def _message_subscribe(self, partner_ids=None, subtype_ids=None, customer_ids=None):
        return True


class HotelBookingTransferWizard(models.TransientModel):
    _name = 'tourism.hotel.booking.transfer.wizard'
    _description = 'Booking Transfer Wizard'

    type = fields.Selection([('in', 'Check In'), ('out', 'Check Out')], string='Type', required=True)
    transfer_time = fields.Datetime(string="Time", required=True)
    # booking_id = fields.Many2one('hotel.booking', string="Booking #", required=True)
    booking_line_id = fields.Many2one('tourism.hotel.booking.line', required=True)

    def action_apply(self):
        self.ensure_one()
        transfer = self.env['tourism.hotel.transfer'].create({
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
