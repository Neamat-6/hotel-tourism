import math

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
import logging
from collections import defaultdict
logger = logging.getLogger(__name__)

class HotelBooking(models.Model):
    _inherit = 'hotel.booking'

    package_id = fields.Many2one('booking.package')
    package_assign_type = fields.Selection(selection=[
        ('gender', 'Gender'), ('family_member', 'Family Member'),
    ])
    room_summary_ids = fields.One2many(
        'guest.room.summary', 'booking_id',
        string='Room Summaries',
        compute='_compute_room_summary',
        store=True
    )
    guest_count = fields.Integer(string="Guests", compute="_compute_guest_count")

    @api.depends('guest_ids')
    def _compute_guest_count(self):
        for record in self:
            record.guest_count = len(record.guest_ids)

    @api.depends('guest_ids', 'guest_ids.room_id', 'guest_ids.booked_room_type', 'guest_ids.pilgrim_type')
    def _compute_room_summary(self):
        for rec in self:
            rec.room_summary_ids = [(5, 0, 0)]
            if rec.hotel_id.type not in ['arfa', 'minnah']:
                if rec.guest_ids.filtered(lambda g: g.room_id):
                    room_data = defaultdict(lambda: {
                        'count': 0,
                        'booked_room_type': None,
                        'has_member': False
                    })
                    for line in rec.guest_ids.filtered(lambda g: g.room_id):
                        room = line.room_id
                        booked_type = line.booked_room_type
                        room_data[room]['count'] += 1
                        room_data[room]['booked_room_type'] = booked_type
                        if line.pilgrim_type == 'member':
                            room_data[room]['has_member'] = True  # لو في أي عضو في الغرفة

                    summary_lines = []
                    for room, data in room_data.items():
                        booked_num = int(data['booked_room_type']) if data[
                            'booked_room_type'].isdigit() else 0
                        unassigned = booked_num - data['count']
                        pilgrim_type_final = 'member' if data['has_member'] else 'main'

                        summary_lines.append((0, 0, {
                            'room_id': room.id,
                            'booked_room_type': data['booked_room_type'],
                            'assigned_beds': data['count'],
                            'unassigned_beds': unassigned,
                            'room_type': pilgrim_type_final,

                        }))
                    if summary_lines:
                        rec.room_summary_ids = summary_lines
            else:
                if rec.guest_ids.filtered(lambda g: g.room_id):
                    room_data = defaultdict(lambda: {
                        'count': 0,
                        'booked_room_gender': None,
                        'hajj_count': 0
                    })
                    for line in rec.guest_ids.filtered(lambda g: g.room_id):
                        room = line.room_id
                        booked_gender = line.folio_id.room_gender
                        hajj_count = line.folio_id.hajj_count
                        room_data[room]['count'] += 1
                        room_data[room]['booked_room_gender'] = booked_gender
                        room_data[room]['hajj_count'] = hajj_count
                    summary_lines = []
                    for room, data in room_data.items():
                        unassigned = data['hajj_count'] - data['count']

                        summary_lines.append((0, 0, {
                            'room_id': room.id,
                            'booked_beds': data['hajj_count'],
                            'assigned_beds': data['count'],
                            'unassigned_beds': unassigned,
                            'room_gender': data['booked_room_gender'],
                        }))
                    if summary_lines:
                        rec.room_summary_ids = summary_lines


    def action_reset_guest_assign(self):
        for rec in self:
            for line in rec.guest_ids:
                line.write({'folio_id': False})
            for folio in rec.folio_ids:
                folio.write({'room_gender': False})
                for bed in folio.bed_ids:
                    bed.write({'partner_id':False})

    def button_assign_guests(self):
        # if not self.package_assign_type:
        #     raise ValidationError("PLease add Assign Type!")
        if self.folio_ids.filtered(lambda f: not f.room_id):
            raise ValidationError("PLease add rooms for all folios!")
        total_beds = len(self.folio_ids.mapped('bed_ids'))
        if len(self.guest_ids) > total_beds:
            raise ValidationError(f"Guests are more than total beds {total_beds}")

        missed_gender = self.guest_ids.filtered(lambda g: not g.gender)
        if missed_gender:
            return {
                'name': 'Missed Pilgrim Data',
                'type': 'ir.actions.act_window',
                'res_model': 'assign.guest.wizard',
                'view_mode': 'form',
                'target': 'new',  # 'new' means popup window (modal)
                'context': {
                    'default_info_type': 'gender',
                    'default_line_ids': [(0, 0, {'partner_id': guest.partner_id.id}) for guest in
                                         missed_gender]
                }
            }
        missed_type = self.guest_ids.filtered(lambda g: not g.pilgrim_type)
        if missed_type:
            return {
                'name': 'Missed Pilgrim Data',
                'type': 'ir.actions.act_window',
                'res_model': 'assign.guest.wizard',
                'view_mode': 'form',
                'target': 'new',  # 'new' means popup window (modal)
                'context': {
                    'default_info_type': 'pilgrim_type',
                    'default_line_ids': [(0, 0, {'partner_id': guest.partner_id.id}) for guest in
                                         missed_type]
                }
            }

        missed_member = self.guest_ids.filtered(
            lambda g: g.pilgrim_type == 'member' and not g.main_member_id)
        if missed_member:
            return {
                'name': 'Missed Pilgrim Data',
                'type': 'ir.actions.act_window',
                'res_model': 'assign.guest.wizard',
                'view_mode': 'form',
                'target': 'new',  # 'new' means popup window (modal)
                'context': {
                    'default_info_type': 'member',
                    'default_line_ids': [(0, 0, {'partner_id': guest.partner_id.id}) for guest in
                                         missed_member]
                }
            }
        # need to know if i has main and member for his but not all which mean i have main with room type 3 and has only one member
        main_with_members = self.guest_ids.filtered(
            lambda g: g.pilgrim_type == 'member' and g.main_member_id).mapped('main_member_id')
        if main_with_members:
            main_with_members = list(set(main_with_members))
            logger.info(f'main_with_members {main_with_members}')
            wrong_members = []
            for main in main_with_members:
                logger.info(f'main {main} -- makkah_room_type {main.makkah_room_type}')
                if main.makkah_room_type:
                    logger.info(f'makkah_room_type {main.makkah_room_type}')
                    makkah_room_type = int(main.makkah_room_type)
                    members_count = self.guest_ids.filtered(lambda g: g.pilgrim_type == 'member' and g.main_member_id.id == main.id)
                    # if len(members_count) < (makkah_room_type -1):
                    #     raise ValidationError(_("Please add all members for main member %s") % (main.name))
                    if len(members_count) > (makkah_room_type -1):
                        wrong_members.append(main.name)
                    if wrong_members:
                        raise ValidationError(_("Please adjust members for those main members %s") % wrong_members)

        if self.hotel_id.type in ['arfa', 'minnah']:
            self.assign_guests_by_campaign()
        else:
            self.assign_guests_by_family()


    def assign_guests_by_campaign(self):
        new_female_guests = self.guest_ids.filtered(lambda g: g.gender == 'female' and not g.folio_id)
        new_male_guests = self.guest_ids.filtered(lambda g: g.gender == 'male' and not g.folio_id)
        total_female_guests = self.guest_ids.filtered(lambda g: g.gender == 'female')
        total_male_guests = self.guest_ids.filtered(lambda g: g.gender == 'male')
        folio_male = self.folio_ids.filtered(lambda f: f.room_type_id.gender == 'male')
        folio_female = self.folio_ids.filtered(lambda f: f.room_type_id.gender == 'female')
        # hajj_count_male = sum(folio_male.mapped('hajj_count'))
        # hajj_count_female = sum(folio_female.mapped('hajj_count'))

        if folio_female and new_female_guests:
            if folio_female.hajj_count < len(total_female_guests):
                raise ValidationError(_('Female Guests is more than booking female beds'))
            if not folio_female.room_gender:
                folio_female.room_gender = 'female'

            female_partners = new_female_guests.mapped('partner_id').mapped('id')
            female_beds = folio_female.bed_ids.filtered(lambda b: not b.partner_id)
            logger.info(f'assign_guests_by_campaign female_partners {female_partners}')
            logger.info(f'assign_guests_by_campaign female_beds {female_beds}')
            try:
                for index, value in enumerate(female_partners):
                    female_beds[index].write({'partner_id': value})
            except Exception as e:
                raise ValidationError('Not Available Bed for female guest')

        if folio_male and new_male_guests:
            if folio_male.hajj_count < len(new_male_guests):
                raise ValidationError(_('Male Guests is more than booking male beds'))
            if not folio_male.room_gender:
                folio_male.room_gender = 'male'

            male_partners = new_male_guests.mapped('partner_id').mapped('id')
            male_beds = folio_male.bed_ids.filtered(lambda b: not b.partner_id)
            logger.info(f'assign_guests_by_campaign male_partners {male_partners}')
            logger.info(f'assign_guests_by_campaign male_beds {male_beds}')
            try:
                for index, value in enumerate(male_partners):
                    male_beds[index].write({'partner_id': value})
            except Exception as e:
                raise ValidationError('Not Available Bed for male guest')



    def assign_guests_by_gender(self):
        group_counts = defaultdict(int)
        for guest in self.guest_ids:
            if guest.partner_id.group_no:
                group_counts[guest.partner_id.group_no] += 1
        female_guests = self.guest_ids.filtered(lambda g: g.gender == 'female' and not g.folio_id)
        female_guests = female_guests.sorted(
            key=lambda g: (
                -group_counts.get(g.partner_id.group_no or '', 0),  # Sort by group size descending
                not g.partner_id.group_no,  # Put guests with no group_no at the end
                g.partner_id.group_no or ''  # Sort by group_no
            )
        )
        male_guests = self.guest_ids.filtered(lambda g: g.gender == 'male' and not g.folio_id)
        male_guests = male_guests.sorted(
            key=lambda g: (
                -group_counts.get(g.partner_id.group_no or '', 0),  # Sort by group size descending
                not g.partner_id.group_no,  # Put guests with no group_no at the end
                g.partner_id.group_no or ''  # Sort by group_no
            )
        )
        print('female_guests', female_guests)
        print('male_guests', male_guests)
        print('female_guests groups', female_guests.mapped('partner_id').mapped('group_no'))
        print('male_guests groups', male_guests.mapped('partner_id').mapped('group_no'))
        main_members = list(set(self.guest_ids.filtered(lambda g: g.main_member_id).mapped('main_member_id')))
        total_female_guests = self.guest_ids.filtered(lambda g: g.gender == 'female' and not g.main_member_id and g.partner_id not in main_members)
        total_male_guests = self.guest_ids.filtered(lambda g: g.gender == 'male' and not g.main_member_id and g.partner_id not in main_members)
        print('male_guests', male_guests)
        double_female_guests = female_guests.filtered(lambda g: g.booked_room_type == '2')
        double_male_guests = male_guests.filtered(lambda g: g.booked_room_type == '2')
        print('double_male_guests', double_male_guests)
        total_double_male_guests = total_male_guests.filtered(lambda g: g.booked_room_type == '2')
        total_double_female_guests = total_female_guests.filtered(lambda g: g.booked_room_type == '2')
        booked_female_double_rooms = math.ceil(len(double_female_guests) / 2)
        booked_male_double_rooms = math.ceil(len(double_male_guests) / 2)
        total_booked_female_double_rooms = math.ceil(len(total_double_female_guests) / 2)
        total_booked_male_double_rooms = math.ceil(len(total_double_male_guests) / 2)

        booked_double_rooms = booked_female_double_rooms + booked_male_double_rooms
        # total_booked_double_rooms = math.ceil(len(total_double_female_guests) / 2) + math.ceil(len(total_double_male_guests) / 2)
        booking_double_rooms = self.folio_ids.filtered(lambda f: f.room_type_id.mini_adults == 2 and not f.is_family)

        triple_female_guests = female_guests.filtered(lambda g: g.booked_room_type == '3')
        triple_male_guests = male_guests.filtered(lambda g: g.booked_room_type == '3')
        print('triple_female_guests',triple_female_guests)
        print('triple_male_guests',triple_male_guests)
        total_triple_male_guests = total_male_guests.filtered(lambda g: g.booked_room_type == '3')
        total_triple_female_guests = total_female_guests.filtered(lambda g: g.booked_room_type == '3')
        booked_female_triple_rooms = math.ceil(len(triple_female_guests) / 3)
        booked_male_triple_rooms = math.ceil(len(triple_male_guests) / 3)
        print('booked_female_triple_rooms', booked_female_triple_rooms)
        print('booked_male_triple_rooms', booked_male_triple_rooms)
        total_booked_male_triple_rooms = math.ceil(len(total_triple_male_guests) / 3)
        total_booked_female_triple_rooms = math.ceil(len(total_triple_female_guests) / 3)
        booked_triple_rooms = booked_female_triple_rooms + booked_male_triple_rooms
        # total_booked_triple_rooms = math.ceil(len(total_triple_female_guests) / 3) + math.ceil(len(total_triple_male_guests) / 3)
        booking_triple_rooms = self.folio_ids.filtered(lambda f: f.room_type_id.mini_adults == 3 and not f.is_family)

        quad_female_guests = female_guests.filtered(lambda g: g.booked_room_type == '4')
        quad_male_guests = male_guests.filtered(lambda g: g.booked_room_type == '4')
        total_quad_male_guests = total_male_guests.filtered(lambda g: g.booked_room_type == '4')
        total_quad_female_guests = total_female_guests.filtered(lambda g: g.booked_room_type == '4')
        booked_female_quad_rooms = math.ceil(len(quad_female_guests) / 4)
        booked_male_quad_rooms = math.ceil(len(quad_male_guests) / 4)
        total_booked_male_quad_rooms = math.ceil(len(total_quad_male_guests) / 4)
        total_booked_female_quad_rooms = math.ceil(len(total_quad_female_guests) / 4)
        booked_quad_rooms = booked_female_quad_rooms + booked_male_quad_rooms
        # total_booked_quad_rooms = math.ceil(len(total_quad_female_guests) / 4) + math.ceil(len(total_quad_male_guests) / 4)
        booking_quad_rooms = self.folio_ids.filtered(lambda f: f.room_type_id.mini_adults == 4 and not f.is_family)
        print('booked_double_rooms',booked_double_rooms)
        print('booking_double_rooms',booking_double_rooms)
        if booked_double_rooms and booking_double_rooms:
            logger.info(f'booked_double_rooms {booked_double_rooms}')
            logger.info(f'booking_double_rooms {booking_double_rooms}' )
            double_female_partners = double_female_guests.mapped('partner_id')
            double_male_partners = double_male_guests.mapped('partner_id')
            print('double_male_partners', double_male_partners)
            first_assign = booking_double_rooms.filtered(lambda f: not f.bed_ids.mapped('partner_id'))
            if first_assign:
                logger.info(f'first assign double {first_assign}')
                booking_double_rooms_list = list(booking_double_rooms.filtered(lambda f: not f.room_gender))
                already_female_rooms = list(booking_double_rooms.filtered(lambda f: f.room_gender == 'female'))  # Already female
                already_male_rooms = list(booking_double_rooms.filtered(lambda f: f.room_gender == 'male'))  # Already male

                logger.info(f'Unassigned rooms: {booking_double_rooms_list}')
                logger.info(f'Already female rooms: {len(already_female_rooms)}')
                logger.info(f'Already male rooms: {len(already_male_rooms)}')

                # Calculate how many more rooms need to be assigned to each gender
                remaining_female_needed = max(0, total_booked_female_double_rooms - len(already_female_rooms))
                remaining_male_needed = max(0,total_booked_male_double_rooms - len(already_male_rooms))
                logger.info(f'remaining_female_needed: {remaining_female_needed}')
                logger.info(f'remaining_male_needed: {remaining_male_needed}')
                # Assign remaining female rooms first
                for _ in range(remaining_female_needed):
                    if booking_double_rooms_list:
                        booking_double_rooms_list[0].room_gender = 'female'
                        booking_double_rooms_list.remove(booking_double_rooms_list[0])

                # Assign remaining male rooms
                for _ in range(remaining_male_needed):
                    if booking_double_rooms_list:
                        booking_double_rooms_list[0].room_gender = 'male'
                        booking_double_rooms_list.remove(booking_double_rooms_list[0])

            female_folios = booking_double_rooms.filtered(lambda f: f.room_gender == 'female')
            male_folios = booking_double_rooms.filtered(lambda f: f.room_gender == 'male')
            female_beds = female_folios.bed_ids.filtered(lambda b: not b.partner_id)
            male_beds = male_folios.bed_ids.filtered(lambda b: not b.partner_id)
            logger.info(f'female_folios {female_folios}')
            logger.info(f'male_folios {male_folios}')
            logger.info(f'female_beds {female_beds}')
            logger.info(f'male_beds {male_beds}')
            # try:
            #     for index, value in enumerate(double_female_partners):
            #         female_beds[index].write({'partner_id': value})
            # except Exception as e:
            #     raise ValidationError('Not Available Bed for double female guest')
            self.assign_beds_by_gender(double_female_partners, female_beds, 'double female')
            self.assign_beds_by_gender(double_male_partners, male_beds, 'double male')

            # try:
            #     for index, value in enumerate(double_male_partners):
            #         male_beds[index].write({'partner_id': value})
            # except Exception as e:
            #     raise ValidationError('Not Available Bed for double male guest')


        if booked_triple_rooms and booking_triple_rooms:
            logger.info(f'booked_triple_rooms {booked_triple_rooms}')
            logger.info(f'booking_triple_rooms {booking_triple_rooms}')
            triple_female_partners = triple_female_guests.mapped('partner_id')
            triple_male_partners = triple_male_guests.mapped('partner_id')
            first_assign = booking_triple_rooms.filtered(lambda f: not f.bed_ids.mapped('partner_id'))
            logger.info(f'first_assign {first_assign}')
            logger.info(f'triple_male_partners {triple_male_partners}')
            logger.info(f'triple_female_partners {triple_female_partners}')
            if first_assign:
                booking_triple_rooms_list = list(booking_triple_rooms.filtered(lambda f: not f.room_gender))
                logger.info(f'booked_male_triple_rooms {booked_male_triple_rooms}' )
                logger.info(f'booked_female_triple_rooms {booked_female_triple_rooms}')
                already_female_rooms = list(booking_triple_rooms.filtered(lambda f: f.room_gender == 'female'))  # Already female
                already_male_rooms = list(booking_triple_rooms.filtered(lambda f: f.room_gender == 'male'))  # Already male

                logger.info(f'Unassigned rooms: {booking_triple_rooms_list}')
                logger.info(f'Already female rooms: {len(already_female_rooms)}')
                logger.info(f'Already male rooms: {len(already_male_rooms)}')

                # Calculate how many more rooms need to be assigned to each gender
                remaining_female_needed = max(0, total_booked_female_triple_rooms - len(already_female_rooms))
                remaining_male_needed = max(0,total_booked_male_triple_rooms - len(already_male_rooms))

                # Assign remaining female rooms first
                for _ in range(remaining_female_needed):
                    if booking_triple_rooms_list:
                        booking_triple_rooms_list[0].room_gender = 'female'
                        booking_triple_rooms_list.remove(booking_triple_rooms_list[0])

                # Assign remaining male rooms
                for _ in range(remaining_male_needed):
                    if booking_triple_rooms_list:
                        booking_triple_rooms_list[0].room_gender = 'male'
                        booking_triple_rooms_list.remove(booking_triple_rooms_list[0])

            logger.info(f'booking_triple_rooms {booking_triple_rooms}')
            female_folios = booking_triple_rooms.filtered(lambda f: f.room_gender == 'female')
            male_folios = booking_triple_rooms.filtered(lambda f: f.room_gender == 'male')
            logger.info(f'female_folios {female_folios}')
            logger.info(f'male_folios {male_folios}')
            female_beds = female_folios.bed_ids
            male_beds = male_folios.bed_ids
            logger.info(f'female_beds {female_beds}')
            logger.info(f'male_beds {male_beds}')
            self.assign_beds_by_gender(triple_female_partners, female_beds, 'triple female')
            self.assign_beds_by_gender(triple_male_partners, male_beds, 'triple male')

            # try:
            #     for index, value in enumerate(triple_female_partners):
            #         female_beds[index].write({'partner_id': value})
            # except Exception as e:
            #     raise ValidationError('Not Available Bed for triple female guest')
            # try:
            #     for index, value in enumerate(triple_male_partners):
            #         male_beds[index].write({'partner_id': value})
            # except Exception as e:
            #     raise ValidationError('Not Available Bed for triple male guest')

        if booked_quad_rooms and booking_quad_rooms:
            quad_female_partners = quad_female_guests.mapped('partner_id')
            quad_male_partners = quad_male_guests.mapped('partner_id')
            first_assign = booking_quad_rooms.filtered(lambda f: not f.bed_ids.mapped('partner_id'))
            if first_assign:
                booking_quad_rooms_list = list(booking_quad_rooms.filtered(lambda f: not f.room_gender))
                logger.info(f'booked_female_quad_rooms {booked_female_quad_rooms}' )
                logger.info(f'booked_male_quad_rooms {booked_male_quad_rooms}')
                already_female_rooms = list(booking_quad_rooms.filtered(lambda f: f.room_gender == 'female'))  # Already female
                already_male_rooms = list(booking_quad_rooms.filtered(lambda f: f.room_gender == 'male'))  # Already male

                logger.info(f'Unassigned rooms: {booking_quad_rooms_list}')
                logger.info(f'Already female rooms: {len(already_female_rooms)}')
                logger.info(f'Already male rooms: {len(already_male_rooms)}')

                # Calculate how many more rooms need to be assigned to each gender
                remaining_female_needed = max(0, total_booked_female_quad_rooms - len(already_female_rooms))
                remaining_male_needed = max(0,total_booked_male_quad_rooms - len(already_male_rooms))

                # Assign remaining female rooms first
                logger.info(f'remaining_female_needed {remaining_female_needed}')
                logger.info(f'remaining_male_needed {remaining_male_needed}')
                for _ in range(remaining_female_needed):
                    if booking_quad_rooms_list:
                        booking_quad_rooms_list[0].write({'room_gender': 'female'})
                        logger.info(f'write {booking_quad_rooms_list[0]}')
                        booking_quad_rooms_list.remove(booking_quad_rooms_list[0])

                # Assign remaining male rooms
                logger.info(f'booking_quad_rooms_list {booking_quad_rooms_list}')
                logger.info(f'remaining_male_needed {remaining_male_needed}')
                for _ in range(remaining_male_needed):
                    if booking_quad_rooms_list:
                        # booking_quad_rooms_list[0].room_gender = 'male'
                        booking_quad_rooms_list[0].write({'room_gender': 'male'})
                        booking_quad_rooms_list.remove(booking_quad_rooms_list[0])

            female_folios = booking_quad_rooms.filtered(lambda f: f.room_gender == 'female')
            male_folios = booking_quad_rooms.filtered(lambda f: f.room_gender == 'male')
            female_beds = female_folios.bed_ids
            male_beds = male_folios.bed_ids
            logger.info(f'female_beds {female_beds}')
            logger.info(f'male_beds {male_beds}')
            logger.info(f'quad_female_partners {quad_female_partners}')
            logger.info(f'quad_male_partners {quad_male_partners}')
            logger.info(f'quad_female_partnersgroups  {quad_female_partners.mapped("group_no")}')
            logger.info(f'quad_male_partnersgroups {quad_male_partners.mapped("group_no")}')
            self.assign_beds_by_gender(quad_female_partners, female_beds, 'quad female')
            self.assign_beds_by_gender(quad_male_partners, male_beds, 'quad male')
            # try:
            #     for index, value in enumerate(quad_female_partners):
            #         female_beds[index].write({'partner_id': value})
            # except Exception as e:
            #     raise ValidationError('Not Available Bed for quad female guest')
            # try:
            #     for index, value in enumerate(quad_male_partners):
            #         male_beds[index].write({'partner_id': value})
            # except Exception as e:
            #     raise ValidationError('Not Available Bed for quad male guest')


    def assign_beds_by_gender(self, partners, beds, message):
        try:
            for partner_id in partners:
                assigned = False
                group_no = partner_id.group_no

                # المرحلة الأولى: نحاول نسكنه في غرفة فيها نفس الجروب أو فاضية بالكامل
                for bed in beds:
                    if bed.partner_id:
                        continue  # السرير مش فاضي

                    # كل السراير في الغرفة
                    room_beds = bed.folio_id.bed_ids

                    # المجموعات المسكنة حاليًا في الغرفة
                    existing_groups = set(b.partner_id.group_no for b in room_beds if b.partner_id)

                    # لو الغرفة فاضية أو فيها نفس الجروب فقط
                    if not existing_groups or (
                            len(existing_groups) == 1 and group_no in existing_groups):
                        bed.write({'partner_id': partner_id.id})
                        assigned = True
                        break

                # المرحلة الثانية: نسكنه في أي سرير فاضي (مع جروب تاني) بشرط يكون آخر شخص من مجموعته
                if not assigned:
                    for bed in beds:
                        if not bed.partner_id:
                            bed.write({'partner_id': partner_id.id})
                            assigned = True
                            break

                if not assigned:
                    raise ValidationError(
                        'Not Available Bed for %s guest: %s' % (message, partner_id.name))

        except Exception as e:
            raise ValidationError('Error assigning beds for %s guests: %s' % (message, str(e)))

    def assign_guests_by_family(self):
        # todo handle singles
        families = self.guest_ids.filtered(lambda g: g.pilgrim_type == 'main')  # family represented by main member
        members = self.guest_ids.filtered(lambda g: g.pilgrim_type == 'member')
        if not members:
            return self.assign_guests_by_gender()
        unassigned = []
        family_2 = []
        family_3 = []
        family_4 = []
        logger.info(f'families {families}')
        logger.info(f'members {members}')
        double_folios = list(self.folio_ids.filtered(lambda f: f.room_type_id.mini_adults == 2).mapped('id'))
        double_folios_count = len(double_folios)
        triple_folios = list(self.folio_ids.filtered(lambda f: f.room_type_id.mini_adults == 3).mapped('id'))
        triple_folios_count = len(triple_folios)
        quad_folios = list(self.folio_ids.filtered(lambda f: f.room_type_id.mini_adults == 4).mapped('id'))
        quad_folios_count = len(quad_folios)
        pool = [2] * double_folios_count + [3] * triple_folios_count + [4] * quad_folios_count
        logger.info(f'pool {pool}' )
        logger.info(f'triple_folios {triple_folios}' )
        logger.info(f'quad_folios {quad_folios}' )
        for family in families:
            family_members = members.filtered(lambda m: m.main_member_id.id == family.partner_id.id)
            if family.booked_room_type and family_members:
                if family.booked_room_type == '2':
                    family_2.append(family)
                elif family.booked_room_type == '3':
                    family_3.append(family)
                elif family.booked_room_type == '4':
                    family_4.append(family)
            else:
                unassigned.append(family)
        logger.info(f'family_2 {family_2}')
        logger.info(f'family_3 {family_3}')
        logger.info(f'family_4 {family_4}')
        logger.info(f'unassigned {unassigned}')
        # assign 2, 3, 4 family members first
        for family in family_2:
            if 2 in pool:
                folio = self.env['booking.folio'].browse(double_folios[0])
                logger.info(f'folio {folio}')
                logger.info(f'family {family}')
                self.assign_beds_by_family(family, folio)
                double_folios.remove(folio.id)
                pool.remove(2)
            else:
                raise ValidationError(f"Can't assign double room for {family.guest_name} family")
        logger.info(f'pool {pool}')
        logger.info(f'double_folios {double_folios}')
        print('familyyyy tripple', len(family_3))
        for family in family_3:
            if 3 in pool:
                folio = self.env['booking.folio'].browse(triple_folios[0])
                self.assign_beds_by_family(family, folio)
                triple_folios.remove(folio.id)
                pool.remove(3)
            else:
                raise ValidationError(f"Can't assign triple room for {family.guest_name} family")
        for family in family_4:
            if 4 in pool:
                folio = self.env['booking.folio'].browse(quad_folios[0])
                self.assign_beds_by_family(family, folio)
                quad_folios.remove(folio.id)
                pool.remove(4)
            elif 2 in pool:
                if pool.count(2) >= 2:
                    for i in range(2):
                        folio = self.env['booking.folio'].browse(quad_folios[i])
                        self.assign_beds_by_family(family, folio)
                        quad_folios.remove(folio.id)
                        pool.remove(2)
            else:
                raise ValidationError(f"Can't assign quad/2 double room for {family.guest_name} family")
        if unassigned:
            logger.info(f'here unassigned {unassigned}')
            self.assign_guests_by_gender()

    def get_family_partners(self, main_member):
        family_members = self.guest_ids.filtered(lambda m: m.main_member_id.id == main_member.partner_id.id)
        family_partners = list(family_members.mapped('partner_id').mapped('id'))
        return family_partners

    def assign_beds_by_family(self, family, folio):
        family_partners = self.get_family_partners(family)
        logger.info(f'family_partners {folio}')
        family_partners.append(family.partner_id.id)
        logger.info(f'family_partnerssss {family_partners}')
        beds = folio.bed_ids
        logger.info(f'beds {beds}')
        folio.write({'is_family': True})
        for index, value in enumerate(family_partners):
            if index < len(beds):
                beds[index].write({'partner_id': value})

    @api.constrains('package_id')
    @api.onchange('package_id')
    def onchange_package_id(self):
        self.guest_ids = [(6, 0, [])]
        partners = self.package_id.partner_ids
        hotel_type = self.hotel_id.type
        if not partners:
            return
        self.guest_list = True
        grouped = {}

        # Step 1: Group all 'main' pilgrims
        mains = partners.filtered(lambda p: p.pilgrim_type == 'main')
        for main in mains:
            grouped[main.id] = [main]
            # Step 2: Find and add members linked to this main
            members = partners.filtered(
                lambda m: m.pilgrim_type == 'member' and m.main_member_id.id == main.id)
            grouped[main.id].extend(members)

        # Step 3: Identify any ungrouped partners (orphans)
        grouped_ids = {p.id for group in grouped.values() for p in group}
        ungrouped = partners.filtered(lambda p: p.id not in grouped_ids)

        # Step 4: Combine all into a single ordered list
        sorted_partners = [p for group in grouped.values() for p in group] + list(ungrouped)

        # Step 5: Create guest_ids with guest_role
        self.guest_ids = [(0, 0, {
            'guest_name': partner.name,
                'booking_id': self.id,
                'guest_email': partner.email,
                'guest_mobile': partner.mobile,
                'partner_id': partner.id,
                'guest_address': partner.street,
                'guest_country_id': partner.country_id.id,
                'guest_state_id': partner.state_id.id,
                'guest_city': partner.city,
                'guest_zip_code': partner.zip,
                'nationality_id': partner.nationality_id.id,
                'region': partner.region,
                'language': partner.language.id,
                'relationship': partner.relationship,
                'gender': partner.gender,
                'pilgrim_type': partner.pilgrim_type,
                'main_member_id': partner.main_member_id.id,
                'booked_room_type': getattr(partner, f'{hotel_type}_room_type', None),
        }) for partner in sorted_partners]

    def action_open_guests(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Guests',
            'view_mode': 'tree',
            'res_model': 'booking.guest',
            'domain': [('booking_id', '=', self.id)],
            'context': {
                'default_booking_id': self.id,
                'create': False,  # Disables the create button
            },
            'target': 'current',
        }

