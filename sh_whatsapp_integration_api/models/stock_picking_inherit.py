# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.http import request
import requests
import json
import base64


class StockPicking(models.Model):
    _inherit = "stock.picking"

    text_message_chat_api = fields.Text(
        "Message", compute="_compute_get_outgoing_detail_chat_api")

    def action_quotation_send_wp(self):
        ''' Opens a wizard to compose an email, with relevant mail template loaded by default '''
        if not self.partner_id.mobile:
            raise UserError(_("Partner Mobile Number Not Exist !"))
        self.ensure_one()
        lang = self.env.context.get('lang')
        template = self.env.ref(
            'sh_whatsapp_integration_api.mail_template_data_stock_picking_custom_chat_api')
        if template.lang:
            lang = template._render_lang(self.ids)[self.id]

        ctx = {
            'default_model': 'stock.picking',
            'default_res_id': self.ids[0],
            'active_model': 'stock.picking',
            'active_id': self.ids[0],
            'default_use_template': bool(template.id),
            'default_template_id': template.id,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True,
            'custom_layout': "mail.mail_notification_paynow",
            'proforma': self.env.context.get('proforma', False),
            'force_email': True,
            'default_is_wp': True,
        }
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }

    @api.depends('partner_id')
    def _compute_get_outgoing_detail_chat_api(self):
        if self and self.picking_type_id.code == "outgoing":
            for rec in self:
                txt_message = ""
                if rec.partner_id:
                    txt_message += "Dear " + str(rec.partner_id.name)+","+"\n\n"+"Here is the order " + \
                        '*'+rec.name+'*'+"\n\n"+"Following is your order details."+"\n\n"
                    if rec.move_ids_without_package:
                        for picking in rec.move_ids_without_package:
                            if picking.quantity_done > 0.00:
                                txt_message += "\n"+'*'+picking.product_id.name+'*'+"\n"+"*Required Qty:* " + \
                                    str(picking.product_uom_qty)+"\n"+"*Delivery Qty:* "+str(
                                        picking.quantity_done)+"\n"+"________________________"+"\n"
                            else:
                                txt_message += "\n"+'*'+picking.product_id.name+'*'+"\n"+"*Required Qty:* " + \
                                    str(picking.product_uom_qty)+"\n" + \
                                    "________________________"+"\n"
                    if rec.env.user.sign:
                        txt_message += "\n\n\n"+str(rec.env.user.sign)
                else:
                    txt_message += "Here is the order "+'*'+rec.name+'*' + \
                        "\n\n"+"Following is your order details."+"\n\n"
                    if rec.move_ids_without_package:
                        for picking in rec.move_ids_without_package:
                            if picking.quantity_done > 0.00:
                                txt_message += "\n"+'*'+picking.product_id.name+'*'+"\n"+"*Required Qty:* " + \
                                    str(picking.product_uom_qty)+"\n"+"*Delivery Qty:* "+str(
                                        picking.quantity_done)+"\n"+"________________________"+"\n"
                            else:
                                txt_message += "\n"+'*'+picking.product_id.name+'*'+"\n"+"*Required Qty:* " + \
                                    str(picking.product_uom_qty)+"\n" + \
                                    "________________________"+"\n"
                    if rec.env.user.sign:
                        txt_message += "\n\n\n"+str(rec.env.user.sign)
            rec.text_message_chat_api = txt_message.replace('&', '%26')
        elif self and self.picking_type_id.code in ['incoming', 'internal']:
            for rec in self:
                txt_message = ""
                if rec.partner_id:
                    txt_message += "Dear " + str(rec.partner_id.name)+","+"\n\n"+"Here is the order " + \
                        '*'+rec.name+'*'+"\n\n"+"Following is your order details."+"\n\n"
                    if rec.move_ids_without_package:
                        for picking in rec.move_ids_without_package:
                            if picking.quantity_done > 0.00:
                                txt_message += "\n"+'*'+picking.product_id.name+'*'+"\n"+"*Required Qty:* " + \
                                    str(picking.product_uom_qty)+"\n"+"*Delivery Qty:* "+str(
                                        picking.quantity_done)+"\n"+"________________________"+"\n"
                            else:
                                txt_message += "\n"+'*'+picking.product_id.name+'*'+"\n"+"*Required Qty:* " + \
                                    str(picking.product_uom_qty)+"\n" + \
                                    "________________________"+"\n"
                    if rec.env.user.sign:
                        txt_message += "\n\n\n"+str(rec.env.user.sign)
                else:
                    txt_message += "Here is the order "+'*'+rec.name+'*' + \
                        "\n\n"+"Following is your order details."+"\n\n"
                    if rec.move_ids_without_package:
                        for picking in rec.move_ids_without_package:
                            if picking.quantity_done > 0.00:
                                txt_message += "\n"+'*'+picking.product_id.name+'*'+"\n"+"*Required Qty:* " + \
                                    str(picking.product_uom_qty)+"\n"+"*Delivery Qty:* "+str(
                                        picking.quantity_done)+"\n"+"________________________"+"\n"
                            else:
                                txt_message += "\n"+'*'+picking.product_id.name+'*'+"\n"+"*Required Qty:* " + \
                                    str(picking.product_uom_qty)+"\n" + \
                                    "________________________"+"\n"
                    if rec.env.user.sign:
                        txt_message += "\n\n\n"+str(rec.env.user.sign)
            rec.text_message_chat_api = txt_message.replace('&', '%26')
        else:
            self.text_message_chat_api = ''

    def generate_report(self, config=False):
        if self.picking_type_id.code == "outgoing":
            report_sudo = request.env.ref('stock.action_report_delivery').sudo()
        elif self.picking_type_id.code == "incoming":
            report_sudo = request.env.ref('stock.action_report_picking').sudo()
        method_name = '_render_qweb_pdf'
        report = getattr(report_sudo, method_name)(
            [self.id], data={'report_type': 'pdf'})[0]
        encoded = base64.b64encode(report)
        encoded = encoded.decode("utf-8")
        base64_file = 'data:application/pdf;base64,{}'.format(encoded)
        return (base64_file)

    def send_by_whatsapp_direct_to_cust_del(self):
        if self:
            base64_file = self.generate_report()
            domain = [('default_send', '=', 'True')]
            find_default = self.env['sh.configuration.manager'].search(
                domain, limit=1)
            domain = [('id', '=', self.partner_id.id)]
            user = self.env['res.partner'].search(domain, limit=1)
            headers = {
                "Content-Type": "application/json"
            }
            if find_default:
                if user.mobile:
                    for rec in self:
                        if rec.company_id.display_in_message:
                            message = ''
                            if rec.text_message_chat_api:
                                message = str(self.text_message_chat_api).replace(
                                    '*', '').replace('_', '').replace('%0A', '<br/>').replace('%20', ' ').replace('%26', '&')
                            if find_default.config_type == 'chat_api':
                                url = "https://api.chat-api.com/%s/sendMessage?token=%s" % (
                                    find_default.instance_id, find_default.token)
                                payload = {
                                    "body": rec.text_message_chat_api,
                                    "phone": user.mobile,
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
                                    "text": rec.text_message_chat_api,
                                    "number": user.mobile,
                                }
                                send_message = requests.post(
                                    url=url, headers=headers, data=json.dumps(payload))
                                if send_message.status_code == 200:
                                    send_message_json = send_message.json()
                                    if 'message' in send_message_json.keys():
                                        e = send_message_json['message']
                                        raise UserError(_(e))
                            self.env['mail.message'].create({
                                'partner_ids': [(6, 0, rec.partner_id.ids)],
                                'model': 'stock.picking',
                                'res_id': rec.id,
                                'author_id': self.env.user.partner_id.id,
                                'body': message or False,
                                'message_type': 'comment',
                            })
                    if find_default.config_type == 'chat_api':
                        url = "https://api.chat-api.com/%s/sendFile?token=%s" % (
                            find_default.instance_id, find_default.token)
                        if self.picking_type_id.code == "outgoing":
                            filename = 'Delivery Slip %s.pdf' % (self.name)
                        elif self.picking_type_id.code == "incoming":
                            filename = 'Picking Slip %s.pdf' % (self.name)
                        else:
                            filename = '%s.pdf' % (self.name)
                        payload = {
                            "body": '%s' % base64_file,
                            "phone": user.mobile,
                            "filename": filename,
                        }
                        requests.get(url=url, headers=headers, data=json.dumps(
                            payload, indent=4, sort_keys=True, default=str))
                    elif find_default.config_type == 'api_chat':
                        url = "https://api.apichat.io/v1/sendFile"
                        payload = {
                            "number": user.mobile,
                            "url": '%s' % base64_file,
                        }
                        sendfile = requests.post(
                            url=url, headers=headers, data=json.dumps(payload))
                        if sendfile.status_code != 200:
                            raise UserError(_(sendfile.text))
                else:
                    raise UserError(_("Partner Mobile Number Not Exist"))
            else:
                raise UserError(_("No Default Configuration is selected"))
