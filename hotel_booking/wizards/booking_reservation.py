from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta


class BookingReservation(models.TransientModel):
    _name = 'booking.reservation.wizard'
    _description = 'Booking Reservation Report'

    booking_creator_ids = fields.Many2many('res.users')
    draft = fields.Boolean()
    confirmed_waiting_payment = fields.Boolean(default=True)
    partially_checked_in = fields.Boolean()
    checked_in = fields.Boolean(default=True)
    partially_checked_out = fields.Boolean()
    checked_out = fields.Boolean()
    paid = fields.Boolean()
    canceled = fields.Boolean()
    created_on_from = fields.Date()
    created_on_to = fields.Date()
    hotel_ids = fields.Many2many('hotel.hotel', string='Related Hotel')
    line_ids = fields.One2many('booking.reservation.wizard.line', 'wizard_id')

    def get_booking_folios(self):
        self.line_ids = [(5, 0, 0)]
        states = []
        if self.draft:
            states.append('draft')
        if self.confirmed_waiting_payment:
            states.append('confirmed')
        if self.partially_checked_in:
            states.append('part_checked_in')
        if self.checked_in:
            states.append('checked_in')
        if self.partially_checked_out:
            states.append('part_checked_out')
        if self.checked_out:
            states.append('checked_out')
        if self.paid:
            states.append('paid')
        if self.canceled:
            states.append('canceled')

        domain = [('state', 'in', states)]

        if self.booking_creator_ids:
            domain.append(('create_uid', 'in', self.booking_creator_ids.ids))
        if self.created_on_to:
            domain.append(('create_date', '<=', self.created_on_to))
        if self.created_on_from:
            domain.append(('create_date', '>=', self.created_on_to))
        if self.hotel_ids:
            domain.append(('hotel_id', 'in', self.hotel_ids.ids))

        hotel_booking_objs = self.env['hotel.booking'].search(domain)

        for hotel_booking_obj in hotel_booking_objs:
            self.env['booking.reservation.wizard.line'].create({
                'wizard_id': self.id,
                'check_in': hotel_booking_obj.check_in,
                'check_out': hotel_booking_obj.check_out,
                'hotel_id': hotel_booking_obj.hotel_id.id,
                'booking_creator_id': hotel_booking_obj.create_uid.id,
                'state': hotel_booking_obj.state,
            })
        return {
            'type': 'ir.actions.act_window',
            'name': _('Booking Reservation'),
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'booking.reservation.wizard',
            'res_id': self.id,
            'target': 'new'
        }

    def print_pdf(self):
        return self.env.ref('hotel_booking.booking_reservation_wizard_action_report').with_context(
            landscape=True).report_action(self)


class BookingReservationLine(models.TransientModel):
    _name = 'booking.reservation.wizard.line'

    wizard_id = fields.Many2one('booking.reservation.wizard')

    booking_creator_id = fields.Many2one('res.users')
    check_in = fields.Date()
    check_out = fields.Date()
    hotel_id = fields.Many2one('hotel.hotel', string='Related Hotel')
    state = fields.Char()
