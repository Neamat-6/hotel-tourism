# -*- coding: utf-8 -*-
from odoo import api, fields, models


class NewModule(models.Model):
    _inherit = 'hotel.hotel'
    _description = 'Hotels'

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

    room_ids = fields.One2many('hotel.room','hotel_id', default=get_default_rooms)
    account_journal_id = fields.Many2one('account.journal')
    journal_id = fields.Many2one('account.journal',string='Journal')
    phone = fields.Char('Phone')
    mobile = fields.Char('Mobile')
    email = fields.Char('Email')
    address = fields.Char('Address')
    partner_id = fields.Many2one('res.partner')
    check_in = fields.Float()
    check_out = fields.Float()
    latitude = fields.Char()
    longitude = fields.Char()


    @api.model
    def create(self, vals):
        if not vals.get('name') or vals.get('partner_id'):
            self.clear_caches()
            return super(NewModule, self).create(vals)
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
        hotel = super(NewModule, self).create(vals)
        return hotel
