from odoo import fields, models, api
from odoo.exceptions import ValidationError
from datetime import date
from dateutil.relativedelta import relativedelta
import logging
logger = logging.getLogger(__name__)


class NightAudit(models.TransientModel):
    _name = 'night.audit'
    _inherit = ['multi.step.wizard.mixin']

    draft_booking_ids = fields.One2many('night.audit.draft.booking', 'audit_id')
    checkout_booking_ids = fields.One2many('night.audit.checkout.booking', 'audit_id')
    room_state_ids = fields.One2many('night.audit.room.state', 'audit_id')
    unsettled_folio_ids = fields.One2many('night.audit.unsettled.folio', 'audit_id')
    folio_ids = fields.One2many('night.audit.folio', 'audit_id')
    date = fields.Date(default=lambda self: self.env.company.audit_date)
    new_date = fields.Date()

    @api.onchange('date')
    def _onchange_date(self):
        if self.env.context.get('allowed_company_ids', False):
            if len(self.env.context.get('allowed_company_ids')) > 1:
                raise ValidationError("You must activate one company only!")
        if self.date > date.today():
            raise ValidationError("Night Audit Date is {} and today is {}".format(self.date, date.today()))
        # draft
        draft_booking_ids = [(5,)]
        line_fields = [f for f in self.env['night.audit.draft.booking']._fields.keys()]
        draft_booking_ids_data_tmpl = self.env['night.audit.draft.booking'].default_get(line_fields)
        draft_bookings = self.env['hotel.booking'].search([
            ('check_in_date', '=', self.date), ('state', 'in', ['draft', 'confirmed'])
        ])
        for booking in draft_bookings:
            draft_booking_ids_data = dict(draft_booking_ids_data_tmpl)
            draft_booking_ids_data.update(self._prepare_booking_vals(booking))
            draft_booking_ids.append((0, 0, draft_booking_ids_data))
        # checkout
        checkout_booking_ids = [(5,)]
        line_fields = [f for f in self.env['night.audit.checkout.booking']._fields.keys()]
        checkout_booking_ids_data_tmpl = self.env['night.audit.checkout.booking'].default_get(line_fields)
        checkout_bookings = self.env['hotel.booking'].search([
            ('check_out_date', '=', self.date), ('state', 'not in', ['checked_out', 'cancelled'])
        ])
        for booking in checkout_bookings:
            checkout_booking_ids_data = dict(checkout_booking_ids_data_tmpl)
            checkout_booking_ids_data.update(self._prepare_booking_vals(booking))
            checkout_booking_ids.append((0, 0, checkout_booking_ids_data))
        # room state
        room_state_ids = [(5,)]
        line_fields = [f for f in self.env['night.audit.room.state']._fields.keys()]
        room_state_ids_data_tmpl = self.env['night.audit.room.state'].default_get(line_fields)
        bookings = self.env['hotel.booking'].search([
            ('state', 'not in', ['checked_out', 'cancelled']), '|',
            ('check_in_date', '=', self.date), ('check_out_date', '=', self.date)
        ])
        for booking_line in bookings.line_ids.filtered(lambda l: l.room_id):
            room_state_ids_data = dict(room_state_ids_data_tmpl)
            room_state_ids_data.update(self._prepare_booking_line_vals(booking_line))
            room_state_ids.append((0, 0, room_state_ids_data))
        # folio
        logger.info('night_audight old folio_ids: %s', self.folio_ids)
        folio_ids = [(5,)]
        line_fields = [f for f in self.env['night.audit.folio']._fields.keys()]
        folio_ids_data_tmpl = self.env['night.audit.folio'].default_get(line_fields)
        folio_line_ids = self.env['booking.folio.line'].search([
            ('day', '=', self.date), ('payment_id', '=', False),('is_city_ledger', '=', False), ('type', '!=', 'tax'), ('folio_id.booking_id.state', '=', 'checked_in'),
            '|', ('folio_id.booking_line_id.room_id', '!=', False), ('folio_id.booking_line_id.room_ids', '!=', False)
        ])
        logger.info('night_audight folio line: %s', folio_line_ids)
        for folio_line in folio_line_ids:
            folio_ids_data = dict(folio_ids_data_tmpl)
            folio_ids_data.update(self._prepare_folio_line_vals(folio_line))
            folio_ids.append((0, 0, folio_ids_data))
        logger.info('night_audight folio_ids: %s', folio_ids)
        self.update({
            'draft_booking_ids': draft_booking_ids,
            'checkout_booking_ids': checkout_booking_ids,
            'room_state_ids': room_state_ids,
            'folio_ids': folio_ids,
        })

    @api.model
    def _prepare_booking_vals(self, booking):
        return {
            'booking_id': booking.id,
            'room_ids': booking.line_ids.mapped('room_id').mapped('id'),
            'room_type_ids': booking.line_ids.mapped('room_type').mapped('id'),
        }

    @api.model
    def _prepare_booking_line_vals(self, booking_line):
        return {
            'booking_line_id': booking_line.id,
            'booking_id': booking_line.booking_id.id,
        }

    @api.model
    def _prepare_folio_line_vals(self, folio_line):
        folio = folio_line.folio_id
        return {
            'booking_line_id': folio.booking_line_id.id,
            'booking_id': folio.booking_line_id.booking_id.id,
            'folio_id': folio.id,
            'folio_line_id': folio_line.id,
            'description': folio_line.particulars,
        }

    @api.model
    def _selection_state(self):
        return [
            ('start', 'Pending Reservation'),
            ('release_reservation', 'Release Reservation'),
            ('room_status', 'Room Status'),
            ('unsettled_folios', 'Unsettled Folios'),
            ('nightly_charge', 'Nightly Charge'),
            ('final', 'Create New Day'),
        ]

    def state_exit_start(self):
        self.state = 'release_reservation'
        for booking in self.draft_booking_ids:
            if not booking.action:
                raise ValidationError("You have to select action per line!")
            if booking.action == 'cancel':
                booking.booking_id.cancel_reason_id = booking.cancel_reason_id.id
                booking.booking_id.state = 'cancelled'
                booking.unlink()
            elif booking.action == 'check_in':
                if len(booking.room_ids) + len(booking.check_in_room_id) != len(booking.booking_id.line_ids):
                    raise ValidationError("reservation needs {}."
                                          "you have {}".format(len(booking.booking_id.line_ids), len(booking.room_ids) + len(booking.check_in_room_id)))
                if len(booking.check_in_room_id) + len(booking.room_ids) == len(booking.booking_id.line_ids):
                    available_rooms = booking.check_in_room_id.ids
                    for line in booking.booking_id.line_ids.filtered(lambda l: not l.room_id):
                        line.room_id = available_rooms.pop()
                booking.booking_id.button_check_in()
                if booking.booking_id.state == 'checked_in':
                    booking.unlink()

    def state_exit_release_reservation(self):
        self.state = 'room_status'
        for line in self.checkout_booking_ids:
            if not line.action:
                raise ValidationError("You have to select action per line!")
            elif line.action == 'check_out':
                line.booking_id.button_check_out()
                if line.booking_id.state == 'checked_out':
                    line.unlink()

    def state_previous_release_reservation(self):
        self.state = 'start'

    def state_exit_room_status(self):
        self.state = 'unsettled_folios'
        for line in self.room_state_ids:
            # if not line.action:
            #     raise ValidationError("You have to select action per line!")
            if line.action == 'check_out':
                line.booking_id.button_check_out()
                if line.booking_id.state == 'checked_out':
                    line.unlink()

    def state_previous_room_status(self):
        self.state = 'release_reservation'

    def state_exit_unsettled_folios(self):
        print('callllllllllllllled state_exit_unsettled_folios')
        self.state = 'nightly_charge'

    def state_previous_nightly_charge(self):
        self.state = 'unsettled_folios'

    def state_exit_nightly_charge(self):
        print('callllllllllllllled state_exit_nightly_charge')
        for line in self.folio_ids.filtered(lambda f: f.booking_id):
            move = line.booking_id.move_id
            if move:
                invoice_line_vals = []
                for folio in line.booking_id.folio_ids:
                    for folio_line in folio.line_ids.filtered(lambda l: l.day == self.date and not l.payment_id and not l.is_city_ledger and l.type != 'tax'):
                        invoice_line_vals += [(0, 0, {
                            'product_id': folio.booking_line_id.room_id.product_id.id,
                            'name': 'Room Charges',
                            'quantity': 1,
                            'price_unit': folio_line.amount,
                            'source_booking_id': folio.booking_line_id.id,
                            'tax_ids': [(6, 0, folio.booking_line_id.tax_id.ids or [])],
                        })]
                move.write({'invoice_line_ids': invoice_line_vals})
            else:
                self.create_invoice(line.booking_id)
        self.state = 'final'
        self.new_date = self.date + relativedelta(days=1)

    def create_invoice(self, booking):
        """
        create draft invoice containing folio lines
        """
        self.ensure_one()
        invoice_line_vals = []
        for folio in booking.folio_ids:
            for line in folio.line_ids.filtered(lambda l: l.day == self.date and not l.payment_id and not l.is_city_ledger and l.type != 'tax'):
                invoice_line_vals += [(0, 0, self.prepare_invoice_lines(folio, line))]
        move_vals = {
            'move_type': 'out_invoice',
            'partner_id': booking.company_booking_source.id if booking.company_booking_source else booking.partner_id.id,
            'booking_id': booking.id,
            'guest_id': booking.partner_id.id,
            # 'narration': booking.conditions,
            'invoice_user_id': self._uid,
            'invoice_date': self.date,
            'invoice_line_ids': invoice_line_vals
        }
        move = self.env['account.move'].with_context({'line_ids': False}).create(move_vals)
        booking.move_id = move.id

    def prepare_invoice_lines(self, folio, line):
        default_account = folio.booking_line_id.room_id.product_id.categ_id.property_account_income_categ_id.id
        vals = {
            'product_id': folio.booking_line_id.room_id.product_id.id,
            'name': line.particulars,
            'quantity': 1,
            'price_unit': line.amount,
            'source_booking_id': folio.booking_line_id.id,
            'tax_ids': [(6, 0, folio.booking_line_id.tax_id.ids or [])],
            'account_id': line.get_account(line.type) or default_account
        }
        return vals

    def state_previous_unsettled_folios(self):
        self.state = 'room_status'

    def state_previous_final(self):
        self.state = 'nightly_charge'

    def button_done(self):
        self.env.company.sudo().audit_date = self.new_date

        arrived = self.env.ref('hotel_booking.data_hotel_room_stay_status_arrived')
        stay_over = self.env.ref('hotel_booking.data_hotel_room_stay_status')
        duo_out = self.env.ref('hotel_booking.data_hotel_room_stay_status_duo_out')
        vacant = self.env.ref('hotel_booking.hotel_room_stay_status_vacant')
        arrived_rooms = self.env['hotel.room'].search([('stay_state', '=', arrived.id)])
        check_in_bookings = self.env['hotel.booking'].search([('state', '=', 'checked_in')])
        check_out_bookings = self.env['hotel.booking'].search([('state', '=', 'checked_out')])

        for booking in check_in_bookings:
            if not booking.quick_group_booking and not booking.book_all_available_rooms:
                rooms = booking.line_ids.mapped('room_id')
            elif booking.quick_group_booking or booking.book_all_available_rooms:
                rooms = booking.line_ids.mapped('room_ids')
            else:
                rooms = []
            for room in rooms:
                if room in arrived_rooms:
                    if booking.check_in.date() < self.new_date == booking.check_out.date():
                        room.stay_state = duo_out.id
                    elif booking.check_in.date() < date.today() < booking.check_out.date():
                        room.stay_state = stay_over.id

        for booking in check_out_bookings:
            if not booking.quick_group_booking and not booking.book_all_available_rooms:
                rooms = booking.line_ids.mapped('room_id')
            elif booking.quick_group_booking or booking.book_all_available_rooms:
                rooms = booking.line_ids.mapped('room_ids')
            else:
                rooms = []


