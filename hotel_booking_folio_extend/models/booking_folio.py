from odoo import fields, models, api
from odoo.exceptions import ValidationError


class BookingFolio(models.Model):
    _inherit = 'booking.folio'


    def get_available_rooms(self, check_in_date=False, check_out_date=False):
        '''
        There are 3 cases of overlapping to consider:
        s1   s2   e1   e2
        (    [----)----]
        s2   s1   e2   e1
        [----(----]    )
        s1   s2   e2   e1
        (    [----]    )
        '''
        available_rooms = []
        check_in_date = check_in_date if check_in_date else self.check_in_date
        check_out_date = check_out_date if check_out_date else self.check_out_date
        self.env.cr.execute("""
            SELECT id
            FROM hotel_room
            WHERE
                (room_type = %s) AND
                (
                    (out_of_order_from <= %s AND out_of_order_to > %s) OR
                    (out_of_order_from <= %s AND out_of_order_to > %s) OR
                    (out_of_order_from <= %s AND out_of_order_to > %s)
                )
        """, [self.room_type_id.id, check_in_date, check_in_date, check_out_date, check_out_date, check_in_date,
              check_out_date])
        out_of_order_vals = self.env.cr.dictfetchall()
        out_of_order_ids = [val['id'] for val in out_of_order_vals]
        if tuple(out_of_order_ids):
            self.env.cr.execute("""SELECT id FROM hotel_room WHERE room_type = %s AND id NOT IN %s""",
                                [self.room_type_id.id, tuple(out_of_order_ids)])
        else:
            self.env.cr.execute("""SELECT id FROM hotel_room WHERE room_type = %s""", [self.room_type_id.id])
        rooms_vals = self.env.cr.dictfetchall()
        room_ids = [val['id'] for val in rooms_vals]
        print('room_ids', room_ids)
        for room_id in room_ids:
            # s1 = check_in_date # s2 = self.check_in_date
            # e1 = check_out_date # e2 = self.check_out_date
            self.env.cr.execute("""
                SELECT id
                FROM booking_folio
                WHERE
                    id != %s
                    AND company_id = %s
                    AND room_id = %s
                    AND state IN ('part_checked_in', 'checked_in', 'confirmed', 'draft')
                    AND (
                        check_in_date < %s
                        AND check_out_date > %s
                    )
            """, [
                self.id,
                self.company_id.id,
                room_id,
                check_out_date,  # existing.check_in < new.check_out
                check_in_date  # existing.check_out > new.check_in
            ])
            folio_vals = self.env.cr.dictfetchall()
            folio_ids = [val['id'] for val in folio_vals]
            if not folio_ids:
                available_rooms.append(room_id)
        print('available_rooms', available_rooms)
        return available_rooms

    def button_manual_assign(self):
        wizard = self.env['booking.group.action'].browse(self.group_action_wizard)
        if wizard:
            rooms = self.get_manual_rooms(wizard)
            return {
                'type': 'ir.actions.act_window',
                'name': "Manual Assign",
                'res_model': 'folio.manual.assign',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_wizard_id': self.group_action_wizard,
                    'default_folio_id': self.id,
                    'default_room_ids': [(6, 0, rooms)],
                }
            }
        else:
            raise ValidationError("please enable manual booking first!")


    def get_manual_rooms(self, wizard):
        start = wizard.floor_start_sequence
        end = wizard.floor_end.sequence
        company_id = wizard.booking_id.company_id.id
        clean = self.env.ref('hotel_booking.hotel_room_status_clean').id
        vacant = self.env.ref('hotel_booking.hotel_room_stay_status_vacant').id
        available_rooms = self.get_available_rooms()
        print('available_rooms', available_rooms)
        manual_rooms = []
        for i in range(start, end+1):
            floor = self.env['hotel.floor'].search([('company_id', '=', company_id), ('sequence', '=', i)])
            floor_rooms = floor.room_ids.filtered(
                lambda r: r.room_type.id == self.room_type_id.id and r.stay_state.id == vacant
            )
            print('floor_rooms', floor_rooms)
            if wizard.assign_clean_room:
                floor_rooms = floor_rooms.filtered(lambda r: r.state.id == clean)
            intersection = list(set(floor_rooms.ids) & set(available_rooms))
            print('intersection', intersection)
            if intersection:
                manual_rooms.extend(intersection)
        return manual_rooms
