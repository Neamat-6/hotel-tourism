# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from urllib import response
from odoo import models, fields, _ , api
from odoo.exceptions import UserError
from lxml import etree
import requests

class GeneratedCode(models.TransientModel):
    _name = 'sh.qr.code.wizard'
    _description = "Generated QR Code Shown Here"

    qr_code = fields.Char("QR Code")

    sh_qr_code_img = fields.Binary(string = "QR Code Image")

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        active_id = self.env.context.get('active_id')
        domain = [('id', '=', active_id)]
        find_base64 = self.env['sh.configuration.manager'].search(domain,limit=1)
        if find_base64.config_type == 'chat_api':
            res = super(GeneratedCode, self).fields_view_get(
                view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu
            )
            if view_type == 'form':
                doc = etree.XML(res['arch'])
                for node in doc.xpath("//img[hasclass('qr_img')]"):
                    node.set('src', '%s' %(find_base64.send_base64_data))
                res['arch'] = etree.tostring(doc, encoding='unicode')
            return res
        else:
            return super(GeneratedCode, self).fields_view_get(
                view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu
            )

    def refresh_qr(self):
        active_id = self.env.context.get('active_id')
        active_model = self.env.context.get('active_model')
        active_record_set = self.env[active_model].browse(active_id)
        active_record_set.authenticate()

    def verify(self):
        active_id = self.env.context.get('active_id')
        active_model = self.env.context.get('active_model')
        active_record_set = self.env[active_model].browse(active_id)
        if active_record_set.config_type == 'chat_api':
            url = "https://api.chat-api.com/%s/status?token=%s" %(active_record_set.instance_id,active_record_set.token)
            headers = {
                    "Content-Type" : "application/json"
                }
            get_status = requests.get(url = url,headers=headers)
            get_status_json = get_status.json()
            if 'error' in get_status_json:
                e = get_status_json['error']
                raise UserError(_(e))
            if 'accountStatus'in get_status_json:
                if get_status_json['accountStatus'] == "authenticated":
                    active_record_set.status = "verified"
        elif active_record_set.config_type == 'api_chat':
            url = "https://api.apichat.io/v1/status"
            headers = {
                    "Content-Type" : "application/json",
                    "client-id" : active_record_set.instance_id,
                    "token" : active_record_set.token
                }
            get_status = requests.get(url = url,headers=headers)
            if get_status.status_code == 200:
                get_status_json = get_status.json()
                if get_status_json['is_connected']:
                    active_record_set.status = "verified"