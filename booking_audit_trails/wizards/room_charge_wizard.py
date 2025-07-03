from odoo import fields, models, api


class RoomChargeWizard(models.TransientModel):
    _inherit = 'room.charge.wizard'

    def button_add_room_charge(self):
        result = super().button_add_room_charge()
        self.env['audit.trails'].create({
            'booking_id': self.folio_id.booking_id.id,
            'folio_id': self.folio_id.id,
            'user_id': self.env.user.id,
            'operation': 'manual_charge',
            'datetime': fields.Datetime.now(),
            'notes': f'Add {self.room_charge_id.name}'
        })
        return result
