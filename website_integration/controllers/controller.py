# -*- coding: utf-8 -*-
import itertools
from operator import itemgetter

from odoo import http, _, models
from odoo.http import request, content_disposition
import random, base64
from ast import literal_eval
import re
from odoo.tools import image_process
import phonenumbers
import base64
import json


class HotelWebsiteAPI(http.Controller):

    @http.route('/create_user', method=['POST'], type='json', auth="public", cors="*")
    def create_user(self):
        args = literal_eval(request.httprequest.data.decode('utf-8'))
        pat = "^[a-zA-Z0-9-_]+@[a-zA-Z0-9]+\.[a-z]{1,3}$"
        if 'name' not in args:
            return {
                "Code": 500,
                "StatusDescription": "Failed",
                "Data": {},
                "ArabicMessage": "اسم المستخدم غير موجود",
                "EnglishMessage": "Name Is Required"
            }
        if 'email' not in args:
            return {
                "Code": 500,
                "StatusDescription": "Failed",
                "Data": {},
                "ArabicMessage": "البريد الالكتروني غير موجود",
                "EnglishMessage": "Email Is Required"
            }
        if 'email' in args and not re.match(pat, args.get('email')):
            return {
                "Code": 500,
                "StatusDescription": "Failed",
                "Data": {},
                "ArabicMessage": "البريد الالكتروني غير صالح",
                "EnglishMessage": "Email Is not Valid"
            }
        if 'mobile' not in args:
            return {
                "Code": 500,
                "StatusDescription": "Failed",
                "Data": {},
                "ArabicMessage": "رقم الهاتف غير موجود",
                "EnglishMessage": "Mobile Is Required"
            }
        if 'mobile' in args:
            try:
                mobile_number = phonenumbers.parse(args.get('mobile'))
                if phonenumbers.is_valid_number(mobile_number):
                    pass
            except Exception as e:
                return {
                    "Code": 500,
                    "StatusDescription": "Failed",
                    "Data": {},
                    "ArabicMessage": "رقم الهاتف غير صالح",
                    "EnglishMessage": str(e)
                }
        if 'password' not in args:
            return {
                "Code": 500,
                "StatusDescription": "Failed",
                "Data": {},
                "ArabicMessage": "كلمة المرور غير موجودة",
                "EnglishMessage": "Password Is Required"
            }
        if 'partner_type' not in args:
            return {
                "Code": 500,
                "StatusDescription": "Failed",
                "Data": {},
                "ArabicMessage": "نوع جهة الاتصال غير موجودة",
                "EnglishMessage": "Partner Type Is Required"
            }
        if args.get('partner_type') not in ['person', 'company']:
            return {
                "Code": 500,
                "StatusDescription": "Failed",
                "Data": {},
                "ArabicMessage": "نوع جهة الاتصال غير صالحة",
                "EnglishMessage": "Partner Type Is Not Valid"
            }
        if args.get('travel_type') not in ['agent', 'company']:
            return {
                "Code": 500,
                "StatusDescription": "Failed",
                "Data": {},
                "ArabicMessage": "نوع  السفر غير صالحة",
                "EnglishMessage": "Travel Type Is Not Valid"
            }
        res_users_objs = request.env['res.users'].sudo().search(['|', ('login', '=', args.get('email')), ('mobile', '=', args.get('mobile'))],limit=1)
        if res_users_objs:
            return "User is Already Registered"
        else:
            try:
                # create user
                res_user_obj = request.env['res.users'].sudo().create({
                    'name': args.get('name'),
                    'login': args.get('email'),
                    'password': args.get('password'),
                    'mobile': args.get('mobile'),
                    'groups_id': [(6, 0, [request.env.ref('base.group_portal').id])],
                })
                # update partner info
                res_user_obj.partner_id.company_type = args.get('partner_type')
                res_user_obj.partner_id.mobile = args.get('mobile')
                res_user_obj.partner_id.email = args.get('email')
                res_user_obj.partner_id.travel_type = args.get('travel_type')
            except Exception as e:
                return {
                    "Code": 500,
                    "StatusDescription": "Failed",
                    "Data": {},
                    "ArabicMessage": "حدثت مشكلة يرجي المحاولة مرة اخري",
                    "EnglishMessage": str(e)
                }
        return {
            "Code": 200,
            "StatusDescription": "Success",
            "Data": {'UserID': res_user_obj.id},
            "ArabicMessage": "تم الاضافة بنجــاح",
            "EnglishMessage": "User Registered successfully"
        }

    @http.route('/user_login', method=['POST'], type='json', auth="public", cors="*")
    def check_authenticate(self):
        args = literal_eval(request.httprequest.data.decode('utf-8'))
        if 'db' not in args:
            return {
                "Code": 500,
                "StatusDescription": "Failed",
                "Data": {},
                "ArabicMessage": "اسم الداتابيز غير موجود",
                "EnglishMessage": "DB Is Required"
            }
        if 'login' not in args:
            return {
                "Code": 500,
                "StatusDescription": "Failed",
                "Data": {},
                "ArabicMessage": "اسم المستخدم غير موجود",
                "EnglishMessage": "Login Is Required"
            }
        if 'password' not in args:
            return {
                "Code": 500,
                "StatusDescription": "Failed",
                "Data": {},
                "ArabicMessage": "كلمه المرور غير موجود",
                "EnglishMessage": "password Is Required"
            }
        user_authenticate = request.session.authenticate(args.get('db'), args.get('login'), args.get('password'))
        session_info = request.session
        # return session_info
        # session_info = request.env['ir.http'].sudo().session_info()
        if 'uid' in session_info and session_info.get('uid') not in [False, None]:
            uid = session_info.get('uid')
        elif 'pre_uid' in session_info and session_info.get('pre_uid') not in [False, None]:
            uid = session_info.get('pre_uid')
        else:
            session_info.update({
                "Code": 404,
                "StatusDescription": "Failed",
                "ArabicMessage": "عفوا البيانات المدخلة خاطئة",
                "EnglishMessage": "Invalid Username or password"
            })
        user = request.env['res.users'].sudo().browse(uid)
        token = user.api_access_token
        if not token:
            token = user.sudo()._generate_api_access_token()
        session_info.update({'token': token, "Code": 200, "StatusDescription": "Failed",
                             "ArabicMessage": "تم تسجيل الدخول بنجاح",
                             "EnglishMessage": "Login Successfully"
                             })
        # return session_info.data
        UserInfo = {
            'context': session_info['context'],
            'token': token,
            "db": session_info['db'] if 'db' in session_info else '',
            "debug": session_info['debug'] if 'debug' in session_info else '',
            "login": session_info['login'] if 'login' in session_info else '',
            "uid": session_info['uid'] if 'uid' in session_info else '',
            "session_token": session_info['session_token'] if 'session_token' in session_info else '',
            "profile_session": session_info['profile_session'] if 'profile_session' in session_info else '',
            "profile_collectors": session_info['profile_collectors'] if 'profile_collectors' in session_info else '',
            "profile_params": session_info['profile_params'] if 'profile_params' in session_info else '',
            "partner_type": user.partner_id.company_type,
            "name": user.name,
            "mobile": user.mobile,
        }
        return {
            "Code": 200,
            "StatusDescription": "Success",
            "Data": {'UserInfo': UserInfo},
            "ArabicMessage": "تم تسجيل الدخول بنجاح",
            "EnglishMessage": "Login Successfully",
        }

    def convert_bytes_dic(self, args):
        string = str(args)
        s = string.replace("{", "")
        finalstring = s.replace("}", "")
        list = finalstring.split(",")
        dictionary = {}
        for i in list:
            if ":" in i:
                keyvalue = i.split(":")
                y = 0
                x = 1
                m = str(keyvalue[0].strip('\''))
                s = keyvalue[1].strip('"\'')
                if len(keyvalue) > 2:
                    y = 1
                    x = 2
                    m = keyvalue[1].strip('\'')
                    s = keyvalue[2].strip('"\'')
            m = m.replace("b'\\n\\t", "")
            m = m.replace("\r", "")
            m = m.replace("\n  ", "")
            m = m.replace("\\n  ", "")
            m = m.replace("\n ", "")
            m = m.replace("\n", "")
            m = m.replace('  "', '')
            m = m.replace(' "', '')
            m = m.replace('"', '')
            m = m.replace("b'", '')
            s = s.replace('  "', '')
            s = s.replace(' "', '')
            s = s.replace('"', '')
            s = s.replace("\r", "")
            s = s.replace("\n  ", "")
            s = s.replace("\n ", "")
            s = s.replace("\n", "")
            dictionary[m] = s
        return dictionary

    @http.route('/update_user_info', method=['POST'], type='json', auth="public", cors="*")
    def update_user_info(self):
        # args = literal_eval(request.httprequest.data.decode('utf-8'))
        args = request.httprequest.data
        args = self.convert_bytes_dic(request.httprequest.data)
        token = request.httprequest.headers.get('token', "")
        if not token:
            return {
                "Code": 500,
                "StatusDescription": "Failed",
                "Data": {},
                "ArabicMessage": "اسم المستخدم غير متاح",
                "EnglishMessage": "User Token is not Provided"
            }
        res_users_objs = request.env['res.users'].sudo().search([('api_access_token', '=', token)], limit=1)
        if not res_users_objs:
            return {
                "Code": 500,
                "StatusDescription": "Failed",
                "Data": {},
                "ArabicMessage": "اسم المستخدم غير صحيح",
                "EnglishMessage": "User is not Correct"
            }
        user_dic = {}
        if 'name' in args:
            user_dic['name'] = args.get('name')
        if 'email' in args:
            user_dic['login'] = args.get('email')
        if user_dic:
            try:
                res_users_objs.sudo().write(user_dic)
            except Exception as e:
                return {
                    "Code": 500,
                    "StatusDescription": "Failed",
                    "Data": {},
                    "ArabicMessage": "اسم المستخدم غير صحيح",
                    "EnglishMessage": "User is not Correct"
                }
        if 'login' in user_dic and user_dic.get('login'):
            user_dic.pop('login')
        if 'email' in args:
            user_dic['email'] = args.get('email')
        if 'mobile' in args:
            user_dic['mobile'] = args.get('mobile')
        if 'gender' in args:
            user_dic['gender'] = args.get('gender')
        if 'civil_id' in args:
            user_dic['civil_id'] = args.get('civil_id')
        if 'civil_img_front' in args:
            if args.get('civil_img_front') == '\\n':
                user_dic['civil_img_front'] = ""
            else:
                user_dic['civil_img_front'] = args.get('civil_img_front')
        if 'civil_img_back' in args:
            if args.get('civil_img_back') == '\\n':
                user_dic['civil_img_back'] = ""
            else:
                user_dic['civil_img_back'] = args.get('civil_img_back')
        if user_dic:
            res_users_objs.sudo().partner_id.write(user_dic)
        civil_img_front_link = ''
        civil_img_back_link = ''
        if res_users_objs.sudo().partner_id.civil_img_front:
            # base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
            # civil_img_front_link = base_url + '/web/image?' + 'model=res_partner&id=' + str(
            #     res_users_objs.sudo().partner_id.id) + '&field=civil_img_front'

            filecontent = base64.b64decode(res_users_objs.sudo().partner_id.civil_img_front or '')
            civil_img_front_link = request.make_response(filecontent,
                                                         [('Content-Type', 'application/octet-stream'),
                                                          ('Content-Disposition',
                                                           content_disposition('civil_img_front_link'))])
        if res_users_objs.sudo().partner_id.civil_img_back:
            filecontent = base64.b64decode(res_users_objs.sudo().partner_id.civil_img_back or '')
            civil_img_back_link = request.make_response(filecontent,
                                                        [('Content-Type', 'application/octet-stream'),
                                                         ('Content-Disposition',
                                                          content_disposition('civil_img_back_link'))])
        return {
            "Code": 200,
            "StatusDescription": "Success",
            "Data": {'UserInfo':
                {
                    'name': res_users_objs.sudo().name or "",
                    'email': res_users_objs.sudo().login or "",
                    'mobile': res_users_objs.sudo().partner_id.mobile or '',
                    'gender': res_users_objs.sudo().partner_id.gender or '',
                    'civil_id': res_users_objs.sudo().partner_id.civil_id or '',
                    'civil_img_front': res_users_objs.sudo().partner_id.civil_img_front or '',
                    'civil_img_front_link': "",
                    'civil_img_back': res_users_objs.sudo().partner_id.civil_img_back or '',
                    'civil_img_back_link': ""
                }
            },
            "ArabicMessage": "تم التعديل بنحاج",
            "EnglishMessage": "User Updated successfully"
        }

    @http.route('/get_hotels', method=['POST'], type='json', auth="public", cors="*")
    def get_hotels(self):
        args = literal_eval(request.httprequest.data.decode('utf-8'))
        token = request.httprequest.headers.get('token', "")
        if not token:
            return {
                "Code": 500,
                "StatusDescription": "Failed",
                "Data": {},
                "ArabicMessage": "اسم المستخدم غير متاح",
                "EnglishMessage": "User Token is not Provided"
            }
        res_users_objs = request.env['res.users'].sudo().search([('api_access_token', '=', token)], limit=1)
        if not res_users_objs:
            return {
                "Code": 500,
                "StatusDescription": "Failed",
                "Data": {},
                "ArabicMessage": "اسم المستخدم غير صحيح",
                "EnglishMessage": "User is not Correct"
            }
        hotel_hotel_objs = request.env['hotel.hotel'].sudo().search([])
        hotel_hotel_list = []
        for hotel_hotel_obj in hotel_hotel_objs:
            hotel_hotel_link = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
            hotel_hotel_link = hotel_hotel_link + "/web/binary/download_document?model=hotel.hotel&field=image&id=" + str(
                hotel_hotel_obj.id) + "&filename=image"
            hotel_hotel_link = hotel_hotel_link + "/web/binary/download_document?model=hotel.hotel&field=icon&id=" + str(
                hotel_hotel_obj.id) + "&filename=image"

            hotel_hotel_list.append({'hotel_id': hotel_hotel_obj.id,
                                     'hotel_name': hotel_hotel_obj.name,
                                     'hotel_address': hotel_hotel_obj.address,
                                     'hotel_rate': hotel_hotel_obj.hotel_rate,
                                     'hotel_image_link': hotel_hotel_link,
                                     })
        return {
            "Code": 200,
            "StatusDescription": "Success",
            "Data": {'hotel_info': hotel_hotel_list},
            "ArabicMessage": "تم الرجوع بنجــاح",
            "EnglishMessage": "Hotel Info List Return successfully"
        }

    @http.route('/get_rooms', method=['POST'], type='json', auth="public", cors="*")
    def get_rooms(self):
        args = literal_eval(request.httprequest.data.decode('utf-8'))
        token = request.httprequest.headers.get('token', "")

        if not token:
            return {
                "Code": 500,
                "StatusDescription": "Failed",
                "Data": {},
                "ArabicMessage": "اسم المستخدم غير متاح",
                "EnglishMessage": "User Token is not Provided"
            }

        res_users_objs = request.env['res.users'].sudo().search([('api_access_token', '=', token)], limit=1)
        if not res_users_objs:
            return {
                "Code": 500,
                "StatusDescription": "Failed",
                "Data": {},
                "ArabicMessage": "اسم المستخدم غير صحيح",
                "EnglishMessage": "User is not Correct"
            }

        room_type_objs = request.env['room.type'].sudo().search([])
        room_type_list = []

        for room_type_obj in room_type_objs:
            room_list = []
            base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
            image_url = base_url + '/web/image?' + 'model=room_type&id=' + str(
                room_type_obj.id) + '&field=image_1920'

            for hotel_room in room_type_obj.room_ids:
                room_list.append({
                    'room_id': hotel_room.id,
                    'hotel_id': hotel_room.hotel_id.id,
                    'hotel_name': hotel_room.hotel_id.name,
                    'room_number': hotel_room.name,
                    'room_price': hotel_room.price,
                    'room_size': hotel_room.room_size,
                    'floor': hotel_room.floor_id.name,
                    'can_booked': hotel_room.booking_ok
                })

            room_type_list.append({
                'room_type_id': room_type_obj.id,
                'room_type_name': room_type_obj.name,
                'number_of_rooms': room_type_obj.room_count,
                'room_type_image_link': image_url,
                'room_info': room_list
            })

        return {
            "Code": 200,
            "StatusDescription": "Success",
            "Data": room_type_list,
            "ArabicMessage": "تم استرجاع بيانات الغرف بنجاح",
            "EnglishMessage": "Successfully retrieved room data"
        }
