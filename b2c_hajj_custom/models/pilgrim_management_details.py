from odoo import fields, models, api, _
from datetime import datetime, time
from odoo.exceptions import ValidationError
import logging
logger = logging.getLogger(__name__)


class PilgrimManagementDetails(models.Model):
    _name = 'pilgrim.management.details'
    _inherit = ["mail.thread", 'portal.mixin']
    _rec_name = 'create_date'

    hotel_type = fields.Selection(string="Hotel Type", selection=[
        ('makkah', 'Makkah'), ('madinah', 'Madinah'), ('arfa', 'Arfa'),
        ('minnah', 'Minnah'), ('hotel', 'Main Shift')
    ])
    hotel_id = fields.Many2one("hotel.hotel", string='Hotel', domain="[('type', '=', hotel_type)]")
    partner_id = fields.Many2one('res.partner', domain="[('package_id', '!=', False), ('pilgrim_type', '=', 'main')]")
    airport = fields.Char("Airport")
    arrival_airport_id = fields.Many2one('airport.management', "Airport")
    departure_airport_id = fields.Many2one('airport.management', "Airport")
    arrival_flight_date = fields.Date("Flight Date")
    departure_flight_date = fields.Date("Flight Date")
    flight_contract_id = fields.Many2one('flight.schedule', string="Flight Contract")
    arrival_flight_no = fields.Char("Flight Number")
    departure_flight_no = fields.Char("Flight Number")
    arrival_hall_no = fields.Char("Hall No.")
    departure_hall_no = fields.Char("Hall No.")
    pilgrims_no = fields.Integer("Pilgrims No.")
    hotel_arrival_date_from = fields.Date("Date From")
    hotel_arrival_date_to = fields.Date("Date To")
    hotel_dep_date_from = fields.Date("Date From")
    hotel_dep_date_to = fields.Date("Date To")
    package_id = fields.Many2one('booking.package')
    flight_schedule_id = fields.Many2one('flight.schedule')
    transportation_contract_ids = fields.Many2many('transportation.contract')
    pilgrim_type = fields.Selection(selection=[('main', 'Main'), ('member', 'Family Member')])
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
    ], string="Gender")
    line_ids = fields.One2many(comodel_name="pilgrim.management.line", inverse_name="pilgrim_management_id")

    def print_pdf(self):
        return self.env.ref('b2c_hajj_custom.action_pilgrim_management_report').with_context(
            landscape=True).report_action(self)

    @api.constrains('hotel_dep_date_from', 'hotel_dep_date_to')
    def check_dep_date(self):
        if self.hotel_dep_date_to and self.hotel_dep_date_from:
            if self.hotel_dep_date_to < self.hotel_dep_date_from:
                raise ValidationError(_('Hotel Departure Date To Must be Greater than From'))

    @api.constrains('hotel_arrival_date_from', 'hotel_arrival_date_to')
    def check_arrival_date(self):
        if self.hotel_arrival_date_to and self.hotel_arrival_date_from:
            if self.hotel_arrival_date_to < self.hotel_arrival_date_from:
                raise ValidationError(_('Hotel Arrival Date To Must be Greater than From'))

    def button_search(self):
        self.line_ids = [(5, 0, 0)]
        domain = []
        if self.hotel_type:
            field_name = f'main_{self.hotel_type}'
            domain = [(field_name, '!=', False)]
            if self.hotel_id:
                hotel_id = self.hotel_id.id
                domain = [(field_name, '=', hotel_id)]
            field_arrival = f'{self.hotel_type}_arrival_date'
            field_departure = f'{self.hotel_type}_departure_date'
            if self.hotel_arrival_date_from:
                domain.append((field_arrival, '>=', self.hotel_arrival_date_from))
            if self.hotel_arrival_date_to:
                domain.append((field_arrival, '<=', self.hotel_arrival_date_to))
            if self.hotel_dep_date_from:
                domain.append((field_departure, '>=', self.hotel_dep_date_from))
            if self.hotel_dep_date_to:
                domain.append((field_departure, '<=', self.hotel_dep_date_to))
        else:
            if self.hotel_id:
                hotel_id = self.hotel_id.id
                domain = [
                    '|', '|', '|', '|',
                    ('main_makkah', '=', hotel_id),
                    ('main_madinah', '=', hotel_id),
                    ('main_arfa', '=', hotel_id),
                    ('main_minnah', '=', hotel_id),
                    ('main_hotel', '=', hotel_id),
                ]
        if self.flight_contract_id:
            domain.append(('flight_schedule_id', '=', self.flight_contract_id.id))
        if self.pilgrims_no:
            domain.append(('flight_schedule_id.pilgrims_no', '=', self.pilgrims_no))
        if self.arrival_flight_no:
            domain.append(('flight_schedule_id.arrival_flight_no', '=', self.arrival_flight_no))
        if self.departure_flight_no:
            domain.append(('flight_schedule_id.departure_flight_no', '=', self.departure_flight_no))
        if self.arrival_airport_id:
            domain.append(('arrival_airport_id', '=', self.arrival_airport_id.id))
        if self.arrival_flight_date:
            date_value = self.arrival_flight_date
            start_datetime = datetime.combine(date_value, time.min)
            end_datetime = datetime.combine(date_value, time.max)
            domain.append(('flight_arrival_date', '>=', start_datetime))
            domain.append(('flight_arrival_date', '<=', end_datetime))
        if self.arrival_hall_no:
            domain.append(('flight_schedule_id.arrival_hall_no', 'ilike', self.arrival_hall_no))
        if self.departure_airport_id:
            domain.append(('dep_airport_id', '=', self.departure_airport_id.id))
        if self.departure_flight_date:
            date_value = self.departure_flight_date
            start_datetime = datetime.combine(date_value, time.min)
            end_datetime = datetime.combine(date_value, time.max)
            domain.append(('flight_departure_date', '>=', start_datetime))
            domain.append(('flight_departure_date', '<=', end_datetime))
        if self.departure_hall_no:
            domain.append(('flight_schedule_id.departure_hall_no', 'ilike', self.departure_hall_no))

        if self.package_id:
            domain.append(('package_id', '=', self.package_id.id))
        if self.pilgrim_type:
            domain.append(('pilgrim_type', '=', self.pilgrim_type))
        if self.gender:
            domain.append(('gender', '=', self.gender))
        if domain:
            logger.info(f'domainnn {domain}')
            res_partner_obj = self.env['res.partner'].sudo().search(domain)
        else:
            res_partner_obj = False

        if res_partner_obj:
            lines = []
            for partner in res_partner_obj:
                lines.append((0, 0, {
                    'partner_id': partner.id,
                    'pilgrim_type': partner.pilgrim_type,
                    'gender': partner.gender,
                    'package_id': partner.package_id.id,
                    'region': partner.region,
                    'language': partner.language.id,
                    'main_member_id': partner.main_member_id.id,
                    'flight_schedule_id': partner.flight_schedule_id.id,
                    'flight_arrival_date': partner.flight_arrival_date,
                    'departure_flight_no': partner.departure_flight_no,
                    'arrival_flight_no': partner.arrival_flight_no,
                    'arrival_airport_id': partner.arrival_airport_id.id,
                    'flight_departure_date': partner.flight_departure_date,
                    'dep_airport_id': partner.dep_airport_id.id,
                    'residence_country': partner.residence_country,
                    'nationality': partner.nationality,
                    'visa_status': partner.visa_status,
                    'ticket_link': partner.ticket_link,
                    "transportation_contract_ids": partner.transportation_contract_ids.ids,
                    "main_makkah": partner.main_makkah.id,
                    "main_madinah": partner.main_madinah.id,
                    "main_arfa": partner.main_arfa.id,
                    "main_minnah": partner.main_minnah.id,
                    "main_hotel": partner.main_hotel.id,
                    "hajj_source": partner.hajj_source,
                    "passport_no": partner.passport_no,
                    "makkah_contract_id": partner.package_id.makkah_contract_id.id if partner.package_id else False,
                    "madinah_contract_id": partner.package_id.madinah_contract_id.id if partner.package_id else False,
                    "main_hotel_contract_id": partner.package_id.main_hotel_contract_id.id if partner.package_id else False,

                }))
            self.line_ids = lines

    def print_xlsx(self):
        return self.env.ref('b2c_hajj_custom.action_report_pilgrim_management_excel').report_action(self)


