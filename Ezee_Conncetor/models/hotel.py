import requests
import json
from odoo import fields, models, api
import logging
logger = logging.getLogger(__name__)


class Hotel(models.Model):
    _inherit = 'hotel.hotel'

    enable_ezee = fields.Boolean()
    ezee_base_url = fields.Char()
    ezee_hotel_code = fields.Char()
    ezee_api_key = fields.Char()

    def get_ezee_extra_charge(self):
        base_url = self.ezee_base_url
        url = f"{base_url}booking/reservation_api/listing.php"
        params = {
            "request_type": "ExtraCharges",
            "HotelCode": self.ezee_hotel_code,
            "APIKey": self.ezee_api_key,
            "language": "en",
            "publishtoweb": "1"
        }
        response = requests.get(url, params=params)
        charges = json.loads(response.content)
        for charge in charges:
            if charge.get('charge', False):
                vals = {
                    'name': charge['charge'],
                    'ezee_id': charge['ExtraChargeId'],
                    'short_code': charge.get('ShortCode', False),
                    'rate': charge.get('Rate', False),
                    'hotel_id': self.id,
                    'company_id': self.env['res.company'].search([('related_hotel_id', '=', self.id)]).id
                }
                extra_charge = self.env['ezee.extra.charge'].search([('ezee_id', '=', charge['ExtraChargeId'])])
                if extra_charge:
                    extra_charge.write(vals)
                else:
                    self.env['ezee.extra.charge'].create(vals)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Ezee',
                'message': 'Charges Retrieved Successfully',
                'type': 'success',
                'sticky': False,
            },
        }

    def get_ezee_room_type(self):
        logger.info('callleddddddddddd get_ezee_room_type')
        base_url = self.ezee_base_url
        url = f"{base_url}booking/reservation_api/listing.php"
        logger.info(f'callleddddddddddd get_ezee_room_type {url}')
        params = {
            "request_type": "RoomTypeList",
            "HotelCode": self.ezee_hotel_code,
            "APIKey": self.ezee_api_key,
            "language": "en",
            "publishtoweb": "1"
        }
        logger.info(f'callleddddddddddd get_ezee_room_type {params}')
        response = requests.get(url, params=params)
        logger.info(f'callleddddddddddd get_ezee_room_type {response.status_code}')
        logger.info(f'callleddddddddddd get_ezee_room_type {response.content}')
        room_types = json.loads(response.content)
        logger.info(f'callleddddddddddd get_ezee_room_type {room_types}')
        for room_type in room_types:
            if room_type.get('roomtype', False):
                vals = {
                    'name': room_type['roomtype'],
                    'code': room_type['roomtypeunkid'],
                    'short_code': room_type.get('shortcode', False),
                    'base_adult_occupancy': room_type.get('base_adult_occupancy', 0),
                    'base_child_occupancy': room_type.get('base_child_occupancy', 0),
                    'max_adult_occupancy': room_type.get('max_adult_occupancy', 0),
                    'max_child_occupancy': room_type.get('max_child_occupancy', 0),
                    'hotel_id': self.id,
                    'company_id': self.env['res.company'].search([('related_hotel_id', '=', self.id)]).id
                }
                room_type = self.env['ezee.room.type'].search([('code', '=', room_type['roomtypeunkid'])])
                if room_type:
                    room_type.write(vals)
                else:
                    self.env['ezee.room.type'].create(vals)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Ezee',
                'message': 'Room Types Retrieved Successfully',
                'type': 'success',
                'sticky': False,
            },
        }

    def get_ezee_rate_plan(self):
        base_url = self.ezee_base_url
        headers = {
            "Content-Type": "application/json"
        }
        url = f"{base_url}pmsinterface/pms_connectivity.php"
        data = {
            "RES_Request": {
                "Request_Type": "RoomInfo",
                "NeedPhysicalRooms": 1,
                "Authentication": {
                    "HotelCode": self.ezee_hotel_code,
                    "AuthCode": self.ezee_api_key
                }
            }
        }

        response = requests.post(url, headers=headers, json=data)
        data = json.loads(response.content)
        if data.get('RoomInfo', False):
            rate_types = data['RoomInfo'].get('RateTypes', False)
            if rate_types:
                rate_types = data['RoomInfo']['RateTypes'].get('RateType', False)
                for rate_type in rate_types:
                    if rate_type.get('Name', False):
                        vals = {
                            'name': rate_type['Name'],
                            'code': rate_type['ID'],
                            'hotel_id': self.id,
                            'company_id': self.env['res.company'].search([('related_hotel_id', '=', self.id)]).id
                        }
                        ezee_rate_type = self.env['ezee.rate.type'].search([('code', '=', rate_type['ID'])])
                        if ezee_rate_type:
                            ezee_rate_type.write(vals)
                        else:
                            self.env['ezee.rate.type'].create(vals)
            rate_plans = data['RoomInfo'].get('RateTypes', False)
            if rate_plans:
                rate_plans = data['RoomInfo']['RatePlans'].get('RatePlan', False)
                for rate_plan in rate_plans:
                    if rate_plan.get('Name', False):
                        ezee_room_type_id = self.env['ezee.room.type'].search([('code', '=', rate_plan['RoomTypeID'])])
                        ezee_rate_type_id = self.env['ezee.rate.type'].search([('code', '=', rate_plan['RateTypeID'])])
                        vals = {
                            'name': rate_plan['Name'],
                            'code': rate_plan['RatePlanID'],
                            'room_type_id': ezee_room_type_id.id if ezee_room_type_id else False,
                            'rate_type_id': ezee_rate_type_id.id if ezee_rate_type_id else False,
                            'hotel_id': self.id,
                            'company_id': self.env['res.company'].search([('related_hotel_id', '=', self.id)]).id
                        }
                        ezee_rate_plan = self.env['ezee.rate.plan'].search([('code', '=', rate_plan['RatePlanID'])])
                        if ezee_rate_plan:
                            ezee_rate_plan.write(vals)
                        else:
                            self.env['ezee.rate.plan'].create(vals)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Ezee',
                'message': 'Room Plans Retrieved Successfully',
                'type': 'success',
                'sticky': False,
            },
        }
