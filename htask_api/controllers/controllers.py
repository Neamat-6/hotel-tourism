import base64
import json
from datetime import datetime

import requests

from odoo import http, fields
from odoo.exceptions import _logger
from odoo.http import request
from odoo.tools.image import image_data_uri


class HtaskApi(http.Controller):

    def get_uid(self, headers):
        uid = False
        if headers:
            if headers.get('HTTP_AUTHORIZATION', False):
                lst = headers['HTTP_AUTHORIZATION'].split(" ")
                if len(lst) == 2:
                    binary_data = base64.b64decode(lst[1])
                    str_data = binary_data.decode('utf-8')
                    if str_data:
                        credentials = str_data.split(":")
                        if len(credentials) == 2:
                            username = credentials[0]
                            password = credentials[1]
                            try:
                                request.session.authenticate(request.cr.dbname, username, password)
                            except Exception:
                                return uid
                            uid = request.session.uid
                            if not uid:
                                return uid
        return uid

    @http.route('/api/hotel/info', auth='none', website=False, csrf=False, type='http', methods=['GET'])
    def get_hotel_info(self, **kw):
        uid = self.get_uid(request.httprequest.headers.environ)
        headers = [('Content-Type', 'application/json')]
        if not uid:
            data = json.dumps({
                "status": 403,
                "message": "Authentication failed",
            })
            return request.make_response(data, headers)
        vals = []
        companies = request.env['res.company'].with_user(uid).search([])
        for company in companies:
            hotel = company.related_hotel_id
            room_types = request.env['room.type'].with_user(uid).search([('company_id', '=', company.id)])
            room_type_vals = []
            for room_type in room_types:
                rate_type_vals = []
                rate_types = request.env['hotel.rate.type'].with_user(uid).search([('company_id', '=', company.id)])
                for rate_type in rate_types:
                    rate_type_vals.append({
                        "ID": rate_type.id,
                        "name": rate_type.name,
                    })
                rate_plan_vals = []
                rate_plans = room_type.rate_plan_ids
                for rate_plan in rate_plans:
                    rate_plan_vals.append({
                        "ID": rate_plan.id,
                        "name": rate_plan.name,
                    })
                if room_type.image:
                    image = image_data_uri(room_type.image)
                else:
                    base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
                    image = base64.b64encode(requests.get(base_url + '/web/static/img/placeholder.png').content)
                    image = image_data_uri(image)
                room_type_vals.append({
                    "ID": room_type.id,
                    "name": room_type.name,
                    "image": image,
                    "mini_adults": room_type.mini_adults,
                    "max_adults": room_type.max_adults,
                    "mini_children": room_type.mini_children,
                    "max_children": room_type.max_children,
                    "rate_types": rate_type_vals,
                    "rate_plans": rate_plan_vals,
                })
            if hotel.image:
                image = image_data_uri(hotel.image)
            else:
                base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
                image = base64.b64encode(requests.get(base_url + '/web/static/img/placeholder.png').content)
                image = image_data_uri(image)
            vals.append({
                "ID": hotel.id,
                "name": hotel.name,
                "address": hotel.address,
                "description": hotel.description,
                "image": image,
                "expiration_date": str(hotel.expiration_date) if hotel.expiration_date else False,
                "room_types": room_type_vals
            })
        data = json.dumps({
            "status": 200,
            "message": "Hotels Retrieved successfully",
            "response": {
                "hotels": vals,
            }
        })
        headers = [('Content-Type', 'application/json')]
        return request.make_response(data, headers)

    @http.route('/api/company_accounting/details', auth='none', website=False, csrf=False, type='json', methods=['GET'])
    def get_company_accounting_details(self, **kwargs):
        uid = self.get_uid(request.httprequest.headers.environ)
        args = request.httprequest.data.decode()
        args = json.loads(args)
        headers = [('Content-Type', 'application/json')]
        if not uid:
            data = json.dumps({
                "status": 403,
                "message": "Authentication failed",
            })
            return request.make_response(data, headers)

        company_id = args.get('id')
        company_name = args.get('name')

        vals = []
        domain = [('is_company', '=', True)]
        if company_id:
            domain.append(('id', '=', int(company_id)))
        if company_name:
            domain.append(('name', 'ilike', company_name))

        companies = request.env['res.partner'].with_user(uid).search(domain)

        for company in companies:
            vals.append({
                "ID": company.id,
                "english_name": company.name,
                "arabic_name": company.company_arabic_name,
                "company_code": company.company_code,
                "company_credit_limit": company.customer_credit_limit,
                "company_due_amount": company.customer_due_amount,
                "balance": company.balance,
                "company_advance_payment": company.total_advanced_payment
            })

        if not vals:
            return {
                "status": 404,
                "message": "No companies found matching the criteria.",
            }

        return {
            "status": 200,
            "message": "Companies Details retrieved successfully",
            "response": {
                "companies": vals,
            }
        }

    @http.route('/api/hotel/expiration', auth='none', website=False, csrf=False, type='http', methods=['GET'])
    def get_hotel_expiration(self, **kw):
        uid = self.get_uid(request.httprequest.headers.environ)
        headers = [('Content-Type', 'application/json')]
        if not uid:
            data = json.dumps({
                "status": 403,
                "message": "Authentication failed",
            })
            return request.make_response(data, headers)
        vals = []
        companies = request.env['res.company'].with_user(uid).search([])
        for company in companies:
            hotel = company.related_hotel_id
            vals.append({
                "ID": hotel.id,
                "name": hotel.name,
                "expiration_date": str(hotel.expiration_date) if hotel.expiration_date else False,
            })
        data = json.dumps({
            "status": 200,
            "message": "Hotels Expiration Retrieved successfully",
            "response": {
                "hotels": vals,
            }
        })
        headers = [('Content-Type', 'application/json')]
        return request.make_response(data, headers)

    @http.route('/api/travel/agent', auth='none', website=False, csrf=False, type='http', methods=['GET'])
    def get_travel_agents(self, **kw):
        uid = self.get_uid(request.httprequest.headers.environ)
        headers = [('Content-Type', 'application/json')]
        if not uid:
            data = json.dumps({
                "status": 403,
                "message": "Authentication failed",
            })
            return request.make_response(data, headers)
        vals = []
        agents = request.env['res.partner'].with_user(uid).search([('online_travel_agent', '=', True)])
        for agent in agents:
            vals.append({
                "ID": agent.id,
                "name": agent.name,
            })
        data = json.dumps({
            "status": 200,
            "message": "Travel Agents Retrieved successfully",
            "response": {
                "agents": vals,
            }
        })
        headers = [('Content-Type', 'application/json')]
        return request.make_response(data, headers)

    @http.route('/api/booking/create', auth='none', website=False, csrf=False, type='json', methods=['POST'])
    def create_booking(self, **kw):
        uid = self.get_uid(request.httprequest.headers.environ)
        if not uid:
            return {
                "status": 403,
                "message": "Authentication failed",
            }
        args = request.httprequest.data.decode()
        args = json.loads(args)
        lang = request.httprequest.accept_languages.best
        required_fields = {
            'hotel_id': 'اسم الفندق',
            'check_in': 'تاريخ الوصول',
            'check_out': 'تاريخ المغادرة',
            'guest_name': 'اسم النزيل',
            'lines': 'تفاصيل الحجز',
        }
        for k, v in required_fields.items():
            if not args.get(k, False):
                return {
                    "status": 405,
                    "message": f" برجاء إدخال {v}" if lang == 'ar' else f"{k} is missing!",
                }
        hotel_id = request.env['hotel.hotel'].with_user(uid).search([('id', '=', args['hotel_id'])])
        company_id = hotel_id.company_id
        check_in = fields.Date.to_date(args['check_in'])
        check_out = fields.Date.to_date(args['check_out'])
        if check_in >= check_out:
            return {
                "status": 405,
                "message": " تاريخ الوصول يجب ان يكون قبل تاريخ المغادرة " if lang == 'ar' else "check in date must be before checkout date",
            }
        partner_id = self.get_or_create_guest(args['guest_name'], args.get('mobile', ''), uid)
        # validate room types and rate plans
        for line in args['lines']:
            if not line.get('room_type_id', False):
                return {
                    "status": 405,
                    "message": " برجاء إدخال room_type_id" if lang == 'ar' else "room_type_id  is missing!",
                }
            room_type = self.get_room_type(company_id, line['room_type_id'], uid)
            if not room_type:
                return {
                    "status": 405,
                    "message": f" نوع الغرفة غير موجود{line['room_type_id']}" if lang == 'ar' else f"Room type with ID {line['room_type_id']} not exist",
                }
            if not line.get('rate_type_id', False):
                return {
                    "status": 405,
                    "message": " برجاء إدخال rate_type_id" if lang == 'ar' else "rate_type_id  is missing!",
                }
            rate_plan = self.get_rate_plan(company_id.id, line['rate_type_id'], room_type.id, uid)
            if not rate_plan:
                return {
                    "status": 405,
                    "message": f" خطة الاسعار غير موجود{line['rate_type_id']}" if lang == 'ar' else f"Rate type with ID {line['rate_type_id']} not exist",
                }
        lines = self.prepare_booking_lines(args['lines'], company_id, uid)
        booking_id = request.env['hotel.booking'].sudo().with_user(uid).with_company(company_id).create({
            'company_id': company_id.id,
            'hotel_id': hotel_id.id,
            'new_check_in': check_in,
            'new_check_out': check_out,
            'total_nights': (check_out - check_in).days,
            'partner_id': partner_id.id,
            'quick_group_booking': args.get('group_booking', False),
        })
        booking_id.onchange_new_check_in()
        booking_id.onchange_new_check_out()
        booking_id.write({
            'line_ids': lines
        })
        for folio in booking_id.folio_ids:
            folio.write({
                'partner_id': booking_id.partner_id.id
            })
            folio.button_confirm()
        return {
            "status": 200,
            "message": f"Booking {booking_id.sudo().name} has been created successfully!",
            "response": {
                "booking_id": booking_id.id,
                "booking_number": booking_id.name,
            }
        }

    @http.route('/api/booking/create_contact', auth='none', website=False, csrf=False, type='json', methods=['POST'])
    def create_contact(self, **kw):
        uid = self.get_uid(request.httprequest.headers.environ)
        if not uid:
            return {
                "status": 403,
                "message": "Authentication failed",
            }
        args = request.httprequest.data.decode()
        args = json.loads(args)
        lang = request.httprequest.accept_languages.best
        required_fields = {
            'partner_type': 'نوع الشريك',
            'name': 'الاسم',
            'gender': 'نوع',
        }
        for k, v in required_fields.items():
            if not args.get(k, False):
                return {
                    "status": 405,
                    "message": f" برجاء إدخال {v}" if lang == 'ar' else f"{k} is missing!",
                }

        if args.get('partner_type', '') == 'person':
            partner_type = 'person'
        elif args.get('partner_type', '') == 'company':
            partner_type = 'company'
        else:
            return {
                "status": 405,
                "message": "Please Add Valid Type For Contact",
            }

        partner_id = request.env['res.partner'].with_user(uid).create({
                "name": args.get('name', ''),
                "company_arabic_name": args.get('company_arabic_name', ''),
                "person_arabic_name": args.get('person_arabic_name', ''),
                "mobile": args.get('mobile', ''),
                "gender": args.get('gender', ''),
                "email": args.get('email', ''),
                "company_type": partner_type
            })

        return {
            "status": 200,
            "message": f"Partner {partner_id.name} has been created successfully!",
            "response": {
                "partner_id": partner_id.id,
            }
        }

    def get_room_type(self, company_id, type_id, uid):
        return request.env['room.type'].with_user(uid).search([
            ('company_id', '=', company_id.id), ('id', '=', type_id)
        ], limit=1)

    def get_rate_plan(self, company_id, rate_type_id, room_type, uid):
        return request.env['hotel.rate.plan'].with_user(uid).search([
            ('company_id', '=', company_id), ('rate_type_id', '=', rate_type_id), ('room_type_id', '=', room_type)
        ], limit=1)

    @http.route('/api/get_folios', auth='none', website=False, csrf=False, type='json', methods=['GET'])
    def get_folio_lines(self, **kwargs):
        uid = request.session.uid
        args = request.httprequest.data.decode()
        args = json.loads(args)
        if not uid:
            return {
                "status": 403,
                "message": "Authentication failed",
            }

        check_in_from = args.get('check_in_from')
        check_in_to = args.get('check_in_to')
        check_out_from = args.get('check_out_from')
        check_out_to = args.get('check_out_to')
        booking_source = args.get('booking_source')
        online_travel_agent_source = args.get('online_travel_agent_source')
        company_booking_source = args.get('company_booking_source')
        state_ids = args.get('state_ids', [])
        reference_number = args.get('reference_number')
        related_hotel = args.get('related_hotel')
        partner_id = args.get('partner_id')
        booking_id = args.get('booking_id')
        folio_id = args.get('folio_id')
        room_id = args.get('room_id')
        mobile = args.get('mobile')
        include_cancelled = args.get('include_cancelled', True)
        filter_type = args.get('filter_type')
        payment_type = args.get('payment_type')

        if not related_hotel:
            return {
                "status": 403,
                "message": "hotel is required",
            }
        if not filter_type:
            return {
                "status": 403,
                "message": "you must select filter type",
            }

        if filter_type not in ['manual', 'arrival', 'departure', 'inhouse']:
            return {
                "status": 403,
                "message": "filter type is not correct",
            }
        if payment_type not in ['cash', 'city_ledger', 'charge_city_ledger']:
            return {
                "status": 403,
                "message": "Payment type is not correct",
            }
        if booking_source not in ['direct', 'online_agent', 'company']:
            return {
                "status": 403,
                "message": "Booking Source is not correct",
            }

        domain = []
        if check_in_from:
            domain.append(('check_in_date', '>=', check_in_from))
        if check_in_to:
            domain.append(('check_in_date', '<=', check_in_to))
        if check_out_from:
            domain.append(('check_out_date', '>=', check_out_from))
        if check_out_to:
            domain.append(('check_out_date', '<=', check_out_to))
        if booking_source:
            domain.append(('booking_id.booking_source', '=', booking_source))
            if booking_source == 'online_agent' and online_travel_agent_source:
                domain.append(('booking_id.online_travel_agent_source', '=', int(online_travel_agent_source)))
            elif booking_source == 'company' and company_booking_source:
                domain.append(('booking_id.company_booking_source', 'ilike', company_booking_source))
        if state_ids:
            domain.append(('state', 'in', state_ids))
        if reference_number:
            domain.append(('booking_id.ref', '=', reference_number))
        if related_hotel:
            domain.append(('hotel_id', '=', related_hotel))
        if booking_id:
            domain.append(('booking_id.name', 'ilike', booking_id))
        if payment_type:
            domain.append(('booking_id.payment_type_id', 'ilike', payment_type))

        folios = request.env['booking.folio'].sudo().search(domain)

        if partner_id:
            folios = folios.filtered(lambda f: partner_id.lower() in f.partner_id.name.lower())
        if booking_id:
            folios = folios.filtered(lambda f: booking_id.lower() in f.booking_id.name.lower())
        if folio_id:
            folios = folios.filtered(lambda f: f.id == int(folio_id))
        if room_id:
            folios = folios.filtered(lambda f: f.room_id.id == int(room_id))
        if mobile:
            folios = folios.filtered(lambda f: mobile in (f.partner_id.mobile or ''))

        if not include_cancelled:
            folios = folios.filtered(lambda f: f.state != 'cancelled')

        hotel_id = request.env['hotel.hotel'].with_user(uid).search([('id', '=', args['related_hotel'])])
        company_id = hotel_id.company_id

        audit_date_start = datetime.combine(company_id.audit_date, datetime.min.time())
        audit_date_end = datetime.combine(company_id.audit_date, datetime.max.time())

        if filter_type == 'arrival':
            folios = folios.filtered(
                lambda f: f.state in ['confirmed', 'draft'] and audit_date_start <= f.check_in <= audit_date_end)
        elif filter_type == 'manual':
            pass
        elif filter_type == 'departure':
            folios = folios.filtered(
                lambda f: f.state == 'checked_in' and audit_date_start <= f.check_out <= audit_date_end)

        lines = []
        for folio in folios:
            lines.append({
                "folio_id": folio.name,
                "booking_id": folio.booking_id.name,
                "ref": folio.booking_id.ref,
                "company_booking_source": folio.booking_id.company_booking_source.name,
                "customer_credit_limit": folio.booking_id.company_booking_source.customer_credit_limit,
                "balance": folio.booking_id.company_booking_source.balance,
                "partner_id": folio.partner_id.name,
                "room_type_name": folio.room_type_id.name,
                "room_name": folio.room_id.name,
                "check_in": folio.check_in,
                "check_out": folio.check_out,
                "price_subtotal": folio.price_subtotal,
                "price_total": folio.price_total,
                "price_tax": folio.price_tax,
                "price_paid": folio.price_paid,
                "price_due": folio.price_due,
                "currency_id": folio.booking_id.currency_id.name,
                "state": folio.state,
                "company_id": folio.company_id.name,
            })

        return {
            "status": 200,
            "message": "Folios retrieved successfully.",
            "data": lines,
        }

    def prepare_booking_lines(self, lines, company_id, uid):
        #  TODO handle many booking lines
        vals = []
        for line in lines:
            room_type = self.get_room_type(company_id, line['room_type_id'], uid)
            rate_plan = self.get_rate_plan(company_id.id, line['rate_type_id'], room_type.id, uid)
            if room_type and rate_plan:
                vals.append((0, 0, {
                    'company_id': company_id.id,
                    'hotel_id': company_id.related_hotel_id.id,
                    'room_type': room_type.id,
                    'rate_plan': rate_plan.id,
                    'number_of_rooms': line.get('number_of_rooms', 1),
                    'tax_id': rate_plan.sudo().tax_ids.filtered(lambda t: t.price_include).ids,
                    'price_include_tax': False
                }))
        return vals

    def get_or_create_guest(self, name, mobile, uid):
        partner_id = request.env['res.partner'].with_user(uid).search([('name', '=', name)], limit=1)
        if not partner_id:
            partner_id = request.env['res.partner'].with_user(uid).create({
                "name": name,
                "mobile": mobile,
            })
        return partner_id

    def get_or_create_guest2(self, name, uid):
        partner_id = request.env['res.partner'].with_user(uid).search([('name', '=', name)], limit=1)
        if not partner_id:
            partner_id = request.env['res.partner'].with_user(uid).create({
                "name": name,
            })
        return partner_id

    def get_headers(self):
        return [('Content-Type', 'application/json')]

    @http.route('/api/room/availability', auth='none', website=False, csrf=False, type='json', methods=['GET'])
    def get_availability(self, **kw):
        uid = self.get_uid(request.httprequest.headers.environ)
        args = request.httprequest.data.decode()
        args = json.loads(args)
        _logger.info(f">>>>>>>> ENVIRON >>>>>>{request.httprequest.headers.environ}")
        headers = [('Content-Type', 'application/json')]
        if not uid:
            return {
                "status": 403,
                "message": "Authentication failed",
            }
            # return request.make_response(data, headers)
        check_in = args.get('check_in', False)
        check_in = fields.Date.to_date(check_in)
        check_out = args.get('check_out', False)
        check_out = fields.Date.to_date(check_out)
        hotel = args.get('hotel')
        if not check_in:
            return {
                "status": 403,
                "message": "Missing Check in",
            }
            # return request.make_response(data, headers)
        if not check_out:
            return {
                "status": 403,
                "message": "Missing Check Out",
            }
            # return request.make_response(data, headers)
        if not hotel:
            return {
                "status": 403,
                "message": "Missing Hotel",
            }
            # return request.make_response(data, headers)
        hotel_id = request.env['hotel.hotel'].with_user(uid).search([('id', '=', int(hotel))])
        company_id = hotel_id.company_id

        vals = self.get_available_rooms(check_in, check_out, company_id, uid)
        return {
            "status": 200,
            "message": "Room Availability Retrieved successfully",
            "response": {
                "room_availability": vals,
            }
        }
        # headers = [('Content-Type', 'application/json')]
        # return request.make_response(data, headers)

    def get_available_rooms(self, check_in_date, check_out_date, company_id, uid):
        vals = []
        room_types = request.env['room.type'].with_user(uid).search([('company_id', '=', company_id.id)])
        for room_type_id in room_types:
            available_rooms = 0
            out_of_order_rooms = request.env["hotel.room"].search([
                ('room_type', '=', room_type_id.id),
                '|', '|',
                '&', ('out_of_order_from', '<=', check_in_date), ('out_of_order_to', '>', check_in_date),
                '&', ('out_of_order_from', '<=', check_out_date), ('out_of_order_to', '>', check_out_date),
                '&', ('out_of_order_from', '<=', check_in_date), ('out_of_order_to', '>', check_out_date),
            ])
            rooms = request.env["hotel.room"].search([
                ('room_type', '=', room_type_id.id), ('id', 'not in', out_of_order_rooms.ids)
            ])

            for room in rooms:
                domain = [
                    ('company_id', '=', company_id.id),
                    ('room_id', '=', room.id),
                    ('state', 'in', ['part_checked_in', 'checked_in', 'confirmed', 'draft']),
                    '|', '|',
                    '&', ('check_in_date', '<=', check_in_date), ('check_out_date', '>', check_in_date),
                    '&', ('check_in_date', '<=', check_out_date), ('check_out_date', '>', check_out_date),
                    '&', ('check_in_date', '<=', check_in_date), ('check_out_date', '>', check_out_date),
                ]
                folio = request.env['booking.folio'].search(domain)
                if not folio:
                    available_rooms += 1
            rate_plan_vals = []
            rate_plans = request.env['hotel.rate.plan'].with_user(uid).search([
                ('company_id', '=', company_id.id), ('room_type_id', '=', room_type_id.id)
            ])
            for rate_plan in rate_plans:
                prices = rate_plan.day_price_ids.filtered(lambda p: check_in_date <= p.date < check_out_date)
                rate_plan_vals.append({
                    "ID": rate_plan.rate_type_id.id,
                    "name": rate_plan.rate_type_id.name,
                    "prices": [{"date": str(day_price.date), "price": day_price.price} for day_price in prices]
                })

            vals.append({
                "room_type_id": room_type_id.id,
                "room_type_name": room_type_id.name,
                "available_rooms": available_rooms,
                "rate_plans": rate_plan_vals
            })
        return vals

    @http.route('/api/booking/price', auth='none', website=False, csrf=False, type='json', methods=['POST'])
    def check_booking_price(self, **kw):
        total = 0
        uid = self.get_uid(request.httprequest.headers.environ)
        if not uid:
            return {
                "status": 403,
                "message": "Authentication failed",
            }
        args = request.httprequest.data.decode()
        args = json.loads(args)
        lang = request.httprequest.accept_languages.best
        required_fields = {
            'hotel_id': 'اسم الفندق',
            'check_in': 'تاريخ الوصول',
            'check_out': 'تاريخ المغادرة',
            'lines': 'تفاصيل الحجز',
        }
        for k, v in required_fields.items():
            if not args.get(k, False):
                return {
                    "status": 405,
                    "message": f" برجاء إدخال {v}" if lang == 'ar' else f"{k} is missing!",
                }
        hotel_id = request.env['hotel.hotel'].with_user(uid).search([('id', '=', args['hotel_id'])])
        company_id = hotel_id.company_id
        check_in = fields.Date.to_date(args['check_in'])
        check_out = fields.Date.to_date(args['check_out'])
        if check_in >= check_out:
            return {
                "status": 405,
                "message": " تاريخ الوصول يجب ان يكون قبل تاريخ المغادرة " if lang == 'ar' else "check in date must be before checkout date",
            }
        date_list = request.env['booking.folio'].with_user(uid).get_dates_between_exclude_checkout(check_in, check_out)
        # validate room types and rate plans
        for line in args['lines']:
            if not line.get('room_type_id', False):
                return {
                    "status": 405,
                    "message": " برجاء إدخال room_type_id" if lang == 'ar' else "room_type_id  is missing!",
                }
            room_type = self.get_room_type(company_id, line['room_type_id'], uid)
            if not room_type:
                return {
                    "status": 405,
                    "message": f" نوع الغرفة غير موجود{line['room_type_id']}" if lang == 'ar' else f"Room type with ID {line['room_type_id']} not exist",
                }
            if not line.get('rate_type_id', False):
                return {
                    "status": 405,
                    "message": " برجاء إدخال rate_type_id" if lang == 'ar' else "rate_type_id  is missing!",
                }
            rate_plan = self.get_rate_plan(company_id.id, line['rate_type_id'], room_type.id, uid)
            if not rate_plan:
                return {
                    "status": 405,
                    "message": f" خطة الاسعار غير موجود{line['rate_type_id']}" if lang == 'ar' else f"Rate type with ID {line['rate_type_id']} not exist",
                }

            for day in date_list:
                prices = self.get_prices(day, rate_plan, uid)
                price_untaxed = prices['price_untaxed']
                price_vat = prices['price_vat']
                price_municipality = prices['price_municipality']
                total += line.get('number_of_rooms', 1) * (price_untaxed + price_vat + price_municipality)

        return {
            "status": 200,
            "message": f"Price Retrieved successfully!",
            "response": {
                "total_price": round(total, 2),
            }
        }

    def get_prices(self, day, plan, uid):
        price_unit = request.env['rate.plan.day.price'].with_user(uid).search(
            [('plan_id', '=', plan.id), ('date', '=', day)], limit=1).price
        # if not price_unit
        price_vat = 0
        price_municipality = 0
        price_untaxed = price_unit
        price_total = price_unit
        municipality = plan.with_user(uid).tax_ids.filtered(lambda t: t.type == 'municipality')
        if municipality:
            municipality = municipality[0]
            price_total = price_unit * (municipality.amount / 100 + 1)
            price_municipality = price_total - price_unit

        vat = plan.with_user(uid).tax_ids.filtered(lambda t: t.type == 'vat')
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

    @http.route('/api/booking/<string:booking_number>', auth='none', website=False, csrf=False, type='http',
                methods=['GET'])
    def get_booking_by_number(self, booking_number, **kw):
        uid = self.get_uid(request.httprequest.headers.environ)
        headers = [('Content-Type', 'application/json')]
        if not uid:
            data = json.dumps({
                "status": 403,
                "message": "Authentication failed",
            })
            return request.make_response(data, headers)
        booking = request.env['hotel.booking'].with_user(uid).search([('name', '=', booking_number)])
        if not booking:
            data = json.dumps({
                "status": 403,
                "message": "Invalid booking number",
            })
            return request.make_response(data, headers)

        lines = []
        for line in booking.line_ids:
            lines.append({
                "line_id": line.id,
                "room_type": line.room_type.id,
                "rate_type": line.rate_plan.rate_type_id.id,
                "rate_plan": line.rate_plan.id,
                "number_of_rooms": line.number_of_rooms,
                "price_include_tax": line.price_include_tax,
            })
        payments = []
        account_payments = request.env['account.payment'].with_user(uid).search(
            [('booking_id', '=', booking.id), ('state', '=', 'posted')])
        for payment in account_payments:
            payments.append({
                "payment_id": payment.id,
                "amount": payment.amount,
                "payment_date": str(payment.date),
                "status": payment.state,
            })
        data = json.dumps({
            "status": 200,
            "message": "Booking retrieved successfully",
            "response": {
                "booking": {
                    "ID": booking.id,
                    "booking_number": booking.name,
                    "hotel_id": booking.hotel_id.id,
                    "hotel_name": booking.hotel_id.name,
                    "check_in": str(booking.check_in_date),
                    "check_out": str(booking.check_out_date),
                    "guest_name": booking.partner_id.name,
                    "guest_mobile": booking.partner_id.phone or booking.partner_id.mobile,
                    "amount_total": booking.amount_total,
                    "amount_paid": booking.amount_paid,
                    "amount_due": booking.amount_due,
                    "lines": lines,
                    "payments": payments,
                },
            }
        })
        headers = [('Content-Type', 'application/json')]
        return request.make_response(data, headers)

    @http.route('/api/booking/mobile/<string:mobile>', auth='none', website=False, csrf=False, type='http',
                methods=['GET'])
    def get_booking_by_mobile(self, mobile, **kw):
        uid = self.get_uid(request.httprequest.headers.environ)
        headers = [('Content-Type', 'application/json')]
        if not uid:
            data = json.dumps({
                "status": 403,
                "message": "Authentication failed",
            })
            return request.make_response(data, headers)
        vals = []
        bookings = request.env['hotel.booking'].with_user(uid).search(
            ['|', ('partner_id.phone', '=', mobile), ('partner_id.mobile', '=', mobile)])
        if not bookings:
            data = json.dumps({
                "status": 403,
                "message": "Invalid mobile number",
            })
            return request.make_response(data, headers)
        for booking in bookings:
            lines = []
            for line in booking.line_ids:
                lines.append({
                    "line_id": line.id,
                    "room_type": line.room_type.id,
                    "rate_type": line.rate_plan.rate_type_id.id,
                    "rate_plan": line.rate_plan.id,
                    "number_of_rooms": line.number_of_rooms,
                    "price_include_tax": line.price_include_tax,
                })
            vals.append({
                "ID": booking.id,
                "booking_number": booking.name,
                "hotel_id": booking.hotel_id.id,
                "hotel_name": booking.hotel_id.name,
                "check_in": str(booking.check_in_date),
                "check_out": str(booking.check_out_date),
                "guest_name": booking.partner_id.name,
                "guest_mobile": booking.partner_id.phone or booking.partner_id.mobile,
                "lines": lines
            }, )
        data = json.dumps({
            "status": 200,
            "message": "Bookings Retrieved successfully",
            "response": {
                "bookings": vals
            }
        })
        headers = [('Content-Type', 'application/json')]
        return request.make_response(data, headers)

    @http.route('/api/booking/<string:booking_number>/update', auth='none', website=False, csrf=False, type='json',
                methods=['POST'])
    def update_booking(self, booking_number, **kw):
        uid = self.get_uid(request.httprequest.headers.environ)
        if not uid:
            return {
                "status": 403,
                "message": "Authentication failed",
            }
        booking = request.env['hotel.booking'].with_user(uid).search([('name', '=', booking_number)])
        if not booking:
            return {
                "status": 403,
                "message": "Invalid booking number",
            }
        args = request.httprequest.data.decode()
        args = json.loads(args)
        lang = request.httprequest.accept_languages.best
        vals = {}
        # check in/out
        if args.get('check_in', False):
            check_in_date = fields.Date.to_date(args['check_in'])
            check_in_datetime = datetime.combine(check_in_date, datetime.strptime('000000', '%H%M%S').time())

            vals['check_in'] = check_in_datetime
            vals['new_check_in'] = check_in_date
        else:
            check_in_date = booking.check_in_date
        if args.get('check_out', False):
            check_out_date = fields.Date.to_date(args['check_out'])
            check_out_datetime = datetime.combine(check_out_date, datetime.strptime('000000', '%H%M%S').time())
            vals['check_out'] = check_out_datetime
            vals['new_check_out'] = check_out_date
        else:
            check_out_date = booking.check_out_date
        if check_in_date >= check_out_date:
            return {
                "status": 405,
                "message": " تاريخ الوصول يجب ان يكون قبل تاريخ المغادرة " if lang == 'ar' else "check in date must be before checkout date",
            }
        delta = (check_out_date - check_in_date).days
        vals['total_nights'] = delta if delta > 0 else 0
        if args.get("guest_name", False):
            partner_id = self.get_or_create_guest2(args['guest_name'], uid)
            vals['partner_id'] = partner_id.id
        # update booking data
        booking.with_user(uid).write(vals)
        # update booking lines
        if args.get("booking_lines", False):
            for booking_line_dict in args['booking_lines']:
                if booking_line_dict.get('line_id', False):
                    booking_line = request.env['hotel.booking.line'].with_user(uid).search(
                        [('id', '=', booking_line_dict['line_id'])])
                    if not booking_line:
                        return {
                            "status": 403,
                            "message": "Invalid booking line ID",
                        }
                    company = booking_line.company_id
                    room_type_id = booking_line_dict.get('room_type', booking_line.room_type.id)
                    rate_type_id = booking_line_dict.get('rate_type', booking_line.rate_plan.rate_type_id.id)
                    rate_plan = self.get_rate_plan(company.id, rate_type_id, room_type_id, uid)
                    booking_line_vals = {
                        "company_id": company.id,
                        "hotel_id": company.related_hotel_id.id,
                        "room_type": room_type_id,
                        "rate_plan": rate_plan.id,
                        "number_of_rooms": booking_line_dict.get('number_of_rooms', booking_line.number_of_rooms),
                        'tax_id': rate_plan.sudo().tax_ids.filtered(lambda t: t.price_include).ids,
                        'price_include_tax': False
                    }
                    for folio in booking_line.folio_ids:
                        for folio_line in folio.line_ids:
                            folio_line.unlink()
                        folio.unlink()
                    booking_line.unlink()
                    booking.with_user(uid).write({
                        'line_ids': [(0, 0, booking_line_vals)]
                    })
                else:
                    company = booking.company_id
                    # validate room type and rate type
                    if not booking_line_dict.get('room_type', False):
                        return {
                            "status": 405,
                            "message": " برجاء إدخال room_type" if lang == 'ar' else "room_type  is missing!",
                        }
                    room_type = self.get_room_type(company, booking_line_dict['room_type'], uid)
                    if not room_type:
                        return {
                            "status": 405,
                            "message": f" نوع الغرفة غير موجود{booking_line_dict['room_type']}" if lang == 'ar' else f"Room type with ID {booking_line_dict['room_type']} not exist",
                        }
                    if not booking_line_dict.get('rate_type', False):
                        return {
                            "status": 405,
                            "message": " برجاء إدخال rate_type" if lang == 'ar' else "rate_type  is missing!",
                        }
                    rate_plan = self.get_rate_plan(company.id, booking_line_dict['rate_type'], room_type.id, uid)
                    if not rate_plan:
                        return {
                            "status": 405,
                            "message": f" خطة الاسعار غير موجود{booking_line_dict['rate_type']}" if lang == 'ar' else f"Rate type with ID {booking_line_dict['rate_type']} not exist",
                        }

                    booking_line_vals = {
                        "company_id": company.id,
                        "hotel_id": company.related_hotel_id.id,
                        "room_type": room_type.id,
                        "rate_plan": rate_plan.id,
                        "number_of_rooms": booking_line_dict.get('number_of_rooms', 1),
                        'tax_id': rate_plan.sudo().tax_ids.filtered(lambda t: t.price_include).ids,
                        'price_include_tax': False
                    }
                    booking.with_user(uid).write({
                        'line_ids': [(0, 0, booking_line_vals)]
                    })
        return {
            "status": 200,
            "message": f"Booking {booking.sudo().name} has been updated successfully!",
            "response": {
                "booking_id": booking.id,
                "booking_number": booking.name,
                "booking_lines": self.get_booking_lines(booking)
            }
        }

    def get_booking_lines(self, booking_id):
        lines = []
        for line in booking_id.line_ids:
            lines.append({
                "line_id": line.id,
                "room_type": line.room_type.id,
                "rate_type": line.rate_plan.rate_type_id.id,
                "number_of_rooms": line.number_of_rooms,
            })
        return lines

    @http.route('/api/booking/check_in', auth='none', website=False, csrf=False, type='json',
                methods=['POST'])
    def booking_check_in(self, **kw):
        uid = self.get_uid(request.httprequest.headers.environ)
        args = request.httprequest.data.decode()
        args = json.loads(args)
        lang = request.httprequest.accept_languages.best
        if not uid:
            return {
                "status": 403,
                "message": "Authentication failed",
            }
        if not args.get('guest_name', False):
            return {
                "status": 405,
                "message": "برجاء إدخال اسم العميل" if lang == 'ar' else "guest name is missing!",
            }
        if not args.get('birth_date', False):
            return {
                "status": 405,
                "message": "برجاء إدخال تاريخ الميلاد" if lang == 'ar' else "Birth Date is missing!",
            }
        if not args.get('nationality', False):
            return {
                "status": 405,
                "message": "برجاء إدخال الجنسية" if lang == 'ar' else "Nationality is missing!",
            }
        if not args.get('id_number', False):
            return {
                "status": 405,
                "message": "برجاء إدخال الرقم التعريفي الخاص بالعميل " if lang == 'ar' else "Identification Card ID is missing!",
            }
        if not args.get('floor_preference', False):
            return {
                "status": 405,
                "message": "برجاء إدخال الدور المفضل العلوي ام السفلي" if lang == 'ar' else "Floor Preference is missing!",
            }
        floor_preference = args.get('floor_preference').lower()
        booking = request.env['hotel.booking'].with_user(uid).search([('name', '=', args.get('booking_number', False))])
        if not booking:
            return {
                "status": 403,
                "message": "Invalid booking number",
            }
        if booking.amount_due != 0.0:
            return {
                "status": 403,
                "message": f"Booking Has Due {booking.amount_due} {booking.currency_id.name}",
            }
        hotel_id = request.env['res.company'].search([('related_hotel_id', '=', booking.hotel_id.id)], limit=1)
        # clean_rooms = self.get_clean_rooms(floor_preference, hotel_id)
        vals = self.get_available_rooms(booking.new_check_in, booking.new_check_out, booking.company_id, uid)
        filtered_rooms = [room for room in vals if room['room_type_id'] == args.get('room_type_id', False)]
        room_model = request.env['hotel.room']
        rooms = room_model.with_user(uid).search(
            [('state_selection', '!=', 'dirty'), ('hotel_id', '=', booking.hotel_id.id),
             ('room_type', '=', args.get('room_type_id', False)),
             ('floor_id.floor_level', '=', args.get('floor_preference', False)),
             ('stay_state.display_name', '=', 'Vacant')], order='id').filtered(lambda l: not l.booking_id)
        if not rooms:
            return {
                "status": 403,
                "message": f"no room available right now",
            }
        room_list = []
        try:
            for folio, room_id in zip(booking.folio_ids, rooms):
                if folio.state not in ['draft', 'confirmed']:
                    return {
                        "status": 403,
                        "message": f"folio {folio.name} status is not draft or confirmed",
                    }
                if not folio.today_is_checkin:
                    return {
                        "status": 403,
                        "message": f"folio {folio.name} check in is not today!",
                    }
                msg = folio.js_validate_check_in(room_id)
                if msg:
                    return {
                        "status": 403,
                        "message": msg,
                    }
                room_list.append(room_id.name)
            # booking.button_check_in()
            for folio, room_id in zip(booking.folio_ids, rooms):
                folio.room_id = room_id
                folio.button_check_in()
            return {
                "status": 200,
                "message": f"Booking {booking.sudo().name} has been checked in successfully!",
                "response": {
                    "booking_id": booking.id,
                    "booking_number": booking.name,
                    "rooms": room_list
                }
            }
        except Exception as e:
            return {
                "status": 403,
                "message": e,
            }

    @http.route('/api/booking/<string:booking_number>/check_out', auth='none', website=False, csrf=False, type='json',
                methods=['POST'])
    def booking_check_out(self, booking_number, **kw):
        uid = self.get_uid(request.httprequest.headers.environ)
        if not uid:
            return {
                "status": 403,
                "message": "Authentication failed",
            }
        booking = request.env['hotel.booking'].with_user(uid).search([('name', '=', booking_number)])
        if not booking:
            return {
                "status": 403,
                "message": "Invalid booking number",
            }
        if booking.state != 'checked_in':
            return {
                "status": 403,
                "message": f"booking {booking.name} status is not checked in",
            }
        try:
            for folio in booking.folio_ids:
                if folio.state != 'checked_in':
                    return {
                        "status": 403,
                        "message": f"folio {folio.name} status is not checked in",
                    }
                if not folio.today_is_checkout:
                    return {
                        "status": 403,
                        "message": f'folio {folio.name} check out is not today!',
                    }
                msg = folio.js_validate_check_out()
                if msg:
                    return {
                        "status": 403,
                        "message": msg,
                    }
            booking.button_check_out()
            for folio in booking.folio_ids:
                folio.button_check_out()
            return {
                "status": 200,
                "message": f"Booking {booking.sudo().name} has been checked out successfully!",
                "response": {
                    "booking_id": booking.id,
                    "booking_number": booking.name,
                }
            }
        except Exception as e:
            return {
                "status": 403,
                "message": e,
            }

    @http.route('/api/allocate_room', auth='none', website=False, csrf=False, type='json', methods=['GET'])
    def allocate_room(self, **kw):
        uid = self.get_uid(request.httprequest.headers.environ)
        lang = request.httprequest.accept_languages.best
        if not uid:
            return {
                "status": 403,
                "message": "Authentication failed",
            }
        args = request.httprequest.data.decode()
        args = json.loads(args)
        hotel_id_value = args.get('hotel_id', False)
        if not hotel_id_value:
            return {
                "status": 405,
                "message": "برجاء إدخال الفندق" if lang == 'ar' else "Hotel ID is missing!",
            }
        hotel_id = request.env['res.company'].search([('related_hotel_id', '=', hotel_id_value)], limit=1)
        if not hotel_id:
            return {
                "status": 404,
                "message": "الفندق غير موجود" if lang == 'ar' else "Hotel not found!",
            }
        if not args.get('name', False):
            return {
                "status": 405,
                "message": "برجاء إدخال اسم العميل" if lang == 'ar' else "guest name is missing!",
            }
        if not args.get('birth_date', False):
            return {
                "status": 405,
                "message": "برجاء إدخال تاريخ الميلاد" if lang == 'ar' else "Birth Date is missing!",
            }
        if not args.get('nationality', False):
            return {
                "status": 405,
                "message": "برجاء إدخال الجنسية" if lang == 'ar' else "Nationality is missing!",
            }
        if not args.get('id_number', False):
            return {
                "status": 405,
                "message": "برجاء إدخال الرقم التعريفي الخاص بالعميل " if lang == 'ar' else "Identification Card ID is missing!",
            }
        if not args.get('floor_preference', False):
            return {
                "status": 405,
                "message": "برجاء إدخال الدور المفضل العلوي ام السفلي" if lang == 'ar' else "Floor Preference is missing!",
            }

        floor_preference = args.get('floor_preference').lower()

        clean_rooms = self.get_clean_rooms(floor_preference, hotel_id)

        return {
            "status": 200,
            "message": "Rooms fetched successfully",
            "data": clean_rooms
        }

    def get_clean_rooms(self, floor_preference, hotel_id):
        uid = self.get_uid(request.httprequest.headers.environ)
        floor_model = request.env['hotel.floor']
        floors = floor_model.search([('hotel_id', '=', hotel_id.id)])
        valid_levels = {'lower': 'lower', 'middle': 'middle', 'upper': 'upper'}

        level_mapping = {
            'lower': 'lower',
            'middle': 'middle',
            'upper': 'upper'
        }

        if floor_preference in valid_levels:
            floor_level = level_mapping.get(floor_preference)
        else:
            return []

        floor_ids = [floor.id for floor in floors if floor.floor_level == floor_level]

        room_model = request.env['hotel.room']
        rooms = room_model.with_user(uid).search([('floor_id', 'in', floor_ids), ('state.display_name', '=', 'Clean'),
                                                  ('stay_state.display_name', '=', 'Vacant'),
                                                  ('hotel_id', '=', hotel_id.id)], order='id')

        clean_rooms = []
        for room in rooms:
            clean_rooms.append({
                "room_id": room.id,
                "room_name": room.name,
                "room_type_id": room.room_type.id,
                "floor_id": room.floor_id.id,
                "floor_name": room.floor_id.name
            })
        return clean_rooms
