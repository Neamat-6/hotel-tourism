from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta


class ReceivedRoom(models.TransientModel):
    _name = 'payment.folio.refund.wizard'
    _description = 'Folio Refund Report'

    date_from = fields.Date()
    date_to = fields.Date()
    draft = fields.Boolean()
    confirmed_waiting_payment = fields.Boolean(default=True)
    partially_checked_in = fields.Boolean()
    checked_in = fields.Boolean(default=True)
    partially_checked_out = fields.Boolean()
    checked_out = fields.Boolean()
    paid = fields.Boolean()
    canceled = fields.Boolean()
    booking_id = fields.Many2one('hotel.booking')
    folio_id = fields.Many2one('booking.folio')
    partner_id = fields.Many2one('res.partner', 'Customer')
    hotel_id = fields.Many2one('hotel.hotel', 'Related Hotel')
    room_id = fields.Many2one('hotel.room', string='Room No')
    particular_type = fields.Selection(string="Particular Type",
                                       selection=[('transfer', 'Transfer'), ('refund', 'Refund')], required=False, )
    line_ids = fields.One2many('payment.folio.refund.wizard.line', 'wizard_id')

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

        domain = [('state', 'in', ['confirmed', 'checked_in']), ('amount', '>', 0)]

        if self.particular_type:
            if self.particular_type == 'transfer':
                domain.append(('particulars', 'ilike', 'Transfer'))
            if self.particular_type == 'refund':
                domain.append(('particulars', 'ilike', 'Refund'))

        if self.room_id:
            domain.append(('room_id', '=', self.room_id.id))
        if self.date_from:
            domain.append(('day', '>=', self.date_from))
        if self.date_to:
            domain.append(('day', '<=', self.date_to))
        if self.booking_id:
            domain.append(('booking_id', '=', self.booking_id.id))
        if self.folio_id:
            domain.append(('folio_id', '=', self.folio_id.id))
        if self.partner_id:
            domain.append(('booking_id', '=', self.partner_id.id))
        if self.hotel_id:
            domain.append(('booking_id', '=', self.hotel_id.id))

        folio_lines = self.env['booking.folio.line'].search(domain)

        for folio in folio_lines:
            if folio_lines:
                self.env['payment.folio.refund.wizard.line'].create({
                    'wizard_id': self.id,
                    'booking_id': folio.booking_id.id,
                    'folio_id': folio.folio_id.id,
                    'partner_id': folio.partner_id.id,
                    'hotel_id': folio.hotel_id.id,
                    'room_id': folio.room_id.id,
                    'amount': folio.amount,
                    'particulars': folio.particulars,
                    'description': folio.description,
                    'type': folio.type,
                    'state': folio.state,
                    'day': folio.day,
                })
        return {
            'type': 'ir.actions.act_window',
            'name': _('Folio Refund'),
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'payment.folio.refund.wizard',
            'res_id': self.id,
            'target': 'new'
        }

    def print_pdf(self):
        return self.env.ref('hotel_booking.payment_folio_refund_wizard_action_report').with_context(
            landscape=True).report_action(self)


class BookingArrivalLine(models.TransientModel):
    _name = 'payment.folio.refund.wizard.line'

    wizard_id = fields.Many2one('payment.folio.refund.wizard')

    day = fields.Date()
    booking_id = fields.Many2one('hotel.booking')
    folio_id = fields.Many2one('booking.folio')
    partner_id = fields.Many2one('res.partner', 'Customer')
    hotel_id = fields.Many2one('hotel.hotel', 'Related Hotel')
    amount = fields.Float()
    particulars = fields.Char()
    description = fields.Char()
    type = fields.Selection([
        ('room_charge', 'Room Charge'),
        ('food', 'Food'),
        ('beverage', 'Beverage'),
        ('rent', 'Rent'),
        ('tax', 'Tax'),
        ('discount', 'Discount'),
    ])
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed Waiting Payment'),
        ('part_checked_in', 'Partially Checked In'),
        ('checked_in', 'Checked In'),
        ('part_checked_out', 'Partially Checked Out'),
        ('checked_out', 'Checked Out'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled')])
    room_id = fields.Many2one('hotel.room', string='Room No')
