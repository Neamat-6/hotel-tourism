# -*- coding: utf-8 -*-
from odoo import fields, models
from odoo.addons.base.models.res_partner import _tz_get


class ResCompany(models.Model):
    _inherit = 'res.company'

    # hotel_room_type_default_id = fields.Many2one('hotel.room.type')
    english_name = fields.Char()
    hotel_default_tax_ids = fields.Many2many('account.tax', 'hotel_booking_tax_conf_company_rel')
    hotel_check_in_point = fields.Float()
    hotel_check_out_point = fields.Float()
    hotel_check_in_am_pm = fields.Selection([('AM', 'AM'), ('PM', 'PM')])
    hotel_check_out_am_pm = fields.Selection([('AM', 'AM'), ('PM', 'PM')])
    hotel_timezone = fields.Selection(_tz_get)
    hotel_default_customer_id = fields.Many2one("res.partner")
    hotel_booking_display_only_available = fields.Boolean()
    related_hotel_id = fields.Many2one('hotel.hotel')
    audit_date = fields.Date(default=fields.Date.today())
    can_edit_audit_date = fields.Boolean(compute='compute_can_edit_audit_date')
    # Bank Details
    bank_name = fields.Char()
    account_name = fields.Char()
    account_number = fields.Char()
    account_iban = fields.Char()
    account_swift = fields.Char()
    use_whatsapp = fields.Boolean(default=True)
    checkout_charge = fields.Boolean()
    limited_access_payment = fields.Boolean("Limited Access Payment", default=True)
    is_required_company = fields.Boolean("Required Company Fields (ZAKAT)")
    apply_ntmp = fields.Boolean(string='Apply NTMP', default=True)

    def compute_can_edit_audit_date(self):
        for rec in self:
            rec.can_edit_audit_date = False
            if rec.env.user.has_group('hotel_booking.group_update_audit_date'):
                rec.can_edit_audit_date = True

    def button_open_hotel_form(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Create Hotel',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': "hotel.hotel",
            'target': 'new',
            'context': {
                'default_company_id': self.id
            },
        }