class NightAuditDraftBooking(models.TransientModel):
    _name = 'night.audit.draft.booking'
    _description = 'Draft Booking'

    audit_id = fields.Many2one('night.audit')
    booking_id = fields.Many2one('hotel.booking')
    partner_id = fields.Many2one('res.partner', related='booking_id.partner_id', string='Guest')
    room_type_ids = fields.Many2many('room.type')
    room_ids = fields.Many2many('hotel.room')
    check_in_room_id = fields.Many2many('hotel.room', 'night_audit_check_room', 'room_id', string='CheckIn Rooms',
                                        domain="[('room_type', 'in', room_type_ids), ('id', 'not in', room_ids)]")
    reservation_type = fields.Many2one('booking.type', related='booking_id.reservation_type')
    booking_source = fields.Selection(related='booking_id.booking_source')
    check_out = fields.Datetime(related='booking_id.check_out')
    currency_id = fields.Many2one('res.currency', related='booking_id.currency_id', store=True)
    amount_total = fields.Monetary(string='Total', related='booking_id.amount_total', store=True)
    paid_total = fields.Monetary(string='Deposit', compute='compute_paid_total', store=True)
    amount_balance = fields.Monetary(string='Balance', compute='compute_amount_balance', store=True)
    action = fields.Selection(selection=[
        ('check_in', 'Check In'),
        ('cancel', 'Cancel'),
    ])
    cancel_reason_id = fields.Many2one('booking.cancel.reason')

    @api.depends('booking_id')
    def compute_paid_total(self):
        for rec in self:
            rec.paid_total = 0
            if rec.booking_id:
                paid_total = 0
                for folio in rec.booking_id.folio_ids:
                    for line in folio.line_ids:
                        if line.payment_id or line.is_city_ledger:
                            paid_total += abs(line.amount)
                rec.paid_total = paid_total

    @api.depends('amount_total', 'paid_total')
    def compute_amount_balance(self):
        for rec in self:
            rec.amount_balance = rec.amount_total - rec.paid_total

    def cancel_booking(self):
        if self.folio_id:
            self.folio_id.button_cancel()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Cancel Booking Wizard',
            'res_model': self._name,
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'target': 'new',
        }


