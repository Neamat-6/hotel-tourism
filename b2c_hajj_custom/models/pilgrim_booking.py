from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.http import request
import requests
import json
import base64


class ExtraBooking(models.Model):
    _name = 'extra.booking'
    _description= 'Extras'

    name = fields.Char(required=True)

class ExtraBookingLine(models.Model):
    _name = 'extra.booking.line'

    book_id = fields.Many2one('pilgrim.booking', ondelete='cascade')
    extra_id = fields.Many2one('extra.booking')
    quantity = fields.Integer()
    price_unit = fields.Float()


class AccountMove(models.Model):
    _inherit = 'account.move'

    pilgrim_booking_id = fields.Many2one('pilgrim.booking')


class PilgrimBooking(models.Model):
    _name = 'pilgrim.booking'
    _rec_name = 'partner_id'
    _inherit = ["mail.thread", 'portal.mixin']

    source = fields.Selection([('person','Direct'), ('company','Company')],required=True)
    partner_id = fields.Many2one('res.partner',required=True)
    package_id = fields.Many2one('booking.package', required=True, domain="[('package_closed', '=', False)]")
    pilgrim_count = fields.Integer()
    pilgrim_cost = fields.Float(string="sales Price")
    total_cost = fields.Float(compute='compute_total_cost', store=True)
    room_type = fields.Selection(selection=[('2', '2'), ('3', '3'), ('4', '4')])
    line_ids = fields.One2many('pilgrim.booking.line', 'book_id')
    state= fields.Selection([('draft', 'Tentative Confirmation'),('hotel_confirm', 'Confirmed Waiting Payment'),('confirmed', 'Confirmed'),('cancelled', 'Cancelled')], default='draft')
    move_id = fields.Many2one('account.move', copy=False)
    extra_lines = fields.One2many('extra.booking.line', 'book_id')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id, string='Company')

    @api.constrains('line_ids', 'pilgrim_count', 'source')
    def _check_line_count(self):
        for rec in self:
            if rec.pilgrim_count:
                if rec.source == 'company':
                    if len(rec.line_ids) != rec.pilgrim_count:
                        raise UserError(_("The number of pilgrims must match the number of pilgrims lines"))
                elif rec.source == 'person':
                    if len(rec.line_ids) != rec.pilgrim_count - 1:
                        raise UserError(_("The number of pilgrims must match the number of pilgrims lines minus one."))

    @api.onchange('source')
    def _onchange_source(self):
        self.partner_id = False
        domain = []
        if self.source == 'person':
            domain = [('is_company', '=', False)]
        elif self.source == 'company':
            domain = [('is_company', '=', True)]

        return {
            'domain': {
                'partner_id': domain
            }
        }

    @api.depends('pilgrim_count', 'pilgrim_cost', 'extra_lines.quantity', 'extra_lines.price_unit')
    def compute_total_cost(self):
        for rec in self:
            total_cost = 0.0
            for line in rec.extra_lines:
                total_cost += line.quantity * line.price_unit
            total_cost += rec.pilgrim_count * rec.pilgrim_cost
            rec.total_cost = total_cost


    def create_invoice(self):
        self.ensure_one()
        tax_ids = self.env.company.hotel_default_tax_ids.ids
        invoice_line_vals = [(0, 0, {
                # 'product_id': line.room_id.product_id.id,
                'name': self.package_id.package_code,
                'quantity': self.pilgrim_count,
                'price_unit': self.pilgrim_cost,
                # 'tax_ids': line.tax_id,
                # 'account_id': hotel_hotel_obj.account_journal_id.default_account_id.id
            })]
        for line in self.extra_lines:
            invoice_line_vals.append((0, 0, {
                'name': line.extra_id.name,
                'quantity': line.quantity,
                'price_unit': line.price_unit,
            }))
        move_vals = {
            'move_type': 'out_invoice',
            'partner_id': self.partner_id.id,
            'pilgrim_booking_id': self.id,
            # 'journal_id': journal_id,
            'invoice_user_id': self._uid,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': invoice_line_vals,
            'company_id': self.company_id.id,
        }
        move = self.env['account.move'].with_context({'line_ids': False}).create(move_vals)
        move.action_post()
        print('mmmmmmmmmove', move)
        self.move_id = move.id

    def update_invoice(self):
        print('callllllllllllllllllled')
        self.move_id.line_ids.unlink()
        self.move_id.invoice_line_ids.unlink()
        print('after delete', self.move_id)
        income_account = self.env['account.account'].search([
            ('user_type_id.type', '=', 'income'),
            ('deprecated', '=', False),
            ('company_id', '=', self.env.company.id)
        ], limit=1)
        print('income_account', income_account)
        invoice_line_vals = [(0, 0, {
                # 'product_id': line.room_id.product_id.id,
                'name': self.package_id.package_code,
                'quantity': self.pilgrim_count,
                'price_unit': self.pilgrim_cost,
                'account_id': income_account.id,
                # 'tax_ids': line.tax_id,
                # 'account_id': hotel_hotel_obj.account_journal_id.default_account_id.id
            })]
        self.move_id.write({
            'partner_id': self.partner_id.id,
            'invoice_line_ids': invoice_line_vals
        })
        self.move_id._recompute_dynamic_lines(recompute_all_taxes=True)
        self.move_id.action_post()

    def create_booking(self):
        for rec in self:
            if not rec.total_cost:
                raise UserError(_("can not create invoice with zero amount"))
            if not rec.move_id:
                rec.create_invoice()
            else:
                print('hhhhhhhhhhhhhhhhhhhhhhhh')
                rec.update_invoice()
            if rec.source == 'person':
                rec.partner_id.write({'package_id': rec.package_id,
                                      'makkah_room_type': rec.room_type,
                                       'madinah_room_type': rec.room_type,
                                       'hotel_room_type': rec.room_type})
            for line in rec.line_ids:
                vals = line.get_pilgrim_data()
                if line.partner_id:
                    line.partner_id.sudo().write(vals)
                else:
                    pilgrim = self.env['res.partner'].sudo().create(vals)
                    line.write({'partner_id': pilgrim.id})
            rec.state = 'hotel_confirm'

    def action_confirm(self):
        for rec in self:
            if rec.move_id:
                # if rec.move_id.payment_state != 'paid':
                if rec.move_id.amount_residual != 0:
                    raise UserError("The linked invoice must be fully paid before confirming.")
                rec.state = 'confirmed'
            else:
                raise UserError("Must create invoice first")


    def action_reset_to_draft(self):
        for rec in self:
            if rec.source == 'person':
                rec.partner_id.sudo().update({
                    'package_id': False,
                })
            for line in rec.line_ids:
                line.partner_id.write({
                    'package_id': False,
                })
            rec.move_id.button_draft()
            rec.state = 'draft'


    def action_cancel(self):
        for rec in self:
            if rec.source == 'person':
                rec.partner_id.sudo().update({
                    'package_id': False,
                })
            for line in rec.line_ids:
                line.partner_id.write({
                    'package_id': False,
                })
            rec.move_id.button_cancel()
            rec.state = 'cancelled'

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('Cannot delete a record which is in state \'%s\'.') % (rec.state,))
        return super(PilgrimBooking, self).unlink()

    def action_open_invoice(self):
        self.ensure_one()
        if self.move_id:
            return {
                'type': 'ir.actions.act_window',
                'name': _('Invoice'),
                'view_mode': 'form',
                'res_model': 'account.move',
                'res_id': self.move_id.id,
                'target': 'current',
            }
        else:
            return {
                'type': 'ir.actions.act_window_close',
            }


    def generate_report(self):
        report_sudo = request.env.ref('b2c_hajj_custom.action_pilgrim_booking_report').sudo()
        method_name = '_render_qweb_pdf'
        report = getattr(report_sudo, method_name)(
            [self.id], data={'report_type': 'pdf'})[0]
        encoded = base64.b64encode(report)
        encoded = encoded.decode("utf-8")
        base64_file = 'data:application/pdf;base64,{}'.format(encoded)
        return (base64_file)

    def send_by_whatsapp_direct_to_booking(self):
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
                            message = "Dear " + str(rec.partner_id.name)
                            if find_default.config_type == 'chat_api':
                                url = "https://api.chat-api.com/%s/sendMessage?token=%s" % (
                                    find_default.instance_id, find_default.token)
                                payload = {
                                    "body": message,
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
                                    "text": message,
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
                                'model': 'pilgrim.booking',
                                'res_id': rec.id,
                                'author_id': self.env.user.partner_id.id,
                                'body': message or False,
                                'message_type': 'comment',
                            })
                    if find_default.config_type == 'chat_api':
                        url = "https://api.chat-api.com/%s/sendFile?token=%s" % (
                            find_default.instance_id, find_default.token)
                        if self.state == 'draft' or self.state == 'sent':
                            filename = "Pilgrim Booking - %s.pdf" % (
                                self.partner_id.name)
                        else:
                            filename = "Pilgrim Booking - %s.pdf" % (self.partner_id.name)
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




class PilgrimBookingLine(models.Model):
    _name = 'pilgrim.booking.line'

    name = fields.Char()
    main_member_id = fields.Many2one('res.partner')
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
    ], string="Gender")
    pilgrim_type = fields.Selection(selection=[
        ('main', 'Main'), ('member', 'Family Member')
    ])
    book_id = fields.Many2one('pilgrim.booking', ondelete='cascade')
    partner_id = fields.Many2one('res.partner')

    @api.onchange('pilgrim_type')
    def onchange_pilgrim_type(self):
        for rec in self:
            if rec.pilgrim_type == 'member':
                if rec.book_id.source == 'person':
                    rec.main_member_id = rec.book_id.partner_id.id
            else:
                rec.main_member_id = False

    def get_pilgrim_data(self):
        return {
            'name': self.name,
            'gender': self.gender,
            'pilgrim_type': self.pilgrim_type,
            'main_member_id': self.main_member_id.id if self.main_member_id else None,
            'package_id': self.book_id.package_id.id,
            'makkah_room_type': self.book_id.room_type,
            'madinah_room_type': self.book_id.room_type,
            'hotel_room_type': self.book_id.room_type,
        }