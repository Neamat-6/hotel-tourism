from odoo import fields, models, api, _
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError
import logging
logger = logging.getLogger(__name__)


class BookingGroupAction(models.TransientModel):
    _inherit = 'booking.group.action'

    def button_unassign_rooms(self):
        for folio in self.folio_ids.filtered(lambda f: f.state in ['draft', 'confirmed']):
            folio.room_id.write({
                'stay_state': self.env.ref('hotel_booking.hotel_room_stay_status_vacant').id,
            })
            folio.with_context(ignore_updates=True).write({
                'room_id': False
            })
        return self.button_refresh()

    # manual assign
    @api.onchange('floor_start', 'floor_end')
    def onchange_floor_start_end(self):
        if self.floor_start and self.floor_end:
            for folio in self.folio_ids:
                folio.write({
                    'floor_start': self.floor_start.id,
                    'floor_end': self.floor_end.id
                })