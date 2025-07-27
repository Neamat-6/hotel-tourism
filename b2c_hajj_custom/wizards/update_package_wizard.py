from odoo import fields, models, api
from datetime import datetime


class UpdatePackageWizard(models.TransientModel):
    _name = 'update.package.wizard'
    _description = 'Select which hotel to update'

    makkah_hotel = fields.Boolean()
    madinah_hotel = fields.Boolean()
    main_hotel = fields.Boolean(string="Main Shift Hotel")
    arfa_hotel = fields.Boolean()
    minnah_hotel = fields.Boolean()
    package_id = fields.Many2one('booking.package')

    def button_confirm(self):
        print(self.package_id)
        cities = []
        camps = []
        if self.makkah_hotel:
            cities.append('makkah')
        if self.madinah_hotel:
            cities.append('madinah')
        if self.main_hotel:
            cities.append('hotel')
        if self.arfa_hotel:
            camps.append('arfa')
        if self.minnah_hotel:
            camps.append('minnah')

        print('cities', cities)
        print('camps', camps)
        rooms = ['single','double', 'triple', 'quad', 'quint']
        for city in cities:
            hotel_id = getattr(self.package_id, f'main_{city}', None)
            if hotel_id:
                lines = []
                for room in rooms:
                    number_of_rooms = getattr(self.package_id, f'{city}_no_{room}', None)
                    print('number_of_rooms', number_of_rooms)
                    if number_of_rooms > 0:
                        rate_plan_id = getattr(self.package_id, f'{city}_{room}_plan_id', None)
                        lines.append((0, 0, {
                            'room_type': rate_plan_id.room_type_id.id,
                            'rate_plan': rate_plan_id.id,
                            'tax_id': rate_plan_id.sudo().tax_ids.filtered(lambda t: t.price_include).ids,
                            'price_include_tax': True,
                            'number_of_rooms': number_of_rooms,
                        }))
                if lines:
                    new_check_in = getattr(self.package_id, f'{city}_arrival_date', None)
                    check_in = datetime.combine(new_check_in, datetime.strptime('120000', '%H%M%S').time())
                    new_check_out = getattr(self.package_id, f'{city}_departure_date', None)
                    check_out = datetime.combine(new_check_out, datetime.strptime('120000', '%H%M%S').time())
                    total_nights = check_out - check_in
                    booking_vals = {
                        'partner_id': self.package_id.partner_id.id,
                        # 'booking_source': 'online_agent',
                        # 'online_travel_agent_source': source_partner.id if partner else None,
                        'package_id': self.package_id.id,
                        'quick_group_booking': True,
                        'book_by_bed': True,
                        'guest_list': True,
                        'check_in': check_in,
                        'new_check_in': new_check_in,
                        'check_out': check_out,
                        'new_check_out': new_check_out,
                        'total_nights': total_nights.days,
                        # 'reservation_type': booking_type_objs.id,
                        'company_id': hotel_id.company_id.id,
                        'apply_daily_price': True,
                        'line_ids': lines
                    }
                    hotel_booking_obj = self.package_id.booking_ids.filtered(lambda b: b.hotel_id == hotel_id)
                    print('hotel_booking_obj', hotel_booking_obj)
                    if hotel_booking_obj:
                        if hotel_booking_obj[0].state != 'draft':
                            hotel_booking_obj[0].action_reset_to_draft()
                        hotel_booking_obj[0].line_ids.unlink()
                        hotel_booking_obj[0].write(booking_vals)
        for camp in camps:
            hotel_id = getattr(self.package_id, f'main_{camp}', None)
            if hotel_id:
                lines = []
                male_booking = getattr(self.package_id, f'{camp}_male_total_beds', None)
                female_booking = getattr(self.package_id, f'{camp}_female_total_beds', None)
                if male_booking > 0:
                    rate_plan_id = getattr(self.package_id, f'{camp}_male_plan_id', None)
                    lines.append((0, 0, {
                        'room_type': rate_plan_id.room_type_id.id,
                        'rate_plan': rate_plan_id.id,
                        'tax_id': rate_plan_id.sudo().tax_ids.filtered(
                            lambda t: t.price_include).ids,
                        'price_include_tax': True,
                        'number_of_rooms': 1,
                        'hajj_count': getattr(self.package_id, f'{camp}_male_total_beds', None),
                    }))
                if female_booking > 0:
                    rate_plan_id = getattr(self.package_id, f'{camp}_female_plan_id', None)
                    lines.append((0, 0, {
                        'room_type': rate_plan_id.room_type_id.id,
                        'rate_plan': rate_plan_id.id,
                        'tax_id': rate_plan_id.sudo().tax_ids.filtered(
                            lambda t: t.price_include).ids,
                        'price_include_tax': True,
                        'number_of_rooms': 1,
                        'hajj_count': getattr(self.package_id, f'{camp}_female_total_beds', None),
                    }))
                if lines:
                    new_check_in = getattr(self.package_id, f'{camp}_arrival_date', None)
                    check_in = datetime.combine(new_check_in,
                                                datetime.strptime('120000', '%H%M%S').time())
                    new_check_out = getattr(self.package_id, f'{camp}_departure_date', None)
                    check_out = datetime.combine(new_check_out,
                                                 datetime.strptime('120000', '%H%M%S').time())
                    total_nights = check_out - check_in
                    booking_vals = {
                        'partner_id': self.package_id.partner_id.id,
                        # 'booking_source': 'online_agent',
                        # 'online_travel_agent_source': source_partner.id if partner else None,
                        'package_id': self.package_id.id,
                        'quick_group_booking': True,
                        'book_by_bed': True,
                        'guest_list': True,
                        'check_in': check_in,
                        'new_check_in': new_check_in,
                        'check_out': check_out,
                        'new_check_out': new_check_out,
                        'total_nights': total_nights.days,
                        # 'reservation_type': booking_type_objs.id,
                        'company_id': hotel_id.company_id.id,
                        'apply_daily_price': True,
                        'line_ids': lines
                    }
                    hotel_booking_obj = self.package_id.booking_ids.filtered(lambda b: b.hotel_id == hotel_id)
                    print('hotel_booking_obj', hotel_booking_obj)
                    if hotel_booking_obj:
                        if hotel_booking_obj[0].state != 'draft':
                            hotel_booking_obj[0].action_reset_to_draft()
                        hotel_booking_obj[0].line_ids.unlink()
                        hotel_booking_obj[0].write(booking_vals)
