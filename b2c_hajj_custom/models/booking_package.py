from datetime import datetime,timedelta

from odoo import fields, models, api, _, exceptions
from odoo.exceptions import ValidationError
import logging
from markupsafe import Markup
logger = logging.getLogger(__name__)


class BookingPackage(models.Model):
    _name = 'booking.package'
    _rec_name = 'package_code'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']

    name = fields.Char('#', default='New', copy=False, required=True, readonly=True)
    partner_id = fields.Many2one('res.partner', 'Booking Customer', required=True)
    package_code = fields.Char("Code", required=True)
    guide_ids = fields.Many2many('res.partner', string='Guide', domain=[('is_guide', '=', True)],
                                 context={'default_is_guide': True}, tracking=True)
    partner_ids = fields.One2many('res.partner', 'package_id')
    booking_ids = fields.One2many('hotel.booking', 'package_id')
    booking_count = fields.Integer(compute='compute_booking_count', store=True)
    partner_count = fields.Integer(compute='compute_partner_count', store=True)
    state = fields.Selection(selection=[
        ('draft', 'Draft'), ('confirmed', 'Confirmed'),
    ], default='draft', tracking=True)
    flight_contract_lines = fields.One2many('flight.schedule.line', 'package_id')
    flight_sale_price = fields.Float(string="Flight Sale Price", compute='compute_flight_price', store=True)
    flight_purchase_price = fields.Float(string="Flight Purchase Price", compute='compute_flight_price', store=True)

    #  makkah
    main_makkah = fields.Many2one('hotel.hotel', domain="[('type', '=', 'makkah')]", string='Makkah Hotel', tracking=True)
    actual_main_makkah = fields.Many2one('actual.hotel', domain="[('hotel_id', '=', main_makkah)]", string='Actual Makkah Hotel')
    makkah_contract_id = fields.Many2one('hotel.contract.management', string="Makkah Contract", domain="[('hotel_id', '=', main_makkah)]")
    makkah_date_from = fields.Date("Contract Start Date", related='makkah_contract_id.date_from', store=True)
    makkah_date_to = fields.Date("Contract End Date", related='makkah_contract_id.date_to', store=True)
    main_makkah_company_id = fields.Many2one('res.company', related='main_makkah.company_id', store=True)
    makkah_arrival_date = fields.Date("Makkah Arrival Date", tracking=True)
    makkah_departure_date = fields.Date("Makkah Departure Date", tracking=True)
    makkah_no_double = fields.Integer("Makkah Double", tracking=True)
    makkah_no_triple = fields.Integer("Makkah Triple", tracking=True)
    makkah_no_quad = fields.Integer("Makkah Quad", tracking=True)
    makkah_double_available = fields.Integer("Makkah Double Available", tracking=True)
    makkah_triple_available = fields.Integer("Makkah Triple Available", tracking=True)
    makkah_quad_available = fields.Integer("Makkah Quad Available", tracking=True)
    makkah_double_plan_id = fields.Many2one('hotel.rate.plan',
                                            domain="[('room_type_id.mini_adults', '=', 2), ('company_id', '=', main_makkah_company_id)]",
                                            tracking=True)
    makkah_triple_plan_id = fields.Many2one('hotel.rate.plan',
                                            domain="[('room_type_id.mini_adults', '=', 3), ('company_id', '=', main_makkah_company_id)]",
                                            tracking=True)
    makkah_quad_plan_id = fields.Many2one('hotel.rate.plan',
                                          domain="[('room_type_id.mini_adults', '=', 4), ('company_id', '=', main_makkah_company_id)]",
                                          tracking=True)

    makkah_double_total_beds = fields.Integer(compute='compute_makkah_double_total_beds', store=True, tracking=True)
    makka_double_male_beds = fields.Integer("Booking Male Beds")
    makka_double_female_beds = fields.Integer("Booking Female Beds")
    makkah_double_male_booked_beds = fields.Integer(tracking=True, string="Male Booked Beds", compute='compute_booked_beds', store=True)
    makkah_double_female_booked_beds = fields.Integer(tracking=True, string="Female Booked Beds", compute='compute_booked_beds', store=True)
    makkah_double_male_total_beds = fields.Integer(compute='compute_makkah_double_male_total_beds', store=True, tracking=True)
    makkah_double_female_total_beds = fields.Integer(compute='compute_makkah_double_female_total_beds', store=True, tracking=True)
    makkah_double_male_available_beds = fields.Integer(compute='compute_makkah_double_male_available_beds',  tracking=True, store=True)
    makkah_double_female_available_beds = fields.Integer(compute='compute_makkah_double_female_available_beds',  tracking=True, store=True)

    makkah_triple_total_beds = fields.Integer(compute='compute_makkah_triple_total_beds', store=True, tracking=True)
    makka_triple_male_beds = fields.Integer("Booking Male Beds")
    makka_triple_female_beds = fields.Integer("Booking Female Beds")
    makkah_triple_male_total_beds = fields.Integer(compute='compute_makkah_triple_male_total_beds', store=True, tracking=True)
    makkah_triple_female_total_beds = fields.Integer(compute='compute_makkah_triple_female_total_beds', store=True, tracking=True)

    makkah_triple_male_booked_beds = fields.Integer(tracking=True, string="Male Booked Beds", compute='compute_booked_beds', store=True)
    makkah_triple_female_booked_beds = fields.Integer(tracking=True, string="Female Booked Beds", compute='compute_booked_beds', store=True)
    makkah_triple_male_available_beds = fields.Integer(compute='compute_makkah_triple_male_available_beds', tracking=True, store=True)
    makkah_triple_female_available_beds = fields.Integer(compute='compute_makkah_triple_female_available_beds', tracking=True, store=True)

    makkah_quad_total_beds = fields.Integer(compute='compute_makkah_quad_total_beds', store=True, tracking=True)
    makka_quad_male_beds = fields.Integer("Booking Male Beds")
    makka_quad_female_beds = fields.Integer("Booking Female Beds")

    makkah_quad_male_total_beds = fields.Integer(compute='compute_makkah_quad_male_total_beds', store=True, tracking=True)
    makkah_quad_female_total_beds = fields.Integer(compute='compute_makkah_quad_female_total_beds', store=True, tracking=True)
    makkah_quad_male_booked_beds = fields.Integer(tracking=True, string="Male Booked Beds", compute='compute_booked_beds', store=True)
    makkah_quad_female_booked_beds = fields.Integer(tracking=True, string="Female Booked Beds", compute='compute_booked_beds', store=True)

    makkah_quad_male_available_beds = fields.Integer(compute='compute_makkah_quad_male_available_beds', tracking=True, store=True)
    makkah_quad_female_available_beds = fields.Integer(compute='compute_makkah_quad_female_available_beds',  tracking=True, store=True)

    # madinah
    main_madinah = fields.Many2one('hotel.hotel', domain="[('type', '=', 'madinah')]", string='Madinah Hotel', tracking=True)
    actual_main_madinah = fields.Many2one('actual.hotel', domain="[('hotel_id', '=', main_madinah)]", string='Actual Madinah Hotel')
    madinah_contract_id = fields.Many2one('hotel.contract.management', string="Madinah Contract", domain="[('hotel_id', '=', main_madinah)]")
    madinah_date_from = fields.Date("Contract Start Date", related='madinah_contract_id.date_from', store=True)
    madinah_date_to = fields.Date("Contract End Date", related='madinah_contract_id.date_to', store=True)
    main_madinah_company_id = fields.Many2one('res.company', related='main_madinah.company_id', store=True)
    madinah_arrival_date = fields.Date("Madinah Arrival Date", tracking=True)
    madinah_departure_date = fields.Date("Madinah Departure Date", tracking=True)
    madinah_no_double = fields.Integer("Madinah Double", tracking=True)
    madinah_no_triple = fields.Integer("Madinah Triple", tracking=True)
    madinah_no_quad = fields.Integer("Madinah Quad", tracking=True)
    madinah_double_available = fields.Integer("Madinah Double Available", tracking=True)
    madinah_triple_available = fields.Integer("Madinah Triple Available", tracking=True)
    madinah_quad_available = fields.Integer("Madinah Quad Available", tracking=True)
    madinah_double_plan_id = fields.Many2one('hotel.rate.plan',
                                             domain="[('room_type_id.mini_adults', '=', 2), ('company_id', '=', main_madinah_company_id)]",
                                             tracking=True)
    madinah_triple_plan_id = fields.Many2one('hotel.rate.plan',
                                             domain="[('room_type_id.mini_adults', '=', 3), ('company_id', '=', main_madinah_company_id)]",
                                             tracking=True)
    madinah_quad_plan_id = fields.Many2one('hotel.rate.plan',
                                           domain="[('room_type_id.mini_adults', '=', 4), ('company_id', '=', main_madinah_company_id)]",
                                           tracking=True)

    madinah_double_total_beds = fields.Integer(compute='compute_madinah_double_total_beds', store=True, tracking=True)
    madinah_double_male_beds = fields.Integer("Booking Male Beds")
    madinah_double_female_beds = fields.Integer("Booking Female Beds")
    madinah_double_male_total_beds = fields.Integer(compute='compute_madinah_double_male_total_beds', store=True, tracking=True)
    madinah_double_female_total_beds = fields.Integer(compute='compute_madinah_double_female_total_beds', store=True, tracking=True)
    madinah_double_male_booked_beds = fields.Integer(tracking=True, compute='compute_booked_beds', store=True)
    madinah_double_female_booked_beds = fields.Integer(tracking=True, compute='compute_booked_beds', store=True)
    madinah_double_male_available_beds = fields.Integer(compute='compute_madinah_double_male_available_beds', tracking=True, store=True)
    madinah_double_female_available_beds = fields.Integer(compute='compute_madinah_double_female_available_beds', tracking=True, store=True)

    madinah_triple_total_beds = fields.Integer(compute='compute_madinah_triple_total_beds', store=True, tracking=True)
    madinah_triple_male_beds = fields.Integer("Booking Male Beds")
    madinah_triple_female_beds = fields.Integer("Booking Female Beds")
    madinah_triple_male_total_beds = fields.Integer(compute='compute_madinah_male_triple_total_beds', store=True, tracking=True)
    madinah_triple_female_total_beds = fields.Integer(compute='compute_madinah_female_triple_total_beds', store=True, tracking=True)
    madinah_triple_male_booked_beds = fields.Integer(tracking=True,compute='compute_booked_beds', store=True)
    madinah_triple_female_booked_beds = fields.Integer(tracking=True, compute='compute_booked_beds', store=True)
    madinah_triple_male_available_beds = fields.Integer(compute='compute_madinah_triple_male_available_beds', tracking=True, store=True)
    madinah_triple_female_available_beds = fields.Integer(compute='compute_madinah_triple_female_available_beds', tracking=True, store=True)

    madinah_quad_total_beds = fields.Integer(compute='compute_madinah_quad_total_beds', store=True, tracking=True)
    madinah_quad_male_beds = fields.Integer("Booking Male Beds")
    madinah_quad_female_beds = fields.Integer("Booking Female Beds")
    madinah_quad_male_total_beds = fields.Integer(compute='compute_madinah_quad_male_total_beds', store=True, tracking=True)
    madinah_quad_female_total_beds = fields.Integer(compute='compute_madinah_quad_female_total_beds', store=True, tracking=True)
    madinah_quad_male_booked_beds = fields.Integer(tracking=True, compute='compute_booked_beds', store=True)
    madinah_quad_female_booked_beds = fields.Integer(tracking=True, compute='compute_booked_beds', store=True)
    madinah_quad_male_available_beds = fields.Integer(compute='compute_madinah_quad_male_available_beds', tracking=True, store=True)
    madinah_quad_female_available_beds = fields.Integer(compute='compute_madinah_quad_female_available_beds', tracking=True, store=True)

    #  arfa
    main_arfa = fields.Many2one('hotel.hotel', domain="[('type', '=', 'arfa')]", string='Arfa Hotel', tracking=True)
    main_arfa_company_id = fields.Many2one('res.company', related='main_arfa.company_id', store=True)
    arfa_arrival_date = fields.Date("Arfa Arrival Date", tracking=True)
    arfa_departure_date = fields.Date("Arfa Departure Date", tracking=True)
    arfa_male_available_beds = fields.Integer(tracking=True, compute='onchange_arfa_data')
    arfa_female_available_beds = fields.Integer(tracking=True, compute='onchange_arfa_data')
    arfa_male_plan_id = fields.Many2one('hotel.rate.plan',
                                          domain="[('company_id', '=', main_arfa_company_id)]",
                                          tracking=True)
    arfa_female_plan_id = fields.Many2one('hotel.rate.plan',
                                          domain="[('company_id', '=', main_arfa_company_id)]",
                                          tracking=True)
    arfa_male_total_beds = fields.Integer(tracking=True)
    arfa_female_total_beds = fields.Integer(tracking=True)
    arfa_male_booked_beds = fields.Integer(tracking=True,  compute='compute_booked_beds', store=True)
    arfa_female_booked_beds = fields.Integer(tracking=True,  compute='compute_booked_beds', store=True)
    arfa_male_unbooked_beds = fields.Integer(compute='compute_arfa_male_unbooked_beds', tracking=True, store=True)
    arfa_female_unbooked_beds = fields.Integer(compute='compute_arfa_female_unbooked_beds', tracking=True, store=True)


    # minnah
    main_minnah = fields.Many2one('hotel.hotel', domain="[('type', '=', 'minnah')]", string='Minnah Hotel', tracking=True)
    main_minnah_company_id = fields.Many2one('res.company', related='main_minnah.company_id', store=True)
    minnah_arrival_date = fields.Date("Minnah Arrival Date", tracking=True)
    minnah_departure_date = fields.Date("Minnah Departure Date", tracking=True)
    minnah_male_available_beds = fields.Integer(tracking=True, compute='onchange_minnah_data')
    minnah_female_available_beds = fields.Integer(tracking=True, compute='onchange_minnah_data')
    minnah_male_plan_id = fields.Many2one('hotel.rate.plan',
                                          domain="[('company_id', '=', main_minnah_company_id)]",
                                          tracking=True)
    minnah_female_plan_id = fields.Many2one('hotel.rate.plan',
                                          domain="[('company_id', '=', main_minnah_company_id)]",
                                          tracking=True)
    minnah_male_total_beds = fields.Integer(tracking=True)
    minnah_female_total_beds = fields.Integer(tracking=True)
    minnah_male_booked_beds = fields.Integer(tracking=True,  compute='compute_booked_beds', store=True)
    minnah_female_booked_beds = fields.Integer(tracking=True,  compute='compute_booked_beds', store=True)
    minnah_male_unbooked_beds = fields.Integer(compute='compute_minnah_male_unbooked_beds', tracking=True, store=True)
    minnah_female_unbooked_beds = fields.Integer(compute='compute_minnah_female_unbooked_beds', tracking=True, store=True)


    # main shift
    main_hotel = fields.Many2one('hotel.hotel', "Main Shift", domain="[('type', 'in', ['hotel','makkah'])]", tracking=True)
    actual_main_hotel = fields.Many2one('actual.hotel', domain="[('hotel_id', '=', main_hotel)]", string='Actual Main Shift')
    main_hotel_contract_id = fields.Many2one('hotel.contract.management', string="Main Shift Contract", domain="[('hotel_id', '=', main_hotel)]")
    main_hotel_date_from = fields.Date("Contract Start Date", related='main_hotel_contract_id.date_from', store=True)
    main_hotel_date_to = fields.Date("Contract End Date", related='main_hotel_contract_id.date_to', store=True)
    main_hotel_company_id = fields.Many2one('res.company', related='main_hotel.company_id')
    hotel_arrival_date = fields.Date("Main Shift Arrival Date", tracking=True)
    hotel_departure_date = fields.Date("Main Shift Departure Date", tracking=True)
    hotel_no_double = fields.Integer("Main Double", tracking=True)
    hotel_double_male_beds = fields.Integer("Booking Male Beds")
    hotel_double_female_beds = fields.Integer("Booking Female Beds")
    hotel_double_available = fields.Integer("Main Double", tracking=True)
    hotel_no_triple = fields.Integer("Main Triple", tracking=True)
    hotel_triple_male_beds = fields.Integer("Booking Male Beds")
    hotel_triple_female_beds = fields.Integer("Booking Female Beds")
    hotel_triple_available = fields.Integer(tracking=True)
    hotel_no_quad = fields.Integer("Main Quad", tracking=True)
    hotel_quad_male_beds = fields.Integer("Booking Male Beds")
    hotel_quad_female_beds = fields.Integer("Booking Female Beds")
    hotel_quad_available = fields.Integer(tracking=True)
    hotel_double_plan_id = fields.Many2one('hotel.rate.plan',
                                           domain="[('room_type_id.mini_adults', '=', 2), ('company_id', '=', main_hotel_company_id)]",
                                           tracking=True)
    hotel_triple_plan_id = fields.Many2one('hotel.rate.plan',
                                           domain="[('room_type_id.mini_adults', '=', 3), ('company_id', '=', main_hotel_company_id)]",
                                           tracking=True)
    hotel_quad_plan_id = fields.Many2one('hotel.rate.plan',
                                         domain="[('room_type_id.mini_adults', '=', 4), ('company_id', '=', main_hotel_company_id)]",
                                         tracking=True)
    hotel_double_total_beds = fields.Integer(compute='compute_hotel_double_total_beds', store=True, tracking=True)
    hotel_double_male_total_beds = fields.Integer(compute='compute_hotel_double_male_total_beds', store=True, tracking=True)
    hotel_double_female_total_beds = fields.Integer(compute='compute_hotel_double_female_total_beds', store=True, tracking=True)
    hotel_double_male_booked_beds = fields.Integer(tracking=True, compute='compute_booked_beds', store=True)
    hotel_double_female_booked_beds = fields.Integer(tracking=True, compute='compute_booked_beds', store=True)
    hotel_double_male_available_beds = fields.Integer(compute='compute_hotel_double_male_available_beds', tracking=True, store=True)
    hotel_double_female_available_beds = fields.Integer(compute='compute_hotel_double_female_available_beds', tracking=True, store=True)
    hotel_triple_total_beds = fields.Integer(compute='compute_hotel_triple_total_beds', store=True, tracking=True)
    hotel_triple_male_total_beds = fields.Integer(compute='compute_hotel_triple_male_total_beds', store=True, tracking=True)
    hotel_triple_female_total_beds = fields.Integer(compute='compute_hotel_triple_female_total_beds', store=True, tracking=True)
    hotel_triple_male_booked_beds = fields.Integer(tracking=True, compute='compute_booked_beds', store=True)
    hotel_triple_female_booked_beds = fields.Integer(tracking=True, compute='compute_booked_beds', store=True)
    hotel_triple_male_available_beds = fields.Integer(compute='compute_hotel_triple_male_available_beds',tracking=True, store=True)
    hotel_triple_female_available_beds = fields.Integer(compute='compute_hotel_triple_female_available_beds',tracking=True, store=True)
    hotel_quad_total_beds = fields.Integer(compute='compute_hotel_quad_total_beds', store=True, tracking=True)
    hotel_quad_male_total_beds = fields.Integer(compute='compute_hotel_quad_male_total_beds', store=True, tracking=True)
    hotel_quad_female_total_beds = fields.Integer(compute='compute_hotel_quad_female_total_beds', store=True, tracking=True)
    hotel_quad_male_booked_beds = fields.Integer(tracking=True, compute='compute_booked_beds', store=True)
    hotel_quad_female_booked_beds = fields.Integer(tracking=True, compute='compute_booked_beds', store=True)
    hotel_quad_male_available_beds = fields.Integer(compute='compute_hotel_quad_male_available_beds', tracking=True, store=True)
    hotel_quad_female_available_beds = fields.Integer(compute='compute_hotel_quad_female_available_beds', tracking=True, store=True)
    transportation_contract_ids = fields.Many2many('transportation.contract',  string="Transportation Contracts")
    package_closing_date = fields.Date(string='Package Closing Date', required=True)
    allow_booking = fields.Boolean(
        string="Allow Booking",
        compute='_compute_allow_booking',
        store=True
    )
    sale_price_ids = fields.One2many('package.price', 'package_id', string="Sale Prices",
                                     domain=[('price_type', '=', 'sale')])
    purchase_price_ids = fields.One2many('package.price', 'package_id', string="Purchase Prices",
                                     domain=[('price_type', '=', 'purchase')])
    package_sale_price = fields.Float(string="Package Sale Price", compute='compute_package_sale_price')
    package_purchase_price = fields.Float(string="Package Purchase Price", compute='compute_package_purchase_price')
    package_extra_service = fields.One2many('extra.service.line', 'package_id', string="Extra Service")
    extra_service_sale = fields.Float(string="Extra Service Sale", compute='compute_extra_service', store=True)
    extra_service_purchase = fields.Float(string="Extra Service Purchase", compute='compute_extra_service', store=True)
    makkah_activity_line_ids = fields.One2many(
        'booking.package.activity.line', 'package_id',
        domain=[('location', '=', 'makkah')],
        string="Makkah Activities"
    )
    madina_activity_line_ids = fields.One2many(
        'booking.package.activity.line', 'package_id',
        domain=[('location', '=', 'madina')],
        string="Madina Activities"
    )
    arfa_activity_line_ids = fields.One2many(
        'booking.package.activity.line', 'package_id',
        domain=[('location', '=', 'arfa')],
        string="Arafat Activities"
    )
    minah_activity_line_ids = fields.One2many(
        'booking.package.activity.line', 'package_id',
        domain=[('location', '=', 'minah')],
        string="Minah Activities"
    )
    hotel_activity_line_ids = fields.One2many(
        'booking.package.activity.line', 'package_id',
        domain=[('location', '=', 'hotel')],
        string="Hotel Activities"
    )


    _sql_constraints = [
        ('package_code', 'unique (package_code)', 'Package Code must be unique')
    ]

    @api.depends('package_extra_service')
    def compute_extra_service(self):
        for rec in self:
            extra_service_sale = 0
            extra_service_purchase = 0
            for line in rec.package_extra_service:
                extra_service_sale += line.sale_price
                extra_service_purchase += line.cost_price
            rec.extra_service_sale = extra_service_sale
            rec.extra_service_purchase = extra_service_purchase

    @api.depends('sale_price_ids')
    def compute_package_sale_price(self):
        for record in self:
            package_sale_price = 0
            for line in record.sale_price_ids:
                package_sale_price += line.total_price_per_group
            record.package_sale_price = package_sale_price

    @api.depends('purchase_price_ids')
    def compute_package_purchase_price(self):
        for record in self:
            package_purchase_price = 0
            for line in record.purchase_price_ids:
                package_purchase_price += line.total_price_per_group
            record.package_purchase_price = package_purchase_price



    @api.depends('flight_contract_lines', 'flight_contract_lines.sale_price', 'flight_contract_lines.purchase_price')
    def compute_flight_price(self):
        for record in self:
            flight_sale_price = 0
            flight_purchase_price = 0
            for line in record.flight_contract_lines:
                flight_sale_price += line.sale_price
                flight_purchase_price += line.purchase_price
            record.flight_sale_price = (flight_sale_price/len(record.flight_contract_lines)) if record.flight_contract_lines else 0
            record.flight_purchase_price = (flight_purchase_price/len(record.flight_contract_lines)) if record.flight_contract_lines else 0

    @api.depends('partner_ids.package_id', 'partner_ids.makkah_room_type', 'partner_ids.madinah_room_type', 'partner_ids.hotel_room_type', 'partner_ids.gender')
    def compute_booked_beds(self):
        print('compute_booked_beds')
        for record in self:
            makkah_beds = {
                'male': {2: 0, 3: 0, 4: 0},
                'female': {2: 0, 3: 0, 4: 0},
            }
            madinah_beds = {
                'male': {2: 0, 3: 0, 4: 0},
                'female': {2: 0, 3: 0, 4: 0},
            }
            hotel_beds = {
                'male': {2: 0, 3: 0, 4: 0},
                'female': {2: 0, 3: 0, 4: 0},
            }
            arfa_beds = {
                'male': 0,
                'female': 0
            }
            minnah_beds = {
                'male': 0,
                'female': 0
            }
            if not record.booking_ids:
                record.makkah_double_male_booked_beds = 0
                record.makkah_double_female_booked_beds = 0
                record.makkah_triple_male_booked_beds = 0
                record.makkah_triple_female_booked_beds = 0
                record.makkah_quad_male_booked_beds = 0
                record.makkah_quad_female_booked_beds = 0
                record.madinah_double_male_booked_beds = 0
                record.madinah_double_female_booked_beds = 0
                record.madinah_triple_male_booked_beds = 0
                record.madinah_triple_female_booked_beds = 0
                record.madinah_quad_male_booked_beds = 0
                record.madinah_quad_female_booked_beds = 0
                record.hotel_double_male_booked_beds = 0
                record.hotel_double_female_booked_beds = 0
                record.hotel_triple_male_booked_beds = 0
                record.hotel_triple_female_booked_beds = 0
                record.hotel_quad_male_booked_beds = 0
                record.hotel_quad_female_booked_beds = 0
                record.arfa_male_booked_beds = 0
                record.arfa_female_booked_beds = 0
                record.minnah_male_booked_beds = 0
                record.minnah_female_booked_beds = 0
            for booking in record.booking_ids:
                if booking.hotel_id.type == 'makkah':
                    counts = self.env['res.partner'].read_group(
                        domain=[('package_id', '=', record.id)],
                        fields=['makkah_room_type', 'gender'],
                        groupby=['makkah_room_type', 'gender'],
                        lazy=False
                    )
                    for res in counts:
                        room_type = int(res['makkah_room_type']) if res['makkah_room_type'] else 0
                        gender = res['gender']
                        count = res['__count']
                        if gender in makkah_beds and room_type in makkah_beds[gender]:
                            makkah_beds[gender][room_type] = count
                    # Extract final values

                elif booking.hotel_id.type == 'madinah':
                    counts = self.env['res.partner'].read_group(
                        domain=[('package_id', '=', record.id)],
                        fields=['madinah_room_type', 'gender'],
                        groupby=['madinah_room_type', 'gender'],
                        lazy=False
                    )
                    for res in counts:
                        room_type = int(res['madinah_room_type']) if res['madinah_room_type'] else 0
                        gender = res['gender']
                        count = res['__count']
                        if gender in madinah_beds and room_type in madinah_beds[gender]:
                            madinah_beds[gender][room_type] = count
                    # Extract final values

                elif booking.hotel_id.type == 'hotel':
                    counts = self.env['res.partner'].read_group(
                        domain=[('package_id', '=', record.id)],
                        fields=['hotel_room_type', 'gender'],
                        groupby=['hotel_room_type', 'gender'],
                        lazy=False
                    )
                    for res in counts:
                        room_type = int(res['hotel_room_type']) if res['hotel_room_type'] else 0
                        gender = res['gender']
                        count = res['__count']
                        if gender in hotel_beds and room_type in hotel_beds[gender]:
                            hotel_beds[gender][room_type] = count

                elif booking.hotel_id.type == 'arfa':
                    counts = self.env['res.partner'].read_group(
                        domain=[('package_id', '=', record.id)],
                        fields=['gender'],
                        groupby=['gender'],
                        lazy=False
                    )
                    print('countsssssss', counts)
                    for res in counts:
                        gender = res['gender']
                        count = res['__count']
                        if gender in arfa_beds:
                            arfa_beds[gender] = count

                elif booking.hotel_id.type == 'minnah':
                    counts = self.env['res.partner'].read_group(
                        domain=[('package_id', '=', record.id)],
                        fields=['gender'],
                        groupby=['gender'],
                        lazy=False
                    )
                    print('countsssssss', counts)
                    for res in counts:
                        gender = res['gender']
                        count = res['__count']
                        if gender in minnah_beds:
                            minnah_beds[gender] = count

                record.makkah_double_male_booked_beds = makkah_beds['male'][2]
                record.makkah_double_female_booked_beds = makkah_beds['female'][2]
                record.makkah_triple_male_booked_beds = makkah_beds['male'][3]
                record.makkah_triple_female_booked_beds = makkah_beds['female'][3]
                record.makkah_quad_male_booked_beds = makkah_beds['male'][4]
                record.makkah_quad_female_booked_beds = makkah_beds['female'][4]
                record.madinah_double_male_booked_beds = madinah_beds['male'][2]
                record.madinah_double_female_booked_beds = madinah_beds['female'][2]
                record.madinah_triple_male_booked_beds = madinah_beds['male'][3]
                record.madinah_triple_female_booked_beds = madinah_beds['female'][3]
                record.madinah_quad_male_booked_beds = madinah_beds['male'][4]
                record.madinah_quad_female_booked_beds = madinah_beds['female'][4]
                record.hotel_double_male_booked_beds = hotel_beds['male'][2]
                record.hotel_double_female_booked_beds = hotel_beds['female'][2]
                record.hotel_triple_male_booked_beds = hotel_beds['male'][3]
                record.hotel_triple_female_booked_beds = hotel_beds['female'][3]
                record.hotel_quad_male_booked_beds = hotel_beds['male'][4]
                record.hotel_quad_female_booked_beds = hotel_beds['female'][4]
                record.arfa_male_booked_beds = arfa_beds['male']
                record.arfa_female_booked_beds = arfa_beds['female']
                record.minnah_male_booked_beds = minnah_beds['male']
                record.minnah_female_booked_beds = minnah_beds['female']


    @api.constrains('makka_quad_male_beds', 'makka_quad_female_beds', 'makkah_no_quad')
    def check_makkah_quad_bed_distribution(self):
        for record in self:
            total_assigned = record.makka_quad_male_beds + record.makka_quad_female_beds
            if total_assigned != record.makkah_no_quad:
                raise ValidationError("The sum of Male Beds and Female Beds must equal the total bookings (Booking)")

    @api.constrains('makka_triple_male_beds', 'makka_triple_female_beds', 'makkah_no_triple')
    def check_makkah_triple_bed_distribution(self):
        for record in self:
            total_assigned = record.makka_triple_male_beds + record.makka_triple_female_beds
            if total_assigned != record.makkah_no_triple:
                raise ValidationError("The sum of Male Beds and Female Beds must equal the total bookings (Booking)")

    @api.constrains('makka_double_male_beds', 'makka_double_female_beds', 'makkah_no_double')
    def check_makkah_double_bed_distribution(self):
        for record in self:
            total_assigned = record.makka_double_male_beds + record.makka_double_female_beds
            if total_assigned != record.makkah_no_double:
                raise ValidationError("The sum of Male Beds and Female Beds must equal the total bookings (Booking)")

    @api.constrains('madinah_double_male_beds', 'madinah_double_female_beds', 'madinah_no_double')
    def check_double_madinah_bed_distribution(self):
        for record in self:
            total_assigned = record.madinah_double_male_beds + record.madinah_double_female_beds
            if total_assigned != record.madinah_no_double:
                raise ValidationError("The sum of Male Beds and Female Beds must equal the total bookings (Booking)")

    @api.constrains('madinah_triple_male_beds', 'madinah_triple_female_beds', 'madinah_no_triple')
    def check_triple_madinah_bed_distribution(self):
        for record in self:
            total_assigned = record.madinah_triple_male_beds + record.madinah_triple_female_beds
            if total_assigned != record.madinah_no_triple:
                raise ValidationError("The sum of Male Beds and Female Beds must equal the total bookings (Booking)")

    @api.constrains('madinah_quad_male_beds', 'madinah_quad_female_beds', 'madinah_no_quad')
    def check_quad_madinah_bed_distribution(self):
        for record in self:
            total_assigned = record.madinah_quad_male_beds + record.madinah_quad_female_beds
            if total_assigned != record.madinah_no_quad:
                raise ValidationError("The sum of Male Beds and Female Beds must equal the total bookings (Booking)")

    @api.constrains('hotel_quad_male_beds', 'hotel_quad_female_beds', 'hotel_no_quad')
    def check_hotel_quad_bed_distribution(self):
        for record in self:
            total_assigned = record.hotel_quad_male_beds + record.hotel_quad_female_beds
            if total_assigned != record.hotel_no_quad:
                raise ValidationError("The sum of Male Beds and Female Beds must equal the total bookings (Booking)")

    @api.constrains('hotel_triple_male_beds', 'hotel_triple_female_beds', 'hotel_no_triple')
    def check_hotel_triple_bed_distribution(self):
        for record in self:
            total_assigned = record.hotel_triple_male_beds + record.hotel_triple_female_beds
            if total_assigned != record.hotel_no_triple:
                raise ValidationError("The sum of Male Beds and Female Beds must equal the total bookings (Booking)")

    @api.constrains('hotel_double_male_beds', 'hotel_double_female_beds', 'hotel_no_double')
    def check_hotel_double_bed_distribution(self):
        for record in self:
            total_assigned = record.hotel_double_male_beds + record.hotel_double_female_beds
            if total_assigned != record.hotel_no_double:
                raise ValidationError("The sum of Male Beds and Female Beds must equal the total bookings (Booking)")

    @api.constrains('package_closing_date', 'makkah_arrival_date', 'madinah_arrival_date',
                    'arfa_arrival_date', 'minnah_arrival_date', 'hotel_arrival_date')
    def _check_booking_date(self):
        for record in self:
            earliest_date = min(filter(None, [
                record.makkah_arrival_date,
                record.madinah_arrival_date,
                record.arfa_arrival_date,
                record.minnah_arrival_date,
                record.hotel_arrival_date
            ]))
            if record.package_closing_date < earliest_date:
                raise exceptions.ValidationError(
                    "The Package Closing Date cannot be earlier than the earliest arrival date")
            else:
                self._compute_allow_booking()

    @api.onchange('package_closing_date')
    def _compute_allow_booking(self):
        for record in self:
            if record.package_closing_date:
                record.allow_booking = record.package_closing_date >= fields.Date.today()
            else:
                record.allow_booking = False

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('booking.package') or '/'
        record = super().create(vals)
        record._generate_activity_lines()
        return record

    def _generate_activity_lines(self):
        """Generate activity lines for each location based on date range."""
        self.ensure_one()

        def generate_lines(start_date, end_date, location):
            if not start_date or not end_date:
                return []
            current_date = start_date
            lines = []
            while current_date <= end_date:
                lines.append((0, 0, {
                    'date': current_date,
                    'location': location,
                    'package_id': self.id,
                }))
                current_date += timedelta(days=1)
            return lines

        if not self.madina_activity_line_ids:
            self.makkah_activity_line_ids = generate_lines(
                self.makkah_arrival_date, self.makkah_departure_date, 'makkah'
            )
        if not self.madina_activity_line_ids:
            self.madina_activity_line_ids = generate_lines(
                self.madinah_arrival_date, self.madinah_departure_date, 'madina'
            )
        if not self.arfa_activity_line_ids:
            self.arfa_activity_line_ids = generate_lines(
                self.arfa_arrival_date, self.arfa_departure_date, 'arfa'
            )
        if not self.minah_activity_line_ids:
            self.minah_activity_line_ids = generate_lines(
                self.minnah_arrival_date, self.minnah_departure_date, 'minah'
            )
        if not self.hotel_activity_line_ids:
            self.hotel_activity_line_ids = generate_lines(
                self.hotel_arrival_date, self.hotel_departure_date, 'hotel'
            )

    def action_generate_activity_lines(self):
        for rec in self:
            rec._generate_activity_lines()

    # add constrains on check in / out

    @api.onchange('main_makkah', 'makkah_arrival_date', 'makkah_departure_date')
    def onchange_makkah_data(self):
        logger.info('onchange_makkah_data')
        self.makkah_double_plan_id = False
        self.makkah_triple_plan_id = False
        self.makkah_quad_plan_id = False
        if self.main_makkah and self.makkah_arrival_date and self.makkah_departure_date:
            available_rooms = self.get_available_rooms(self.main_makkah, self.makkah_arrival_date,
                                                       self.makkah_departure_date)
            logger.info(f'onchange_makkah_data available_rooms {available_rooms}')
            not_assigned_booking = self.env['hotel.booking'].search([
                ('state', '!=', 'cancelled'),
                ('hotel_id', '=', self.main_makkah.id),
                ('new_check_in', '<', self.makkah_departure_date),
                ('new_check_out', '>', self.makkah_arrival_date),
            ])
            logger.info(f'onchange_makkah_data not_assigned_booking {not_assigned_booking}')
            not_assigned_folio_room = not_assigned_booking.folio_ids.filtered(lambda f: not f.room_id)
            double_rooms_decrease = not_assigned_folio_room.filtered(lambda r: r.room_type_id.mini_adults == 2)
            triple_rooms_decrease = not_assigned_folio_room.filtered(lambda r: r.room_type_id.mini_adults == 3)
            quad_rooms_decrease = not_assigned_folio_room.filtered(lambda r: r.room_type_id.mini_adults == 4)
            logger.info(f'onchange_makkah_data double_rooms_decrease {double_rooms_decrease}')
            logger.info(f'onchange_makkah_data triple_rooms_decrease {triple_rooms_decrease}')
            logger.info(f'onchange_makkah_data quad_rooms_decrease {quad_rooms_decrease}')
            available_rooms = self.env['hotel.room'].browse(available_rooms)
            double_rooms = available_rooms.filtered(lambda r: r.room_type.mini_adults == 2)
            triple_rooms = available_rooms.filtered(lambda r: r.room_type.mini_adults == 3)
            quad_rooms = available_rooms.filtered(lambda r: r.room_type.mini_adults == 4)
            self.makkah_double_available = len(double_rooms) - len(double_rooms_decrease)
            self.makkah_triple_available = len(triple_rooms) - len(triple_rooms_decrease)
            self.makkah_quad_available = len(quad_rooms) - len(quad_rooms_decrease)

    @api.onchange('main_madinah', 'madinah_arrival_date', 'madinah_departure_date')
    def onchange_madinah_data(self):
        logger.info('onchange_madinah_data')
        self.madinah_double_plan_id = False
        self.madinah_triple_plan_id = False
        self.madinah_quad_plan_id = False
        if self.main_madinah and self.madinah_arrival_date and self.madinah_departure_date:
            available_rooms = self.get_available_rooms(self.main_madinah, self.madinah_arrival_date,
                                                       self.madinah_departure_date)
            available_rooms = self.env['hotel.room'].browse(available_rooms)
            print('available_roomsssss', available_rooms)
            print('available_roomsssss', len(available_rooms))
            not_assigned_booking = self.env['hotel.booking'].search([
                ('state', '!=', 'cancelled'),
                ('hotel_id', '=', self.main_madinah.id),
                ('new_check_in', '<', self.madinah_departure_date),
                ('new_check_out', '>', self.madinah_arrival_date),
            ])
            logger.info(f'onchange_madinah_data not_assigned_booking {not_assigned_booking}')
            not_assigned_folio_room = not_assigned_booking.folio_ids.filtered(lambda f: not f.room_id)
            logger.info(f'onchange_madinah_data not_assigned_folio_room {not_assigned_folio_room}')
            double_rooms_decrease = not_assigned_folio_room.filtered(lambda r: r.room_type_id.mini_adults == 2)
            triple_rooms_decrease = not_assigned_folio_room.filtered(lambda r: r.room_type_id.mini_adults == 3)
            quad_rooms_decrease = not_assigned_folio_room.filtered(lambda r: r.room_type_id.mini_adults == 4)
            logger.info(f'onchange_madinah_data double_rooms_decrease {double_rooms_decrease}')
            logger.info(f'onchange_madinah_data triple_rooms_decrease {triple_rooms_decrease}')
            logger.info(f'onchange_madinah_data quad_rooms_decrease {quad_rooms_decrease}')
            double_rooms = available_rooms.filtered(lambda r: r.room_type.mini_adults == 2)
            triple_rooms = available_rooms.filtered(lambda r: r.room_type.mini_adults == 3)
            quad_rooms = available_rooms.filtered(lambda r: r.room_type.mini_adults == 4)
            self.madinah_double_available = len(double_rooms) - len(double_rooms_decrease)
            logger.info(f'onchange_madinah_data self.madinah_double_available {self.madinah_double_available}')
            self.madinah_triple_available = len(triple_rooms) - len(triple_rooms_decrease)
            self.madinah_quad_available = len(quad_rooms) - len(quad_rooms_decrease)

    @api.depends('main_arfa', 'arfa_arrival_date', 'arfa_departure_date')
    def onchange_arfa_data(self):
        for rec in self:
            available_male_beds = 0
            available_female_beds = 0
            if rec.main_arfa and rec.arfa_arrival_date and rec.arfa_departure_date:
                print('self._origin.id', rec.id)
                record_id = rec._origin.id if rec._origin else False
                print('Record ID:', record_id)

                # Only apply the filter if the record has been saved (not a NewId object)
                domain = [('main_arfa', '=', rec.main_arfa.id),
                          ('arfa_arrival_date', '=', rec.arfa_arrival_date),
                          ('arfa_departure_date', '=', rec.arfa_departure_date)]

                if record_id:
                    domain.append(('id', '<', record_id))
                exist_package = self.env['booking.package'].sudo().search(domain)
                available_rooms = self.env['hotel.room'].sudo().search([('hotel_id', '=', rec.main_arfa.id)])
                if available_rooms:
                    available_male_rooms = available_rooms.filtered(lambda r: r.room_type.gender == 'male')
                    available_female_rooms = available_rooms.filtered(lambda r: r.room_type.gender == 'female')
                    for room in available_male_rooms:
                        available_male_beds += room.room_type.mini_adults
                    for room in available_female_rooms:
                        available_female_beds += room.room_type.mini_adults
                if exist_package:
                    available_male_beds -= sum(exist_package.mapped('arfa_male_total_beds'))
                    available_female_beds -= sum(exist_package.mapped('arfa_female_total_beds'))
            rec.arfa_male_available_beds = available_male_beds
            rec.arfa_female_available_beds = available_female_beds

    @api.depends('main_minnah', 'minnah_arrival_date', 'minnah_departure_date')
    def onchange_minnah_data(self):
        for rec in self:
            available_male_beds = 0
            available_female_beds = 0
            if rec.main_minnah and rec.minnah_arrival_date and rec.minnah_departure_date:
                print('self._origin.id', rec.id)
                record_id = rec._origin.id if rec._origin else False
                print('Record ID:', record_id)

                # Only apply the filter if the record has been saved (not a NewId object)
                domain = [('main_minnah', '=', rec.main_minnah.id),
                          ('minnah_arrival_date', '=', rec.minnah_arrival_date),
                          ('minnah_departure_date', '=', rec.minnah_departure_date)]

                if record_id:
                    domain.append(('id', '<', record_id))
                exist_package = self.env['booking.package'].sudo().search(domain)
                available_rooms = self.env['hotel.room'].sudo().search([('hotel_id', '=', rec.main_minnah.id)])
                if available_rooms:
                    available_male_rooms = available_rooms.filtered(lambda r: r.room_type.gender == 'male')
                    available_female_rooms = available_rooms.filtered(lambda r: r.room_type.gender == 'female')
                    for room in available_male_rooms:
                        available_male_beds += room.room_type.mini_adults
                    for room in available_female_rooms:
                        available_female_beds += room.room_type.mini_adults
                if exist_package:
                    available_male_beds -= sum(exist_package.mapped('minnah_male_total_beds'))
                    available_female_beds -= sum(exist_package.mapped('minnah_female_total_beds'))
            rec.minnah_male_available_beds = available_male_beds
            rec.minnah_female_available_beds = available_female_beds

    @api.onchange('main_minnah')
    def onchange_minnah_hotel(self):
        self.minnah_male_plan_id = False
        self.minnah_female_plan_id = False

    @api.onchange('main_arfa')
    def onchange_arfa_hotel(self):
        self.arfa_male_plan_id = False
        self.arfa_female_plan_id = False

    @api.onchange('main_hotel', 'hotel_arrival_date', 'hotel_departure_date')
    def onchange_hotel_data(self):
        self.hotel_double_plan_id = False
        self.hotel_triple_plan_id = False
        self.hotel_quad_plan_id = False
        if self.main_hotel and self.hotel_arrival_date and self.hotel_departure_date:
            available_rooms = self.get_available_rooms(self.main_hotel, self.hotel_arrival_date,
                                                       self.hotel_departure_date)
            not_assigned_booking = self.env['hotel.booking'].search([
                ('state', '!=', 'cancelled'),
                ('hotel_id', '=', self.main_hotel.id),
                ('new_check_in', '<', self.hotel_departure_date),
                ('new_check_out', '>', self.hotel_arrival_date),
            ])
            not_assigned_folio_room = not_assigned_booking.folio_ids.filtered(lambda f: not f.room_id)
            double_rooms_decrease = not_assigned_folio_room.filtered(lambda r: r.room_type_id.mini_adults == 2)
            triple_rooms_decrease = not_assigned_folio_room.filtered(lambda r: r.room_type_id.mini_adults == 3)
            quad_rooms_decrease = not_assigned_folio_room.filtered(lambda r: r.room_type_id.mini_adults == 4)
            available_rooms = self.env['hotel.room'].browse(available_rooms)
            double_rooms = available_rooms.filtered(lambda r: r.room_type.mini_adults == 2)
            triple_rooms = available_rooms.filtered(lambda r: r.room_type.mini_adults == 3)
            quad_rooms = available_rooms.filtered(lambda r: r.room_type.mini_adults == 4)
            self.hotel_double_available = len(double_rooms) - len(double_rooms_decrease)
            self.hotel_triple_available = len(triple_rooms) - len(triple_rooms_decrease)
            self.hotel_quad_available = len(quad_rooms) - len(quad_rooms_decrease)

    def get_available_rooms(self, hotel_id, check_in_date, check_out_date):
        available_rooms = []
        self.env.cr.execute("""
            SELECT id
            FROM hotel_room
            WHERE
                (hotel_id = %s) AND
                (
                    (out_of_order_from <= %s AND out_of_order_to > %s) OR
                    (out_of_order_from <= %s AND out_of_order_to > %s) OR
                    (out_of_order_from <= %s AND out_of_order_to > %s)
                )
        """, [hotel_id.id, check_in_date, check_in_date, check_out_date, check_out_date, check_in_date,
              check_out_date])
        out_of_order_vals = self.env.cr.dictfetchall()
        print('out_of_order_vals', out_of_order_vals)
        out_of_order_ids = [val['id'] for val in out_of_order_vals]
        if tuple(out_of_order_ids):
            self.env.cr.execute("""SELECT id FROM hotel_room WHERE hotel_id = %s AND id NOT IN %s""",
                                [hotel_id.id, tuple(out_of_order_ids)])
        else:
            self.env.cr.execute("""SELECT id FROM hotel_room WHERE hotel_id = %s""", [hotel_id.id])

        rooms_vals = self.env.cr.dictfetchall()
        print('rooms_vals', rooms_vals)
        room_ids = [val['id'] for val in rooms_vals]
        for room_id in room_ids:
            self.env.cr.execute("""
                SELECT id
                FROM booking_folio
                WHERE
                    hotel_id = %s
                    AND room_id = %s
                    AND state IN ('part_checked_in', 'checked_in', 'confirmed', 'draft')
                    AND (
                        check_in_date < %s
                        AND check_out_date > %s
                    )
            """, [
                hotel_id.id,
                room_id,
                check_out_date,  # existing.check_in < new.check_out
                check_in_date  # existing.check_out > new.check_in
            ])
            folio_vals = self.env.cr.dictfetchall()
            print('folio_vals', folio_vals)
            folio_ids = [val['id'] for val in folio_vals]
            if not folio_ids:
                available_rooms.append(room_id)
                print('available_rooms', available_rooms)
        return available_rooms

    def button_create_bookings(self):
        cities = ['makkah', 'madinah', 'hotel']
        camps = ['arfa', 'minnah']
        rooms = ['double', 'triple', 'quad']
        for city in cities:
            hotel_id = getattr(self, f'main_{city}', None)
            if hotel_id:
                hotel_booking_obj = self.booking_ids.filtered(lambda b: b.hotel_id == hotel_id)
                print('hotel_id', hotel_id)
                print('hotel_booking_obj', hotel_booking_obj)
                if not hotel_booking_obj:
                    lines = []
                    for room in rooms:
                        number_of_rooms = getattr(self, f'{city}_no_{room}', None)
                        print('number_of_rooms', number_of_rooms)
                        if number_of_rooms > 0:
                            rate_plan_id = getattr(self, f'{city}_{room}_plan_id', None)
                            lines.append((0, 0, {
                                'room_type': rate_plan_id.sudo().room_type_id.id,
                                'rate_plan': rate_plan_id.sudo().id,
                                'tax_id': rate_plan_id.sudo().tax_ids.filtered(lambda t: t.price_include).ids,
                                'price_include_tax': True,
                                'number_of_rooms': number_of_rooms,
                            }))
                    if lines:
                        new_check_in = getattr(self, f'{city}_arrival_date', None)
                        check_in = datetime.combine(new_check_in, datetime.strptime('120000', '%H%M%S').time())
                        new_check_out = getattr(self, f'{city}_departure_date', None)
                        check_out = datetime.combine(new_check_out, datetime.strptime('120000', '%H%M%S').time())
                        total_nights = check_out - check_in
                        booking_vals = {
                            'partner_id': self.partner_id.id,
                            # 'booking_source': 'online_agent',
                            # 'online_travel_agent_source': source_partner.id if partner else None,
                            'package_id': self.id,
                            'quick_group_booking': True,
                            'book_by_bed': True,
                            'guest_list': True,
                            'check_in': check_in,
                            'new_check_in': new_check_in,
                            'check_out': check_out,
                            'new_check_out': new_check_out,
                            'total_nights': total_nights.days,
                            # 'reservation_type': booking_type_objs.id,
                            'company_id': hotel_id.sudo().company_id.id,
                            'apply_daily_price': True,
                            # 'daily_price_ids': daily_prices,
                        }
                        hotel_booking_obj = self.env['hotel.booking'].sudo().create(booking_vals)
                        hotel_booking_obj.write({
                            'line_ids': lines
                        })
        for camp in camps:
            hotel_id = getattr(self, f'main_{camp}', None)
            if hotel_id:
                hotel_booking_obj = self.booking_ids.filtered(lambda b: b.hotel_id == hotel_id)
                print('hotel_id', hotel_id)
                print('hotel_booking_obj', hotel_booking_obj)
                if not hotel_booking_obj:
                    print('here empty')
                    lines = []
                    number_of_rooms = 1
                    male_booking = getattr(self, f'{camp}_male_total_beds', None)
                    female_booking = getattr(self, f'{camp}_female_total_beds', None)
                    if male_booking > 0:
                        rate_plan_id = getattr(self, f'{camp}_male_plan_id', None)
                        lines.append((0, 0, {
                            'room_type': rate_plan_id.room_type_id.id,
                            'rate_plan': rate_plan_id.id,
                            'tax_id': rate_plan_id.sudo().tax_ids.filtered(
                                lambda t: t.price_include).ids,
                            'price_include_tax': True,
                            'number_of_rooms': 1,
                            'hajj_count': getattr(self, f'{camp}_male_total_beds', None),
                        }))
                    if female_booking > 0:
                        rate_plan_id = getattr(self, f'{camp}_female_plan_id', None)
                        lines.append((0, 0, {
                            'room_type': rate_plan_id.room_type_id.id,
                            'rate_plan': rate_plan_id.id,
                            'tax_id': rate_plan_id.sudo().tax_ids.filtered(
                                lambda t: t.price_include).ids,
                            'price_include_tax': True,
                            'number_of_rooms': 1,
                            'hajj_count': getattr(self, f'{camp}_female_total_beds', None),
                        }))
                    if lines:
                        new_check_in = getattr(self, f'{camp}_arrival_date', None)
                        check_in = datetime.combine(new_check_in,
                                                    datetime.strptime('120000', '%H%M%S').time())
                        new_check_out = getattr(self, f'{camp}_departure_date', None)
                        check_out = datetime.combine(new_check_out,
                                                     datetime.strptime('120000', '%H%M%S').time())
                        total_nights = check_out - check_in
                        booking_vals = {
                            'partner_id': self.partner_id.id,
                            # 'booking_source': 'online_agent',
                            # 'online_travel_agent_source': source_partner.id if partner else None,
                            'package_id': self.id,
                            'quick_group_booking': True,
                            'book_by_bed': True,
                            'guest_list': True,
                            'check_in': check_in,
                            'new_check_in': new_check_in,
                            'check_out': check_out,
                            'new_check_out': new_check_out,
                            'total_nights': total_nights.days,
                            # 'reservation_type': booking_type_objs.id,
                            'company_id': hotel_id.company_id.id,
                            'apply_daily_price': True,
                            # 'daily_price_ids': daily_prices,
                        }
                        hotel_booking_obj = self.env['hotel.booking'].sudo().create(booking_vals)
                        hotel_booking_obj.write({
                            'line_ids': lines
                        })
        if self.booking_ids:
            self.write({'state': 'confirmed'})
            self.compute_booked_beds()




    def button_update_bookings(self):
        return {
            'name': 'Update Package',
            'type': 'ir.actions.act_window',
            'res_model': 'update.package.wizard',
            'view_mode': 'form',
            'target': 'new',  # opens in a modal dialog
            'context': {
                'default_package_id': self.id,  # optional default values
            },
        }

    # <<<<computed methods>>>>>
    # ==============================================================
    @api.depends('makkah_no_double')
    def compute_makkah_double_total_beds(self):
        for rec in self:
            rec.makkah_double_total_beds = rec.makkah_no_double * 2

    @api.depends('makka_double_male_beds')
    def compute_makkah_double_male_total_beds(self):
        for rec in self:
            rec.makkah_double_male_total_beds = rec.makka_double_male_beds * 2

    @api.depends('makka_double_female_beds')
    def compute_makkah_double_female_total_beds(self):
        for rec in self:
            rec.makkah_double_female_total_beds = rec.makka_double_female_beds * 2

    @api.depends('makkah_double_male_total_beds', 'makkah_double_male_booked_beds')
    def compute_makkah_double_male_available_beds(self):
        for rec in self:
            rec.makkah_double_male_available_beds = rec.makkah_double_male_total_beds - rec.makkah_double_male_booked_beds

    @api.depends('makkah_double_female_total_beds', 'makkah_double_female_booked_beds')
    def compute_makkah_double_female_available_beds(self):
        for rec in self:
            rec.makkah_double_female_available_beds = rec.makkah_double_female_total_beds - rec.makkah_double_female_booked_beds

    @api.depends('makka_triple_male_beds')
    def compute_makkah_triple_male_total_beds(self):
        for rec in self:
            rec.makkah_triple_male_total_beds = rec.makka_triple_male_beds * 3

    @api.depends('makka_triple_female_beds')
    def compute_makkah_triple_female_total_beds(self):
        for rec in self:
            rec.makkah_triple_female_total_beds = rec.makka_triple_female_beds * 3

    @api.depends('makkah_no_triple')
    def compute_makkah_triple_total_beds(self):
        for rec in self:
            rec.makkah_triple_total_beds = rec.makkah_no_triple * 3


    @api.depends('makkah_triple_male_total_beds', 'makkah_triple_male_booked_beds')
    def compute_makkah_triple_male_available_beds(self):
        for rec in self:
            rec.makkah_triple_male_available_beds = rec.makkah_triple_male_total_beds - rec.makkah_triple_male_booked_beds

    @api.depends('makkah_triple_female_total_beds', 'makkah_triple_female_booked_beds')
    def compute_makkah_triple_female_available_beds(self):
        for rec in self:
            rec.makkah_triple_female_available_beds = rec.makkah_triple_female_total_beds - rec.makkah_triple_female_booked_beds

    @api.depends('makkah_no_quad')
    def compute_makkah_quad_total_beds(self):
        for rec in self:
            rec.makkah_quad_total_beds = rec.makkah_no_quad * 4

    @api.depends('makka_quad_male_beds')
    def compute_makkah_quad_male_total_beds(self):
        for rec in self:
            rec.makkah_quad_male_total_beds = rec.makka_quad_male_beds * 4

    @api.depends('makka_quad_female_beds')
    def compute_makkah_quad_female_total_beds(self):
        for rec in self:
            rec.makkah_quad_female_total_beds = rec.makka_quad_female_beds * 4


    @api.depends('makkah_quad_male_total_beds', 'makkah_quad_male_booked_beds')
    def compute_makkah_quad_male_available_beds(self):
        for rec in self:
            rec.makkah_quad_male_available_beds = rec.makkah_quad_male_total_beds - rec.makkah_quad_male_booked_beds

    @api.depends('makkah_quad_female_total_beds', 'makkah_quad_female_booked_beds')
    def compute_makkah_quad_female_available_beds(self):
        for rec in self:
            rec.makkah_quad_female_available_beds = rec.makkah_quad_female_total_beds - rec.makkah_quad_female_booked_beds

    # =====================================================
    @api.depends('madinah_no_double')
    def compute_madinah_double_total_beds(self):
        for rec in self:
            rec.madinah_double_total_beds = rec.madinah_no_double * 2

    @api.depends('madinah_double_male_beds')
    def compute_madinah_double_male_total_beds(self):
        for rec in self:
            rec.madinah_double_male_total_beds = rec.madinah_double_male_beds * 2

    @api.depends('madinah_double_female_beds')
    def compute_madinah_double_female_total_beds(self):
        for rec in self:
            rec.madinah_double_female_total_beds = rec.madinah_double_female_beds * 2

    @api.depends('madinah_double_male_total_beds', 'madinah_double_male_booked_beds')
    def compute_madinah_double_male_available_beds(self):
        for rec in self:
            rec.madinah_double_male_available_beds = rec.madinah_double_male_total_beds - rec.madinah_double_male_booked_beds

    @api.depends('madinah_double_female_total_beds', 'madinah_double_female_booked_beds')
    def compute_madinah_double_female_available_beds(self):
        for rec in self:
            rec.madinah_double_female_available_beds = rec.madinah_double_female_total_beds - rec.madinah_double_female_booked_beds

    @api.depends('madinah_no_triple')
    def compute_madinah_triple_total_beds(self):
        for rec in self:
            rec.madinah_triple_total_beds = rec.madinah_no_triple * 3

    @api.depends('madinah_triple_male_beds')
    def compute_madinah_male_triple_total_beds(self):
        for rec in self:
            rec.madinah_triple_male_total_beds = rec.madinah_triple_male_beds * 3

    @api.depends('madinah_triple_female_beds')
    def compute_madinah_female_triple_total_beds(self):
        for rec in self:
            rec.madinah_triple_female_total_beds = rec.madinah_triple_female_beds * 3


    @api.depends('madinah_triple_male_total_beds', 'madinah_triple_male_booked_beds')
    def compute_madinah_triple_male_available_beds(self):
        for rec in self:
            rec.madinah_triple_male_available_beds = rec.madinah_triple_male_total_beds - rec.madinah_triple_male_booked_beds

    @api.depends('madinah_triple_female_total_beds', 'madinah_triple_female_booked_beds')
    def compute_madinah_triple_female_available_beds(self):
        for rec in self:
            rec.madinah_triple_female_available_beds = rec.madinah_triple_female_total_beds - rec.madinah_triple_female_booked_beds

    @api.depends('madinah_no_quad')
    def compute_madinah_quad_total_beds(self):
        for rec in self:
            rec.madinah_quad_total_beds = rec.madinah_no_quad * 4

    @api.depends('madinah_quad_male_beds')
    def compute_madinah_quad_male_total_beds(self):
        for rec in self:
            rec.madinah_quad_male_total_beds = rec.madinah_quad_male_beds * 4

    @api.depends('madinah_quad_female_beds')
    def compute_madinah_quad_female_total_beds(self):
        for rec in self:
            rec.madinah_quad_female_total_beds = rec.madinah_quad_female_beds * 4

    @api.depends('madinah_quad_male_total_beds', 'madinah_quad_male_booked_beds')
    def compute_madinah_quad_male_available_beds(self):
        for rec in self:
            rec.madinah_quad_male_available_beds = rec.madinah_quad_male_total_beds - rec.madinah_quad_male_booked_beds

    @api.depends('madinah_quad_female_total_beds', 'madinah_quad_female_booked_beds')
    def compute_madinah_quad_female_available_beds(self):
        for rec in self:
            rec.madinah_quad_female_available_beds = rec.madinah_quad_female_total_beds - rec.madinah_quad_female_booked_beds

    # =====================================================

    @api.depends('arfa_male_total_beds', 'arfa_male_booked_beds')
    def compute_arfa_male_unbooked_beds(self):
        for rec in self:
            rec.arfa_male_unbooked_beds = rec.arfa_male_total_beds - rec.arfa_male_booked_beds

    @api.depends('arfa_female_total_beds', 'arfa_female_booked_beds')
    def compute_arfa_female_unbooked_beds(self):
        for rec in self:
            rec.arfa_female_unbooked_beds = rec.arfa_female_total_beds - rec.arfa_female_booked_beds
    # =====================================================


    @api.depends('minnah_male_total_beds', 'minnah_male_booked_beds')
    def compute_minnah_male_unbooked_beds(self):
        for rec in self:
            rec.minnah_male_unbooked_beds = rec.minnah_male_total_beds - rec.minnah_male_booked_beds

    @api.depends('minnah_female_total_beds', 'minnah_female_booked_beds')
    def compute_minnah_female_unbooked_beds(self):
        for rec in self:
            rec.minnah_female_unbooked_beds = rec.minnah_female_total_beds - rec.minnah_female_booked_beds

    # =====================================================

    @api.depends('hotel_no_double')
    def compute_hotel_double_total_beds(self):
        for rec in self:
            rec.hotel_double_total_beds = rec.hotel_no_double * 2

    @api.depends('hotel_double_male_beds')
    def compute_hotel_double_male_total_beds(self):
        for rec in self:
            rec.hotel_double_male_total_beds = rec.hotel_double_male_beds * 2

    @api.depends('hotel_double_female_beds')
    def compute_hotel_double_female_total_beds(self):
        for rec in self:
            rec.hotel_double_female_total_beds = rec.hotel_double_female_beds * 2

    @api.depends('hotel_double_female_total_beds', 'hotel_double_female_booked_beds')
    def compute_hotel_double_female_available_beds(self):
        for rec in self:
            rec.hotel_double_female_available_beds = rec.hotel_double_female_total_beds - rec.hotel_double_female_booked_beds

    @api.depends('hotel_double_male_total_beds', 'hotel_double_male_booked_beds')
    def compute_hotel_double_male_available_beds(self):
        for rec in self:
            rec.hotel_double_male_available_beds = rec.hotel_double_male_total_beds - rec.hotel_double_male_booked_beds

    @api.depends('hotel_no_triple')
    def compute_hotel_triple_total_beds(self):
        for rec in self:
            rec.hotel_triple_total_beds = rec.hotel_no_triple * 3

    @api.depends('hotel_triple_male_beds')
    def compute_hotel_triple_male_total_beds(self):
        for rec in self:
            rec.hotel_triple_male_total_beds = rec.hotel_triple_male_beds * 3

    @api.depends('hotel_triple_female_beds')
    def compute_hotel_triple_female_total_beds(self):
        for rec in self:
            rec.hotel_triple_female_total_beds = rec.hotel_triple_female_beds * 3

    @api.depends('hotel_triple_female_total_beds', 'hotel_triple_female_booked_beds')
    def compute_hotel_triple_female_available_beds(self):
        for rec in self:
            rec.hotel_triple_female_available_beds = rec.hotel_triple_female_total_beds - rec.hotel_triple_female_booked_beds

    @api.depends('hotel_triple_male_total_beds', 'hotel_triple_male_booked_beds')
    def compute_hotel_triple_male_available_beds(self):
        for rec in self:
            rec.hotel_triple_male_available_beds = rec.hotel_triple_male_total_beds - rec.hotel_triple_male_booked_beds

    @api.depends('hotel_no_quad')
    def compute_hotel_quad_total_beds(self):
        for rec in self:
            rec.hotel_quad_total_beds = rec.hotel_no_quad * 4

    @api.depends('hotel_quad_male_beds')
    def compute_hotel_quad_male_total_beds(self):
        for rec in self:
            rec.hotel_quad_male_total_beds = rec.hotel_quad_male_beds * 4

    @api.depends('hotel_quad_female_beds')
    def compute_hotel_quad_female_total_beds(self):
        for rec in self:
            rec.hotel_quad_female_total_beds = rec.hotel_quad_female_beds * 4

    @api.depends('hotel_quad_female_total_beds', 'hotel_quad_female_booked_beds')
    def compute_hotel_quad_female_available_beds(self):
        for rec in self:
            rec.hotel_quad_female_available_beds = rec.hotel_quad_female_total_beds - rec.hotel_quad_female_booked_beds

    @api.depends('hotel_quad_male_total_beds', 'hotel_quad_male_booked_beds')
    def compute_hotel_quad_male_available_beds(self):
        for rec in self:
            rec.hotel_quad_male_available_beds = rec.hotel_quad_male_total_beds - rec.hotel_quad_male_booked_beds

    # =====================================================
    # constrains

    @api.constrains('makkah_arrival_date', 'makkah_departure_date', 'makkah_date_from', 'makkah_date_to')
    def check_makkah_dates(self):
        for rec in self:
            if rec.makkah_departure_date and rec.makkah_arrival_date:
                if rec.makkah_departure_date < rec.makkah_arrival_date:
                    raise ValidationError(_('Makkah departure date cannot be earlier than arrival date!'))
            if rec.makkah_contract_id:
                if not (rec.makkah_date_from <= rec.makkah_arrival_date <= rec.makkah_date_to):
                    raise ValidationError(_(
                        "Makkah Arrival Date Must Be Between Contract Start Date And End Date"))
                if not (rec.makkah_date_from <= rec.makkah_departure_date <= rec.makkah_date_to):
                    raise ValidationError(_(
                        "Makkah Departure Date Must Be Between Contract Start Date And End Date"))

    @api.constrains('madinah_arrival_date', 'madinah_departure_date', 'madinah_date_from','madinah_date_to')
    def check_madinah_dates(self):
        for rec in self:
            if rec.madinah_departure_date and rec.madinah_arrival_date:
                if rec.madinah_departure_date < rec.madinah_arrival_date:
                    raise ValidationError(_('Madinah departure date cannot be earlier than arrival date!'))
            if rec.madinah_contract_id:
                if not (rec.madinah_date_from <= rec.madinah_arrival_date <= rec.madinah_date_to):
                    raise ValidationError(_(
                        "Madinah Arrival Date Must Be Between Contract Start Date And End Date"))
                if not (rec.madinah_date_from <= rec.madinah_departure_date <= rec.madinah_date_to):
                    raise ValidationError(_(
                        "Madinah Departure Date Must Be Between Contract Start Date And End Date"))

    @api.constrains('arfa_arrival_date', 'arfa_departure_date')
    def check_arfa_dates(self):
        for rec in self:
            if rec.arfa_departure_date and rec.arfa_arrival_date:
                if rec.arfa_departure_date < rec.arfa_arrival_date:
                    raise ValidationError(_('Arfa departure date cannot be earlier than arrival date!'))

    @api.constrains('minnah_arrival_date', 'minnah_departure_date')
    def check_minnah_dates(self):
        for rec in self:
            if rec.minnah_departure_date and rec.minnah_arrival_date:
                if rec.minnah_departure_date < rec.minnah_arrival_date:
                    raise ValidationError(_('Minnah departure date cannot be earlier than arrival date!'))

    @api.constrains('hotel_arrival_date', 'hotel_departure_date', 'main_hotel_date_from', 'main_hotel_date_to')
    def check_hotel_dates(self):
        for rec in self:
            if rec.hotel_departure_date and rec.hotel_arrival_date:
                if rec.hotel_departure_date < rec.hotel_arrival_date:
                    raise ValidationError(_('Main shift departure date cannot be earlier than arrival date!'))
            if rec.main_hotel_contract_id:
                if not (rec.main_hotel_date_from <= rec.hotel_arrival_date <= rec.main_hotel_date_to):
                    raise ValidationError(_(
                        "Main Shift Arrival Date Must Be Between Contract Start Date And End Date"))
                if not (rec.main_hotel_date_from <= rec.hotel_departure_date <= rec.main_hotel_date_to):
                    raise ValidationError(_(
                        "Main Shift Departure Date Must Be Between Contract Start Date And End Date"))

    @api.constrains('makkah_double_available', 'makkah_no_double')
    def check_makkah_double(self):
        for rec in self:
            if rec.makkah_double_available and rec.makkah_no_double:
                if rec.makkah_double_available < rec.makkah_no_double:
                    raise ValidationError(_('Makkah double rooms cannot be more than available rooms!'))

    @api.constrains('makkah_triple_available', 'makkah_no_triple')
    def check_makkah_triple(self):
        for rec in self:
            if rec.makkah_triple_available and rec.makkah_no_triple:
                if rec.makkah_triple_available < rec.makkah_no_triple:
                    raise ValidationError(_('Makkah triple rooms cannot be more than available rooms!'))

    @api.constrains('makkah_quad_available', 'makkah_no_quad')
    def check_makkah_quad(self):
        for rec in self:
            if rec.makkah_quad_available and rec.makkah_no_quad:
                if rec.makkah_quad_available < rec.makkah_no_quad:
                    raise ValidationError(_('Makkah quad rooms cannot be more than available rooms!'))

    @api.constrains('madinah_double_available', 'madinah_no_double')
    def check_madinah_double(self):
        for rec in self:
            if rec.madinah_double_available and rec.madinah_no_double:
                if rec.madinah_double_available < rec.madinah_no_double:
                    raise ValidationError(_('Madinah double rooms cannot be more than available rooms!'))

    @api.constrains('madinah_triple_available', 'madinah_no_triple')
    def check_madinah_triple(self):
        for rec in self:
            if rec.madinah_triple_available and rec.madinah_no_triple:
                if rec.madinah_triple_available < rec.madinah_no_triple:
                    raise ValidationError(_('Madinah triple rooms cannot be more than available rooms!'))

    @api.constrains('madinah_quad_available', 'madinah_no_quad')
    def check_madinah_quad(self):
        for rec in self:
            if rec.madinah_quad_available and rec.madinah_no_quad:
                if rec.madinah_quad_available < rec.madinah_no_quad:
                    raise ValidationError(_('Madinah quad rooms cannot be more than available rooms!'))



    @api.constrains('hotel_double_available', 'hotel_no_double')
    def check_hotel_double(self):
        for rec in self:
            if rec.hotel_double_available and rec.hotel_no_double:
                if rec.hotel_double_available < rec.hotel_no_double:
                    raise ValidationError(_('Main shift double rooms cannot be more than available rooms!'))

    @api.constrains('hotel_triple_available', 'hotel_no_triple')
    def check_hotel_triple(self):
        for rec in self:
            if rec.hotel_triple_available and rec.hotel_no_triple:
                if rec.hotel_triple_available < rec.hotel_no_triple:
                    raise ValidationError(_('Main shift triple rooms cannot be more than available rooms!'))

    @api.constrains('hotel_quad_available', 'hotel_no_quad')
    def check_hotel_quad(self):
        for rec in self:
            if rec.hotel_quad_available and rec.hotel_no_quad:
                if rec.hotel_quad_available < rec.hotel_no_quad:
                    raise ValidationError(_('Main shift quad rooms cannot be more than available rooms!'))


    @api.constrains('arfa_male_available_beds', 'arfa_male_total_beds')
    def check_arfa_male(self):
        for rec in self:
            if rec.arfa_male_available_beds and rec.arfa_male_total_beds:
                if rec.arfa_male_available_beds < rec.arfa_male_total_beds:
                    raise ValidationError(_('Booking Arfa male beds cannot be more than available beds!'))

    @api.constrains('arfa_female_available_beds', 'arfa_female_total_beds')
    def check_arfa_female(self):
        for rec in self:
            if rec.arfa_female_available_beds and rec.arfa_female_total_beds:
                if rec.arfa_female_available_beds < rec.arfa_female_total_beds:
                    raise ValidationError(_('Booking Arfa female beds cannot be more than available beds!'))


    @api.constrains('minnah_male_available_beds', 'minnah_male_total_beds')
    def check_minnah_male(self):
        for rec in self:
            if rec.minnah_male_available_beds and rec.minnah_male_total_beds:
                if rec.minnah_male_available_beds < rec.minnah_male_total_beds:
                    raise ValidationError(_('Booking Minnah male beds cannot be more than available beds!'))

    @api.constrains('minnah_female_available_beds', 'minnah_female_total_beds')
    def check_minnah_female(self):
        for rec in self:
            if rec.minnah_female_available_beds and rec.minnah_female_total_beds:
                if rec.minnah_female_available_beds < rec.minnah_female_total_beds:
                    raise ValidationError(_('Booking Minnah female beds cannot be more than available beds!'))

    @api.depends('booking_ids')
    def compute_booking_count(self):
        for rec in self:
            rec.booking_count = len(self.booking_ids or [])

    @api.depends('partner_ids')
    def compute_partner_count(self):
        for rec in self:
            rec.partner_count = len(self.partner_ids or [])

    def action_view_bookings(self):
        return {
            'name': _('Bookings'),
            'view_mode': 'tree,form',
            'res_model': 'hotel.booking',
            'type': 'ir.actions.act_window',
            'domain': [('package_id', '=', self.id)],
        }

    def action_view_pilgrims(self):
        return {
            'name': _('Pilgrims'),
            'view_mode': 'tree,form',
            'res_model': 'res.partner',
            'type': 'ir.actions.act_window',
            'domain': [('package_id', '=', self.id)],
        }

    def _compute_access_url(self):
        super(BookingPackage, self)._compute_access_url()
        for rec in self:
            rec.access_url = '/my/package/%s' % (rec.id)
