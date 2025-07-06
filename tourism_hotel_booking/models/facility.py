# -*- coding: utf-8 -*-
from odoo import api, fields, models


class HotelFacility(models.Model):
    _name = 'tourism.hotel.facility'
    _description = 'Hotel Facility'

    name = fields.Char(string="Facility", required=True)

    sequence = fields.Integer('Sequence', default=10)


