# -*- coding: utf-8 -*-
import ast
from odoo import api, fields, models
from odoo.addons.base.models.res_partner import _tz_get


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # hotel_room_type_default_id = fields.Many2one('hotel.room.type')
    hotel_default_tax_ids = fields.Many2many('account.tax', 'hotel_booking_tax_conf_rel', string='Taxes', )
    hotel_check_in_point = fields.Float(string="Check In Point")
    hotel_check_out_point = fields.Float(string="Check Out Point")
    hotel_check_in_am_pm = fields.Selection([('AM', 'AM'), ('PM', 'PM')])
    hotel_check_out_am_pm = fields.Selection([('AM', 'AM'), ('PM', 'PM')])
    hotel_timezone = fields.Selection(_tz_get, string='Timezone') # , default=lambda self: self._context.get('tz')
    hotel_default_customer_id = fields.Many2one("res.partner")
    hotel_booking_display_only_available = fields.Boolean()
    particulars = fields.Selection([('Municipality', 'Municipality'), ('Service Charge', 'Service Charge')], default='Municipality')

    def set_values(self):
        super(ResConfigSettings, self).set_values()

        company = self.env.company

        company.hotel_default_tax_ids = self.hotel_default_tax_ids.ids or []
        company.hotel_check_in_point = self.hotel_check_in_point
        company.hotel_check_out_point = self.hotel_check_out_point
        company.hotel_timezone = self.hotel_timezone
        company.hotel_check_in_am_pm = self.hotel_check_in_am_pm
        company.hotel_check_out_am_pm = self.hotel_check_out_am_pm
        company.hotel_default_customer_id = self.hotel_default_customer_id.id
        company.hotel_booking_display_only_available = self.hotel_booking_display_only_available

        self.env['ir.config_parameter'].sudo().set_param('hotel_booking.particulars', self.particulars or '')

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()

        company = self.env.company

        res['hotel_default_tax_ids'] = company.hotel_default_tax_ids.ids or []
        res['hotel_check_in_point'] = company.hotel_check_in_point
        res['hotel_check_out_point'] = company.hotel_check_out_point
        res['hotel_timezone'] = company.hotel_timezone
        res['hotel_check_in_am_pm'] = company.hotel_check_in_am_pm
        res['hotel_check_out_am_pm'] = company.hotel_check_out_am_pm
        res['hotel_default_customer_id'] = company.hotel_default_customer_id.id
        res['hotel_booking_display_only_available'] = company.hotel_booking_display_only_available
        config = self.env['ir.config_parameter'].sudo()
        particulars_value = config.get_param('hotel_booking.particulars', default='Municipality')
        res.update({
            'particulars': particulars_value,
        })
        return res




