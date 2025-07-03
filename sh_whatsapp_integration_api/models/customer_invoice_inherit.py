# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.http import request
import requests
import json
import base64


class AccountInvoice(models.Model):
    _inherit = "account.move"

    text_message_chat_api = fields.Text(
        "Message", compute="_compute_get_message_detail_so_chat_api")

    def action_quotation_send_wp(self):
        if not self.partner_id.mobile:
            raise UserError(_("Partner Mobile Number Not Exist !"))
        self.ensure_one()
        lang = self.env.context.get('lang')
        template = self.env.ref(
            'sh_whatsapp_integration_api.email_template_edi_invoice_custom_chat_api')
        if template.lang:
            lang = template._render_lang(self.ids)[self.id]
        ctx = {
            'default_model': 'account.move',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template.id),
            'default_template_id': template.id,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True,
            'custom_layout': "mail.mail_notification_paynow",
            'proforma': self.env.context.get('proforma', False),
            'force_email': True,
            'model_description': self.with_context(lang=lang).type_name,
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

    @api.depends('partner_id', 'currency_id', 'company_id')
    def _compute_get_message_detail_so_chat_api(self):
        if self:
            for inv in self:
                if inv.move_type in ['out_invoice', 'out_refund']:
                    txt_message = ""
                    if inv.company_id.invoice_order_information_in_message and inv.partner_id and inv.currency_id and inv.company_id:
                        txt_message += "Dear " + \
                            str(inv.partner_id.name)+","+"\n\n"
                        if inv.name and inv.state != "draft":
                            txt_message += "Here is the your invoice " + \
                                '*'+str(inv.name)+'*'+""
                        else:
                            txt_message += "Here is the your invoice "
                        txt_message += " amounting in "+'*' + \
                            str(inv.amount_total)+'*'+""+str(inv.currency_id.symbol) + \
                            " from "+inv.company_id.name+"."
                        if inv.state == "paid":
                            txt_message += "This invoice is already paid."+"\n\n"
                        else:
                            txt_message += "Please remit payment at your earliest convenience."+"\n\n"
                    if inv.company_id.invoice_product_detail_in_message:
                        txt_message += "Following is your order details."+"\n"
                        if inv.invoice_line_ids:
                            for invoices_line in inv.invoice_line_ids:
                                if invoices_line.product_id and invoices_line.quantity and invoices_line.price_unit:
                                    txt_message += "\n"+"*"+invoices_line.product_id.name+"*"+"\n"+"*Qty:* " + \
                                        str(invoices_line.quantity)+"\n"+"*Price:* "+str(
                                            invoices_line.price_unit)+""+str(invoices_line.move_id.currency_id.symbol)+"\n"
                                else:
                                    txt_message += "\n"+"*"+invoices_line.name+"*"+"\n"+"*Qty:* "+str(invoices_line.quantity)+"\n"+"*Price:* "+str(
                                        invoices_line.price_unit)+""+str(invoices_line.move_id.currency_id.symbol)+"\n"
                                if invoices_line.discount > 0.00:
                                    txt_message += "*Discount:* " + \
                                        str(invoices_line.discount)+"%25"+"\n"
                                txt_message += "________________________"+"\n"
                        txt_message += "*"+"Total Amount:"+"*" + \
                            str(inv.amount_total)+"" + \
                            str(inv.currency_id.symbol)
                    if inv.company_id.invoice_signature and inv.env.user.sign:
                        txt_message += "\n\n\n"+str(inv.env.user.sign)
                    inv.text_message_chat_api = txt_message.replace('&', '%26')

                elif inv.move_type in ['in_invoice', 'in_refund']:
                    txt_message = ""
                    if inv.company_id.invoice_order_information_in_message and inv.partner_id and inv.currency_id and inv.company_id:
                        txt_message += "Dear " + \
                            str(inv.partner_id.name)+","+"\n\n"
                        if inv.name and inv.state != "draft":
                            txt_message += "Here is the your invoice " + \
                                '*'+str(inv.name)+'*'+""
                        else:
                            txt_message += "Here is the your invoice "+""
                        txt_message += " amounting in "+'*' + \
                            str(inv.amount_total)+'*'+""+str(inv.currency_id.symbol) + \
                            " from "+inv.company_id.name+"."
                        if inv.state == "paid":
                            txt_message += "This invoice is already paid."+"\n\n"
                        else:
                            txt_message += "Please remit payment at your earliest convenience."+"\n\n"
                    if inv.company_id.invoice_product_detail_in_message:
                        txt_message += "Following is your order details."+"\n"
                        if inv.invoice_line_ids:
                            for invoices_line in inv.invoice_line_ids:
                                if invoices_line.product_id and invoices_line.quantity and invoices_line.price_unit:
                                    txt_message += "\n"+"*"+invoices_line.product_id.name+"*"+"\n"+"*Qty:* " + \
                                        str(invoices_line.quantity)+"\n"+"*Price:* "+str(
                                            invoices_line.price_unit)+""+str(invoices_line.move_id.currency_id.symbol)+"\n"
                                else:
                                    txt_message += "\n"+"*"+invoices_line.name+"*"+"\n"+"*Qty:* "+str(invoices_line.quantity)+"\n"+"*Price:* "+str(
                                        invoices_line.price_unit)+""+str(invoices_line.move_id.currency_id.symbol)+"\n"

                                if invoices_line.discount > 0.00:
                                    txt_message += "*Discount:* " + \
                                        str(invoices_line.discount)+"%25"+"\n"
                                txt_message += "________________________"+"\n"
                        txt_message += "*"+"Total Amount:"+"*"+"%20" + \
                            str(inv.amount_total)+"" + \
                            str(inv.currency_id.symbol)
                    if inv.company_id.invoice_signature and inv.env.user.sign:
                        txt_message += "\n\n\n"+str(inv.env.user.sign)
                    inv.text_message_chat_api = txt_message.replace('&', '%26')
                else:
                    inv.text_message_chat_api = ''

    def generate_report(self, config=False):
        report_sudo = request.env.ref('account.account_invoices').sudo()
        method_name = '_render_qweb_pdf'
        report = getattr(report_sudo, method_name)(
            [self.id], data={'report_type': 'pdf'})[0]
        encoded = base64.b64encode(report)
        encoded = encoded.decode("utf-8")
        base64_file = 'data:application/pdf;base64,{}'.format(encoded)
        return (base64_file)

    def send_by_whatsapp_direct_to_ci(self):
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
                            message = ""
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
                                        raise UserError(_(send_message.text))
                                else:
                                    raise UserError(_(e))
                            self.env['mail.message'].create({
                                'partner_ids': [(6, 0, rec.partner_id.ids)],
                                'model': 'account.move',
                                'res_id': rec.id,
                                'author_id': self.env.user.partner_id.id,
                                'body': message or False,
                                'message_type': 'comment',
                            })
                    if find_default.config_type == 'chat_api':
                        url = "https://api.chat-api.com/%s/sendFile?token=%s" % (
                            find_default.instance_id, find_default.token)
                        if self.state == 'draft':
                            filename = "Draft Invoice -.pdf"
                        else:
                            filename = "Invoice_%s.pdf" % (self.name)
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