class NightAuditCheckoutBooking(models.TransientModel):
    _name = 'night.audit.checkout.booking'
    _description = 'Checkout Booking'

    audit_id = fields.Many2one('night.audit')
    booking_id = fields.Many2one('hotel.booking', string='Res No#')
    partner_id = fields.Many2one('res.partner', related='booking_id.partner_id', string='Guest')
    room_type_ids = fields.Many2many('room.type')
    room_ids = fields.Many2many('hotel.room')
    reservation_type = fields.Many2one('booking.type', related='booking_id.reservation_type')
    booking_source = fields.Selection(related='booking_id.booking_source')
    check_out = fields.Datetime(related='booking_id.check_out')
    currency_id = fields.Many2one('res.currency', related='booking_id.currency_id', store=True)
    amount_total = fields.Monetary(string='Total', related='booking_id.amount_total', store=True)
    paid_total = fields.Monetary(string='Deposit', compute='compute_paid_total', store=True)
    amount_balance = fields.Monetary(string='Balance', compute='compute_amount_balance', store=True)
    action = fields.Selection(selection=[
        ('check_out', 'Check Out'),
    ])

    @api.depends('booking_id')
    def compute_paid_total(self):
        for rec in self:
            rec.paid_total = 0
            if rec.booking_id:
                paid_total = 0
                for folio in rec.booking_id.folio_ids:
                    for line in folio.line_ids:
                        if line.payment_id or line.is_city_ledger:
                            paid_total += abs(line.amount)
                rec.paid_total = paid_total

    @api.depends('amount_total', 'paid_total')
    def compute_amount_balance(self):
        for rec in self:
            rec.amount_balance = rec.amount_total - rec.paid_total


