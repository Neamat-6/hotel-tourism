from odoo import fields, models, api, _


class ComplimentaryReservation(models.TransientModel):
    _name = 'complimentary.reservation.wizard'
    _description = 'Complimentary Reservation Report'

    draft = fields.Boolean()
    confirmed_waiting_payment = fields.Boolean(default=True)
    partially_checked_in = fields.Boolean()
    checked_in = fields.Boolean(default=True)
    partially_checked_out = fields.Boolean()
    checked_out = fields.Boolean()
    paid = fields.Boolean()
    canceled = fields.Boolean()
    hotel_ids = fields.Many2many('hotel.hotel', string='Related Hotel')
    partner_ids = fields.Many2many('res.partner', string='Customer')
    line_ids = fields.One2many('complimentary.reservation.wizard.line', 'wizard_id')

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

        domain = [('state', 'in', states), ('complimentary_room', '=', True)]

        if self.partner_ids:
            domain.append(('partner_id', 'in', self.partner_ids.ids))
        if self.hotel_ids:
            domain.append(('hotel_id', 'in', self.hotel_ids.ids))

        hotel_booking_objs = self.env['hotel.booking'].search(domain)

        for folio in hotel_booking_objs.folio_ids:
            self.env['complimentary.reservation.wizard.line'].create({
                'wizard_id': self.id,
                'room_type_id': folio.room_type_id.id,
                'check_in': folio.booking_id.check_in,
                'check_out': folio.booking_id.check_out,
                'partner_id': folio.booking_id.partner_id.id,
                'hotel_id': folio.booking_id.hotel_id.id,
                'state': folio.state,
            })
        return {
            'type': 'ir.actions.act_window',
            'name': _('Complimentary Reservation'),
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'complimentary.reservation.wizard',
            'res_id': self.id,
            'target': 'new'
        }

    def print_pdf(self):
        return self.env.ref('hotel_booking.complimentary_reservation_wizard_action_report').with_context(
            landscape=True).report_action(self)


class ComplimentaryReservationLine(models.TransientModel):
    _name = 'complimentary.reservation.wizard.line'

    wizard_id = fields.Many2one('complimentary.reservation.wizard')

    room_type_id = fields.Many2one('room.type')
    check_in = fields.Date()
    check_out = fields.Date()
    hotel_id = fields.Many2one('hotel.hotel', string='Related Hotel')
    partner_id = fields.Many2one('res.partner')
    state = fields.Char()
