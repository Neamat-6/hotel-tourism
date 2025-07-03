# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models, fields, _
from odoo.exceptions import UserError
import requests
import json


class ShSendWhatsappMessage(models.TransientModel):
    _name = "sh.send.whatsapp.message.wizard"
    _description = "Send whatsapp message wizard"

    partner_ids = fields.Many2one(
        "res.partner", string="Recipients", required=True)
    message = fields.Text("Message", required=True)
    attachment_ids = fields.Many2many(comodel_name="ir.attachment",
                                      string="Attach Files")
    sale_order_id = fields.Many2one('sale.order', string="Sale Order")
    purchase_order_id = fields.Many2one(
        'purchase.order', string="Purchase Order")
    account_invoice_id = fields.Many2one(
        'account.move', string="Account Invoice")
    stock_picking_id = fields.Many2one('stock.picking', string="Stock Picking")
    account_payment_id = fields.Many2one(
        'account.payment', string="Account Payment")

    def action_send_whatsapp_message(self):
        if self:
            headers = {
                "Content-Type": "application/json"
            }
            for rec in self:
                for partner in rec.partner_ids:
                    domain = [('default_send', '=', 'True')]
                    find_default = self.env['sh.configuration.manager'].search(
                        domain, limit=1)
                    if find_default:
                        if self.message and find_default.config_type == 'chat_api':
                            url = "https://api.chat-api.com/%s/sendMessage?token=%s" % (
                                find_default.instance_id, find_default.token)
                            payload = {
                                "body": rec.message,
                                "phone": partner.mobile,
                            }
                            send_message = requests.get(url=url, headers=headers, data=json.dumps(
                                payload, indent=4, sort_keys=True, default=str))
                            send_message_json = send_message.json()
                            if 'sent' in send_message_json.keys():
                                if send_message_json['sent'] == 'False':
                                    e = send_message_json['message']
                                    raise UserError(_(e))
                        elif self.message and find_default.config_type == 'api_chat':
                            url = "https://api.apichat.io/v1/sendText"
                            headers['client-id'] = find_default.instance_id
                            headers['token'] = find_default.token
                            number = str(partner.mobile)
                            updated_number = number.replace("+", "").replace(" ", "")
                            payload = {
                                "text": rec.message,
                                "number": updated_number,
                            }
                            send_message = requests.post(
                                url=url, headers=headers, data=json.dumps(payload))
                            if send_message.status_code == 200:
                                send_message_json = send_message.json()
                                if 'message' in send_message_json.keys():
                                    e = send_message_json['message']
                                    raise UserError(_(e))
                    else:
                        raise UserError(
                            _("No Default Configuration is selected"))
                    active_ids = self.env.context.get('active_ids')
                    active_id = int(active_ids[0])
                    sh_message = ""
                    if rec.message:
                        sh_message = str(self.message).replace(
                            '*', '').replace('_', '').replace('%0A', '<br/>').replace('%20', ' ').replace('%26', '&')
                    # For Sale Order Message Create in Chatter Box.
                    if rec.sale_order_id and rec.sale_order_id.company_id.display_in_message:
                        self.env['mail.message'].create({
                                                        'partner_ids': [(6, 0, partner.ids)],
                                                        'model': 'sale.order',
                                                        'res_id': active_id,
                                                        'author_id': self.env.user.partner_id.id,
                                                        'body': sh_message or False,
                                                        'message_type': 'comment',
                                                        })

                    if rec.purchase_order_id and rec.purchase_order_id.company_id.purchase_display_in_message:
                        self.env['mail.message'].create({
                                                        'partner_ids': [(6, 0, partner.ids)],
                                                        'model': 'purchase.order',
                                                        'res_id': active_id,
                                                        'author_id': self.env.user.partner_id.id,
                                                        'body': sh_message or False,
                                                        'message_type': 'comment',
                                                        })

                    if rec.account_invoice_id and rec.account_invoice_id.company_id.invoice_display_in_message and rec.account_invoice_id.move_type == 'in_invoice':
                        self.env['mail.message'].create({
                                                        'partner_ids': [(6, 0, partner.ids)],
                                                        'model': 'account.move',
                                                        'res_id': active_id,
                                                        'author_id': self.env.user.partner_id.id,
                                                        'body': sh_message or False,
                                                        'message_type': 'comment',
                                                        })

                    if rec.account_invoice_id and rec.account_invoice_id.company_id.invoice_display_in_message and rec.account_invoice_id.move_type == 'out_invoice':
                        self.env['mail.message'].create({
                                                        'partner_ids': [(6, 0, partner.ids)],
                                                        'model': 'account.move',
                                                        'res_id': active_id,
                                                        'author_id': self.env.user.partner_id.id,
                                                        'body': sh_message or False,
                                                        'message_type': 'comment',
                                                        })

                    if rec.stock_picking_id and rec.stock_picking_id.company_id.inventory_display_in_message and rec.stock_picking_id.picking_type_id.code == "outgoing":
                        self.env['mail.message'].create({
                                                        'partner_ids': [(6, 0, partner.ids)],
                                                        'model': 'stock.picking',
                                                        'res_id': active_id,
                                                        'author_id': self.env.user.partner_id.id,
                                                        'body': sh_message or False,
                                                        'message_type': 'comment',
                                                        })

                    if rec.stock_picking_id and rec.stock_picking_id.company_id.inventory_display_in_message and rec.stock_picking_id.picking_type_id.code == "incoming":
                        self.env['mail.message'].create({
                                                        'partner_ids': [(6, 0, partner.ids)],
                                                        'model': 'stock.picking',
                                                        'res_id': active_id,
                                                        'author_id': self.env.user.partner_id.id,
                                                        'body': sh_message or False,
                                                        'message_type': 'comment',
                                                        })

                    if self.account_payment_id and self.account_payment_id.company_id.invoice_display_in_message:
                        self.env['mail.message'].create({
                                                        'partner_ids': [(6, 0, partner.ids)],
                                                        'model': 'account.payment',
                                                        'res_id': active_id,
                                                        'author_id': self.env.user.partner_id.id,
                                                        'body': sh_message or False,
                                                        'message_type': 'comment',
                                                        })
                    if find_default.config_type == 'chat_api':
                        for attach in rec.attachment_ids:
                            encoded = attach.datas.decode("utf-8")
                            base64_file = 'data:%s;base64,{}'.format(
                                encoded) % (attach.mimetype)
                            url = "https://api.chat-api.com/%s/sendFile?token=%s" % (
                                find_default.instance_id, find_default.token)
                            payload = {
                                "body": '%s' % (base64_file),
                                "phone": partner.mobile,
                                "filename": attach.name,
                            }
                            requests.get(url=url, headers=headers, data=json.dumps(
                                payload, indent=4, sort_keys=True, default=str))
                    elif find_default.config_type == 'api_chat':
                        for attach in rec.attachment_ids:
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
                            number = str(partner.mobile)
                            updated_number = number.replace("+", "").replace(" ", "")
                            payload = {
                                "number": updated_number,
                                "url": '%s' % base64_file,
                            }
                            sendfile = requests.post(
                                url=url, headers=headers, data=json.dumps(payload))
                            if sendfile.status_code != 200:
                                raise UserError(_(sendfile.text))