class NightAuditRoomState(models.TransientModel):
    _name = 'night.audit.room.state'
    _description = 'Audit Room State'

    audit_id = fields.Many2one('night.audit')
    booking_id = fields.Many2one('hotel.booking')
    booking_line_id = fields.Many2one('hotel.booking.line')
    partner_id = fields.Many2one('res.partner', related='booking_id.partner_id', string='Guest')
    room_id = fields.Many2one('hotel.room', related='booking_line_id.room_id', store=True)
    stay_state = fields.Many2one('hotel.room.stay.status', related='room_id.stay_state')
    check_in = fields.Datetime(related='booking_id.check_in')
    check_out = fields.Datetime(related='booking_id.check_out')
    currency_id = fields.Many2one('res.currency', related='booking_id.currency_id', store=True)
    amount_total = fields.Monetary(string='Total', related='booking_id.amount_total', store=True)
    paid_total = fields.Monetary(string='Deposit', compute='compute_paid_total', store=True)
    amount_balance = fields.Monetary(string='Balance', compute='compute_amount_balance', store=True)
    action = fields.Selection(selection=[
        ('check_out', 'Check Out'),
    ])

    @api.depends('booking_id')
    def compute_paid_total(self):
        for rec in self:
            rec.paid_total = 0
            if rec.booking_id:
                paid_total = 0
                for folio in rec.booking_id.folio_ids:
                    for line in folio.line_ids:
                        if line.payment_id or line.is_city_ledger:
                            paid_total += abs(line.amount)
                rec.paid_total = paid_total

    @api.depends('amount_total', 'paid_total')
    def compute_amount_balance(self):
        for rec in self:
            rec.amount_balance = rec.amount_total - rec.paid_total