class PilgrimManagementLine(models.Model):
    _name = 'pilgrim.management.line'

    pilgrim_management_id = fields.Many2one('pilgrim.management.details')
    partner_id = fields.Many2one('res.partner', string='Name')
    hall_no = fields.Char("Hall No.")
    package_id = fields.Many2one('booking.package')
    pilgrim_type = fields.Selection(selection=[('main', 'Main'), ('member', 'Family Member')])
    transportation_contract_ids = fields.Many2many('transportation.contract', string="Transportation Contracts")
    flight_schedule_id = fields.Many2one('flight.schedule')
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
    ], string="Gender")
    region = fields.Selection(string="Region", selection=[('sunni', 'Sunni'), ('shiite', 'Shiite'), ], required=False)
    language = fields.Many2one('res.lang', string="Language")
    main_member_id = fields.Many2one('res.partner')
    flight_arrival_date = fields.Datetime("Arrival Flight Date")
    arrival_flight_no = fields.Char(string="Arrival Flight Number")
    departure_flight_no = fields.Char(string="Departure Flight Number")
    arrival_airport_id = fields.Many2one('airport.management')
    flight_departure_date = fields.Datetime("Departure Flight Date")
    dep_airport_id = fields.Many2one('airport.management')
    hajj_source = fields.Selection(selection=[('B2B', 'B2B'), ('B2C', 'B2C'), ('B2G', 'B2G')], string="Source")
    residence_country = fields.Char()
    nationality = fields.Char()
    visa_status = fields.Char(string='Visa Status')
    ticket_link = fields.Char(string='Ticket Link')
    main_makkah = fields.Many2one('hotel.hotel', string="Makkah Hotel")
    main_madinah = fields.Many2one('hotel.hotel', string="Madinah Hotel")
    main_arfa = fields.Many2one('hotel.hotel', string="Arfa Hotel")
    main_minnah = fields.Many2one('hotel.hotel', string="Minnah Hotel")
    main_hotel = fields.Many2one('hotel.hotel', string="Main Shift Hotel")
    passport_no = fields.Char()
    makkah_contract_id = fields.Many2one('hotel.contract.management', string="Makkah Contract")
    madinah_contract_id = fields.Many2one('hotel.contract.management', string="Madinah Contract")
    main_hotel_contract_id = fields.Many2one('hotel.contract.management', string="Main Shift Contract")
