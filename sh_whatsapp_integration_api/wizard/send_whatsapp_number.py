# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models, fields, api, _
import requests
import json
from odoo.exceptions import UserError


class ShSendWhatsappNumber(models.TransientModel):
    _name = "sh.send.whatsapp.number.wizard"
    _description = "Send whatsapp message wizard"

    partner_ids = fields.Many2one("res.partner", string="Recipients")
    whatsapp_mobile = fields.Char(string="Whatsapp Number", required=True)
    message = fields.Text("Message", required=True)
    crm_lead_id = fields.Many2one('crm.lead', string="Lead")
    attachment_ids = fields.Many2many("ir.attachment", string="Attach a file")

    @api.onchange('partner_ids')
    def onchange_partner(self):
        if self.partner_ids:
            self.whatsapp_mobile = self.partner_ids.mobile

    def action_send_whatsapp_number(self):
        if self.whatsapp_mobile and self.message:
            headers = {
                "Content-Type": "application/json"
            }
            domain = [('default_send', '=', 'True')]
            find_default = self.env['sh.configuration.manager'].search(
                domain, limit=1)
            if find_default:
                if find_default.config_type == 'chat_api':
                    url = "https://api.chat-api.com/%s/sendMessage?token=%s" % (
                        find_default.instance_id, find_default.token)
                    payload = {
                        "body": self.message,
                        "phone": self.whatsapp_mobile,
                    }
                    send_message = requests.get(url=url, headers=headers, data=json.dumps(
                        payload, indent=4, sort_keys=True, default=str))
                    send_message_json = send_message.json()
                    if 'sent' in send_message_json.keys():
                        if send_message_json['sent'] == 'False':
                            e = send_message_json['message']
                            raise UserError(_(e))
                elif find_default.config_type == 'api_chat':
                    url = "https://api.apichat.io/v1/sendText"
                    headers['client-id'] = find_default.instance_id
                    headers['token'] = find_default.token
                    payload = {
                        "text": self.message,
                        "number": self.whatsapp_mobile,
                    }
                    send_message = requests.post(
                        url=url, headers=headers, data=json.dumps(payload))
                    if send_message.status_code == 200:
                        send_message_json = send_message.json()
                        if 'message' in send_message_json.keys():
                            e = send_message_json['message']
                            raise UserError(_(e))
                message_send = ''
                if self.message:
                    message_send = str(self.message).replace(
                        '*', '').replace('_', '').replace('%0A', '<br/>').replace('%20', ' ').replace('%26', '&')
                    self.env['mail.message'].create({
                        'partner_ids': [(6, 0, self.partner_ids.ids)] or False,
                        'model': 'res.partner',
                        'res_id': self.partner_ids.id,
                        'author_id': self.env.user.partner_id.id,
                        'body': message_send or False,
                        'message_type': 'comment',
                    })
                if find_default.config_type == 'chat_api':
                    for attach in self.attachment_ids:
                        encoded = attach.datas.decode("utf-8")
                        base64_file = 'data:%s;base64,{}'.format(
                            encoded) % (attach.mimetype)
                        url = "https://api.chat-api.com/%s/sendFile?token=%s" % (
                            find_default.instance_id, find_default.token)
                        payload = {
                            "body": '%s' % (base64_file),
                            "phone": self.whatsapp_mobile,
                            "filename": attach.name,
                        }
                        requests.get(url=url, headers=headers, data=json.dumps(
                            payload, indent=4, sort_keys=True, default=str))
                elif find_default.config_type == 'api_chat':
                    for attach in self.attachment_ids:
                        encoded = attach.datas.decode("utf-8")
                        base64_file = 'data:%s;base64,{}'.format(
                            encoded) % (attach.mimetype)
                        if attach.mimetype == 'image/png':
                            url = "https://api.apichat.io/v1/sendImage"
                        elif attach.mimetype == 'video/mp4':
                            url = "https://api.apichat.io/v1/sendVideo"
                        elif 'audio' in attach.mimetype:
                            url = "https://api.apichat.io/v1/sendVideo"
                        else:
                            url = "https://api.apichat.io/v1/sendFile"
                        payload = {
                            "number": self.whatsapp_mobile,
                            "url": '%s' % base64_file,
                        }
                        sendfile = requests.post(
                            url=url, headers=headers, data=json.dumps(payload))
                        if sendfile.status_code != 200:
                            raise UserError(_(sendfile.text))
            else:
                raise UserError(_("No Default Configuration is selected"))
        else:
            raise UserError(_("Partner Mobile Number Not Exist"))
