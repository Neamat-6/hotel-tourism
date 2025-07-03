from odoo import api, fields, models, exceptions
from .rest_htask import HTASK


class RoomType(models.Model):
    _inherit = 'room.type'
    _htask_type = "RoomInfo"

    room_id = fields.Char(string="Room ID")
    ezee_room_type_id = fields.Many2one('ezee.room.type', string='Ezee Room Type')

    def create_hotel_rooms(self):
        rooms_info = HTASK.get_htask_connector(self, self._htask_type)
        rooms_info_request_params = {
            "RES_Request": {
                "Request_Type": "RoomInfo",
                "NeedPhysicalRooms": 0,
                "Authentication": {
                    "HotelCode": rooms_info.hotel_code,
                    "AuthCode": rooms_info.auth_code
                }
            }
        }

        try:
            res = rooms_info.get_post(arguments={}, data=rooms_info_request_params)
            rooms_info_dic = res.get('RoomInfo', {})
        except Exception as e:
            raise exceptions.UserError(f"Error fetching room information: {e}")

        self.create_room_types(rooms_info_dic.get('RoomTypes', {}).get('RoomType', []))
        self.create_rate_types(rooms_info_dic.get('RateTypes', {}).get('RateType', []))
        self.create_rate_plans(rooms_info_dic.get('RatePlans', {}).get('RatePlan', []))

    def create_room_types(self, room_types):
        for room in room_types:
            room_vals = {
                'name': room.get('Name'),
                'code': room.get('ID'),
            }
            room_type = self.env['ezee.room.type'].search([('name', '=', room_vals['name'])])
            if not room_type:
                room_type_obj = self.env['ezee.room.type'].sudo().create(room_vals)
            else:
                room_type_obj = room_type.write(room_vals)

    def create_rate_types(self, rate_types):
        for rate in rate_types:
            rate_type_vals = {
                'name': rate.get('Name'),
                'code': rate.get('ID'),
            }
            hotel_rate_type = self.env['ezee.rate.type'].search([('name', '=', rate_type_vals['name'])])
            if not hotel_rate_type:
                hotel_rate_type_obj = self.env['ezee.rate.type'].sudo().create(rate_type_vals)
            else:
                hotel_rate_type_obj = hotel_rate_type.sudo().write(rate_type_vals)

    def create_rate_plans(self, rate_plans):
        for plan in rate_plans:
            room_type_obj = self.env['ezee.room.type'].search([('name', '=', plan.get('RoomType'))])
            if not room_type_obj:
                room_type_obj = self.env['ezee.room.type'].sudo().create({'name': plan.get('RoomType')})

            rate_type_obj = self.env['ezee.rate.type'].search([('name', '=', plan.get('RateType'))])
            rate_plan_vals = {
                'code': plan.get('RatePlanID'),
                'name': plan.get('Name'),
                'room_type_id': room_type_obj.id,
                'rate_type_id': rate_type_obj.id,
            }
            ezee_rate_plan = self.env['ezee.rate.plan'].search([('code', '=', plan.get('RatePlanID'))])
            if not ezee_rate_plan:
                hotel_rate_plan_obj = self.env['ezee.rate.plan'].sudo().create(rate_plan_vals)
            else:
                hotel_rate_plan_obj = ezee_rate_plan.sudo().write(rate_plan_vals)
