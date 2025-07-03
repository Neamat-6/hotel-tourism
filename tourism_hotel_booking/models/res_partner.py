# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def action_open_tourism_bookings(self):
        self.ensure_one()
        action = self.env.ref('tourism_hotel_booking.action_hotel_booking').read()[0]
        action['domain'] = [('partner_id', '=', self.id)]
        return action



