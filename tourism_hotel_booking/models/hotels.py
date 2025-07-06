# -*- coding: utf-8 -*-
from odoo import api, fields, models


class TourismHotel(models.Model):
    _name = 'tourism.hotel.hotel'
    _description = 'Tourism Hotels'

    def get_default_rooms(self):
        default_rooms_list = []
        default_rooms = self.env['hotel.default.room'].search([])
        for room in default_rooms:
            default_rooms_list.append(
                (0, 0, {
                    'name': room.name,
                    'floor_id': room.floor_id.id,
                    'sequence': room.sequence,
                    'booking_ok': room.booking_ok,
                    'telephone_extension': room.telephone_extension,
                    'room_size': room.room_size,
                    'note': room.note,
                }),
            )
        return default_rooms_list

    name = fields.Char(string="Name", required=True)
    floor_ids = fields.One2many("tourism.hotel.floor", "hotel_id")
    sequence = fields.Integer('Sequence', default=10)
    room_count = fields.Integer(compute="_compute_room_count", string="No. of Rooms")
    default_room_type_id = fields.Many2one('tourism.hotel.room.type', string='Default Room Type')
    country_id = fields.Many2one('res.country', string='Country')
    state_id = fields.Many2one('res.country.state', string='City', domain="[('country_id', '=', country_id)]")
    room_ids = fields.One2many('tourism.hotel.room','hotel_id', default=get_default_rooms)
    facility_line_ids = fields.Many2many('tourism.hotel.room.facility')
    account_journal_id = fields.Many2one('account.journal')
    journal_id = fields.Many2one('account.journal',string='Journal')
    phone = fields.Char('Phone')
    mobile = fields.Char('Mobile')
    email = fields.Char('Email')
    address = fields.Char('Address')
    partner_id = fields.Many2one('res.partner')
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
    check_in = fields.Float()
    check_out = fields.Float()
    latitude = fields.Char()
    longitude = fields.Char()

    def _compute_room_count(self):
        for hotel in self:
            count = 0
            for floor in hotel.floor_ids:
                count += len(floor.room_ids)
            hotel.room_count = count

    @api.model
    def create(self, vals):
        if not vals.get('name') or vals.get('partner_id'):
            self.clear_caches()
            return super(TourismHotel, self).create(vals)
        partner = self.env['res.partner'].create({
            'name': vals['name'],
            'phone': vals.get('phone'),
            'mobile': vals.get('mobile'),
            'email': vals.get('email'),
            'street': vals.get('address'),
            'supplier_rank': 1,
            'check': True,
            'is_company': True
        })
        partner.flush()
        vals['partner_id'] = partner.id
        self.clear_caches()
        hotel = super(TourismHotel, self).create(vals)
        return hotel
