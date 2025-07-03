from odoo import fields, models, api
from odoo.exceptions import ValidationError


class HotelRoomGenerate(models.TransientModel):
    _name = 'hotel.room.generate'
    _description = 'Hotel Room Generate'

    hotel_id = fields.Many2one('hotel.hotel')
    company_id = fields.Many2one('res.company')
    room_type_id = fields.Many2one('room.type', required=True, domain="[('company_id', '=', company_id)]")
    floor_id = fields.Many2one('hotel.floor', domain="[('company_id', '=', company_id)]")
    start = fields.Integer(default=101, required=True)
    count = fields.Integer(default=1, required=True)

    @api.constrains('start', 'count')
    def validate_start_and_count(self):
        for rec in self:
            if not rec.start:
                raise ValidationError("Please add start number!")
            if not rec.count:
                raise ValidationError("Please add count!")

    def button_generate_rooms(self):
        clean = self.env.ref('hotel_booking.hotel_room_status_clean').id
        vacant = self.env.ref('hotel_booking.hotel_room_stay_status_vacant').id
        for i in range(self.count):
            room_number = self.start + i
            self.env['hotel.room'].create({
                'hotel_id': self.hotel_id.id,
                'company_id': self.company_id.id,
                'name': str(room_number),
                'room_type': self.room_type_id.id,
                'floor_id': self.floor_id.id,
                'state': clean,
                'stay_state': vacant,
            })