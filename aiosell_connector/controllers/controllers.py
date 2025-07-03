import json
import pytz
from odoo import http, api, fields
from odoo.http import request
from datetime import datetime


class AiosellController(http.Controller):

    @http.route('/update_reservation', auth='none', csrf=False, type='json', methods=['POST'])
    def update_reservation(self):
        args = request.httprequest.data.decode()
        args = json.loads(args)
        required_fields = ['action', 'hotelCode', 'bookingId']
        for field in required_fields:
            if not args.get(field, False):
                return {
                    "status": 403,
                    "message": "Missing Data",
                    "response": {
                        "message": f"{field} is missing!",
                    }
                }
        company = request.env['res.company'].sudo().search([
            ('enable_aiosell', '=', True), ('aiosell_code', '=', args["hotelCode"])
        ])
        if not company:
            return {
                "status": 403,
                "message": "Invalid Hotel Code",
                "response": {
                    "message": "Invalid Hotel Code!",
                }
            }
        if args['action'] == 'book':
            booking_id = self.create_booking(args, company)
            return {
                "status": 200,
                "message": "Booking Created Successfully",
                "response": {
                    "message": f"Booking {booking_id.sudo().name} has been created successfully!",
                }
            }
        elif args['action'] == 'modify':
            booking_id = request.env['hotel.booking'].sudo().search([
                ('aiosell_booking_ref', '=', args['bookingId']), ('state', '!=', 'cancelled')
            ])
            self.update_booking(args, company, booking_id)
            return {
                "status": 200,
                "message": "Booking Updated Successfully",
                "response": {
                    "message": f"Booking {booking_id.sudo().name} has been updated successfully!",
                }
            }
        else:
            booking_id = request.env['hotel.booking'].sudo().search([
                ('aiosell_booking_ref', '=', args['bookingId']), ('state', '!=', 'cancelled')
            ])
            if booking_id:
                if company.apply_ntmp:
                    reason = request.env.ref('ntmp_connector.ntmp_cancel_reason_0')
                    wizard = request.env['folio.cancel'].sudo().create({
                        'booking_id': booking_id.id,
                        'reason_id': reason.id,
                        'cancel_with_charge': '0'
                    })
                    wizard.sudo().button_cancel_folio()
                else:
                    booking_id.sudo().button_cancel()
                return {
                    "status": 200,
                    "message": "Booking Cancelled Successfully",
                    "response": {
                        "message": f"Booking {booking_id.sudo().name} has been cancelled successfully!",
                    }
                }
            else:
                return {
                    "status": 403,
                    "message": "Invalid Booking Number",
                    "response": {
                        "message": "Invalid Booking Number!",
                    }
                }

    def create_booking(self, args, company):
        required_fields = ['action', 'hotelCode', 'checkin', 'checkout', 'guest', 'rooms', 'amount']
        for field in required_fields:
            if not args.get(field, False):
                return {
                    "status": 403,
                    "message": "Missing Data",
                    "response": {
                        "message": f"{field} is missing!",
                    }
                }
        hotel = company.related_hotel_id
        partner_id = self.create_or_get_partner_id(args['guest'], company)
        checkin = fields.Date.to_date(args['checkin'])
        checkin = datetime.combine(checkin, datetime.strptime('000000', '%H%M%S').time())
        checkout = fields.Date.to_date(args['checkout'])
        checkout = datetime.combine(checkout, datetime.strptime('000000', '%H%M%S').time())
        delta = (checkout - checkin).days
        total_nights = delta if delta > 0 else 0
        daily_price_ids = self.prepare_daily_price_ids(args['rooms'], company)
        lines = self.prepare_booking_lines(args['rooms'], company)

        booking_id = request.env['hotel.booking'].sudo().with_company(company).create({
            'company_id': company.id,
            'hotel_id': hotel.id,
            'aiosell_channel': args.get('channel', False),
            'aiosell_booking_ref': args.get('bookingId', False),
            'aiosell_cm_booking_ref': args.get('cmBookingId', False),
            'aiosell_booking_date': args.get('bookedOn', False),
            'check_in': checkin,
            'check_out': checkout,
            'total_nights': total_nights,
            'aiosell_segment': args.get('segment', False),
            'note': args.get('specialRequests', False),
            'aiosell_pah': args.get('pah', False),
            'booking_source': 'online_agent',
            'online_travel_agent_source': company.related_hotel_id.aiosell_partner_id.id or False,
            'ref': args.get('bookingId', False),
            'reservation_type': request.env['booking.type'].sudo().search([], limit=1).id,
            'partner_id': partner_id,
            'aiosell_apply_daily_price': True,
            'daily_price_ids': daily_price_ids,
        })
        # remove duplicated booking daily price
        for daily_price in booking_id.daily_price_ids:
            duplicates = booking_id.daily_price_ids.filtered(
                lambda p: p.rate_plan_id.id == daily_price.rate_plan_id.id and p.date == daily_price.date and p.id != daily_price.id
            )
            if duplicates:
                daily_price.unlink()

        booking_id.write({
            'line_ids': lines
        })
        for folio in booking_id.folio_ids:
            folio.write({
                'partner_id': booking_id.partner_id.id
            })
            folio.button_confirm()
        return booking_id

    def update_booking(self, args, company, booking_id):
        if args.get('guest', False):
            partner_id = self.create_or_get_partner_id(args['guest'], company)
        else:
            partner_id = booking_id.partner_id
        if args.get('checkin', False):
            checkin = fields.Date.to_date(args['checkin'])
            checkin = datetime.combine(checkin, datetime.strptime('000000', '%H%M%S').time())
        else:
            checkin = booking_id.check_in
        if args.get('checkout', False):
            checkout = fields.Date.to_date(args['checkout'])
            checkout = datetime.combine(checkout, datetime.strptime('000000', '%H%M%S').time())
        else:
            checkout = booking_id.check_out
        if args.get('checkout', False) or args.get('checkin', False):
            delta = (checkout - checkin).days
            total_nights = delta if delta > 0 else 0
        else:
            total_nights = booking_id.total_nights

        if args.get('rooms', False):
            booking_id.line_ids.sudo().unlink()
            lines = self.prepare_booking_lines(args['rooms'], company)
        else:
            lines = booking_id.line_ids

        booking_id.sudo().with_company(company).write({
            'company_id': company.id,
            'hotel_id': company.related_hotel_id.id,
            'aiosell_channel': args.get('channel', booking_id.aiosell_channel),
            'aiosell_booking_ref': args.get('bookingId', booking_id.aiosell_booking_ref),
            'aiosell_cm_booking_ref': args.get('cmBookingId', booking_id.aiosell_cm_booking_ref),
            'check_in': checkin,
            'check_out': checkout,
            'total_nights': total_nights,
            'aiosell_segment': args.get('segment', booking_id.aiosell_segment),
            'note': args.get('specialRequests', booking_id.note),
            'aiosell_pah': args.get('pah', booking_id.aiosell_pah),
            'partner_id': partner_id,
            'line_ids': lines
        })
        return booking_id

    def create_or_get_partner_id(self, guest_dict, company):
        domain = []
        name = False
        if guest_dict.get('firstName', False):
            name = guest_dict['firstName']
            if guest_dict.get('lastName', False):
                name += ' '
                name += guest_dict['lastName']
            domain.append(('name', '=', name))
        if guest_dict.get('email', False):
            domain.append(('email', '=', guest_dict['email']))
        if guest_dict.get('phone', False):
            domain.append(('phone', '=', guest_dict['phone']))
        partner = request.env['res.partner'].sudo().search(domain)
        if not partner:
            country = False
            state = False
            street = False
            city = False
            zip = False
            if guest_dict.get('address', False):
                address_dict = guest_dict['address']
                if address_dict.get('country', False):
                    street = address_dict.get('line1', False)
                    city = address_dict.get('city', False)
                    zip = address_dict.get('zipCode', False)
                    country = request.env['res.country'].sudo().search([('name', '=', address_dict['country'])]).id
                    if country and address_dict.get('state', False):
                        state = request.env['res.country.state'].sudo().search([
                            ('country_id', '=', country), ('name', '=', address_dict['state'])
                        ], limit=1).id
            partner = request.env['res.partner'].with_company(company).sudo().create({
                'name': name,
                'email': guest_dict.get('email', False),
                'phone': guest_dict.get('phone', False),
                'company_id': company.id,
                'street': street,
                'city': city,
                'zip': zip,
                'country_id': country,
                'state_id': state,
            })
        if partner.sudo():
            return partner.sudo().id
        else:
            return False

    def get_rate_plan_room_type(self, room_dict, company):
        required_fields = ['roomCode', 'rateplanCode', 'occupancy', 'prices']
        for field in required_fields:
            if not room_dict.get(field, False):
                return {
                    "status": 403,
                    "message": "Room Missing Data",
                    "response": {
                        "message": f"Room {field} is missing!",
                    }
                }
        room_type = request.env['room.type'].sudo().search([
            ('company_id', '=', company.id), ('aiosell_code', '=', room_dict['roomCode'])
        ])
        if not room_type:
            return {
                "status": 403,
                "message": "Invalid Room Code",
                "response": {
                    "message": f"Room Code {room_dict['roomCode']} is invalid!",
                }
            }

        rate_plan = request.env['hotel.rate.plan'].sudo().search([
            ('company_id', '=', company.id), ('aiosell_code', '=', room_dict['rateplanCode'])
        ])
        if not rate_plan:
            return {
                "status": 403,
                "message": "Invalid Rate Plan",
                "response": {
                    "message": f"Rate Plan Code {room_dict['rateplanCode']} is invalid!",
                }
            }
        return {
            'room_type': room_type,
            'rate_plan': rate_plan,
        }

    def prepare_booking_lines(self, rooms, company):
        vals = []
        for room_dict in rooms:
            data = self.get_rate_plan_room_type(room_dict, company)
            room_type = data.get('room_type', False)
            rate_plan = data.get('rate_plan', False)
            if room_type and rate_plan:
                vals.append((0, 0, {
                    'company_id': company.id,
                    'hotel_id': company.related_hotel_id.id,
                    'room_type': room_type.id,
                    'rate_plan': rate_plan.id,
                    'number_of_rooms': 1,
                    'tax_id': rate_plan.sudo().tax_ids.filtered(lambda t: t.price_include).ids,
                    'price_include_tax': False
                }))
        return vals

    def prepare_daily_price_ids(self, rooms, company):
        vals = []
        for room_dict in rooms:
            data = self.get_rate_plan_room_type(room_dict, company)
            room_type = data.get('room_type', False)
            rate_plan = data.get('rate_plan', False)
            if room_type and rate_plan:
                for price_dict in room_dict['prices']:
                    vals.append((0, 0, {
                        'rate_plan_id': rate_plan.id,
                        'room_type_id': room_type.id,
                        'price': price_dict.get('sellRate', False),
                        'date': price_dict.get('date', False),
                    }))
        return vals
