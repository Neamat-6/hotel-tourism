from odoo import fields, models, api


class RoomStatus(models.Model):
    _name = 'hotel.room.status'
    _description = 'Room Status'

    name = fields.Char(string='Room Status')
    is_default = fields.Boolean()
    color = fields.Char()
    state = fields.Selection(selection=[
        ('dirty', 'dirty'), ('clean', 'clean'),
    ])

    @api.onchange('is_default')
    def onchange_is_default(self):
        if self.is_default:
            default_state = self.env['hotel.room.status'].search([('is_default', '=', True)])
            if default_state:
                default_state.update({'is_default': False})


class RoomStayStatus(models.Model):
    _name = 'hotel.room.stay.status'
    _description = 'Room Stay Over Status'

    name = fields.Char(string='Room Status')
    is_default = fields.Boolean()
    color = fields.Char()

    @api.onchange('is_default')
    def onchange_is_default(self):
        if self.is_default:
            default_state = self.env['hotel.room.stay.status'].search([('is_default', '=', True)])
            if default_state:
                default_state.update({'is_default': False})