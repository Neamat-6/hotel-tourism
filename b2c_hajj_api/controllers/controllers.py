import base64
import json
import requests
from requests.packages import package
from odoo import http, api, SUPERUSER_ID, registry
import base64
from odoo.http import request
import logging
import traceback
logger = logging.getLogger(__name__)


class HajjController(http.Controller):

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

    def _prepare_activities(self, lines):
        link = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        return [{
            'name': line.name or '',
            'date': str(line.date) if line.date else '',
            'from_time': line.from_time,
            'to_time': line.to_time,
            'image_url':  f'{link}/web/image/booking.package.activity.line/{line.id}/image' if line.image else '',
            'image': line.image or None
        } for line in lines]

    @http.route('/api/package', auth='none', csrf=False, type='http', methods=['GET'])
    def get_packages(self, **kw):
        logger.info(f'get_packages {request.httprequest.headers.environ}')
        uid = self.get_uid(request.httprequest.headers.environ)
        headers = [('Content-Type', 'application/json')]
        if not uid:
            data = json.dumps({
                "status": 403,
                "message": "Authentication failed",
            })
            return request.make_response(data, headers)
        vals = []
        packages = request.env['booking.package'].with_user(uid).search([])
        for package in packages:
            vals.append({
                "ID": package.id,
                "name": package.name,
                "code": package.package_code,
                "booking_customer": package.partner_id.name,
                "guides": [g.name for g in package.guide_ids],
                "closing_date": str(package.package_closing_date),
                "flight_contract": [{'arrival_flight_no': line.flight_contract_id.arrival_flight_no, "departure_flight_no": line.flight_contract_id.departure_flight_no} for line in package.flight_contract_lines],
                "transportation_contracts": [contract.transportation_contract_no for contract in package.transportation_contract_ids],
            })
        data = json.dumps({
            "status": 200,
            "message": "Packages Retrieved successfully",
            "response": {
                "packages": vals,
            }
        })
        headers = [('Content-Type', 'application/json')]
        return request.make_response(data, headers)

    @http.route('/api/pilgrim', auth='none',  csrf=False, type='http', methods=['GET'])
    def get_pilgrims(self, **kw):
        uid = self.get_uid(request.httprequest.headers.environ)
        headers = [('Content-Type', 'application/json')]
        if not uid:
            data = json.dumps({
                "status": 403,
                "message": "Authentication failed",
            })
            return request.make_response(data, headers)
        vals = []
        packages = request.env['booking.package'].with_user(uid).search([])
        for package in packages:
            pilgrims = package.partner_ids.sudo().get_pilgrim_data()
            vals.append({
                "ID": package.id,
                "name": package.name,
                "code": package.package_code,
                "booking_customer": package.partner_id.name,
                "guides": [g.name for g in package.guide_ids],
                "closing_date": str(package.package_closing_date),
                "flight_contracts": package.flight_contract_lines.mapped('flight_contract_id').get_contract_data(),
                "transportation_contracts": [contract.transportation_contract_no for contract in package.transportation_contract_ids],
                "pilgrims": pilgrims,
                'activities': {
                    'makkah': self._prepare_activities(package.makkah_activity_line_ids),
                    'madina': self._prepare_activities(package.madina_activity_line_ids),
                    'araf': self._prepare_activities(package.arfa_activity_line_ids),
                    'minah': self._prepare_activities(package.minah_activity_line_ids),
                    'hotel': self._prepare_activities(package.hotel_activity_line_ids),
                }
            })
        data = json.dumps({
            "status": 200,
            "message": "Pilgrims Retrieved successfully",
            "response": {
                "pilgrims": vals,
            }
        })
        headers = [('Content-Type', 'application/json')]
        return request.make_response(data, headers)


    @http.route(
        "/api/get_pilgrim_by_id", auth="none", type="json", method="GET", csrf=False
    )
    def get_pilgrim_by_id(self, pilgrim_id=None, mobile=None, email=None):
        try:
            logger.info(f'get_pilgrim_by_id {request.httprequest.headers.environ}')
            logger.info(f'get_pilgrim_by_id {request.httprequest.headers}')
            uid = self.get_uid(request.httprequest.headers.environ)
            logger.info(f'get_pilgrim_by_id uid {uid}')
            logger.info(f'get_pilgrim_by_id param {pilgrim_id} - {mobile}- {email}')

            uid = self.get_uid(request.httprequest.headers.environ)
            domain = []
            if not uid:
                return {"status": "failure", "error": "Authentication failed"}
            if pilgrim_id:
                domain.append(('pilgrim_id', 'ilike', pilgrim_id))
            if mobile:
                domain.append(('mobile', 'ilike', mobile))
            if email:
                domain.append(('email', 'ilike', email))
            if domain:
                print('domain', domain)
                pilgrim = request.env['res.partner'].sudo().search(domain, limit=1)
                package = pilgrim.package_id
                if pilgrim:
                    pilgrim_data = pilgrim.sudo().get_pilgrim_data()[0]
                    print(pilgrim_data)
                    pilgrim_data.update({
                    "package": {
                        "ID": package.id,
                        "name": package.name,
                        "code": package.package_code,
                        "booking_customer": package.partner_id.name,
                        "guides": [g.name for g in package.guide_ids],
                        "closing_date": str(package.package_closing_date),
                        "flight_contracts": package.flight_contract_lines.mapped(
                            'flight_contract_id').get_contract_data(),
                        "transportation_contracts": [contract.transportation_contract_no for contract in
                                                     package.transportation_contract_ids],
                        'activities': {
                                'makkah': self._prepare_activities(package.makkah_activity_line_ids),
                                'madina': self._prepare_activities(package.madina_activity_line_ids),
                                'araf': self._prepare_activities(package.arfa_activity_line_ids),
                                'minah': self._prepare_activities(package.minah_activity_line_ids),
                                'hotel': self._prepare_activities(package.hotel_activity_line_ids),
                            }
                        }
                    })
                    return {"status": "success", "data": pilgrim_data}
                else:
                    return {"status": "success", 'msg': 'Not Found Pilgrim'}
            else:
                return {"status": "failure", "error": 'please send pilgrim_id or mobile or email'}
        except Exception:
            logger.error(f'get_pilgrim_by_id {traceback.format_exc()}')
            return {"status": "failure", "error": traceback.format_exc()}


    @http.route(
        "/api/update_pilgrim_status", auth="none", type="json", method="POST", csrf=False
    )
    def update_pilgrim_status(self,pilgrim_id , status):
        try:
            logger.info(f'update_pilgrim_status {request.httprequest.headers.environ}')
            uid = self.get_uid(request.httprequest.headers.environ)
            logger.info(f'update_pilgrim_status uid {uid}')
            logger.info(f'update_pilgrim_status status {pilgrim_id} - {status}')
            if not uid:
                return {"status": "failure", "error": "Authentication failed"}
            pilgrim = request.env['res.partner'].sudo().browse(int(pilgrim_id))
            pilgrim.write({'status': status})
            return {"status": "success", 'msg': 'Update Successfully'}
        except Exception:
            logger.error(f'update_pilgrim_status {traceback.format_exc()}')
            return {"status": "failure", "error": traceback.format_exc()}


    @http.route('/api/flight', auth='none',  csrf=False, type='http', methods=['GET'])
    def get_flights(self, **kw):
        uid = self.get_uid(request.httprequest.headers.environ)
        headers = [('Content-Type', 'application/json')]
        if not uid:
            data = json.dumps({
                "status": 403,
                "message": "Authentication failed",
            })
            return request.make_response(data, headers)
        flights = request.env['flight.schedule'].with_user(uid).search([])
        vals = flights.sudo().get_contract_data()
        data = json.dumps({
            "status": 200,
            "message": "Flight Contracts Retrieved successfully",
            "response": {
                "packages": vals,
            }
        })
        headers = [('Content-Type', 'application/json')]
        return request.make_response(data, headers)


    @http.route('/api/package/<string:package_code>/room/booked', auth='none', csrf=False, type='http', methods=['GET'])
    def get_package_booked_rooms(self, package_code, **kw):
        uid = self.get_uid(request.httprequest.headers.environ)
        headers = [('Content-Type', 'application/json')]
        if not uid:
            data = json.dumps({
                "status": 403,
                "message": "Authentication failed",
            })
            return request.make_response(data, headers)
        package = request.env['booking.package'].with_user(uid).search([('package_code', '=', package_code)])
        if not package:
            data = json.dumps({
                "status": 403,
                "message": "Invalid package code",
            })
            return request.make_response(data, headers)


        data = json.dumps({
            "status": 200,
            "message": "Booked Rooms retrieved successfully",
            "response": self.prepare_package_booked_rooms(package)
        })
        headers = [('Content-Type', 'application/json')]
        return request.make_response(data, headers)

    @http.route('/api/package/room/booked', auth='none', csrf=False, type='http', methods=['GET'])
    def get_all_package_booked_rooms(self, **kw):
        uid = self.get_uid(request.httprequest.headers.environ)
        headers = [('Content-Type', 'application/json')]
        if not uid:
            data = json.dumps({
                "status": 403,
                "message": "Authentication failed",
            })
            return request.make_response(data, headers)
        vals = []
        for package in request.env['booking.package'].with_user(uid).search([]):
            vals.append(self.prepare_package_booked_rooms(package))
        data = json.dumps({
            "status": 200,
            "message": "Booked Rooms retrieved successfully",
            "response": vals
        })
        headers = [('Content-Type', 'application/json')]
        return request.make_response(data, headers)

    @http.route('/api/package/<string:package_code>/bed/booked', auth='none', csrf=False, type='http', methods=['GET'])
    def get_package_booked_beds(self, package_code, **kw):
        uid = self.get_uid(request.httprequest.headers.environ)
        headers = [('Content-Type', 'application/json')]
        if not uid:
            data = json.dumps({
                "status": 403,
                "message": "Authentication failed",
            })
            return request.make_response(data, headers)
        package = request.env['booking.package'].with_user(uid).search([('package_code', '=', package_code)])
        if not package:
            data = json.dumps({
                "status": 403,
                "message": "Invalid package code",
            })
            return request.make_response(data, headers)


        data = json.dumps({
            "status": 200,
            "message": "Booked Beds retrieved successfully",
            "response": self.prepare_package_booked_beds(package)
        })
        headers = [('Content-Type', 'application/json')]
        return request.make_response(data, headers)

    @http.route('/api/package/bed/booked', auth='none', csrf=False, type='http', methods=['GET'])
    def get_all_package_booked_beds(self, **kw):
        uid = self.get_uid(request.httprequest.headers.environ)
        headers = [('Content-Type', 'application/json')]
        if not uid:
            data = json.dumps({
                "status": 403,
                "message": "Authentication failed",
            })
            return request.make_response(data, headers)
        vals = []
        for package in request.env['booking.package'].with_user(uid).search([]):
            vals.append(self.prepare_package_booked_beds(package))
        data = json.dumps({
            "status": 200,
            "message": "Booked Beds retrieved successfully",
            "response": vals
        })
        headers = [('Content-Type', 'application/json')]
        return request.make_response(data, headers)

    @http.route('/api/package/<string:package_code>/bed/available', auth='none', csrf=False, type='http', methods=['GET'])
    def get_package_available_beds(self, package_code, **kw):
        uid = self.get_uid(request.httprequest.headers.environ)
        headers = [('Content-Type', 'application/json')]
        if not uid:
            data = json.dumps({
                "status": 403,
                "message": "Authentication failed",
            })
            return request.make_response(data, headers)
        package = request.env['booking.package'].with_user(uid).search([('package_code', '=', package_code)])
        if not package:
            data = json.dumps({
                "status": 403,
                "message": "Invalid package code",
            })
            return request.make_response(data, headers)


        data = json.dumps({
            "status": 200,
            "message": "Available Beds retrieved successfully",
            "response": self.prepare_package_available_beds(package)
        })
        headers = [('Content-Type', 'application/json')]
        return request.make_response(data, headers)

    @http.route('/api/package/bed/available', auth='none', csrf=False, type='http', methods=['GET'])
    def get_all_package_available_beds(self, **kw):
        uid = self.get_uid(request.httprequest.headers.environ)
        headers = [('Content-Type', 'application/json')]
        if not uid:
            data = json.dumps({
                "status": 403,
                "message": "Authentication failed",
            })
            return request.make_response(data, headers)
        vals = []
        for package in request.env['booking.package'].with_user(uid).search([]):
            vals.append(self.prepare_package_available_beds(package))
        data = json.dumps({
            "status": 200,
            "message": "Available Beds retrieved successfully",
            "response": vals
        })
        headers = [('Content-Type', 'application/json')]
        return request.make_response(data, headers)

    @api.model
    def prepare_package_booked_rooms(self, package):
        return {
            "package": {
                "ID": package.id,
                "code": package.package_code,
                "makkah": {
                    "hotel": package.main_makkah.name,
                    "arrival_date": str(package.makkah_arrival_date),
                    "departure_date": str(package.makkah_departure_date),
                    "double": package.makkah_no_double,
                    "double_male": package.makka_double_male_beds,
                    "double_female": package.makka_double_female_beds,
                    "double_rate_plan": package.makkah_double_plan_id.name,
                    "triple": package.makkah_no_triple,
                    "triple_male": package.makka_triple_male_beds,
                    "triple_female": package.makka_triple_female_beds,
                    "triple_rate_plan": package.makkah_triple_plan_id.name,
                    "quad": package.makkah_no_quad,
                    "quad_rate_plan": package.makkah_quad_plan_id.name,
                    "quad_male": package.makka_quad_male_beds,
                    "quad_female": package.makka_quad_female_beds,
                },
                "madinah": {
                    "hotel": package.main_madinah.name,
                    "arrival_date": str(package.madinah_arrival_date),
                    "departure_date": str(package.madinah_departure_date),
                    "double": package.madinah_no_double,
                    "double_male": package.madinah_double_male_beds,
                    "double_female": package.madinah_double_female_beds,
                    "double_rate_plan": package.madinah_double_plan_id.name,
                    "triple": package.madinah_no_triple,
                    "triple_male": package.madinah_triple_male_beds,
                    "triple_female": package.madinah_triple_female_beds,
                    "triple_rate_plan": package.madinah_triple_plan_id.name,
                    "quad": package.madinah_no_quad,
                    "quad_male": package.madinah_quad_male_beds,
                    "quad_female": package.madinah_quad_female_beds,
                    "quad_rate_plan": package.madinah_quad_plan_id.name,
                },
                "arfa": {
                    "hotel": package.main_arfa.name,
                    "arrival_date": str(package.arfa_arrival_date),
                    "departure_date": str(package.arfa_departure_date),
                    # "double": package.arfa_no_double,
                    # "double_rate_plan": package.arfa_double_plan_id.name,
                    # "triple": package.arfa_no_triple,
                    # "triple_rate_plan": package.arfa_triple_plan_id.name,
                    # "quad": package.arfa_no_quad,
                    # "quad_rate_plan": package.arfa_quad_plan_id.name,
                },
                "minnah": {
                    "hotel": package.main_minnah.name,
                    "arrival_date": str(package.minnah_arrival_date),
                    "departure_date": str(package.minnah_departure_date),
                    # "double": package.minnah_no_double,
                    # "double_rate_plan": package.minnah_double_plan_id.name,
                    # "triple": package.minnah_no_triple,
                    # "triple_rate_plan": package.minnah_triple_plan_id.name,
                    # "quad": package.minnah_no_quad,
                    # "quad_rate_plan": package.minnah_quad_plan_id.name,
                },
                "main": {
                    "hotel": package.main_hotel.name,
                    "arrival_date": str(package.hotel_arrival_date),
                    "departure_date": str(package.hotel_departure_date),
                    "double": package.hotel_no_double,
                    "double_rate_plan": package.hotel_double_plan_id.name,
                    "triple": package.hotel_no_triple,
                    "triple_rate_plan": package.hotel_triple_plan_id.name,
                    "quad": package.hotel_no_quad,
                    "quad_rate_plan": package.hotel_quad_plan_id.name,
                },
            },
        }

    @api.model
    def prepare_package_booked_beds(self, package):
        return {
            "package": {
                "ID": package.id,
                "code": package.package_code,
                "makkah": {
                    "hotel": package.main_makkah.name,
                    "arrival_date": str(package.makkah_arrival_date),
                    "departure_date": str(package.makkah_departure_date),
                    "double_male": package.makkah_double_male_booked_beds,
                    "double_female": package.makkah_double_female_booked_beds,
                    "triple_male": package.makkah_triple_male_booked_beds,
                    "triple_female": package.makkah_triple_female_booked_beds,
                    "quad_male": package.makkah_quad_male_booked_beds,
                    "quad_female": package.makkah_quad_female_booked_beds,
                },
                "madinah": {
                    "hotel": package.main_madinah.name,
                    "arrival_date": str(package.madinah_arrival_date),
                    "departure_date": str(package.madinah_departure_date),
                    "double_male": package.madinah_double_male_booked_beds,
                    "double_female": package.madinah_double_female_booked_beds,
                    "triple_male": package.madinah_triple_male_booked_beds,
                    "triple_female": package.madinah_triple_female_booked_beds,
                    "quad_male": package.madinah_quad_male_booked_beds,
                    "quad_female": package.madinah_quad_female_booked_beds,
                },
                "arfa": {
                    "hotel": package.main_arfa.name,
                    "arrival_date": str(package.arfa_arrival_date),
                    "departure_date": str(package.arfa_departure_date),
                    # "double": package.arfa_double_booked_beds,
                    # "triple": package.arfa_triple_booked_beds,
                    # "quad": package.arfa_quad_booked_beds,
                },
                "minnah": {
                    "hotel": package.main_minnah.name,
                    "arrival_date": str(package.minnah_arrival_date),
                    "departure_date": str(package.minnah_departure_date),
                    # "double": package.minnah_double_booked_beds,
                    # "triple": package.minnah_triple_booked_beds,
                    # "quad": package.minnah_quad_booked_beds,
                },
                "main": {
                    "hotel": package.main_hotel.name,
                    "arrival_date": str(package.hotel_arrival_date),
                    "departure_date": str(package.hotel_departure_date),
                    "double": package.hotel_double_booked_beds,
                    "triple": package.hotel_triple_booked_beds,
                    "quad": package.hotel_quad_booked_beds,
                },
            },
        }

    @api.model
    def prepare_package_available_beds(self, package):
        return {
            "package": {
                "ID": package.id,
                "code": package.package_code,
                "makkah": {
                    "hotel": package.main_makkah.name,
                    "arrival_date": str(package.makkah_arrival_date),
                    "departure_date": str(package.makkah_departure_date),
                    "double_male": package.makkah_double_male_available_beds,
                    "double_female": package.makkah_double_female_available_beds,
                    "triple_male": package.makkah_triple_male_available_beds,
                    "triple_female": package.makkah_triple_female_available_beds,
                    "quad_male": package.makkah_quad_male_available_beds,
                    "quad_female": package.makkah_quad_female_available_beds,
                },
                "madinah": {
                    "hotel": package.main_madinah.name,
                    "arrival_date": str(package.madinah_arrival_date),
                    "departure_date": str(package.madinah_departure_date),
                    "double_male": package.madinah_double_male_booked_beds,
                    "double_female": package.madinah_double_female_available_beds,
                    "triple_male": package.madinah_triple_male_available_beds,
                    "triple_female": package.madinah_triple_female_available_beds,
                    "quad_male": package.madinah_quad_male_available_beds,
                    "quad_female": package.madinah_quad_female_available_beds,
                },
                "arfa": {
                    "hotel": package.main_arfa.name,
                    "arrival_date": str(package.arfa_arrival_date),
                    "departure_date": str(package.arfa_departure_date),
                    # "double": package.arfa_double_available_beds,
                    # "triple": package.arfa_triple_available_beds,
                    # "quad": package.arfa_quad_available_beds,
                },
                "minnah": {
                    "hotel": package.main_minnah.name,
                    "arrival_date": str(package.minnah_arrival_date),
                    "departure_date": str(package.minnah_departure_date),
                    # "double": package.minnah_double_available_beds,
                    # "triple": package.minnah_triple_available_beds,
                    # "quad": package.minnah_quad_available_beds,
                },
                "main": {
                    "hotel": package.main_hotel.name,
                    "arrival_date": str(package.hotel_arrival_date),
                    "departure_date": str(package.hotel_departure_date),
                    "double": package.hotel_double_available_beds,
                    "triple": package.hotel_triple_available_beds,
                    "quad": package.hotel_quad_available_beds,
                },
            },
        }

    @http.route('/api/hotel/<string:hotel_id>/floor', auth='none', csrf=False, type='http', methods=['GET'])
    def get_hotel_floor(self, hotel_id, **kw):
        uid = self.get_uid(request.httprequest.headers.environ)
        headers = [('Content-Type', 'application/json')]
        if not uid:
            data = json.dumps({
                "status": 403,
                "message": "Authentication failed",
            })
            return request.make_response(data, headers)
        hotel_id = request.env['hotel.hotel'].with_user(uid).browse(hotel_id)
        if not hotel_id:
            data = json.dumps({
                "status": 403,
                "message": "Invalid hotel",
            })
            return request.make_response(data, headers)
        vals = []
        for floor in request.env['hotel.floor'].with_user(uid).search([('hotel_id', '=', int(hotel_id.id))]):
            vals.append({
                "ID": floor.id,
                "name": floor.name,
            })
        data = json.dumps({
            "status": 200,
            "message": "Floors retrieved successfully",
            "response": vals
        })
        headers = [('Content-Type', 'application/json')]
        return request.make_response(data, headers)

    @http.route('/api/group/assign_room', auth='none', csrf=False, type='json', methods=['POST'])
    def group_assign_room(self, **kw):
        uid = self.get_uid(request.httprequest.headers.environ)
        headers = [('Content-Type', 'application/json')]
        if not uid:
            return {
                "status": 403,
                "message": "Authentication failed",
            }
        args = request.httprequest.data.decode()
        args = json.loads(args)
        lang = request.httprequest.accept_languages.best
        required_fields = {
            'booking_number': 'رقم الحجز',
            'from_floor': 'من الطابق',
            'to_floor': 'الي الطابق',
        }
        for k, v in required_fields.items():
            if not args.get(k, False):
                return {
                    "status": 405,
                    "message": f" برجاء إدخال {v}" if lang == 'ar' else f"{k} is missing!",
                }
        booking_id = request.env['hotel.booking'].with_user(uid).search([('name', '=', args['booking_number'])])
        if not booking_id:
            return {
                "status": 403,
                "message": "Invalid booking number",
            }
        folios = booking_id.folio_ids.filtered(lambda f: f.state in ['draft', 'confirmed']).ids
        wizard = request.env['booking.group.action'].with_user(uid).create({
            'booking_id': booking_id.id,
            'type': 'assign',
            'floor_start': args['from_floor'],
            'floor_end': args['to_floor'],
            'assign_clean_room': args.get('assign_clean_room', False),
            'folio_ids': [(6, 0, folios)],
        })
        wizard.button_auto_assign()
        return {
            "status": 200,
            "message": f"Booking {booking_id.sudo().name} rooms has been assigned successfully!",
        }

    @http.route('/api/package/assign_guest', auth='none', csrf=False, type='json', methods=['POST'])
    def assign_package_guest(self, **kw):
        uid = self.get_uid(request.httprequest.headers.environ)
        headers = [('Content-Type', 'application/json')]
        if not uid:
            return {
                "status": 403,
                "message": "Authentication failed",
            }
        args = request.httprequest.data.decode()
        args = json.loads(args)
        lang = request.httprequest.accept_languages.best
        required_fields = {
            'booking_number': 'رقم الحجز',
            'assign_type': 'التعيين',
        }
        for k, v in required_fields.items():
            if not args.get(k, False):
                return {
                    "status": 405,
                    "message": f" برجاء إدخال {v}" if lang == 'ar' else f"{k} is missing!",
                }
        booking_id = request.env['hotel.booking'].with_user(uid).search([('name', '=', args['booking_number'])])
        if not booking_id:
            return {
                "status": 403,
                "message": "Invalid booking number",
            }
        if not booking_id.package_id:
            return {
                "status": 403,
                "message": "Booking has no package",
            }
        if booking_id.package_assign_type not in ['gender', 'family_member']:
            return {
                "status": 403,
                "message": "Booking assign type should br gender or family_member",
            }
        booking_id.with_user(uid).write({
            'package_assign_type': args['assign_type']
        })
        try:
            booking_id.button_assign_guests()
            return {
                "status": 200,
                "message": f"Booking {booking_id.sudo().name} rooms has been assigned successfully!",
            }
        except Exception as e:
            return {
                "status": 403,
                "message": e,
            }

    @http.route('/api/hajj/<string:passport>/room', auth='none', csrf=False, type='http', methods=['GET'])
    def get_hajj_room(self, passport, **kw):
        uid = self.get_uid(request.httprequest.headers.environ)
        headers = [('Content-Type', 'application/json')]
        if not uid:
            data = json.dumps({
                "status": 403,
                "message": "Authentication failed",
            })
            return request.make_response(data, headers)
        partner_id = request.env['res.partner'].with_user(uid).search([('passport_no', '=', passport)])
        if not partner_id:
            data = json.dumps({
                "status": 403,
                "message": "Invalid passport",
            })
            return request.make_response(data, headers)
        vals = []
        package_id = partner_id.package_id
        if not package_id:
            data = json.dumps({
                "status": 403,
                "message": "No Package related to this hajj",
            })
            return request.make_response(data, headers)
        for booking in package_id.booking_ids:
            guest_id = booking.guest_ids.filtered(lambda g: g.partner_id.id == partner_id.id)
            if not guest_id.folio_id:
                data = json.dumps({
                    "status": 403,
                    "message": "hajj is not assigned to room yet!",
                })
                return request.make_response(data, headers)
            vals.append({
                "booking_number": booking.name,
                "folio": guest_id.folio_id.name,
                "room": guest_id.folio_id.room_id.name,
            })
        data = json.dumps({
            "status": 200,
            "message": "Floors retrieved successfully",
            "response": vals
        })
        headers = [('Content-Type', 'application/json')]
        return request.make_response(data, headers)

    @http.route('/api/hajj/checkin', auth='none', csrf=False, type='json', methods=['POST'])
    def checkin_hajj_bed(self, **kw):
        uid = self.get_uid(request.httprequest.headers.environ)
        headers = [('Content-Type', 'application/json')]
        if not uid:
            return {
                "status": 403,
                "message": "Authentication failed",
            }
        args = request.httprequest.data.decode()
        args = json.loads(args)
        lang = request.httprequest.accept_languages.best
        required_fields = {
            'passport': 'رقم جواز السفر',
            'booking_number': 'رقم الحجز',
        }
        for k, v in required_fields.items():
            if not args.get(k, False):
                return {
                    "status": 405,
                    "message": f" برجاء إدخال {v}" if lang == 'ar' else f"{k} is missing!",
                }
        booking_id = request.env['hotel.booking'].with_user(uid).search([('name', '=', args['booking_number'])])
        if not booking_id:
            return {
                "status": 403,
                "message": "Invalid booking number",
            }
        if not booking_id.package_id:
            return {
                "status": 403,
                "message": "Booking has no package",
            }
        partner_id = request.env['res.partner'].with_user(uid).search([('passport_no', '=', args['passport'])])
        if not partner_id:
            return {
                "status": 403,
                "message": "Invalid passport",
            }
        guest_id = booking_id.guest_ids.filtered(lambda g: g.partner_id.id == partner_id.id)
        if not guest_id.folio_id:
            return {
                "status": 403,
                "message": "hajj is not assigned to room yet!",
            }
        bed = guest_id.folio_id.bed_ids.filtered(lambda b: b.partner_id.id == partner_id.id)
        if not bed:
            return {
                "status": 403,
                "message": "hajj is not assigned to bed yet!",
            }
        try:
            bed.button_check_in()
            return {
                "status": 200,
                "message": f"Hajj {partner_id.sudo().name} has checked in successfully!",
            }
        except Exception as e:
            return {
                "status": 403,
                "message": e,
            }

    @http.route('/api/hajj/checkout', auth='none', csrf=False, type='json', methods=['POST'])
    def checkout_hajj_bed(self, **kw):
        uid = self.get_uid(request.httprequest.headers.environ)
        headers = [('Content-Type', 'application/json')]
        if not uid:
            return {
                "status": 403,
                "message": "Authentication failed",
            }
        args = request.httprequest.data.decode()
        args = json.loads(args)
        lang = request.httprequest.accept_languages.best
        required_fields = {
            'passport': 'رقم جواز السفر',
            'booking_number': 'رقم الحجز',
        }
        for k, v in required_fields.items():
            if not args.get(k, False):
                return {
                    "status": 405,
                    "message": f" برجاء إدخال {v}" if lang == 'ar' else f"{k} is missing!",
                }
        booking_id = request.env['hotel.booking'].with_user(uid).search([('name', '=', args['booking_number'])])
        if not booking_id:
            return {
                "status": 403,
                "message": "Invalid booking number",
            }
        if not booking_id.package_id:
            return {
                "status": 403,
                "message": "Booking has no package",
            }
        partner_id = request.env['res.partner'].with_user(uid).search([('passport_no', '=', args['passport'])])
        if not partner_id:
            return {
                "status": 403,
                "message": "Invalid passport",
            }
        guest_id = booking_id.guest_ids.filtered(lambda g: g.partner_id.id == partner_id.id)
        if not guest_id.folio_id:
            return {
                "status": 403,
                "message": "hajj is not assigned to room yet!",
            }
        bed = guest_id.folio_id.bed_ids.filtered(lambda b: b.partner_id.id == partner_id.id)
        if not bed:
            return {
                "status": 403,
                "message": "hajj is not assigned to bed yet!",
            }
        try:
            bed.button_check_out()
            return {
                "status": 200,
                "message": f"Hajj {partner_id.sudo().name} has checked out successfully!",
            }
        except Exception as e:
            return {
                "status": 403,
                "message": e,
            }
    @http.route('/api/account/journal', auth='none', csrf=False, type='http', methods=['GET'])
    def get_journals(self, **kw):
        uid = self.get_uid(request.httprequest.headers.environ)
        headers = [('Content-Type', 'application/json')]
        if not uid:
            data = json.dumps({
                "status": 403,
                "message": "Authentication failed",
            })
            return request.make_response(data, headers)
        hotels = request.env['hotel.hotel'].with_user(uid).search([])
        vals = {}
        for hotel in hotels:
            hotel_vals = []
            journals = request.env['account.journal'].with_user(uid).search([
                ('company_id', '=', hotel.company_id.id), ('type', 'in', ['bank', 'cash']),
            ])
            if journals:
                for journal in journals:
                    hotel_vals.append({
                        "ID": journal.id,
                        "name": journal.name,
                    })
                vals[hotel.name] = hotel_vals
        data = json.dumps({
            "status": 200,
            "message": "Journals retrieved successfully",
            "response": vals
        })
        headers = [('Content-Type', 'application/json')]
        return request.make_response(data, headers)

    @http.route('/api/account/currency', auth='none', csrf=False, type='http', methods=['GET'])
    def get_currencies(self, **kw):
        uid = self.get_uid(request.httprequest.headers.environ)
        headers = [('Content-Type', 'application/json')]
        if not uid:
            data = json.dumps({
                "status": 403,
                "message": "Authentication failed",
            })
            return request.make_response(data, headers)
        currencies = request.env['res.currency'].with_user(uid).search([])
        vals = []
        for currency in currencies:
            vals.append({
                "ID": currency.id,
                "name": currency.name,
            })
        data = json.dumps({
            "status": 200,
            "message": "Currencies retrieved successfully",
            "response": vals
        })
        headers = [('Content-Type', 'application/json')]
        return request.make_response(data, headers)

    @http.route('/api/folio/register_payment', auth='none', csrf=False, type='json', methods=['POST'])
    def register_folio_payment(self, **kw):
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
            'folio_number': 'رقم الفوليو',
            'journal_id': 'دفتر اليومية',
            'amount': 'المبلغ',
            'currency_id': 'العملة',
            'payment_date': 'تاريخ الدفع',
        }
        for k, v in required_fields.items():
            if not args.get(k, False):
                return {
                    "status": 405,
                    "message": f" برجاء إدخال {v}" if lang == 'ar' else f"{k} is missing!",
                }
        folio_id = request.env['booking.folio'].with_user(uid).search([('name', '=', args['folio_number'])])
        if not folio_id:
            return {
                "status": 403,
                "message": "Invalid folio number",
            }
        wizard = request.env['booking.payment.register'].with_user(uid).create({
            'folio_id': folio_id.id,
            'booking': folio_id.booking_id.id,
            'payment_type': 'inbound',
            'partner_type': 'customer',
            'journal_id': args['journal_id'],
            'notes': args.get('notes', False),
            'payment_note': args.get('payment_note', False),
            'amount': args['amount'],
            'currency_id': args['currency_id'],
            'payment_date': args['payment_date'],
            'communication': folio_id.name
        })
        try:
            wizard.action_create_payments()
            return {
                "status": 200,
                "message": f"Folio {folio_id.sudo().name} has been paid successfully!",
            }
        except Exception as e:
            return {
                "status": 403,
                "message": e,
            }

    @http.route('/api/booking/register_payment', auth='none', csrf=False, type='json', methods=['POST'])
    def register_booking_payment(self, **kw):
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
            'booking_number': 'رقم الفوليو',
            'journal_id': 'دفتر اليومية',
            'amount': 'المبلغ',
            'currency_id': 'العملة',
            'payment_date': 'تاريخ الدفع',
        }
        for k, v in required_fields.items():
            if not args.get(k, False):
                return {
                    "status": 405,
                    "message": f" برجاء إدخال {v}" if lang == 'ar' else f"{k} is missing!",
                }
        booking_id = request.env['hotel.booking'].with_user(uid).search([('name', '=', args['booking_number'])])
        if not booking_id:
            return {
                "status": 403,
                "message": "Invalid booking number",
            }
        if not booking_id.quick_group_booking:
            return {
                "status": 403,
                "message": "Booking should be group booking",
            }
        if args.get('select_all', False):
            booking_folio_ids = booking_id.folio_ids.filtered(lambda f: f.state != 'cancelled').ids
            folio_ids = request.env['booking.folio'].browse(booking_folio_ids)
        else:
            folio_ids = False
        wizard = request.env['booking.payment.register'].with_user(uid).create({
            'booking': booking_id.id,
            'payment_type': 'inbound',
            'partner_type': 'customer',
            'journal_id': args['journal_id'],
            'notes': args.get('notes', False),
            'payment_note': args.get('payment_note', False),
            'amount': args['amount'],
            'currency_id': args['currency_id'],
            'payment_date': args['payment_date'],
            'communication': booking_id.folio_ids[0].name,
            'select_all': args.get('select_all', False),
            'folio_ids': [(6, 0, folio_ids.ids)] if folio_ids else False
        })
        try:
            wizard.action_create_payments()
            return {
                "status": 200,
                "message": f"Booking {booking_id.sudo().name} has been paid successfully!",
            }
        except Exception as e:
            return {
                "status": 403,
                "message": e,
            }

    @http.route('/api/room', auth='none', csrf=False, type='http', methods=['GET'])
    def get_rooms(self, **kw):
        uid = self.get_uid(request.httprequest.headers.environ)
        headers = [('Content-Type', 'application/json')]
        if not uid:
            data = json.dumps({
                "status": 403,
                "message": "Authentication failed",
            })
            return request.make_response(data, headers)
        hotels = request.env['hotel.hotel'].with_user(uid).search([])
        vals = {}
        for hotel in hotels:
            hotel_vals = []
            rooms = request.env['hotel.room'].with_user(uid).search([('company_id', '=', hotel.company_id.id)])
            if rooms:
                for room in rooms:
                    hotel_vals.append({
                        "ID": room.id,
                        "name": room.name,
                    })
                vals[hotel.name] = hotel_vals
        data = json.dumps({
            "status": 200,
            "message": "Rooms retrieved successfully",
            "response": vals
        })
        headers = [('Content-Type', 'application/json')]
        return request.make_response(data, headers)


    @http.route('/api/room/<int:room_id>', auth='none', csrf=False, type='http', methods=['GET'])
    def get_room_info(self, room_id, **kw):
        uid = self.get_uid(request.httprequest.headers.environ)
        headers = [('Content-Type', 'application/json')]
        if not uid:
            data = json.dumps({
                "status": 403,
                "message": "Authentication failed",
            })
            return request.make_response(data, headers)
        room_id = request.env['hotel.room'].with_user(uid).browse(room_id)
        if not room_id:
            data = json.dumps({
                "status": 403,
                "message": "Invalid room id",
            })
            return request.make_response(data, headers)
        audit_date = room_id.company_id.audit_date
        folio = request.env['booking.folio'].search([('room_id', '=', room_id.id)]).filtered(
            lambda f: f.check_in_date <= audit_date <= f.check_out_date and f.state in ['part_checked_in','checked_in','confirmed'])
        vals = {
            'name': room_id.name,
            'hotel': room_id.hotel_id.name,
            'stay_state': room_id.stay_state.name,
            'housekeeping_state': room_id.state.name,
        }
        if folio:
            vals.update({
                'booking_number': folio.booking_id.name,
                'booking_date': str(folio.create_date),
                'folio_number': folio.name,
                'folio_state': folio.state,
                'guest_name': folio.partner_id.name,
                'check_in': str(folio.check_in),
                'check_out': str(folio.check_out),
                'total_nights': folio.total_nights,
                'price_total': folio.price_total,
                'paid_amount': folio.price_paid,
                'price_due': folio.price_due,
                'total_beds': folio.total_beds,
                'available_beds': folio.available_beds,
                'number_of_guests': folio.number_of_guests,
            })
        data = json.dumps({
            "status": 200,
            "message": "Room retrieved successfully",
            "response": vals
        })
        headers = [('Content-Type', 'application/json')]
        return request.make_response(data, headers)
