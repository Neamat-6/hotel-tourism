# -*- coding: utf-8 -*-
import base64
import datetime
import json
import xmltodict
import werkzeug
import pytz

from odoo import _, exceptions, http, tools
from odoo.http import request


class HTaskController(http.Controller):

    @http.route('/htask/roominfo', type='json', auth='public')
    def retrieve_room_info(self, room_no):

        HTaskModel = request.env['abstract.htask.model']
        htask_room_info = HTaskModel.get_htask_connector('room_info')

        data = '<?xml version="1.0" standalone="yes"?><request><auth>%s</auth><oprn>roomquery</oprn><room>%s</room></request>' % (htask_room_info.auth_code, room_no)

        room_info = htask_room_info.get_post(arguments={}, data=data, content_type="xml")
        data_dict = xmltodict.parse(room_info)

        room_rows = ['Guest Name', 'Guest Email', 'Guest Mobile', 'Adult(s)', 'Child(s)', 'Arrival', 'Departure', 'Folio No.', 'Room Type', 'Rate Type', 'Reservation No.']

        res = json.loads(json.dumps(data_dict))
        resp = res['response']
        if resp['status'] == 'ok':
            resp['roomrows']['row'] = dict(zip(room_rows, list(resp['roomrows']['row'].values())))
        
        return res

    @http.route('/htask/postcharge', type='json', auth='public')
    def post_charge_to_room(self, **kw):

        HTaskModel = request.env['abstract.htask.model']
        htask_room_info = HTaskModel.get_htask_connector('room_info')
        user_time_zone = request.env.user.tz
        user_tz = pytz.timezone(user_time_zone)
        data = '<request><auth>%s</auth><oprn>chargepost</oprn><room>%s</room><folio>%s</folio><table>%s</table><outlet>%s</outlet><charge>%s</charge><postingdate>%s</postingdate><trandate>%s</trandate><amount>%s</amount><tax>%s</tax><gross_amount>%s</gross_amount><voucherno>%s</voucherno><remark>%s</remark><posuser>%s</posuser></request>' % (
            htask_room_info.auth_code,
            kw.get('room_no'),
            kw.get('folio_no'),
            kw.get('table_no'),
            kw.get('outlet_name').encode('utf-8').decode('utf-8'),
            '[Datetime: ' + str(datetime.datetime.now().replace(tzinfo=pytz.utc).astimezone(user_tz).replace(tzinfo=None)) + '] ' + kw.get('charge_desc'),
            kw.get('post_date'),
            kw.get('trans_date'),
            kw.get('total_amount'),
            kw.get('tax_amount'),
            kw.get('gross_amount'),
            kw.get('receipt_no'),
            kw.get('comment').encode('utf-8').decode('utf-8'),
            kw.get('pos_user_name').encode('utf-8').decode('utf-8'),
        )

        post_res = htask_room_info.get_post(arguments={}, data=data, content_type="xml")
        data_dict = xmltodict.parse(post_res)
        print(data_dict)

        res = json.loads(json.dumps(data_dict))
        print(res)
        response = res.get('response')
        if response and response.get('status') == 'ok' and response.get('requestid'):
            print("HOHOHOHO")
            pos_order_id = request.env['pos.order'].search([('pos_reference', '=', kw.get('pos_order_id'))])
            pos_order_id.write({
                'post_request_ref': response.get('requestid'),
                'room_no': kw.get('room_no'),
                'folio_no': kw.get('folio_no'),
            })
        return res

    @http.route('/htask/voidcharge', type='json', auth='public')
    def void_room_charge(self, **kw):

        HTaskModel = request.env['abstract.htask.model']
        htask_room_info = HTaskModel.get_htask_connector('room_info')

        data = '<?xml version="1.0" standalone="yes"?><request><auth>%s</auth><oprn>voidcharge</oprn><requestid>%s</requestid></request>' % (
            htask_room_info.auth_code,
            kw.get('request_id'),
        )

        void_res = htask_room_info.get_post(arguments={}, data=data, content_type="xml")
        data_dict = xmltodict.parse(void_res)
        res = json.loads(json.dumps(data_dict))
        return res
