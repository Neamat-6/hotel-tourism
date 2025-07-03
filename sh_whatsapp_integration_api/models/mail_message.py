# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
from odoo import models, fields, _
from odoo.exceptions import UserError
import requests
import json
import re


class Message(models.TransientModel):
    _inherit = 'mail.compose.message'
    is_wp = fields.Boolean("Is whatsapp ?")

    def _get_default_values_config(self):
        get_id = False
        domain = [('config_type', '=', 'chat_api'),
                  ('default_send', '=', 'True')]
        get_id = self.env['sh.configuration.manager'].search(domain, limit=1)
        if get_id:
            return get_id
    config_details = fields.Many2one(
        "sh.configuration.manager", string="Config Details", default=_get_default_values_config)

    def action_send_wp(self):
        text = self.body
        context = dict(self._context or {})
        active_id = context.get('active_id', False)
        active_model = context.get('active_model', False)
        active_record_set = self.env[active_model].browse(active_id)
        if text and active_id and active_model:
            tag_re = re.compile(r'<[^>]+>')
            message = tag_re.sub('', text)
            message_sends = str(text).replace('*', '').replace('_', '')
            if active_model == 'sale.order' and self.env['sale.order'].browse(
                    active_id).company_id.display_in_message:
                self.env['mail.message'].create({
                    'partner_ids': [(6, 0, self.partner_ids.ids)],
                    'model': 'sale.order',
                    'res_id': active_id,
                    'author_id': self.env.user.partner_id.id,
                    'body': message_sends or False,
                    'message_type': 'comment',
                })
            if active_model == 'purchase.order' and self.env['purchase.order'].browse(
                    active_id).company_id.purchase_display_in_message:
                self.env['mail.message'].create({
                    'partner_ids': [(6, 0, self.partner_ids.ids)],
                    'model': 'purchase.order',
                    'res_id': active_id,
                    'author_id': self.env.user.partner_id.id,
                    'body': message_sends or False,
                    'message_type': 'comment',
                })
            if (active_model == 'account.move' and self.env['account.move'].browse(active_id).company_id.invoice_display_in_message) or (active_model == 'account.payment' and self.env['account.payment'].browse(active_id).company_id.invoice_display_in_message):
                self.env['mail.message'].create({
                    'partner_ids': [(6, 0, self.partner_ids.ids)],
                    'model': active_model,
                    'res_id': active_id,
                    'author_id': self.env.user.partner_id.id,
                    'body': message_sends or False,
                    'message_type': 'comment',
                })

            if active_model == 'stock.picking' and self.env['stock.picking'].browse(
                    active_id).company_id.inventory_display_in_message:
                self.env['mail.message'].create({
                    'partner_ids': [(6, 0, self.partner_ids.ids)],
                    'model': 'stock.picking',
                    'res_id': active_id,
                    'author_id': self.env.user.partner_id.id,
                    'body': message_sends or False,
                    'message_type': 'comment',
                })
        headers = {
            "Content-Type": "application/json"
        }
        if self.config_details or self.config_details.default_send == True:
            if text and self.config_details.config_type == 'chat_api':
                url = "https://api.chat-api.com/%s/sendMessage?token=%s" % (
                    self.config_details.instance_id, self.config_details.token)
                payload = {
                    "body": message,
                    "phone": active_record_set.partner_id.mobile,
                }
                send_message = requests.get(url=url, headers=headers, data=json.dumps(
                    payload, indent=4, sort_keys=True, default=str))
                send_message_json = send_message.json()
                if 'sent' in send_message_json.keys():
                    if send_message_json['sent'] == 'False':
                        e = send_message_json['message']
                        raise UserError(_(e))
            elif text and self.config_details.config_type == 'api_chat':
                url = "https://api.apichat.io/v1/sendText"
                headers['client-id'] = self.config_details.instance_id
                headers['token'] = self.config_details.token
                payload = {
                    "text": message,
                    "number": active_record_set.partner_id.mobile,
                }
                send_message = requests.post(
                    url=url, headers=headers, data=json.dumps(payload))
                if send_message.status_code == 200:
                    send_message_json = send_message.json()
                    if 'message' in send_message_json.keys():
                        e = send_message_json['message']
                        raise UserError(_(e))
            if self.config_details.config_type == 'chat_api':
                for attach in self.attachment_ids:
                    encoded = attach.datas.decode("utf-8")
                    base64_file = 'data:%s;base64,{}'.format(
                        encoded) % (attach.mimetype)
                    url = "https://api.chat-api.com/%s/sendFile?token=%s" % (
                        self.config_details.instance_id, self.config_details.token)
                    payload = {
                        "body": '%s' % (base64_file),
                        "phone": active_record_set.partner_id.mobile,
                        "filename": attach.name,
                    }
                    requests.get(url=url, headers=headers, data=json.dumps(
                        payload, indent=4, sort_keys=True, default=str))
            elif self.config_details.config_type == 'api_chat':
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
                        "number": active_record_set.partner_id.mobile,
                        "url": '%s' % base64_file,
                    }
                    sendfile = requests.post(
                        url=url, headers=headers, data=json.dumps(payload))
                    if sendfile.status_code != 200:
                        raise UserError(_(sendfile.text))
        else:
            raise UserError(
                _("Please Select the account from which you want to send"))
