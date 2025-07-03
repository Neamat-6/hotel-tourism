from odoo import fields, models, api, _


class HotelRoomUpdate(models.TransientModel):
    _name = 'hotel.room.update'
    _description = 'Hotel Room Update'

    hotel_id = fields.Many2one('hotel.hotel')
    company_id = fields.Many2one('res.company')
    name = fields.Char()
    room_type_ids = fields.Many2many('room.type', domain="[('company_id', '=', company_id)]", string='Room Types')
    floor_ids = fields.Many2many('hotel.floor', domain="[('company_id', '=', company_id)]", string='Floors')
    line_ids = fields.One2many('hotel.room.update.line', 'wizard_id')

    def button_search(self):
        self.line_ids = [(5, 0, 0)]
        domain = [('hotel_id', '=', self.hotel_id.id)]
        if self.name:
            domain.append(('name', 'ilike', self.name))
        if self.room_type_ids:
            domain.append(('room_type', 'in', self.room_type_ids.ids))
        if self.floor_ids:
            domain.append(('floor_id', 'in', self.floor_ids.ids))
        rooms = self.env['hotel.room'].sudo().search(domain)

        for room in rooms:
            self.line_ids = [(0, 0, {
                'room_id': room.id,
                'old_name': room.name,
            })]
        return {
            'name': _('Customer Inquiry'),
            'type': 'ir.actions.act_window',
            'res_model': 'hotel.room.update',
            'view_mode': 'form',
            'target': 'new',
            'res_id': self.id
        }


    def button_update_rooms(self):
        for line in self.line_ids.filtered(lambda l: l.new_name):
            line.room_id.write({
                'name': line.new_name
            })


class HotelRoomUpdateLine(models.TransientModel):
    _name = 'hotel.room.update.line'
    _description = 'Hotel Room Update Line'

    wizard_id = fields.Many2one('hotel.room.update')
    room_id = fields.Many2one('hotel.room')
    old_name = fields.Char(string='OLd Room Number')
    new_name = fields.Char(string='New Room Number')
