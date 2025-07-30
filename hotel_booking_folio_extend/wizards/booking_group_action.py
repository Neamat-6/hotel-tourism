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

    def button_auto_assign(self):
        logger.info('auto assign from extend')
        start = self.floor_start_sequence
        end = self.floor_end.sequence
        company_id = self.booking_id.company_id.id
        folio_ids = self.folio_ids.filtered(lambda f: not f.room_id)
        folios = [folio.id for folio in folio_ids]

        clean = self.env.ref('hotel_booking.hotel_room_status_clean').id
        vacant = self.env.ref('hotel_booking.hotel_room_stay_status_vacant').id
        # logger.info(f'floor_end {self.floor_end.id}')
        # logger.info(f'Start: {start} -- End: {end}')
        # logger.info(f'Company: {company_id}')
        # logger.info(f'Folios: {folios}')
        assigned_rooms = []
        if not folio_ids:
            raise ValidationError("There is no folios not assigned room")
        first_folio = folio_ids[0]
        current_check_in = first_folio.check_in_date
        current_check_out = first_folio.check_out_date
        current_room_type = first_folio.room_type_id
        current_state = first_folio.state
        available_rooms = first_folio.get_available_rooms()
        # logger.info(f'First Folio: {first_folio}')
        # logger.info(f'available_rooms {available_rooms}')
        # logger.info(f'current_check_in {current_check_in}')
        for i in range(start, end+1):
            # logger.info(f'Sequence: {i}')
            floor = self.env['hotel.floor'].search([('company_id', '=', company_id), ('sequence', '=', i)])
            for folio in folio_ids:
                if folio.id in folios:
                    # logger.info(f'folio {folio}')
                    # if folios shared same checkin, out, room type and state-> no need to call get_available_rooms
                    # we can call it once and exclude assigned rooms
                    if folio.check_in_date != current_check_in or folio.check_out_date != current_check_out or folio.room_type_id != current_room_type or folio.state != current_state:
                        # logger.info('hhhhhhhhhhhhhhhhhhhhh in if condition')
                        current_check_in = folio.check_in_date
                        current_check_out = folio.check_out_date
                        current_room_type = folio.room_type_id
                        current_state = folio.state
                        available_rooms = folio.get_available_rooms()
                        # logger.info(f'available_rooms in if condition {available_rooms}')

                    floor_rooms = floor.room_ids.filtered(
                        lambda r: r.room_type.id == folio.room_type_id.id and r.stay_state.id == vacant and r.id not in assigned_rooms
                    )
                    # logger.info(f'floor_rooms {floor_rooms}')
                    if self.assign_clean_room:
                        floor_rooms = floor_rooms.filtered(lambda r: r.state.id == clean)
                        # logger.info(f'floor_rooms cleaaan {floor_rooms}')
                    intersection = list(set(floor_rooms.ids) & set(available_rooms))
                    # logger.info(f'Intersection: {intersection}')
                    if intersection:
                        old_room_id = folio.room_id
                        new_room_id = self.env['hotel.room'].browse(intersection[0])
                        # old room
                        # logger.info(f'Old Room: {old_room_id}')
                        # logger.info(f'New Room: {new_room_id}')
                        if old_room_id:
                            # logger.info(f'old_room_id.stay_state {old_room_id.stay_state.id}')
                            new_room_id.stay_state = old_room_id.stay_state.id
                        else:
                            if folio.check_in_date == folio.company_id.audit_date:
                                new_room_id.stay_state = self.env.ref('hotel_booking.data_hotel_room_stay_status_arrival').id
                                # logger.info(f'new room arrived {new_room_id}')
                            else:
                                new_room_id.stay_state = self.env.ref('hotel_booking.hotel_room_stay_status_vacant').id
                                # logger.info(f'new room vacant {new_room_id}')
                        # set old room to vacant
                        if old_room_id:
                            # logger.info(f'old room vacant {old_room_id}')
                            old_room_id.stay_state = self.env.ref('hotel_booking.hotel_room_stay_status_vacant').id

                        folio.with_context(ignore_updates=True).write({
                            'room_id': intersection[0]
                        })
                        assigned_rooms.append(intersection[0])
                        folios.remove(folio.id)
                    else:
                        continue
                    if not folios:
                        break
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