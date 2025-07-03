# -*- coding: utf-8 -*-
from odoo import api, fields, models


class Hotel(models.Model):
    _name = 'hotel.hotel'
    _description = 'Hotels'

    name = fields.Char(string="Name", required=True)
    floor_ids = fields.One2many("hotel.floor", "hotel_id")
    sequence = fields.Integer('Sequence', default=10)
    room_count = fields.Integer(compute="_compute_room_count", string="No. of Rooms")
    default_room_type_id = fields.Many2one('hotel.room.type', string='Default Room Type')
    country_id = fields.Many2one('res.country', string='Country')
    state_id = fields.Many2one('res.country.state', string='City', domain="[('country_id', '=', country_id)]")
    room_ids = fields.One2many('hotel.room','hotel_id')
    facility_line_ids = fields.Many2many('hotel.room.facility')
    address = fields.Char('Address')
    hotel_rate = fields.Selection([
        ('0', 'Zero'),
        ('1', 'One'),
        ('2', 'Two'),
        ('3', 'Tree'),
        ('4', 'Four'),
        ('5', 'Five'),
        ('6', 'Six'),
        ('7', 'Seven'),
    ], default='0', index=True, store=True)
    image_1920 = fields.Binary('Image')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, required=True)
    # accounting
    room_charge_account_id = fields.Many2one('account.account')
    municipality_account_id = fields.Many2one('account.account')
    food_revenue_account_id = fields.Many2one('account.account')
    beverage_revenue_account_id = fields.Many2one('account.account')
    laundry_revenue_account_id = fields.Many2one('account.account')
    rent_account_id = fields.Many2one('account.account')
    image = fields.Image()
    expiration_date = fields.Date()
    description = fields.Char()
    can_edit_expiration_date = fields.Boolean(compute='compute_can_edit_expiration_date')

    def compute_can_edit_expiration_date(self):
        for rec in self:
            rec.can_edit_expiration_date = False
            if rec.env.user.has_group('hotel_booking.group_update_expiration_date'):
                rec.can_edit_expiration_date = True

    def _compute_room_count(self):
        for hotel in self:
            count = 0
            for floor in hotel.floor_ids:
                count += len(floor.room_ids)
            hotel.room_count = count

    @api.model
    def create(self, vals):
        res = super(Hotel, self).create(vals)
        if res.company_id:
            # res.company_id.company_has_hotel = True
            res.company_id.related_hotel_id = res.id
        return res
