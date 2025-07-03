import base64

from odoo import fields, models, api, _
import requests
import json

from odoo.addons.test_limits.models import m
from odoo.exceptions import UserError, ValidationError


class HotelWorkOrder(models.Model):
    _name = 'hotel.work.order'
    _description = 'Hotel Work Order'

    name = fields.Char(string='Order Reference', required=True, copy=False, readonly=True,
                       index=True, default=lambda self: _('New'))
    order_type = fields.Selection(selection=[('immediate', 'Immediate'), ('advance', 'Advance')])
    date_start = fields.Datetime()
    date_stop = fields.Datetime()
    date_deadline = fields.Datetime()
    room_id = fields.Many2one('hotel.room', required=True)
    employee_id = fields.Many2one('hr.employee')
    description = fields.Text(required=True)
    type = fields.Selection(selection=[
        ('fix', 'Fix'),
        ('maintenance', 'Maintenance'),
        ('clean', 'Clean'),
        ('other', 'Other'),
    ], required=True)
    priority = fields.Selection(selection=[
        ('high', 'High'),
        ('low', 'Low'),
        ('manual', 'Manual'),
    ], required=True)
    state = fields.Selection(selection=[
        ('new', 'New'),
        ('assigned', 'Assigned'),
        ('progress', 'Progress'),
        ('done', 'Done'),
    ], required=True, default='new')
    department_id = fields.Many2one('hr.department')
    employee_ids = fields.Many2many('hr.employee')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, required=True)
    attachment = fields.Binary("Attachment")
    attachment_name = fields.Char("Attachment Name")
    send_whatsapp = fields.Boolean("Send Whatsapp Message")

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('hotel.work.order.sequence') or _('New')
        result = super(HotelWorkOrder, self).create(vals)
        return result

    @api.onchange('order_type')
    def onchange_order_type(self):
        for record in self:
            if record.order_type == 'immediate':
                record.date_start = fields.Date.today()
            else:
                record.date_start = ""

    @api.onchange('department_id')
    def get_employee(self):
        if self.department_id:
            self.employee_ids = self.env['hr.employee'].search([('department_id', '=', self.department_id.id)])
        else:
            self.employee_ids = False
            self.employee_id = False

    def send_by_whatsapp_direct(self):
        find_default = self.env['sh.configuration.manager'].search([('default_send', '=', 'True')], limit=1)
        user = self.env['hr.employee'].search([('id', '=', self.employee_id.id)], limit=1)
        headers = {"Content-Type": "application/json"}
        if self.send_whatsapp:
            if find_default:
                if user.mobile_phone:
                    for rec in self:
                        if rec.company_id.display_in_message:
                            message = 'لديك طلب نزيل' \
                                      ' غرفة رقم: {}' \
                                      ' الحالة: {}' \
                                      ' الأهمية: {}' \
                                      ' الوصـف: {}'.format(rec.room_id.name, rec.state, rec.priority, rec.description)

                            # attachment_data = rec.attachment if rec.attachment else None

                            if find_default.config_type == 'api_chat':
                                url = "https://api.apichat.io/v1/sendText"
                                headers['client-id'] = find_default.instance_id
                                headers['token'] = find_default.token
                                payload = {
                                    "text": message,
                                    "number": user.mobile_phone,
                                    # "attachment": base64.b64encode(attachment_data).decode('utf-8') if attachment_data else None,
                                    # "attachment_name": rec.attachment_name
                                }
                                send_message = requests.post(url=url, headers=headers, data=json.dumps(payload))
                                if send_message.status_code == 200:
                                    send_message_json = send_message.json()
                                    if 'message' in send_message_json.keys():
                                        e = send_message_json['message']
                                        raise UserError(_(e))
                                else:
                                    raise UserError(_("Message Not Sent %s" % send_message))
                            self.env['mail.message'].create({
                                'model': 'hotel.work.order',
                                'res_id': rec.id,
                                'author_id': self.env.user.partner_id.id,
                                'body': message or False,
                                'message_type': 'comment',
                                # 'attachment_ids': [(0, 0, {
                                #     'name': rec.attachment_name,
                                #     'datas': attachment_data,
                                #     'res_model': 'hotel.work.order',
                                #     'res_id': rec.id,
                                # })] if attachment_data else False,
                            })
                else:
                    pass
            else:
                raise UserError(_("No Default Configuration is selected"))

    def button_assign(self):
        self.state = 'assigned'
        self.send_by_whatsapp_direct()

    def button_progress(self):
        self.state = 'progress'
        self.send_progress_by_whatsapp()

    def button_done(self):
        self.state = 'done'
        self.send_done_by_whatsapp()

    def send_progress_by_whatsapp(self):
        find_default = self.env['sh.configuration.manager'].search([('default_send', '=', 'True')], limit=1)
        user = self.env['booking.folio'].sudo().search(
            [('room_id', '=', self.room_id.id), ('state', '=', 'checked_in')]).partner_id
        headers = {"Content-Type": "application/json"}
        if self.send_whatsapp:
            if find_default:
                if user.mobile:
                    for rec in self:
                        if rec.company_id.display_in_message:
                            message = 'تم بدأ العمل في تنفيذ طلبك ' \
                                      ' غرفة رقم: {} ' \
                                      ' الحالة: {} ' \
                                      ' الأهمية: {} ' \
                                      ' الوصـف: {} '.format(rec.room_id.name, rec.state, rec.priority, rec.description)
                            # attachment_data = rec.attachment if rec.attachment else None

                            if find_default.config_type == 'api_chat':
                                url = "https://api.apichat.io/v1/sendText"
                                headers['client-id'] = find_default.instance_id
                                headers['token'] = find_default.token
                                if user:
                                    payload = {
                                        "text": message,
                                        "number": user.mobile,
                                    }
                                    send_message = requests.post(url=url, headers=headers, data=json.dumps(payload))
                                    if send_message.status_code == 200:
                                        send_message_json = send_message.json()
                                        if 'message' in send_message_json.keys():
                                            e = send_message_json['message']
                                            raise UserError(_(e))
                                    else:
                                        raise UserError(_("Message Not Sent %s" % send_message))

                                # employee message
                                if self.employee_id:
                                    empl_payload = {
                                        "text": message,
                                        "number": self.employee_id.mobile_phone,
                                    }
                                    empl_send_message = requests.post(url=url, headers=headers,
                                                                      data=json.dumps(empl_payload))
                                    if empl_send_message.status_code == 200:
                                        emp_send_message_json = empl_send_message.json()
                                        if 'message' in emp_send_message_json.keys():
                                            err = emp_send_message_json['message']
                                            raise UserError(_(err))
                                    else:
                                        raise UserError(_("Message Not Sent %s" % empl_send_message))
                            self.env['mail.message'].create({
                                'model': 'hotel.work.order',
                                'res_id': rec.id,
                                'author_id': self.env.user.id,
                                'body': message or False,
                                'message_type': 'comment',
                            })
                    else:
                        pass
            else:
                raise UserError(_("No Default Configuration is selected"))

    def send_done_by_whatsapp(self):
        find_default = self.env['sh.configuration.manager'].search([('default_send', '=', 'True')], limit=1)
        user = self.env['booking.folio'].sudo().search(
            [('room_id', '=', self.room_id.id), ('state', '=', 'checked_in')]).partner_id
        headers = {"Content-Type": "application/json"}
        if self.send_whatsapp:
            if find_default:
                if user.mobile:
                    for rec in self:
                        if rec.company_id.display_in_message:
                            message = 'تم الانتهاء من طلبكم ' \
                                      ' غرفة رقم: {} ' \
                                      ' الحالة: {} ' \
                                      ' الأهمية: {} ' \
                                      ' الوصـف: {} '.format(rec.room_id.name, rec.state, rec.priority, rec.description)

                            if find_default.config_type == 'api_chat':
                                url = "https://api.apichat.io/v1/sendText"
                                headers['client-id'] = find_default.instance_id
                                headers['token'] = find_default.token
                                payload = {
                                    "text": message,
                                    "number": user.mobile,
                                }
                                send_message = requests.post(url=url, headers=headers, data=json.dumps(payload))
                                if send_message.status_code == 200:
                                    send_message_json = send_message.json()
                                    if 'message' in send_message_json.keys():
                                        e = send_message_json['message']
                                        raise UserError(_(e))
                                else:
                                    raise UserError(_("Message Not Sent %s" % send_message))
                            self.env['mail.message'].create({
                                'model': 'hotel.work.order',
                                'res_id': rec.id,
                                'author_id': self.env.user.id,
                                'body': message or False,
                                'message_type': 'comment',
                            })
                else:
                    pass
            else:
                raise UserError(_("No Default Configuration is selected"))
