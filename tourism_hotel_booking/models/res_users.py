# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'
    
    hotel_booking_dashboard_hotel_id = fields.Many2one("tourism.hotel.hotel")
