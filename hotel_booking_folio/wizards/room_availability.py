from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from datetime import date


class RoomAvailableWizard(models.TransientModel):
    _name = 'room.available.wizard'
    _description = 'Room Availability with advanced audit date'

    hotel_id = fields.Many2one('hotel.hotel', required=True)
    audit_date = fields.Date(required=True)
    line_ids = fields.One2many('room.available.wizard.line', 'wizard_id', string='Room Availability Lines', readonly=True)


    def action_check_availability(self):
        self.line_ids.unlink()
        # get all rooms related to hotel
        room_ids = self.env['hotel.room'].search([('hotel_id', '=', self.hotel_id.id)])
        print('room_ids', room_ids)
        for room in room_ids:
            # get folio lines within entered audit date
            folio_lines = self.env['booking.folio'].search([
                    ('room_id', '=', room.id),
                    ('check_in_date', '<=', self.audit_date),
                    ('check_out_date', '>=', self.audit_date),
                    ('state', 'in', ['part_checked_in', 'checked_in', 'confirmed'])
                ])
            print('folio_lines', folio_lines)
            assigned_beds = 0
            if folio_lines:
                for folio in folio_lines:
                    # check if assigned beds
                    assigned_beds += len(folio.bed_ids.filtered(lambda b: b.partner_id))
        # Create new lines for each room type
            print('room', assigned_beds)
            self.line_ids.create({
                'wizard_id': self.id,
                'room_type_id': room.room_type.id,
                'total_beds' : room.room_type.max_adults,
                'room_id': room.id,
                'available_beds': room.room_type.max_adults - assigned_beds,
                'assigned_beds': assigned_beds,
            })
        return {
            'type': 'ir.actions.act_window',
            'name': _('Room Availability'),
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'room.available.wizard',
            'res_id': self.id,
            'target': 'new'
        }

    def action_generate_pdf(self):
        return self.env.ref('hotel_booking_folio.action_room_availability_report').with_context(
            landscape=True).report_action(self)

    def action_generate_xls(self):
        return self.env.ref('hotel_booking_folio.action_room_availability_report_excel').report_action(self)


class RoomAvailableWizardLine(models.TransientModel):
    _name = 'room.available.wizard.line'
    _description = 'Room Availability Wizard Line'

    wizard_id = fields.Many2one('room.available.wizard', string='Wizard Reference')
    room_id = fields.Many2one('hotel.room', string='Room')
    room_type_id = fields.Many2one('room.type', string='Room Type')
    total_beds = fields.Integer(string='Total Beds')
    available_beds = fields.Integer(string='Available Beds')
    assigned_beds = fields.Integer(string='Assigned Beds')
