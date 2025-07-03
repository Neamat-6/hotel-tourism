from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class BookingPaymentRegister(models.TransientModel):
    _name = 'booking.payment.register'
    _description = 'Register Payment'

    # == Business fields ==
    payment_date = fields.Date(string="Payment Date", required=True,
                               default=fields.Date.context_today)
    amount = fields.Monetary(currency_field='currency_id')
    communication = fields.Char(string="Folio Number")
    notes = fields.Char("Notes")
    payment_note = fields.Char("Payment Note")
    currency_id = fields.Many2one('res.currency', string='Currency', store=True, readonly=False,
                                  compute='_compute_currency_id',
                                  help="The payment's currency.")
    journal_id = fields.Many2one('account.journal', string='Payment Method',
                                 domain="[('type', 'in', ('bank', 'cash'))]")
    is_city_ledger = fields.Boolean(related='journal_id.is_city_ledger')
    journal_partner_id = fields.Many2one(comodel_name="res.partner", string="City Ledger",
                                         domain=[('is_city_ledger', '=', True)])
    partner_bank_id = fields.Many2one(comodel_name='res.partner.bank', string="Recipient Bank Account", )
    company_currency_id = fields.Many2one('res.currency', string="Company Currency", related='company_id.currency_id')
    audit_date = fields.Date('Audit Date')
    payment_type = fields.Selection([
        ('outbound', 'Send Money'),
        ('inbound', 'Receive Money'),
    ], string='Payment Type')
    partner_type = fields.Selection([
        ('customer', 'Customer'),
        ('supplier', 'Vendor'),
    ])
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, required=True)
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user)
    partner_id = fields.Many2one('res.partner', string="Customer")

    # == Payment methods fields ==
    payment_method_line_id = fields.Many2one('account.payment.method.line', string='Payment Method',
                                             readonly=False, store=True,
                                             compute='_compute_payment_method_line_id',
                                             domain="[('id', 'in', available_payment_method_line_ids)]",
                                             help="Manual: Pay or Get paid by any method outside of Odoo.\n"
                                                  "Payment Acquirers: Each payment acquirer has its own Payment Method. Request a transaction on/to a card thanks to a payment token saved by the partner when buying or subscribing online.\n"
                                                  "Check: Pay bills by check and print it from Odoo.\n"
                                                  "Batch Deposit: Collect several customer checks at once generating and submitting a batch deposit to your bank. Module account_batch_payment is necessary.\n"
                                                  "SEPA Credit Transfer: Pay in the SEPA zone by submitting a SEPA Credit Transfer file to your bank. Module account_sepa is necessary.\n"
                                                  "SEPA Direct Debit: Get paid in the SEPA zone thanks to a mandate your partner will have granted to you. Module account_sepa is necessary.\n")
    available_payment_method_line_ids = fields.Many2many('account.payment.method.line',
                                                         compute='_compute_payment_method_line_fields')
    total_amount_booking = fields.Float()
    hide_payment_method_line = fields.Boolean(
        compute='_compute_payment_method_line_fields',
        help="Technical field used to hide the payment method if the selected journal has only one available which is 'manual'")

    booking = fields.Many2one('hotel.booking')
    booking_payment_type = fields.Selection(string="Payment Type", compute='_onchange_booking_payment_type',
                                            selection=[('cash', 'Cash'), ('city_ledger', 'City Ledger')],
                                            default='cash',
                                            required=False)
    company_booking_source_ids = fields.Many2many('res.partner')
    pay_type = fields.Selection(string="Are You Want To Pay", selection=[('yes', 'yes'), ('no', 'no')], default='no',
                                required=False)
    account_journal_id = fields.Many2one('account.journal', string='Payment Method',
                                         domain="[('company_id', '=', company_id), ('type', 'in', ('bank', 'cash')),('is_city_ledger','!=',True)]")
    advanced_payment = fields.Float("Amount", compute='onchange_pay_type', store=True)
    type = fields.Selection(string="Payment Type", related='booking.payment_type_id',
                            selection=[('cash', 'Cash'), ('city_ledger', 'City Ledger')], store=True)
    max_credit = fields.Boolean("Pay With Max Credit")
    pay_minimum = fields.Boolean(compute='check_price')
    is_cancellation_fee = fields.Boolean()

    @api.onchange('booking_payment_type')
    def check_price(self):
        for rec in self:
            if self.env.user.has_group('hotel_booking.group_edit_amount_register_payment'):
                rec.pay_minimum = True
            else:
                rec.pay_minimum = False

    @api.onchange('pay_type')
    def onchange_pay_type(self):
        for rec in self:
            if rec.pay_type and rec.pay_type == 'yes':
                rec.advanced_payment = rec.amount
            else:
                rec.advanced_payment = 0.0

    @api.onchange('booking_payment_type')
    def _onchange_booking_payment_type(self):
        self.booking_payment_type = False
        if self.env.company.limited_access_payment:
            if self.booking.payment_type_id == 'cash':
                return {
                    'domain': {'journal_id': [('is_city_ledger', '!=', True),
                                              ('type', 'in', ('bank', 'cash'))]}
                }
            elif self.booking.payment_type_id == 'charge_city_ledger':
                return {
                    'domain': {'journal_id': [('type', 'in', ('bank', 'cash'))]
                        , 'journal_partner_id': [('id', 'in', self.company_booking_source_ids.ids)]}
                }
            else:
                return {
                    'domain': {'journal_id': [('is_city_ledger', '=', True)],
                               'journal_partner_id': [('id', 'in', self.company_booking_source_ids.ids)]}
                }

    @api.onchange('journal_id')
    def onchange_journal_id(self):
        for rec in self:
            if rec.journal_id.is_city_ledger:
                rec.journal_partner_id = rec.company_booking_source_ids[
                    0].id if rec.company_booking_source_ids else False
            if rec.booking.payment_type_id == 'charge_city_ledger':
                city_ledger_previous_payments = self.env['account.payment'].search([
                    ('booking_id', '=', rec.booking.id),
                    ('journal_id.is_city_ledger', '=', True),
                    ('state', '!=', 'cancel')
                ])
                cash_previous_payments = self.env['account.payment'].search([
                    ('booking_id', '=', rec.booking.id),
                    ('journal_id.is_city_ledger', '!=', True),
                    ('state', '!=', 'cancel')
                ])
                types = ['food', 'beverage', 'laundry', 'rent']
                if rec.journal_id:
                    if not rec.journal_id.is_city_ledger:
                        if not cash_previous_payments:
                            rec.amount = sum(rec.booking.folio_ids.line_ids.filtered(
                                lambda l: l.is_service_tax or l.type in types and not l.payment_id).mapped('amount'))
                        else:
                            rec.amount = 0.0
                    else:
                        if not city_ledger_previous_payments:
                            rec.amount = sum(rec.booking.folio_ids.line_ids.filtered(
                                lambda l: not l.is_service_tax and not l.type in types and not l.payment_id).mapped(
                                'amount'))
                        else:
                            rec.amount = 0.0

    @api.onchange('amount')
    def onchange_amount(self):
        for rec in self:
            if rec.amount < 0:
                raise ValidationError("amount is not correct , please resign it")

    @api.depends('journal_id')
    def _compute_currency_id(self):
        for wizard in self:
            wizard.currency_id = wizard.journal_id.currency_id or wizard.company_id.currency_id

    @api.depends('payment_type', 'journal_id')
    def _compute_payment_method_line_id(self):
        for wizard in self:
            available_payment_method_lines = wizard.journal_id._get_available_payment_method_lines(wizard.payment_type)

            # Select the first available one by default.
            if available_payment_method_lines:
                wizard.payment_method_line_id = available_payment_method_lines[0]._origin
            else:
                wizard.payment_method_line_id = False

    def action_payment_report(self):
        return self.env.ref('hotel_booking.payment_report_action').report_action(self)

    @api.depends('payment_type', 'journal_id')
    def _compute_payment_method_line_fields(self):
        for wizard in self:
            wizard.available_payment_method_line_ids = wizard.journal_id._get_available_payment_method_lines(
                wizard.payment_type)
            if wizard.payment_method_line_id.id not in wizard.available_payment_method_line_ids.ids:
                # In some cases, we could be linked to a payment method line that has been unlinked from the journal.
                # In such cases, we want to show it on the payment.
                wizard.hide_payment_method_line = False
            else:
                wizard.hide_payment_method_line = len(wizard.available_payment_method_line_ids) == 1 \
                                                  and wizard.available_payment_method_line_ids.code == 'manual'

    def _create_payment_vals_from_wizard(self):
        advance_payment_amount = 0.0
        payment_vals = None
        self.advanced_payment = self.amount if not self.pay_amount else self.pay_amount
        if self.env.user.has_group('hotel_booking.group_set_notes_register_payment') and not self.notes:
            raise ValidationError(f"please, set a notes")
        if self.amount > 0:
            if not self.folio_ids and not self.line_ids:
                if not self.folio_id:
                    if self.booking.amount_due > self.amount:
                        if not self.env.user.has_group('hotel_booking.group_pay_amount_register_payment'):
                            raise ValidationError(
                                f"Attention please, you should pay {self.booking.amount_due} not {self.amount}")
                if self.booking.amount_due < self.amount:
                    if self.booking.payment_type_id == 'city_ledger' and self.booking.booking_source == 'company':
                        if not self.env.user.has_group('hotel_booking.group_pay_amount_register_payment'):
                            raise ValidationError(
                                f"Attention please, you should pay {self.booking.amount_due} not {self.amount}")
                    if self.booking.payment_type_id == 'cash':
                        if self.booking.amount_due == 0.0:
                            raise ValidationError(f"Your booking due amount is zero")
                        else:
                            if not self.env.user.has_group('hotel_booking.group_pay_amount_register_payment'):
                                raise ValidationError(
                                    f"Attention please, you should pay {self.booking.amount_due} not {self.amount}")
                if self.booking.payment_type_id == 'city_ledger' and not self.journal_partner_id.is_credit_limit and self.pay_type == 'no':
                    raise ValidationError(f"Please Set a Credit Limit for {self.journal_partner_id.name}")
                else:
                    if self.pay_type == 'no':
                        if self.booking.payment_type_id == 'city_ledger' and self.booking.booking_source == 'company':
                            if self.journal_partner_id.balance == 0.0:
                                raise ValidationError(f"{self.journal_partner_id.name}, your credit limit is 0")
                            elif self.journal_partner_id.balance < self.amount:
                                if not self.max_credit:
                                    raise ValidationError(
                                        f"your credit limit is {self.journal_partner_id.customer_credit_limit} and Your Balance {self.journal_partner_id.balance} ,you cant pay for this booking")
                                else:
                                    self.amount = self.journal_partner_id.customer_credit_limit
            if self.booking.payment_type_id != 'city_ledger':
                payment_vals = {
                    'date': self.payment_date,
                    'amount': self.amount,
                    'payment_type': self.payment_type,
                    'partner_type': self.partner_type,
                    'ref': self.communication,
                    'journal_id': self.journal_id.id,
                    'currency_id': self.currency_id.id,
                    'partner_id': self.partner_id.id,
                    'partner_bank_id': self.partner_bank_id.id,
                    'journal_partner_id': self.journal_partner_id.id,
                    'payment_method_line_id': self.payment_method_line_id.id,
                    'booking_id': self.booking.id,
                    'audit_date': self.audit_date,
                    'extra_amount': advance_payment_amount,
                    'is_payment': True,
                    'system_note': self.notes,
                    'payment_note': self.payment_note
                }

            if self.booking.payment_type_id == 'city_ledger' and self.booking.booking_source == 'company':
                if self.booking.company_paid != self.amount and self.pay_type == 'yes':
                    if self.advanced_payment > self.amount:
                        advance_payment_amount = self.advanced_payment - self.amount
                        self.booking.company_booking_source.total_advanced_payment += advance_payment_amount
                        self.booking.company_paid += self.amount
                    elif self.advanced_payment < self.amount:
                        self.booking.company_paid += self.advanced_payment
                    else:
                        self.booking.company_paid = self.amount
                else:
                    if self.pay_type == 'no':
                        if not self.journal_partner_id.is_credit_limit:
                            raise ValidationError("You Should Set Credit Limit")
                        else:
                            if self.journal_partner_id.balance < self.amount:
                                raise ValidationError(
                                    f"your credit limit is {self.journal_partner_id.customer_credit_limit} and Your Balance {self.journal_partner_id.balance},you cant pay for this booking")

            if self.pay_type == 'yes' and self.booking.payment_type_id != 'city_ledger':
                if self.pay_more:
                    amount = self.pay_amount - self.amount
                else:
                    amount = self.advanced_payment
                advance_payment_vals = {
                    'date': self.payment_date,
                    'amount': amount,
                    'payment_type': 'inbound',
                    'partner_type': self.partner_type,
                    'partner_id': False,
                    'is_internal_transfer': True,
                    'ref': self.communication,
                    'journal_id': self.account_journal_id.id,
                    'currency_id': self.currency_id.id,
                    'journal_dis_partner_id': self.booking.booking_source_id.id,
                    'partner_bank_id': self.partner_bank_id.id,
                    'journal_partner_id': self.journal_partner_id.id,
                    'payment_method_line_id': self.payment_method_line_id.id,
                    'booking_id': self.booking.id,
                    'audit_date': self.audit_date,
                    'destination_journal_id': self.journal_id.id,
                    'advance_payment_account_id': self.advance_payment_account_id.id,
                    'city_ledger_payment': True,
                    'is_payment': True
                }
                return payment_vals, advance_payment_vals
            else:
                return payment_vals, None
        else:
            raise UserError("There is no amount!")

    def action_create_payments(self):
        self.ensure_one()
        to_process = []
        payments = []
        payment_vals, advance_payment_vals = self._create_payment_vals_from_wizard()
        if payment_vals:
            to_process.append({
                'create_vals': payment_vals,
            })
        if advance_payment_vals:
            to_process.append({
                'create_vals': advance_payment_vals,
            })
        if to_process:
            payments = self.env['account.payment'].create([x['create_vals'] for x in to_process])
            payments.action_post()
        particulars = ''
        if self.journal_id.type == 'cash':
            particulars = 'Cash'
        elif self.journal_id.type == 'bank':
            if self.payment_method_line_id.name == 'Manual':
                particulars = 'Bank'
            else:
                particulars = self.payment_method_line_id.name
        vals = self.prepare_folio_line(payments, particulars)
        self.env['booking.folio.line'].sudo().create(vals)
        self.folio_id.update({'note': self.notes})

    def prepare_folio_line(self, payments, particulars):
        if not self.env.user.has_group('hotel_booking.group_pay_amount_register_payment'):
            amount = -self.booking.amount_due if self.booking.amount_due < self.amount else -self.amount
        else:
            amount = -self.amount
        vals = {
            'folio_id': self.booking.folio_ids[0].id,
            'day': self.payment_date,
            'amount': amount,
            'description': self.communication,
            'payment_id': payments[0].id if payments else False,
            'particulars': particulars,
            'is_cancellation_fee': True if self.is_cancellation_fee else False,
            'is_city_ledger': self.booking.payment_type_id == 'city_ledger',
        }
        return vals
