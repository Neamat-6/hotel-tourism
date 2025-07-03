from odoo import fields, models, api
from odoo.exceptions import ValidationError


class Company(models.Model):
    _inherit = 'res.company'

    hotel_type = fields.Selection(string="Type", selection=[
        ('makkah', 'Makkah'), ('madinah', 'Madinah'), ('arfa', 'Arfa'),
        ('minnah', 'Minnah'), ('hotel', 'Main Shift')
    ])

    def button_create_hotel_data(self):
        if not self.hotel_type:
            raise ValidationError("please add hotel type!")
        hotel_id = self.env['hotel.hotel'].sudo().create({
            'name': self.name,
            'type': self.hotel_type,
            'company_id': self.id,
        })
        self.write({'related_hotel_id': hotel_id.id})
        # room types
        double = self.env['room.type'].sudo().create({
            'name': 'Double',
            'mini_adults': 2,
            'max_adults': 2,
            'company_id': self.id,
        })
        triple = self.env['room.type'].sudo().create({
            'name': 'Triple',
            'mini_adults': 3,
            'max_adults': 3,
            'company_id': self.id,
        })
        quad = self.env['room.type'].sudo().create({
            'name': 'Quad',
            'mini_adults': 4,
            'max_adults': 4,
            'company_id': self.id,
        })
        # floors
        self.env['hotel.floor'].sudo().create({
            'name': 'Floor 1',
            'hotel_id': hotel_id.id,
            'company_id': self.id,
            'sequence': 1,
        })
        self.env['hotel.floor'].sudo().create({
            'name': 'Floor 2',
            'hotel_id': hotel_id.id,
            'company_id': self.id,
            'sequence': 1,
        })
        self.env['hotel.floor'].sudo().create({
            'name': 'Floor 3',
            'hotel_id': hotel_id.id,
            'company_id': self.id,
            'sequence': 3,
        })
        self.env['hotel.floor'].sudo().create({
            'name': 'Floor 4',
            'hotel_id': hotel_id.id,
            'company_id': self.id,
            'sequence': 4,
        })
        # rate type
        room_only = self.env['hotel.rate.type'].sudo().create({
            'name': 'Room Only',
            'code': 'Room Only',
            'company_id': self.id,
        })
        # rate plans
        self.env['hotel.rate.plan'].sudo().create({
            'room_type_id': double.id,
            'rate_type_id': room_only.id,
            'company_id': self.id,
        })
        self.env['hotel.rate.plan'].sudo().create({
            'room_type_id': triple.id,
            'rate_type_id': room_only.id,
            'company_id': self.id,
        })
        self.env['hotel.rate.plan'].sudo().create({
            'room_type_id': quad.id,
            'rate_type_id': room_only.id,
            'company_id': self.id,
        })