class UnsettledFolio(models.TransientModel):
    _name = 'night.audit.unsettled.folio'
    _description = 'Audit Unsettled Folio'

    audit_id = fields.Many2one('night.audit')
    booking_id = fields.Many2one('hotel.booking')
    booking_line_id = fields.Many2one('hotel.booking.line')
    partner_id = fields.Many2one('res.partner', related='booking_id.partner_id', string='Guest')
    invoice_id = fields.Many2one('account.move')
    room_id = fields.Many2one('hotel.room', related='booking_line_id.room_id', store=True)
    description = fields.Char()
    amount_total = fields.Float(string='Total')
    paid_total = fields.Float(string='Deposit')
    action = fields.Selection(selection=[
        ('register', 'Register'),
    ], default='register')


class NightAuditFolio(models.TransientModel):
    _name = 'night.audit.folio'
    _description = 'Audit Folio'

    audit_id = fields.Many2one('night.audit')
    booking_id = fields.Many2one('hotel.booking')
    booking_line_id = fields.Many2one('hotel.booking.line')
    folio_id = fields.Many2one('booking.folio')
    folio_line_id = fields.Many2one('booking.folio.line')
    partner_id = fields.Many2one('res.partner', related='booking_id.partner_id', string='Guest')
    invoice_id = fields.Many2one('account.move')
    room_id = fields.Many2one('hotel.room', related='booking_line_id.room_id', store=True)
    description = fields.Char(default='Room Charges')
    currency_id = fields.Many2one('res.currency', related='booking_id.currency_id', store=True)
    amount = fields.Float(string='Folio Line Total', related='folio_line_id.amount', store=True)
    amount_total = fields.Monetary(string='Total', related='booking_id.amount_total', store=True)
    paid_total = fields.Monetary(string='Deposit', compute='compute_paid_total', store=True)
    amount_balance = fields.Monetary(string='Balance', compute='compute_amount_balance', store=True)
    action = fields.Selection(selection=[
        ('post', 'Post'),
    ], default='post')

    @api.depends('booking_id')
    def compute_paid_total(self):
        for rec in self:
            rec.paid_total = 0
            if rec.booking_id:
                paid_total = 0
                for folio in rec.booking_id.folio_ids:
                    for line in folio.line_ids:
                        if line.payment_id or line.is_city_ledger:
                            paid_total += abs(line.amount)
                rec.paid_total = paid_total

    @api.depends('amount_total', 'paid_total')
    def compute_amount_balance(self):
        for rec in self:
            rec.amount_balance = rec.amount_total - rec.paid_total
