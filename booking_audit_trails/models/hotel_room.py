from odoo import fields, models


class HotelRoom(models.Model):
    _inherit = 'hotel.room'

    audit_trail_ids = fields.One2many('audit.trails', 'room_id')

    def write(self, vals):
        if vals.get('state', False) and self.state:
            new_state = self.env['hotel.room.status'].browse(vals['state'])
            self.env['audit.trails'].create({
                'room_id': self.id,
                'user_id': self.env.user.id,
                'operation': 'update_room_state',
                'datetime': fields.Datetime.now(),
                'notes': f'Update Room {self.name} From Status: {self.state.name} To Status: {new_state.name}'
            })
        if vals.get('stay_state', False) and self.stay_state:
            new_state = self.env['hotel.room.stay.status'].browse(vals['stay_state'])
            self.env['audit.trails'].create({
                'room_id': self.id,
                'user_id': self.env.user.id,
                'operation': 'update_room_stay_state',
                'datetime': fields.Datetime.now(),
                'notes': f'Update Room {self.name} From Stay Status: {self.stay_state.name} To Stay Status: {new_state.name}'
            })
        if vals.get('room_type', False):
            new_room_type = self.env['room.type'].browse(vals.get('room_type', False))
            self.env['audit.trails'].create({
                'room_id': self.id,
                'user_id': self.env.user.id,
                'operation': 'update_room_type',
                'datetime': fields.Datetime.now(),
                'notes': f'Update Room Type From {self.room_type.name} To Type: {new_room_type.name}'
            })
        if vals.get('floor_id', False):
            new_floor = self.env['hotel.floor'].browse(vals.get('floor_id', False))
            self.env['audit.trails'].create({
                'room_id': self.id,
                'user_id': self.env.user.id,
                'operation': 'update_room_floor',
                'datetime': fields.Datetime.now(),
                'notes': f'Update Room Floor From {self.floor_id.name} To Type: {new_floor.name}'
            })
        res = super(HotelRoom, self).write(vals)
        return res
