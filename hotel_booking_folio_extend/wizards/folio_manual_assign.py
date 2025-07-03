from odoo import fields, models, api


class FolioManualAssign(models.TransientModel):
    _name = 'folio.manual.assign'
    _description = 'Folio Manual Assign'

    wizard_id = fields.Many2one('booking.group.action')
    folio_id = fields.Many2one('booking.folio')
    room_ids = fields.Many2many('hotel.room')
    room_id = fields.Many2one('hotel.room', domain="[('id', 'in', room_ids)]", required=True)

    def button_assign(self):
        folio = self.folio_id
        old_room_id = folio.room_id
        new_room_id = self.room_id
        # old room
        if old_room_id:
            new_room_id.stay_state = old_room_id.stay_state.id
        else:
            if folio.check_in_date == folio.company_id.audit_date:
                new_room_id.stay_state = self.env.ref('hotel_booking.data_hotel_room_stay_status_arrival').id
            else:
                new_room_id.stay_state = self.env.ref('hotel_booking.hotel_room_stay_status_vacant').id
        # set old room to vacant
        if old_room_id:
            old_room_id.stay_state = self.env.ref('hotel_booking.hotel_room_stay_status_vacant').id

        folio.with_context(ignore_updates=True).write({
            'room_id': self.room_id.id
        })

        return {
            'type': 'ir.actions.act_window',
            'name': "Group Action",
            'res_model': 'booking.group.action',
            'view_mode': 'form',
            'target': 'new',
            'res_id': self.wizard_id.id
        }