class HotelBookingLine(models.Model):
    _inherit = 'hotel.booking.line'

    hajj_count = fields.Integer()


class HotelBookingFolio(models.Model):
    _inherit = 'booking.folio'

    hajj_count = fields.Integer(related='booking_line_id.hajj_count')
    is_family = fields.Boolean()


class BookingGuest(models.Model):
    _inherit = 'booking.guest'
    _order = 'id, main_member_id'
    _rec_name = 'guest_name'

    package_id = fields.Many2one('booking.package', related='booking_id.package_id', store=True)
    partner_id = fields.Many2one('res.partner')
    # tour_guide_id = fields.Many2one('res.partner', related='partner_id.tour_guide_id', store=True)
    nationality_id = fields.Many2one('res.country', readonly=False)
    region = fields.Selection(selection=[('sunni', 'Sunni'), ('shiite', 'Shiite'), ], readonly=False)
    language = fields.Many2one('res.lang', readonly=False)
    relationship = fields.Selection([
        ('father', 'Father'), ('mother', 'Mother'),
        ('son', 'Son'), ('daughter', 'Daughter'),
        ('husband', 'Husband'), ('wife', 'Wife'),
    ])
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')],readonly=False)
    folio_id = fields.Many2one('booking.folio')
    room_id = fields.Many2one('hotel.room', related='folio_id.room_id', store=True)
    room_type_id = fields.Many2one('room.type', related='room_id.room_type', store=True, string='Room Type')
    booked_room_type = fields.Selection(selection=[('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5')])
    pilgrim_type = fields.Selection(selection=[('main', 'Main'), ('member', 'Family Member')], readonly=False)
    allowed_member_ids = fields.Many2many('res.partner')
    partner_ids = fields.Many2many('res.partner', 'rel_guest_partner',
                                   'guest_id', 'partner_id', domain="[('id', 'in', allowed_member_ids)]",
                                   string="Family Members")
    main_member_id = fields.Many2one('res.partner', readonly=False)



    def button_switch_bed(self):
        guests = self.booking_id.guest_ids.filtered(
            lambda g: g.booked_room_type == self.booked_room_type and g.gender == self.gender and g.id != self.id
        )
        rooms = guests.mapped('room_id')
        return {
            'name': 'Switch Bed',
            'view_mode': 'form',
            'res_model': 'folio.switch.bed',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'target': 'new',
            'context': {
                'default_guest1': self.id,
                'default_allowed_guest_ids': [(6, 0, guests.ids)],
                'default_allowed_room_ids': [(6, 0, rooms.ids)]
            },
        }

    def button_display_guest(self):
        if self.booking_id.package_assign_type == 'family_member' and self.pilgrim_type == 'main':
            member_guests = self.booking_id.guest_ids.filtered(
                lambda
                    g: g.pilgrim_type == 'member' and g.booked_room_type == self.booked_room_type and not g.main_member_id
            )
            self.write({'allowed_member_ids': [(6, 0, member_guests.mapped('partner_id').mapped('id'))]})
        return {
            'name': 'Guest',
            'view_mode': 'form',
            'res_model': 'booking.guest',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'target': 'new',
            'res_id': self.id,
        }


    @api.constrains('partner_ids')
    def validate_partner_ids(self):
        for rec in self:
            count = int(rec.booked_room_type) - 1
            if len(rec.partner_ids or []) > count:
                raise ValidationError(f"you can't add more than {count} member!")

    def write(self, vals):
        res = super(BookingGuest, self).write(vals)
        if vals.get('partner_ids', False):
            members = self.booking_id.guest_ids.filtered(lambda g: g.main_member_id.id == self.partner_id.id)
            for member in members:
                member.write({'main_member_id': False})
            for partner in self.partner_ids:
                guest = self.booking_id.guest_ids.filtered(lambda g: g.partner_id.id == partner.id)
                if guest:
                    guest[0].write({'main_member_id': self.partner_id.id})
        return res


class GuestRoomSummary(models.Model):
    _name = 'guest.room.summary'
    _description = 'Room Summary'

    room_id = fields.Many2one('hotel.room')
    booked_room_type = fields.Selection(selection=[('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5')])
    room_type = fields.Selection(selection=[('main', 'Main'), ('member', 'Family Member')],
                                    readonly=False)
    room_gender = fields.Selection(selection=[('male', 'Male'), ('female', 'Female')], string='Room Gender')
    unassigned_beds = fields.Integer(string='Unassigned Beds')
    assigned_beds = fields.Integer(string='Assigned Beds')
    booking_id = fields.Many2one('hotel.booking', ondelete='cascade')
    booked_beds = fields.Integer(string='Booked Beds')
    is_camp = fields.Boolean(compute='_compute_is_camp', store=True)

    @api.depends('booking_id.hotel_id', 'booking_id.hotel_id.type')
    def _compute_is_camp(self):
        for rec in self:
            rec.is_camp = rec.booking_id.hotel_id.type in ['arfa', 'minnah']
