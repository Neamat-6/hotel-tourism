import datetime

from odoo import api, fields, models
from odoo.tools import float_round


class BookingFilter(models.Model):
    _name = 'booking.filter'
    _inherit = ["mail.thread", 'portal.mixin']
    _description = 'Hotel Booking Filter Screen'
    _rec_name = 'create_date'

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

    partner_id = fields.Many2one('res.partner', "Guest Name")
    user_id = fields.Many2one('res.users', "User")

    arrival_from = fields.Date("Arrival From")
    arrival_to = fields.Date("Arrival To")
    departure_from = fields.Date("Departure From")
    departure_to = fields.Date("Departure To")
    reservation_date_from = fields.Date("Reservation Date From")
    reservation_date_to = fields.Date("Reservation Date To")

    company_id = fields.Many2one('res.company', "Company")
    hotel_ids = fields.Many2many("hotel.hotel", string="Hotel")
    booking_source = fields.Selection(selection=[
        ('online_agent', 'Online Travel Agent'),
        ('company', 'Company'),
        ('direct', 'Direct'),
        ('government_booking', 'Government Booking'),
        ('contract_booking', 'Contract Booking'),
        ('allotment_booking', 'Allotment Booking'),
      ])
    online_travel_agent_source = fields.Many2one('res.partner', domain="[('online_travel_agent', '=', True)]")
    company_booking_source = fields.Many2one('res.partner', domain="[('is_company', '=',True)]")
    state = fields.Selection(STATES)
    booking_id = fields.Many2one('hotel.booking', 'Booking #')
    folio_id = fields.Many2one('booking.folio', string='Folio')
    filter_type = fields.Selection(selection=[('booking', 'Booking'), ('folio', 'Folio')], default="booking",
                                   string="Filter Type", required=True)
    include_cancelled = fields.Boolean("Cancelled Booking")
    mobile = fields.Char("Guest Mobile")
    country_id = fields.Many2one('res.country', "Guest Country")
    reference_number = fields.Char("Reference No")
    line_ids = fields.One2many('booking.filter.line', 'wizard_id')
    paid_without_zero = fields.Boolean('Paid Booking')
    paid_with_zero = fields.Boolean('Unpaid Booking')
    total_without_zero = fields.Boolean('Price Total Not Zero')
    is_cancelled = fields.Boolean("Without Cancelled", default=True)
    print_with_total = fields.Boolean("Print Without Prices")
    grouped_company_source = fields.Boolean("Grouped Company Source")
    grouped_direct_source = fields.Boolean("Grouped Direct Source")
    grouped_online_source = fields.Boolean("Grouped Online Travel Agent Source")
    grouped_booking_source = fields.Boolean("Grouped Booking Source")
    total_amount_direct = fields.Float("Total Amount Direct", digits=(16, 2), compute='calc_direct_online_source')
    total_amount_online = fields.Float("Total Amount Online Travel", digits=(16, 2),
                                       compute='calc_direct_online_source')
    total_amount_booking_source = fields.Float('Total Amount Sources', digits=(16, 2),
                                               compute='calc_direct_online_source')
    total_amount = fields.Float(compute="calc_total_amount", digits=(16, 2))
    total_price_tax = fields.Float(compute="calc_totals", digits=(16, 2))
    total_price_subtotal = fields.Float(compute="calc_totals", digits=(16, 2))
    total_paid = fields.Float(compute="calc_total_amount", digits=(16, 2))
    total_due = fields.Float(compute="calc_total_amount", digits=(16, 2))
    balance = fields.Float(compute="calc_total_amount", digits=(16, 2))
    no_lines = fields.Integer(compute='calc_no_lines', string="No. Booking")
    total_no_rooms = fields.Integer("Total Rooms", compute='calc_totals')
    total_no_nights = fields.Integer("Total Nights", compute='calc_totals')
    total_price_nights = fields.Float("total price night", compute='calc_totals', digits=(16, 2))
    season_id = fields.Many2one('season.duration', string='Season')
    city_ledger_booking = fields.Boolean("Unsettled City Ledger Booking")
    settled_city_ledger_booking = fields.Boolean("Settled City Ledger Booking")
    city_ledger_total = fields.Float("City Ledger Paid", compute='calc_city_ledger_balance')
    city_ledger_balance = fields.Float("City Ledger Balance", compute='calc_city_ledger_balance')
    paid_amount_city_ledger = fields.Float("Transferred To City Ledger", compute='calc_ledgers_balances')
    paid_for_city_ledger = fields.Float("Actual Paid City Ledger", compute='calc_ledgers_balances')
    expected_balance = fields.Float("Expected Balance", compute='calc_ledgers_balances')
    actual_balance = fields.Float("Actual Balance", compute='calc_ledgers_balances')
    total_paid_city_ledger = fields.Float("Total City Ledger Booking", compute='calc_ledgers_balances')
    currency_id = fields.Many2one('res.currency', readonly=True, tracking=True, string='Currency',
                                  default=lambda self: self.env.user.company_id.currency_id)
    total_advanced_payment = fields.Monetary(related='company_booking_source.total_advanced_payment')
    day_use = fields.Boolean("Day Use")
    complimentary_room = fields.Boolean("Complimentary Room")
    house_use = fields.Boolean("House Use")

    @api.onchange('line_ids')
    def calc_ledgers_balances(self):
        for rec in self:
            if rec.line_ids:
                rec.paid_amount_city_ledger = sum(self.line_ids.mapped('paid_amount_city_ledger'))
                rec.total_paid_city_ledger = sum(
                    self.line_ids.filtered(lambda l: l.payment_type_id == 'city_ledger').mapped('price_total'))
                rec.paid_for_city_ledger = sum(self.line_ids.mapped('company_paid'))
                rec.expected_balance = (
                                                   rec.paid_for_city_ledger + self.total_advanced_payment) - rec.total_paid_city_ledger
                rec.actual_balance = (
                                                 rec.paid_for_city_ledger + self.total_advanced_payment) - rec.paid_amount_city_ledger
            else:
                rec.paid_amount_city_ledger = 0.0
                rec.total_paid_city_ledger = 0.0
                rec.paid_for_city_ledger = 0.0
                rec.expected_balance = 0.0
                rec.actual_balance = 0.0

    @api.onchange('line_ids')
    def calc_city_ledger_balance(self):
        for rec in self:
            if rec.city_ledger_booking or rec.settled_city_ledger_booking:
                rec.city_ledger_total = sum(self.line_ids.mapped('company_paid'))
                rec.city_ledger_balance = sum(self.line_ids.mapped('price_paid')) - sum(
                    self.line_ids.mapped('company_paid'))
            else:
                rec.city_ledger_balance = 0.0
                rec.city_ledger_total = 0.0

    def calc_totals(self):
        for rec in self:
            if rec.line_ids:
                total_no_rooms = sum(rec.line_ids.mapped('no_rooms'))
                total_price_tax = sum(rec.line_ids.mapped('price_tax'))
                total_price_subtotal = sum(rec.line_ids.mapped('price_subtotal'))
                total_no_nights = sum(rec.line_ids.mapped('no_nights'))
                total_price_nights = sum(rec.line_ids.mapped('price_night'))
                rec.total_no_rooms = total_no_rooms
                rec.total_no_nights = total_no_nights
                rec.total_price_tax = total_price_tax
                rec.total_price_subtotal = total_price_subtotal
                rec.total_price_nights = total_price_nights
            else:
                rec.total_no_rooms = 0
                rec.total_no_nights = 0
                rec.total_price_subtotal = 0.0
                rec.total_price_tax = 0.0
                rec.total_price_nights = 0.0

    @api.onchange('grouped_booking_source', 'arrival_from', 'arrival_to', 'departure_from', 'departure_to')
    def calc_direct_online_source(self):
        direct_domain = []
        online_domain = []
        self.total_amount_online = 0.0
        self.total_amount_direct = 0.0
        self.total_amount_booking_source = 0.0
        if self.grouped_booking_source:
            if self.arrival_from:
                direct_domain.append(('check_in', '>=', self.arrival_from))
                online_domain.append(('check_in', '>=', self.arrival_from))

            if self.arrival_to:
                direct_domain.append(('check_in', '<=', self.arrival_to))
                online_domain.append(('check_in', '<=', self.arrival_to))

            if self.departure_from:
                direct_domain.append(('check_out', '>=', self.departure_from))
                online_domain.append(('check_out', '>=', self.departure_from))

            if self.departure_to:
                direct_domain.append(('check_out', '<=', self.departure_to))
                online_domain.append(('check_out', '<=', self.departure_to))

            if self.hotel_ids:
                direct_domain.append(('hotel_id', 'in', self.hotel_ids.ids))
                online_domain.append(('hotel_id', 'in', self.hotel_ids.ids))

            direct_domain.append(('state', '!=', 'cancelled'))
            online_domain.append(('state', '!=', 'cancelled'))

            direct_domain.append(('booking_source', '=', 'direct'))
            online_domain.append(('booking_source', '=', 'online_agent'))

            booking_source_direct = self.env['hotel.booking'].sudo().search(direct_domain)
            booking_source_online = self.env['hotel.booking'].sudo().search(online_domain)
            if booking_source_direct:
                self.total_amount_direct = sum(booking_source_direct.mapped('amount_total'))
            else:
                self.total_amount_direct = 0.0

            if booking_source_online:
                self.total_amount_online = sum(booking_source_online.mapped('amount_total'))
            else:
                self.total_amount_online = 0.0

            self.total_amount_booking_source = self.total_amount_online + self.total_amount_direct

    def calc_no_lines(self):
        if self.line_ids:
            self.no_lines = len(self.line_ids)
        else:
            self.no_lines = False

    def calc_total_amount(self):
        for rec in self:
            if rec.line_ids:
                total_amount = sum(rec.line_ids.mapped('price_total'))
                total_paid = sum(rec.line_ids.mapped('price_paid'))
                total_due = sum(rec.line_ids.mapped('price_due'))
                rec.total_amount = float_round(total_amount, precision_digits=2)
                rec.total_paid = float_round(total_paid, precision_digits=2)
                rec.total_due = float_round(total_due, precision_digits=2)
                rec.balance = float_round(total_amount - total_paid, precision_digits=2)
            else:
                rec.total_due = 0.0
                rec.total_amount = 0.0
                rec.total_paid = 0.0
                rec.balance = 0.0

    def button_search(self):
        self.line_ids = [(5, 0, 0)]
        domain = []
        if self.filter_type == 'folio' or self.grouped_company_source or self.grouped_direct_source or self.grouped_online_source:
            if self.season_id:
                domain.append(('booking_id.season_id', '=', self.season_id.id))
            if self.user_id:
                domain.append(('booking_id.user_id', '=', self.user_id.id))
            if self.arrival_from:
                domain.append(('check_in', '>=', self.arrival_from))
            if self.arrival_to:
                domain.append(('check_in', '<=', self.arrival_to))
            if self.departure_from:
                domain.append(('check_out', '>=', self.departure_from))
            if self.departure_to:
                domain.append(('check_out', '<=', self.departure_to))
            if self.booking_source:
                domain.append(('booking_id.booking_source', '=', self.booking_source))
                if self.booking_source == 'online_agent' and self.online_travel_agent_source:
                    domain.append(('booking_id.online_travel_agent_source', '=', self.online_travel_agent_source.id))
                elif self.booking_source == 'company' and self.company_booking_source:
                    domain.append(('booking_id.company_booking_source', '=', self.company_booking_source.id))
            if self.state:
                domain.append(('state', '=', self.state))
            if self.reference_number:
                domain.append(('booking_id.ref', '=', self.reference_number))
            if self.hotel_ids:
                domain.append(('hotel_id', 'in', self.hotel_ids.ids))
            if self.paid_without_zero:
                domain.append(('price_paid', '>', 0.0))
            if self.paid_with_zero:
                domain.append(('price_paid', '=', 0.0))
            if self.total_without_zero:
                domain.append(('price_total', '>', 0.0))
            if self.is_cancelled:
                domain.append(('state', '!=', 'cancelled'))
            if self.booking_id:
                domain.append(('booking_id', '=', self.booking_id.id))
            if self.day_use:
                domain.append(('day_use', '=', self.day_use))
            if self.complimentary_room:
                domain.append(('complimentary_room', '=', self.complimentary_room))
            if self.house_use:
                domain.append(('house_use', '=', self.house_use))
            folios = self.env['booking.folio'].sudo().search(domain)

            if self.mobile:
                folios = self.env['booking.folio'].search(
                    [('id', 'in', folios.ids), ('partner_id.mobile', 'ilike', self.mobile)])
            if self.country_id:
                folios = self.env['booking.folio'].search(
                    [('id', 'in', folios.ids), ('partner_id.country_id', '=', self.country_id.id)])
            if self.folio_id:
                folios = folios.filtered(lambda f: f.id == self.folio_id.id)

            if self.partner_id:
                folios = folios.filtered(lambda f: f.partner_id.id == self.partner_id.id)

            if self.grouped_company_source:
                self.grouped_direct_source = False
                self.grouped_online_source = False
                if self.company_booking_source:
                    domain.append(('company_booking_source', '=', self.company_booking_source.id))
                folios = self.env['booking.folio'].search(
                    [('id', 'in', folios.ids), ('booking_source', '=', 'company')])
                booking_folio_dict = {}
                for line in folios:
                    company_booking_source = line.company_booking_source.id
                    related_hotel = (line.mapped('hotel_id')).id
                    state = line.state
                    subtotal = sum(line.mapped('price_total'))
                    total_paid = sum(line.mapped('price_paid'))
                    paid_amount_city_ledger = sum(line.booking_id.mapped('paid_amount_city_ledger'))
                    paid_for_city_ledger = sum(line.booking_id.mapped('company_paid'))
                    # account_payment_obj = self.env['account.payment'].search(
                    #     [('is_internal_transfer', '=', True), ('destination_journal_id.is_city_ledger', '=', True),
                    #      ('payment_type', '=', 'inbound'), ('journal_dis_partner_id', '=', company_booking_source)])
                    # if account_payment_obj:
                    #     if self.paid_without_zero:
                    #         account_payment_obj.filtered(lambda l: l.amount > 0.0)
                    #         total_paid = sum(account_payment_obj.mapped('amount'))
                    #     else:
                    #         total_paid = sum(account_payment_obj.mapped('amount'))
                    # else:
                    #     total_paid = 0.0
                    balance = subtotal - total_paid
                    if company_booking_source in booking_folio_dict:
                        booking_folio_dict[company_booking_source]['subtotal'] += subtotal
                        booking_folio_dict[company_booking_source]['total_paid'] += total_paid
                        booking_folio_dict[company_booking_source]['balance'] += balance
                        booking_folio_dict[company_booking_source]['paid_amount_city_ledger'] += paid_amount_city_ledger
                        booking_folio_dict[company_booking_source]['paid_for_city_ledger'] += paid_for_city_ledger
                    else:
                        booking_folio_dict[company_booking_source] = {
                            'subtotal': subtotal,
                            'total_paid': total_paid,
                            'balance': balance,
                            'related_hotel': related_hotel,
                            'paid_amount_city_ledger': paid_amount_city_ledger,
                            'paid_for_city_ledger': paid_for_city_ledger,
                            'state': state
                        }

                for company_booking_source, values in booking_folio_dict.items():
                    self.line_ids = [(0, 0, {
                        'wizard_id': self.id,
                        'company_booking_source': company_booking_source,
                        'price_total': values['subtotal'],
                        'price_paid': values['total_paid'],
                        'price_due': values['balance'],
                        'related_hotel': values['related_hotel'],
                        'paid_amount_city_ledger': values['paid_amount_city_ledger'],
                        'company_paid': values['paid_for_city_ledger'],
                        'state': values['state']
                    })]
            if self.grouped_direct_source:
                self.grouped_company_source = False
                self.grouped_online_source = False
                if self.booking_source == 'direct':
                    domain.append(('partner_id', '=', self.partner_id.id))
                folios = self.env['booking.folio'].search([('id', 'in', folios.ids), ('booking_source', '=', 'direct')])
                booking_folio_dict = {}
                for line in folios:
                    direct_booking_source = line.partner_id.id
                    related_hotel = (line.mapped('hotel_id')).id
                    state = line.state
                    subtotal = sum(line.mapped('price_total'))
                    account_payment_obj = self.env['account.payment'].search(
                        [('is_internal_transfer', '=', False), ('payment_type', '=', 'inbound'),
                         ('partner_id', '=', direct_booking_source)])
                    if account_payment_obj:
                        if self.paid_without_zero:
                            account_payment_obj.filtered(lambda l: l.amount > 0.0)
                            total_paid = sum(account_payment_obj.mapped('amount'))
                        else:
                            total_paid = sum(account_payment_obj.mapped('amount'))
                    else:
                        total_paid = 0.0
                    balance = subtotal - total_paid
                    if direct_booking_source in booking_folio_dict:
                        booking_folio_dict[direct_booking_source]['subtotal'] += subtotal
                        booking_folio_dict[direct_booking_source]['total_paid'] += total_paid
                        booking_folio_dict[direct_booking_source]['balance'] += balance
                    else:
                        booking_folio_dict[direct_booking_source] = {
                            'subtotal': subtotal,
                            'total_paid': total_paid,
                            'balance': balance,
                            'related_hotel': related_hotel,
                            'state': state
                        }

                for direct_booking_source, values in booking_folio_dict.items():
                    self.line_ids = [(0, 0, {
                        'wizard_id': self.id,
                        'partner_id': direct_booking_source,
                        'price_total': values['subtotal'],
                        'price_paid': values['total_paid'],
                        'price_due': values['balance'],
                        'related_hotel': values['related_hotel'],
                        'state': values['state']
                    })]
            if self.grouped_online_source:
                self.grouped_company_source = False
                self.grouped_direct_source = False
                if self.online_travel_agent_source:
                    domain.append(('online_travel_agent_source', '=', self.online_travel_agent_source.id))
                folios = self.env['booking.folio'].search(
                    [('id', 'in', folios.ids), ('booking_source', '=', 'online_agent')])
                booking_folio_dict = {}
                for line in folios:
                    online_booking_source = line.online_travel_agent_source.id
                    related_hotel = (line.mapped('hotel_id')).id
                    state = line.state
                    subtotal = sum(line.mapped('price_total'))
                    account_payment_obj = self.env['account.payment'].search(
                        [('is_internal_transfer', '=', False), ('payment_type', '=', 'inbound'),
                         ('partner_id', '=', online_booking_source)])
                    if account_payment_obj:
                        if self.paid_without_zero:
                            account_payment_obj.filtered(lambda l: l.amount > 0.0)
                            total_paid = sum(account_payment_obj.mapped('amount'))
                        else:
                            total_paid = sum(account_payment_obj.mapped('amount'))
                    else:
                        total_paid = 0.0
                    balance = subtotal - total_paid
                    if online_booking_source in booking_folio_dict:
                        booking_folio_dict[online_booking_source]['subtotal'] += subtotal
                        booking_folio_dict[online_booking_source]['total_paid'] += total_paid
                        booking_folio_dict[online_booking_source]['balance'] += balance
                    else:
                        booking_folio_dict[online_booking_source] = {
                            'subtotal': subtotal,
                            'total_paid': total_paid,
                            'balance': balance,
                            'related_hotel': related_hotel,
                            'state': state
                        }

                for online_booking_source, values in booking_folio_dict.items():
                    self.line_ids = [(0, 0, {
                        'wizard_id': self.id,
                        'partner_id': online_booking_source,
                        'price_total': values['subtotal'],
                        'price_paid': values['total_paid'],
                        'price_due': values['balance'],
                        'related_hotel': values['related_hotel'],
                        'state': values['state']
                    })]

            if not self.grouped_company_source and not self.grouped_direct_source and not self.grouped_online_source:
                for folio in folios:
                    room_charge = len(folio.line_ids.filtered(lambda l: l.particulars == 'Room Charge'))
                    price_night_without_tax = folio.room_price_subtotal / room_charge if room_charge else 0.0
                    price_night_with_tax = folio.room_price_total / room_charge if room_charge else 0.0
                    self.line_ids = [(0, 0, {
                        'folio_id': folio.id,
                        'booking_id': folio.booking_id.id,
                        'state': folio.state,
                        'wizard_id': self.id,
                        'related_hotel': folio.booking_id.hotel_id.id,
                        'name': folio.name,
                        'partner_id': folio.partner_id.id,
                        'company_booking_source': folio.booking_id.company_booking_source.id,
                        'check_in': folio.check_in,
                        'check_out': folio.check_out,
                        'user_id': folio.booking_id.user_id.id,
                        'price_subtotal': folio.price_subtotal,
                        'price_total': folio.price_total,
                        'price_tax': folio.price_tax,
                        'price_paid': folio.price_paid,
                        'price_due': folio.price_due,
                        'no_nights': folio.total_nights,
                        'no_rooms': folio.booking_id.actual_no_room,
                        'price_night': price_night_without_tax,
                        'price_night_with_tax': price_night_with_tax,
                        'room_id': folio.room_id.id,
                        'rate_plan_id': folio.rate_plan_id.id,
                        'room_type_id': folio.room_type_id.id,
                    })]

        else:
            if self.user_id:
                domain.append(('user_id', '=', self.user_id.id))
            if self.arrival_from:
                arrival_from_datetime = datetime.datetime.combine(self.arrival_from, datetime.time.min)
                domain.append(('check_in', '>=', arrival_from_datetime))
            if self.arrival_to:
                arrival_to_datetime = datetime.datetime.combine(self.arrival_to, datetime.time.max)
                domain.append(('check_in', '<=', arrival_to_datetime))
            if self.departure_from:
                departure_from_datetime = datetime.datetime.combine(self.departure_from, datetime.time.min)
                domain.append(('check_out', '>=', departure_from_datetime))
            if self.departure_to:
                departure_to_datetime = datetime.datetime.combine(self.departure_to, datetime.time.max)
                domain.append(('check_out', '<=', departure_to_datetime))
            if self.booking_source:
                domain.append(('booking_source', '=', self.booking_source))
                if self.booking_source == 'online_agent' and self.online_travel_agent_source:
                    domain.append(('online_travel_agent_source', '=', self.online_travel_agent_source.id))
                elif self.booking_source == 'company' and self.company_booking_source:
                    domain.append(('company_booking_source', '=', self.company_booking_source.id))
            if self.state:
                domain.append(('state', '=', self.state))
            if self.reference_number:
                domain.append(('ref', '=', self.reference_number))
            if self.hotel_ids:
                domain.append(('hotel_id', 'in', self.hotel_ids.ids))
            if self.is_cancelled:
                domain.append(('state', '!=', 'cancelled'))
            if self.season_id:
                domain.append(('season_id', '=', self.season_id.id))

            folios = self.env['hotel.booking'].sudo().search(domain)

            if self.paid_without_zero:
                folios = folios.filtered(lambda f: f.amount_paid > 0.0)

            if self.paid_with_zero:
                folios = folios.filtered(lambda f: f.amount_paid == 0.0)

            if self.total_without_zero:
                folios = folios.filtered(lambda f: f.amount_total > 0.0)

            if self.city_ledger_booking:
                folios = folios.filtered(lambda f: f.company_paid == 0.0)

            if self.settled_city_ledger_booking:
                folios = folios.filtered(lambda f: f.company_paid != 0.0)

            if self.mobile:
                folios = self.env['hotel.booking'].search(
                    [('id', 'in', folios.ids), ('partner_id.mobile', 'ilike', self.mobile)])
            if self.country_id:
                folios = self.env['hotel.booking'].search(
                    [('id', 'in', folios.ids), ('partner_id.country_id', '=', self.country_id.id)])
            if self.booking_id:
                folios = folios.filtered(lambda f: f.id == self.booking_id.id)

            if self.partner_id:
                folios = folios.filtered(lambda f: f.partner_id.id == self.partner_id.id)

            if not self.grouped_company_source:
                for folio in folios:
                    room_charge = len(folio.folio_ids.line_ids.filtered(lambda l: l.particulars == 'Room Charge'))
                    price_subtotal = sum(folio.folio_ids[0].mapped('price_subtotal')) if folio.folio_ids else 0.0
                    self.line_ids = [(0, 0, {
                        'booking_id': folio.id,
                        'state': folio.state,
                        'wizard_id': self.id,
                        'name': folio.name,
                        'partner_id': folio.partner_id.id,
                        'company_booking_source': folio.company_booking_source.id,
                        'related_hotel': folio.hotel_id.id,
                        'check_in': folio.check_in,
                        'check_out': folio.check_out,
                        'user_id': folio.user_id.id,
                        'price_subtotal': folio.amount_untaxed,
                        'price_total': folio.amount_total,
                        'price_tax': folio.amount_tax,
                        'price_paid': folio.amount_paid,
                        'price_due': folio.amount_due,
                        'no_nights': folio.actual_no_night,
                        'no_rooms': folio.actual_no_room,
                        'price_night': folio.line_ids[0].price_unit if folio.line_ids else 0,
                    })]

    def print_pdf(self):
        return self.env.ref('hotel_booking.action_booking_filter_report').with_context(
            landscape=True).report_action(self)

    def print_booking_source_pdf(self):
        return self.env.ref('hotel_booking.action_dynamic_booking_source_report').with_context(
            landscape=True).report_action(self)

    def print_xlsx(self):
        return self.env.ref('hotel_booking.action_dynamic_reservation_xlsx_report').report_action(self)


