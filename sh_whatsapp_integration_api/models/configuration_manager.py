# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models, fields , _, api
import requests
from odoo.exceptions import UserError
import base64
class ConfigManager(models.Model):
    _name = 'sh.configuration.manager'
    _description = "Stores Your Credentials"

    user_id = fields.Many2one('res.users', index=True, default=lambda self: self.env.user)
    name = fields.Char("Name")
    config_type = fields.Selection([("chat_api","Chat Api"),('api_chat','Api Chat')])
    instance_id = fields.Char("Instance")
    token = fields.Char("Token")
    send_base64_data = fields.Text("base64")
    status = fields.Selection([('draft','Draft'),('verified','Verified')],default='draft')
    default_send = fields.Boolean("Use this Default")
    common_to_all = fields.Boolean("Common Use",default=True)
    def authenticate(self):
        headers = {
                "Content-Type" : "image/png"
            }
        if self.config_type == 'chat_api' and self.instance_id and self.token:
            url = "https://api.chat-api.com/%s/qr_code?token=%s" %(self.instance_id,self.token)                        
            get_qr_code = requests.get(url=url,headers=headers)           
            get_qr_code_bytes = get_qr_code.content
            encoded = base64.b64encode(get_qr_code_bytes)
            encoded = encoded.decode("utf-8")
            base64_png = 'data:image/png;base64,{}'.format(encoded)
            self.send_base64_data = base64_png
            new_wizard = self.env['sh.qr.code.wizard'].create({               
            })
            view_id = self.env.ref('sh_whatsapp_integration_api.sh_qr_code_form').id
            return {
                'type': 'ir.actions.act_window',
                'name': _('Generated QR Code'),
                'view_mode': 'form',
                'res_model': 'sh.qr.code.wizard',
                'target': 'new',
                'res_id': new_wizard.id,
                'views': [[view_id, 'form']],
            }
        elif self.config_type == 'api_chat' and self.instance_id and self.token:
            url = 'https://api.apichat.io/v1/qr_code'
            headers['client-id'] = self.instance_id
            headers['token'] = self.token
            get_qr_code = requests.get(url=url,headers=headers)
            if get_qr_code.status_code == 200:               
                if len(get_qr_code.text) > 200:
                    new_wizard = self.env['sh.qr.code.wizard'].create({
                        'sh_qr_code_img' : get_qr_code.text
                    })
                    view_id = self.env.ref('sh_whatsapp_integration_api.sh_qr_code_form').id
                    return {
                        'type': 'ir.actions.act_window',
                        'name': _('Generated QR Code'),
                        'view_mode': 'form',
                        'res_model': 'sh.qr.code.wizard',
                        'target': 'new',
                        'res_id': new_wizard.id,
                        'views': [[view_id, 'form']],
                    }
                else:
                    self.status = 'verified'
    @api.model
    def create(self,vals):
        if vals['default_send'] == True:
            domain =[('default_send','=',True)]
            get_data = self.search(domain)
            if get_data:
                raise UserError (_("One Default send alredy exists"))
        res = super(ConfigManager,self).create(vals)
        return res
