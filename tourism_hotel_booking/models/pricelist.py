# -*- coding: utf-8 -*-
from odoo import api, fields, models


class TourismHotelPricelist(models.Model):
    _name = 'tourism.hotel.pricelist'
    _description = 'Pricelist'

    name = fields.Char(string="Name", required=True)
    sequence = fields.Integer('Sequence', default=10)
    hotel_id = fields.Many2one("tourism.hotel.hotel", required=True)
    type = fields.Selection([('room', 'Room'), ('room_type', 'Room Type'),], string="Based On", default="room")
    room_ids = fields.Many2many('tourism.hotel.room')
    room_type_ids = fields.Many2many('tourism.hotel.room.type')
    line_ids = fields.One2many('tourism.hotel.pricelist.line', 'pricelist_id')


class TourismHotelPricelistLine(models.Model):
    _name = 'tourism.hotel.pricelist.line'
    _description = 'Pricelist Lines'

    pricelist_id = fields.Many2one('tourism.hotel.pricelist')
    product_id = fields.Many2one("product.product", string="Product", required=True)
    price = fields.Float(string="Price")
    price_type = fields.Selection([('fixed', 'Fixed'), ('multiply_with_guest', 'Multiply With No.of.Guests'),], default="fixed", string="Price Type")
    
    