class BookingFilterLine(models.Model):
    _name = 'booking.filter.line'

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

    state = fields.Selection(STATES, default='draft')
    wizard_id = fields.Many2one('booking.filter')
    folio_id = fields.Many2one('booking.folio')
    booking_id = fields.Many2one('hotel.booking', store=True)
    ref = fields.Char(related='booking_id.ref')
    name = fields.Char(related='folio_id.name')
    company_booking_source = fields.Many2one('res.partner')
    partner_id = fields.Many2one('res.partner')
    user_id = fields.Many2one('res.users', "Booked By")
    check_in = fields.Date()
    check_out = fields.Date()
    price_subtotal = fields.Monetary()
    price_total = fields.Monetary()
    price_tax = fields.Monetary()
    price_paid = fields.Monetary()
    price_due = fields.Monetary()
    company_paid = fields.Float(related='booking_id.company_paid')
    paid_amount_city_ledger = fields.Float(related='booking_id.paid_amount_city_ledger')
    payment_type_id = fields.Selection(related='booking_id.payment_type_id')
    currency_id = fields.Many2one('res.currency', readonly=True, tracking=True, string='Currency',
                                  default=lambda self: self.env.user.company_id.currency_id)
    related_hotel = fields.Many2one('hotel.hotel')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, required=True)
    no_nights = fields.Integer("No. Nights")
    no_rooms = fields.Integer("No. Rooms")
    price_night = fields.Float("Price Night Without Tax")
    price_night_with_tax = fields.Float("Price Night With Tax")
    room_id = fields.Many2one('hotel.room', "Room No")
    total_discount = fields.Float(related='booking_id.price_discount', string="Total Discount")
    # cash_paid = fields.Monetary("Cash Paid", related='booking_id.cash_paid')
    # bank_paid = fields.Monetary("Bank Paid", related='booking_id.bank_paid')
    # paid_amount_city_ledger = fields.Monetary(related='booking_id.paid_amount_city_ledger')
    rate_plan_id = fields.Many2one('hotel.rate.plan')
    room_type_id = fields.Many2one('room.type')
