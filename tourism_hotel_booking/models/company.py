# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.addons.base.models.res_partner import _tz_get


class ResCompany(models.Model):
    _inherit = 'res.company'

    # hotel_room_type_default_id = fields.Many2one('tourism.hotel.room.type')
    hotel_default_tax_ids = fields.Many2many('account.tax', 'hotel_booking_tax_conf_company_rel')
    hotel_check_in_point = fields.Float()
    hotel_check_out_point = fields.Float()
    hotel_check_in_am_pm = fields.Selection([('AM', 'AM'), ('PM', 'PM')])
    hotel_check_out_am_pm = fields.Selection([('AM', 'AM'), ('PM', 'PM')])
    hotel_timezone = fields.Selection(_tz_get)
    hotel_default_customer_id = fields.Many2one("res.partner")
    hotel_booking_display_only_available = fields.Boolean()

