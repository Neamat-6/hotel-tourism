# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'
    
    hotel_booking_screen_color = fields.Char(default="#ff7373")
    hotel_booking_dashboard_hotel_id = fields.Many2one("hotel.hotel")
    hotel_booking_dashboard_view_type = fields.Char()