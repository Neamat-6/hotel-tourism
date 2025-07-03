# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.http import request
import requests
import json
import base64


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    text_message_chat_api = fields.Text(
        "Message", compute="_compute_get_message_detail_po_chat_api")

    def action_quotation_send_wp(self):

        if not self.partner_id.mobile:
            raise UserError(_("Vendor Mobile Number Not Exist !"))
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        template = self.env.ref(
            'sh_whatsapp_integration_api.email_template_edi_purchase_custom_chat_api')

        compose_form_id = False
        ctx = dict(self.env.context or {})
        ctx.update({
            'default_model': 'purchase.order',
            'active_model': 'purchase.order',
            'active_id': self.ids[0],
            'default_res_id': self.ids[0],
            'default_use_template': bool(template.id),
            'default_template_id': template.id,
            'default_composition_mode': 'comment',
            'custom_layout': "mail.mail_notification_paynow",
            'force_email': True,
            'mark_rfq_as_sent': True,
            'default_is_wp': True,
        })
        lang = self.env.context.get('lang')
        if {'default_template_id', 'default_model', 'default_res_id'} <= ctx.keys():
            template = self.env['mail.template'].browse(
                ctx['default_template_id'])
            if template and template.lang:
                lang = template._render_lang([ctx['default_res_id']])[
                    ctx['default_res_id']]

        self = self.with_context(lang=lang)
        if self.state in ['draft', 'sent']:
            ctx['model_description'] = _('Request for Quotation')
        else:
            ctx['model_description'] = _('Purchase Order')
        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

    # Chat API
    @api.depends('partner_id', 'currency_id', 'company_id')
    def _compute_get_message_detail_po_chat_api(self):
        if self:
            for rec in self:
                txt_message = ""
                if rec.company_id.purchase_order_information_in_message and rec.partner_id and rec.currency_id and rec.company_id:
                    txt_message += "Dear " + str(rec.partner_id.name)+","+"\n\n"+"Here is the order "+'*'+rec.name+'*'+" amounting in "+'*'+str(
                        rec.amount_total)+""+str(rec.currency_id.symbol)+'*'+" from "+rec.company_id.name+"\n\n"
                if rec.company_id.purchase_product_detail_in_message:
                    txt_message += "Following is your order details."+"\n"
                    if rec.order_line:
                        for purchase_line in rec.order_line:
                            if purchase_line.product_id and purchase_line.order_id.currency_id and purchase_line.order_id.currency_id.symbol:
                                txt_message += "\n"+"*"+purchase_line.product_id.name+"*"+"\n"+"*Qty:* "+str(purchase_line.product_qty)+"\n"+"*Price:* "+str(
                                    purchase_line.price_unit)+""+str(purchase_line.order_id.currency_id.symbol)+"\n"+"________________________"+"\n"
                    txt_message += "*Total Amount:* " +\
                        str(rec.amount_total)+""+str(rec.currency_id.symbol)
                if rec.company_id.purchase_signature and rec.env.user.sign:
                    txt_message += "\n\n\n"+str(rec.env.user.sign)
                rec.text_message_chat_api = txt_message.replace('&', '%26')

    def generate_report(self, config=False):
        report_sudo = request.env.ref('purchase.action_report_purchase_order').sudo()
        method_name = '_render_qweb_pdf'
        report = getattr(report_sudo, method_name)(
            [self.id], data={'report_type': 'pdf'})[0]
        encoded = base64.b64encode(report)
        encoded = encoded.decode("utf-8")
        base64_file = 'data:application/pdf;base64,{}'.format(encoded)
        return (base64_file)

    def send_by_whatsapp_direct_to_po(self):
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
                                    '*', '').replace('_', '').replace('\n', '<br/>').replace('%20', ' ').replace('%26', '&')
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
                                'model': 'purchase.order',
                                'res_id': rec.id,
                                'author_id': self.env.user.partner_id.id,
                                'body': message or False,
                                'message_type': 'comment',
                            })
                    if find_default.config_type == 'chat_api':
                        url = "https://api.chat-api.com/%s/sendFile?token=%s" % (
                            find_default.instance_id, find_default.token)
                        if self.state == 'draft' or self.state == 'sent':
                            filename = "Request for Quotation - %s.pdf" % (
                                self.name)
                        else:
                            filename = "Purchase Order - %s.pdf" % (self.name)
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
