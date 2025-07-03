from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta


class ReceivedRoom(models.TransientModel):
    _name = 'folio.room.type.wizard'
    _description = 'Received Report'

    date_from = fields.Date(required=True)
    date_to = fields.Date(required=True)
    draft = fields.Boolean()
    confirmed_waiting_payment = fields.Boolean(default=True)
    partially_checked_in = fields.Boolean()
    checked_in = fields.Boolean(default=True)
    partially_checked_out = fields.Boolean()
    checked_out = fields.Boolean()
    paid = fields.Boolean()
    canceled = fields.Boolean()
    line_ids = fields.One2many('folio.room.type.wizard.line', 'wizard_id')

    def get_booking_folios(self):
        self.line_ids = [(5, 0, 0)]
        states = []
        if self.draft:
            states.append('draft')
        if self.confirmed_waiting_payment:
            states.append('confirmed')
        if self.partially_checked_in:
            states.append('part_checked_in')
        if self.checked_in:
            states.append('checked_in')
        if self.partially_checked_out:
            states.append('part_checked_out')
        if self.checked_out:
            states.append('checked_out')
        if self.paid:
            states.append('paid')
        if self.canceled:
            states.append('canceled')

        # domain = [('state', 'in', states), ('day', '<=', self.day)]
        room_type_objs = self.env['room.type'].search([])

        for type in room_type_objs:
            folio_lines = self.env['booking.folio.line'].search_count(
                [('state', 'in', states), ('day', '<=', self.date_to), ('folio_id.room_type_id', '=', type.id)])
            if folio_lines:
                self.env['folio.room.type.wizard.line'].create({
                    'wizard_id': self.id,
                    'room_type_id': type.id,
                    'total_rooms': type.room_count,
                    'number_of_reserved': folio_lines,
                    'difference': type.room_count - folio_lines,
                })
        return {
            'type': 'ir.actions.act_window',
            'name': _('Room Type'),
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'folio.room.type.wizard',
            'res_id': self.id,
            'target': 'new'
        }

    def print_pdf(self):
        return self.env.ref('hotel_booking.folio_room_type_wizard_action_report').with_context(
            landscape=True).report_action(self)


class BookingArrivalLine(models.TransientModel):
    _name = 'folio.room.type.wizard.line'

    wizard_id = fields.Many2one('folio.room.type.wizard')

    room_type_id = fields.Many2one('room.type', string='Room Type')
    total_rooms = fields.Integer()
    number_of_reserved = fields.Integer()
    difference = fields.Integer()
