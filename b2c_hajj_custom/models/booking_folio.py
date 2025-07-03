from odoo import fields, models, api


class Folio(models.Model):
    _inherit = 'booking.folio'

    # room_gender = fields.Selection(related='room_id.gender', store=True)
    room_gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
    ], string="Gender")

    def unlink(self):
        for record in self:
            if record.room_id:
                if record.room_id.gender:
                    record.room_id.gender = False
        return super(Folio, self).unlink()

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
        print('check_in_date', check_in_date)
        check_in_date = check_in_date if check_in_date else self.check_in_date
        check_out_date = check_out_date if check_out_date else self.check_out_date
        print('check_out_date', check_out_date)
        print('check_in_date', check_in_date)
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
        """, [self.room_type_id.id, check_in_date, check_in_date, check_out_date, check_out_date,
              check_in_date,
              check_out_date])
        out_of_order_vals = self.env.cr.dictfetchall()
        out_of_order_ids = [val['id'] for val in out_of_order_vals]
        if tuple(out_of_order_ids):
            self.env.cr.execute(
                """SELECT id FROM hotel_room WHERE room_type = %s AND id NOT IN %s""",
                [self.room_type_id.id, tuple(out_of_order_ids)])
        else:
            self.env.cr.execute("""SELECT id FROM hotel_room WHERE room_type = %s""",
                                [self.room_type_id.id])
        rooms_vals = self.env.cr.dictfetchall()
        room_ids = [val['id'] for val in rooms_vals]

        print('room_ids', room_ids)
        print('out_of_order_ids',out_of_order_ids)

        if self.booking_id.hotel_id.type in ['arfa', 'minnah']:
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
                print('folio_ids', folio_ids)
                print('folio_vals', folio_vals)
                if folio_ids:
                    folio_objs = self.env['booking.folio'].browse(folio_ids)
                    print('folio_objs', folio_objs)
                    booked_count = sum(folio_objs.mapped('hajj_count'))
                    print('booked_count', booked_count)
                    if booked_count < folio_objs[0].available_beds:
                        available_rooms.append(room_id)
                else:
                    available_rooms.append(room_id)
        else:
            for room_id in room_ids:
                print('room_id', room_id)
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
                print('folio_ids', folio_ids)
                if not folio_ids:
                    available_rooms.append(room_id)
        print('available_rooms', available_rooms)
        return available_rooms


