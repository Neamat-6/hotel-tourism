from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta


class ReceivedRoom(models.TransientModel):
    _name = 'revenue.room.type.wizard'
    _description = 'Revenue Rate Plan Report'

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
    booking_id = fields.Many2many('hotel.booking')
    partner_id = fields.Many2many('res.partner')
    hotel_id = fields.Many2many('hotel.hotel')
    room_type_id = fields.Many2many('room.type')
    line_ids = fields.One2many('revenue.room.type.wizard.line', 'wizard_id')
    total_amount = fields.Float(compute="calc_total_amount", digits=(16, 2))

    def calc_total_amount(self):
        for rec in self:
            if rec.line_ids:
                rec.total_amount = sum(rec.line_ids.mapped('amount'))
            else:
                rec.total_amount = 0.0

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

        if self.date_from:
            domain.append(('day', '>=', self.date_from))
        if self.date_to:
            domain.append(('day', '<=', self.date_to))
        if self.booking_id:
            domain.append(('booking_id', 'in', self.booking_id.ids))
        if self.room_type_id:
            domain.append(('folio_id.room_type_id', 'in', self.room_type_id.ids))
        if self.partner_id:
            domain.append(('booking_id', 'in', self.partner_id.ids))
        if self.hotel_id:
            domain.append(('booking_id', '=', self.hotel_id.ids))

        folio_lines = self.env['booking.folio.line'].search(domain)

        for folio in folio_lines:
            if folio_lines:
                self.env['revenue.room.type.wizard.line'].create({
                    'wizard_id': self.id,
                    'booking_id': folio.booking_id.id,
                    'partner_id': folio.partner_id.id,
                    'hotel_id': folio.hotel_id.id,
                    'room_type_id': folio.folio_id.room_type_id.id,
                    'state': folio.state,
                    'day': folio.day,
                    'amount': folio.amount
                })
        return {
            'type': 'ir.actions.act_window',
            'name': _('Revenue Room Type'),
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'revenue.room.type.wizard',
            'res_id': self.id,
            'target': 'new'
        }

    def print_pdf(self):
        return self.env.ref('hotel_booking.revenue_room_type_wizard_action_report').with_context(
            landscape=True).report_action(self)


class BookingArrivalLine(models.TransientModel):
    _name = 'revenue.room.type.wizard.line'

    wizard_id = fields.Many2one('revenue.room.type.wizard')

    day = fields.Date()
    booking_id = fields.Many2one('hotel.booking')
    partner_id = fields.Many2one('res.partner', 'Customer')
    hotel_id = fields.Many2one('hotel.hotel', 'Related Hotel')
    room_type_id = fields.Many2one('room.type')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed Waiting Payment'),
        ('part_checked_in', 'Partially Checked In'),
        ('checked_in', 'Checked In'),
        ('part_checked_out', 'Partially Checked Out'),
        ('checked_out', 'Checked Out'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled')])
    amount = fields.Float("Amount")
