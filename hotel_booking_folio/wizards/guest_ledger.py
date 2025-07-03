from dateutil.relativedelta import relativedelta
from odoo import fields, models, api, _
from odoo.exceptions import UserError

class GuestLedger(models.TransientModel):
    _name = 'guest.ledger'
    _description = 'Guest Ledger'

    name = fields.Char()
    line_ids = fields.One2many('guest.ledger.line', 'wizard_id')
    date = fields.Date(default=fields.Date.today(), required=True)
    total_nights = fields.Integer(compute='compute_total_nights', store=True)
    total_adults = fields.Integer(compute='compute_total_adults', store=True)
    total_breakfast = fields.Integer(compute='compute_total_breakfast', store=True)
    total_lunch = fields.Integer(compute='compute_total_lunch', store=True)
    total_dinner = fields.Integer(compute='compute_total_dinner', store=True)
    total_virtual = fields.Integer(compute='compute_total_virtual', store=True)
    total_actual = fields.Integer(compute='compute_total_actual', store=True)
    total_balance = fields.Integer(compute='compute_total_balance', store=True)

    @api.depends('line_ids.days')
    def compute_total_nights(self):
        for rec in self:
            rec.total_nights = sum(rec.line_ids.mapped('days') or [])

    @api.depends('line_ids.adults')
    def compute_total_adults(self):
        for rec in self:
            rec.total_adults = sum(rec.line_ids.mapped('adults') or [])

    @api.depends('line_ids.breakfast')
    def compute_total_breakfast(self):
        for rec in self:
            rec.total_breakfast = sum(rec.line_ids.mapped('breakfast') or [])

    @api.depends('line_ids.lunch')
    def compute_total_lunch(self):
        for rec in self:
            rec.total_lunch = sum(rec.line_ids.mapped('lunch') or [])

    @api.depends('line_ids.dinner')
    def compute_total_dinner(self):
        for rec in self:
            rec.total_dinner = sum(rec.line_ids.mapped('dinner') or [])

    @api.depends('line_ids.virtual')
    def compute_total_virtual(self):
        for rec in self:
            rec.total_virtual = sum(rec.line_ids.mapped('virtual') or [])

    @api.depends('line_ids.actual')
    def compute_total_actual(self):
        for rec in self:
            rec.total_actual = sum(rec.line_ids.mapped('actual') or [])

    @api.depends('line_ids.balance')
    def compute_total_balance(self):
        for rec in self:
            rec.total_balance = sum(rec.line_ids.mapped('balance') or [])

    def button_search(self):
        self.line_ids = [(5, 0, 0)]
        folios = self.env['booking.folio'].search([
            ('room_id', '!=', False), ('state', 'in', ['checked_in', 'checked_out']), ('partner_id', '!=', False),
            ('booking_id.payment_type_id', '!=', 'city_ledger')
        ])
        filtered_folios = []
        for folio in folios:
            if not folio.new_check_in:
                raise UserError(_('Please set the check-in date for the folio %s' % folio.name))
            if not folio.new_check_out:
                raise UserError(_('Please set the check-out date for the folio %s' % folio.name))
            if folio.new_check_in <= self.date <= folio.new_check_out:
                filtered_folios.append(folio)
        for folio in filtered_folios:
            audit_date = folio.company_id.audit_date
            rate = sum(folio.line_ids.filtered(
                lambda l: (self.date == l.day) and l.type in ['room_charge', 'tax'] and not l.is_service_tax
            ).mapped('amount'))
            if not rate:
                rate = sum(folio.line_ids.filtered(
                    lambda l: (self.date - relativedelta(days=1) == l.day) and l.type in ['room_charge', 'tax'] and not l.is_service_tax
                ).mapped('amount'))
            date = audit_date if audit_date <= self.date else self.date
            virtual_amount = sum(folio.line_ids.filtered(lambda l: not l.payment_id and date >= l.day).mapped('amount'))
            actual_amount = sum(folio.line_ids.filtered(lambda l: l.payment_id).mapped('amount'))
            breakfast = 0
            lunch = 0
            dinner = 0
            if folio.rate_plan_id.include_breakfast:
                breakfast = folio.number_of_guests
            if folio.rate_plan_id.include_lunch:
                lunch = folio.number_of_guests
            if folio.rate_plan_id.include_dinner:
                dinner = folio.number_of_guests
            self.line_ids = [(0, 0, {
                'folio_id': folio.id,
                'state': 'in' if folio.state == 'checked_in' else 'out',
                'breakfast': breakfast,
                'lunch': lunch,
                'dinner': dinner,
                'rate': rate,
                'virtual': virtual_amount,
                'actual': abs(actual_amount),
                'balance': virtual_amount - abs(actual_amount),
            })]

        return {
            'type': 'ir.actions.act_window',
            'name': _('Guest Ledger'),
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'guest.ledger',
            'res_id': self.id,
            'target': 'new'
        }

    def print_pdf(self):
        return self.env.ref('hotel_booking_folio.action_guest_ledger_report').with_context(landscape=True).report_action(self)


class GuestLedgerLine(models.TransientModel):
    _name = 'guest.ledger.line'
    _description = 'Guest Ledger Line'

    wizard_id = fields.Many2one('guest.ledger')
    folio_id = fields.Many2one('booking.folio')
    booking_id = fields.Many2one('hotel.booking', related='folio_id.booking_id', store=True)
    room_id = fields.Many2one('hotel.room', related='folio_id.room_id', store=True)
    room_type_id = fields.Many2one('room.type', related='folio_id.room_type_id', store=True)
    partner_id = fields.Many2one('res.partner', string='Guest Name', related='folio_id.partner_id', store=True)
    check_in = fields.Date(string='Arrival', related='folio_id.new_check_in', store=True)
    check_out = fields.Date(string='Departure', related='folio_id.new_check_out', store=True)
    days = fields.Integer(related='folio_id.total_nights', store=True)
    rate = fields.Float()
    rate_plan_id = fields.Many2one('hotel.rate.plan', related='folio_id.rate_plan_id', store=True)
    adults = fields.Integer(string='Pax', related='folio_id.number_of_guests', store=True)
    breakfast = fields.Integer(string='B')
    lunch = fields.Integer(string='L')
    dinner = fields.Integer(string='D')
    state = fields.Selection(selection=[('in', 'IN'), ('out', 'OUT')], string='Status')
    virtual = fields.Float(string='Charge Posted')
    actual = fields.Float(string='Paid')
    balance = fields.Float()
