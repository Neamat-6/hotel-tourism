from collections import Counter

import pytz
from dateutil.relativedelta import relativedelta

from odoo import fields, models, api
from odoo.exceptions import ValidationError, UserError
import logging
logger = logging.getLogger(__name__)

class Booking(models.Model):
    _inherit = 'hotel.booking'

    master_group_room = fields.Boolean()
    master_folio_id = fields.Many2one('booking.folio', domain="[('id', 'in', folio_ids)]")
    daily_price_ids = fields.One2many('booking.daily.price', 'booking_id')
    apply_daily_price = fields.Boolean(default=True)
    room_type_available_lines = fields.One2many('room.type.availability', 'booking_id')
    room_number = fields.Char()
    hotel_room_id = fields.Many2one('hotel.room')
    is_hotel_room = fields.Boolean()
    is_updated = fields.Boolean()
    is_allotted = fields.Boolean(string='Allotment')

    # def button_cancel_discount(self):
    #     for line in self.folio_ids:



    @api.constrains('total_nights')
    def _onchange_total_nights(self):
        if self.total_nights == 0 and not self.day_use:
            raise ValidationError("Attention Please , Total Nights Is Zero !")

    def cancel_selected_folios(self):
        context = {'selected_folio': True}
        for rec in self:
            if rec.folio_ids:
                for line in rec.folio_ids:
                    if line.select_folio:
                        line.with_context(context).button_cancel()

    def get_total_exclude_vat_municipality(self):
        price = sum(self.folio_ids.mapped('room_price_subtotal')) + sum(self.folio_ids.mapped('service_price_subtotal'))
        return round(price, 2)

    def get_total_municipality(self):
        price = sum(self.folio_ids.mapped('price_municipality')) + sum(
            self.folio_ids.mapped('service_price_municipality'))
        return round(price, 2)

    def get_total_exclude_vat(self):
        return self.get_total_exclude_vat_municipality() + self.get_total_municipality()

    def get_total_vat(self):
        price = sum(self.folio_ids.mapped('price_vat')) + sum(self.folio_ids.mapped('service_price_vat'))
        return round(price, 2)

    def update_new_check(self):
        bookings = self.env['hotel.booking'].browse(self.env.context.get('active_ids')).filtered(
            lambda b: b.check_in_date and b.check_out_date)
        for booking in bookings:
            self.env.cr.execute(
                """update hotel_booking  set new_check_in = %s, new_check_out=%s where id=%s""",
                [booking.check_in_date, booking.check_out_date, booking.id]
            )
            for folio in booking.folio_ids.filtered(lambda f: f.check_in_date and f.check_out_date):
                self.env.cr.execute(
                    """update booking_folio  set new_check_in = %s, new_check_out=%s where id=%s""",
                    [folio.check_in_date, folio.check_out_date, folio.id]
                )

    @api.onchange('quick_group_booking')
    def update_master_group_room(self):
        if not self.quick_group_booking:
            self.master_group_room = False
            self.master_folio_id = False

    def update_folio(self, check_in, check_out):
        pass

    # todo check this again
    # @api.onchange('line_ids', 'new_check_in', 'new_check_out')
    # def check_availability_rooms(self):
    #     for booking in self:
    #         if booking.total_nights or booking.day_use:
    #             for line in booking.line_ids.filtered(lambda l: l.folio_ids and not l.room_type.is_virtual):
    #                 total_available_rooms = []
    #                 date_start = booking.check_in_date
    #                 date_end = booking.check_out_date
    #                 if booking.day_use:
    #                     date_end = date_end + relativedelta(days=1)
    #                 # out_of_order_rooms
    #                 out_of_order_rooms = self.env["hotel.room"].search([
    #                     ('room_type', '=', line.room_type.id),
    #                     '|', '|',
    #                     '&', ('out_of_order_from', '<=', date_start), ('out_of_order_to', '>', date_start),
    #                     '&', ('out_of_order_from', '<=', date_end), ('out_of_order_to', '>', date_end),
    #                     '&', ('out_of_order_from', '<=', date_start), ('out_of_order_to', '>', date_end),
    #                 ])
    #                 while date_start < date_end:
    #                     check_in_folios = self.env['booking.folio'].sudo().search([
    #                         ('state', 'in', ['confirmed', 'draft']), ('company_id', '=', booking.company_id.id),
    #                         ('check_in', '!=', False), ('check_in_date', '=', date_start),
    #                         ('room_type_id', '=', line.room_type.id)
    #                     ])
    #                     # departure
    #                     check_out_folios = self.env['booking.folio'].sudo().search([
    #                         ('room_id', '!=', False), ('company_id', '=', booking.company_id.id),
    #                         ('state', '=', 'checked_in'), ('check_in', '!=', False),
    #                         ('room_type_id', '=', line.room_type.id),
    #                         ('check_out_date', '=', date_start)
    #                     ])
    #                     exp_check_out_folios = self.env['booking.folio'].sudo().search([
    #                         ('company_id', '=', booking.company_id.id), ('check_in', '!=', False),
    #                         ('check_out_date', '=', date_start), ('state', '!=', 'cancelled'),
    #                         ('room_type_id', '=', line.room_type.id)
    #                     ])
    #                     # inhouse
    #                     exp_inhouse_folios = self.env['booking.folio'].search([
    #                         ('check_in', '!=', False), ('company_id', '=', booking.company_id.id),
    #                         ('state', '!=', 'cancelled'),
    #                         ('id', 'not in', check_out_folios.ids), ('id', 'not in', check_in_folios.ids),
    #                         ('id', 'not in', exp_check_out_folios.ids),
    #                         ('room_type_id', '=', line.room_type.id)
    #                     ]).filtered(lambda f: f.check_in_date <= date_start <= f.check_out_date)
    #
    #                     booked = (len(check_in_folios) + len(exp_inhouse_folios))
    #                     total = len(line.room_type.room_ids) - len(out_of_order_rooms.ids)
    #                     available_rooms = (total - booked)
    #                     total_available_rooms.append(available_rooms)
    #                     date_start += relativedelta(days=1)
    #                 if total_available_rooms:
    #                     if min(total_available_rooms) > 0:
    #                         line.available_rooms = min(total_available_rooms)
    #                     else:
    #                         msg = f"There is no available rooms for {line.room_type.name}!"
    #                         if booking.hotel_id.allow_overbooking:
    #                             line.available_rooms = min(total_available_rooms)
    #                             warning = {
    #                                 'title': 'Overbooking',
    #                                 'message': msg
    #                             }
    #                             return {'warning': warning}
    #                         else:
    #                             raise ValidationError(msg)

    @api.onchange('line_ids')
    def get_available_rooms(self):
        for booking in self:
            if booking.total_nights or booking.day_use:
                room_type_lst = [line.room_type.id for line in booking.line_ids if
                                 line.room_type and not line.room_type.is_virtual]
                c = Counter(room_type_lst)
                lines = booking.line_ids
                for key, value in c.items():
                    if value > 1:
                        room_type = self.env['room.type'].browse(key)
                        room_type_lines = lines.filtered(lambda l: l.room_type.id == room_type.id)
                        number_of_rooms = sum(room_type_lines.mapped('number_of_rooms'))
                        available_count = int(room_type_lines[0].available_rooms)
                        if number_of_rooms > available_count:
                            msg = f"Overbooking\n{room_type.name} available rooms is {available_count} and you entered {number_of_rooms}!"
                            if booking.hotel_id.allow_overbooking:
                                warning = {
                                    'title': 'Overbooking',
                                    'message': msg
                                }
                                return {'warning': warning}
                            else:
                                raise ValidationError(msg)
                for line in booking.line_ids.filtered(lambda l: not l.folio_ids and not l.room_type.is_virtual):
                    total_available_rooms = []
                    date_start = booking.check_in_date
                    date_end = booking.check_out_date
                    if booking.day_use:
                        date_end = date_end + relativedelta(days=1)
                    # out_of_order_rooms
                    out_of_order_rooms = self.env["hotel.room"].search([
                        ('room_type', '=', line.room_type.id),
                        '|', '|',
                        '&', ('out_of_order_from', '<=', date_start), ('out_of_order_to', '>', date_start),
                        '&', ('out_of_order_from', '<=', date_end), ('out_of_order_to', '>', date_end),
                        '&', ('out_of_order_from', '<=', date_start), ('out_of_order_to', '>', date_end),
                    ])
                    while date_start < date_end:
                        check_in_folios = self.env['booking.folio'].sudo().search([
                            ('state', 'in', ['confirmed', 'draft']), ('company_id', '=', booking.company_id.id),
                            ('check_in', '!=', False), ('check_in_date', '=', date_start),
                            ('room_type_id', '=', line.room_type.id)
                        ])
                        # departure
                        check_out_folios = self.env['booking.folio'].sudo().search([
                            ('room_id', '!=', False), ('company_id', '=', booking.company_id.id),
                            ('state', '=', 'checked_in'), ('check_in', '!=', False),
                            ('room_type_id', '=', line.room_type.id),
                            ('check_out_date', '=', date_start)
                        ])
                        exp_check_out_folios = self.env['booking.folio'].sudo().search([
                            ('company_id', '=', booking.company_id.id), ('check_in', '!=', False),
                            ('check_out_date', '=', date_start), ('state', '!=', 'cancelled'),
                            ('room_type_id', '=', line.room_type.id)
                        ])
                        # inhouse
                        exp_inhouse_folios = self.env['booking.folio'].search([
                            ('check_in', '!=', False), ('company_id', '=', booking.company_id.id),
                            ('state', '!=', 'cancelled'),
                            ('id', 'not in', check_out_folios.ids), ('id', 'not in', check_in_folios.ids),
                            ('id', 'not in', exp_check_out_folios.ids),
                            ('room_type_id', '=', line.room_type.id)
                        ]).filtered(lambda f: f.check_in_date <= date_start <= f.check_out_date)

                        booked = (len(check_in_folios) + len(exp_inhouse_folios))
                        total = len(line.room_type.room_ids) - len(out_of_order_rooms.ids)
                        available_rooms = (total - booked)
                        total_available_rooms.append(available_rooms)
                        date_start += relativedelta(days=1)
                    if total_available_rooms:
                        if min(total_available_rooms) > 0:
                            line.available_rooms = min(total_available_rooms)
                        else:
                            msg = f"There is no available rooms for {line.room_type.name}!"
                            if booking.hotel_id.allow_overbooking:
                                line.available_rooms = min(total_available_rooms)
                                warning = {
                                    'title': 'Overbooking',
                                    'message': msg
                                }
                                return {'warning': warning}
                            else:
                                raise ValidationError(msg)

    def button_cancel(self):
        for rec in self:
            for line in rec.line_ids:
                if line.room_id.booking_line_id:
                    raise ValidationError(
                        "Sorry customer is still living in this room. You have to check out before cancel.")
            # for inv in rec.invoice_ids:
            #     inv.button_cancel()
            rec.state = 'cancelled'
            for folio in self.folio_ids:
                folio.button_cancel()

    def write(self, vals):
        res = super(Booking, self).write(vals)
        beds = self.folio_ids.mapped('bed_ids')
        if vals.get('total_nights', False):
            total_nights = vals['total_nights']
        else:
            total_nights = self.total_nights
        if vals.get('check_in', False) and vals.get('new_check_in', False):
            for folio in self.folio_ids:
                folio.write({
                    'check_in': vals['check_in'],
                    'new_check_in': vals['new_check_in'],
                    'total_nights': total_nights,
                })
                folio.button_update_folio()
        if vals.get('check_out', False) and vals.get('new_check_out', False):
            for folio in self.folio_ids:
                folio.write({
                    'check_out': vals['check_out'],
                    'new_check_out': vals['new_check_out'],
                    'total_nights': total_nights,
                })
                folio.button_update_folio()
        if vals.get('book_by_bed', False) or self.book_by_bed and not beds:
            for folio in self.folio_ids:
                folio.bed_ids = [(5, 0, 0)]
                count = folio.room_type_id.mini_adults
                folio.available_beds = count
                for i in range(count):
                    self.env['booking.folio.bed'].create({
                        'folio_id': folio.id,
                    })
        return res

    def button_amend_stay(self):
        self.amend_stay = True
        for folio in self.folio_ids:
            folio.amend_stay = True

    def button_change_room(self):
        for line in self.line_ids:
            line.room_id.state = self.env.ref('hotel_booking.hotel_room_stay_status_vacant').id
            line.change_room = True
            line.assign_room = True
        for folio in self.folio_ids:
            folio.change_room = True

    def button_confirm(self):
        if not self.line_ids:
            raise UserError("You have to add at least one line.")
        if not self.partner_id:
            raise ValidationError(f"Please select customer!")
        for folio in self.folio_ids:
            folio.write({'partner_id': self.partner_id.id})
            folio.button_confirm()
        self.state = "confirmed"
        # self.name = self.get_default_sequence()
        self.action_vendor_booking_send_email()
        self.action_customer_booking_send_email()
        if self.automatic_send_confirmation_email_and_folio_invoice:
            self.send_confirmation_and_folio_invoice()
        # self.send_by_whatsapp_direct('confirm')

    def button_group_action(self):
        self.folio_ids.write({'group_action_wizard': False})
        folios = self.folio_ids
        charge_folios = folios.filtered(lambda f: f.state not in ['checked_out', 'part_checked_out', 'cancelled'])
        folio_lines = folios.mapped('line_ids').filtered(lambda l: l.type == 'room_charge').mapped('id')
        charge_folio_lines = charge_folios.mapped('line_ids').filtered(lambda l: l.type == 'room_charge').mapped('id')
        room_ids = folios.mapped('room_id').mapped('id')
        return {
            'type': 'ir.actions.act_window',
            'name': "Group Action",
            'res_model': 'booking.group.action',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_booking_id': self.id,
                'default_folio_ids': folios.filtered(lambda f: f.state in ['draft', 'confirmed']).ids,
                'default_checkout_folio_ids': folios.filtered(
                    lambda f: f.state == 'checked_in' and f.today_is_checkout).ids,
                'default_checkin_folio_ids': folios.filtered(
                    lambda f: f.state in ['draft', 'confirmed'] and f.today_is_checkin).ids,
                'default_amend_folio_ids': folios.filtered(lambda f: f.state not in ['cancelled', 'checked_out']).ids,
                'default_charge_folio_ids': charge_folios.ids,
                'default_all_folio_ids': folios.filtered(lambda f: f.state not in ['cancelled']).ids,
                'default_folio_line_ids': charge_folio_lines,
                'default_all_folio_line_ids': folio_lines,
                'default_room_ids': room_ids,
                'default_all_room_ids': room_ids,
                'default_tax_ids': self.line_ids.rate_plan.tax_ids.filtered(lambda t: t.price_include).ids,
            }
        }

    @api.onchange('check_in', 'check_out')
    def _compute_total_nights(self):
        res = super(Booking, self)._compute_total_nights()
        if self.check_in and self.check_out:
            self.room_type_available_lines = [(5, 0, 0)]
            timezone = pytz.timezone(self.env.user.tz or 'UTC')
            check_in = pytz.utc.localize(self.check_in).astimezone(timezone)
            check_out = pytz.utc.localize(self.check_out).astimezone(timezone)
            check_in_date = check_in.date()
            check_out_date = check_out.date()

            vals = self.prepare_room_type_availability_lines(check_in_date, check_out_date)
            for val in vals:
                new_line = self.room_type_available_lines.new(val)
                self.room_type_available_lines += new_line
        return res

    def get_booked_inventory(self, room_type, rooms, day):
        """
            get booked qty for a specific day
        """
        booked_folios = 0
        if day:
            # arrival
            check_in_folios = self.env['booking.folio'].sudo().search([
                ('state', 'in', ['confirmed', 'draft']), ('company_id', '=', self.company_id.id),
                ('check_in', '!=', False), ('check_in_date', '=', day), ('room_type_id', '=', room_type.id)
            ])
            # departure
            check_out_folios = self.env['booking.folio'].sudo().search([
                ('room_id', '!=', False), ('company_id', '=', self.company_id.id),
                ('state', '=', 'checked_in'), ('check_in', '!=', False),
                ('check_out_date', '=', day), ('room_id', 'in', rooms), ('room_type_id', '=', room_type.id)
            ])
            exp_check_out_folios = self.env['booking.folio'].sudo().search([
                ('company_id', '=', self.company_id.id), ('state', '!=', 'cancelled'),
                ('check_in', '!=', False), ('check_out_date', '=', day), ('room_type_id', '=', room_type.id)
            ])
            exp_inhouse_folios = self.env['booking.folio'].sudo().search([
                ('check_in', '!=', False), ('company_id', '=', self.company_id.id), ('state', '!=', 'cancelled'),
                ('room_type_id', '=', room_type.id),
                ('id', 'not in', check_out_folios.ids), ('id', 'not in', exp_check_out_folios.ids),
                ('id', 'not in', check_in_folios.ids)
            ]).filtered(lambda f: f.check_in_date <= day <= f.check_out_date)

            booked_folios = len(check_in_folios) + len(exp_inhouse_folios)
        return booked_folios

    def prepare_room_type_availability_lines(self, start, end):
        vals = []
        room_types = self.env['room.type'].search([('company_id', '=', self.company_id.id)])
        while start < end:
            for room_type in room_types:
                hotel_id = self.company_id.related_hotel_id
                rooms = self.env['hotel.room'].search(
                    [('hotel_id', '=', hotel_id.id), ('room_type', '=', room_type.id)])
                total_rooms = len(rooms)
                booked_rooms = self.get_booked_inventory(room_type, rooms.ids, start)
                available_rooms = int(total_rooms - booked_rooms)
                if available_rooms > 1:
                    vals.append({
                        'date': start,
                        'room_type_id': room_type.id,
                        'qty_available': available_rooms
                    })
            start += relativedelta(days=1)
        return vals
