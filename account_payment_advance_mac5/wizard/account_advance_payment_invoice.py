from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

from odoo.addons.account_payment_advance_mac5.models.account_move import MAP_INVOICE_TYPE_PARTNER_TYPE


class AccountAdvancePaymentInvoice(models.TransientModel):
    _name = 'account.advance.payment.invoice'
    _description = 'Apply Advance Payments'

    journal_id = fields.Many2one('account.journal', string='Application Journal',
                                 domain="[('company_id', '=', company_id)]",
                                 required=True)
    date = fields.Date(string='Application Date', required=True, default=fields.Date.context_today)
    partner_id = fields.Many2one('res.partner', string='Partner', readonly=True)
    partner_type = fields.Selection([('customer', 'Customer'), ('supplier', 'Vendor')])
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True)
    invoice_residual = fields.Monetary(string='Total Invoice Balances',
                                       currency_field='currency_id', readonly=True)
    advance_payment_total = fields.Monetary(compute='_get_advance_payment_total',
                                            string='Total Advance Payments',
                                            currency_field='currency_id')
    advance_payment_residual = fields.Monetary(compute='_get_advance_payment_total',
                                               string='Remaining Advance Payments',
                                               currency_field='currency_id')
    advance_payment_ids = fields.Many2many('account.payment', 'account_advance_payment_invoice_rel',
                                           'advance_payment_invoice_id', 'payment_id',
                                           'Advance Payments', required=True)
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.user.company_id)
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
    hide_payment_method_line = fields.Boolean(
        compute='_compute_payment_method_line_fields',
        help="Technical field used to hide the payment method if the selected journal has only one available which is 'manual'")
    booking = fields.Many2one('hotel.booking')
    payment_type = fields.Selection([
        ('outbound', 'Send Money'),
        ('inbound', 'Receive Money'),
    ], string='Payment Type')
    amount_total = fields.Float()

    @api.depends('journal_id')
    def _compute_payment_method_line_id(self):
        for wizard in self:
            available_payment_method_lines = wizard.journal_id._get_available_payment_method_lines(wizard.payment_type)

            # Select the first available one by default.
            if available_payment_method_lines:
                wizard.payment_method_line_id = available_payment_method_lines[0]._origin
            else:
                wizard.payment_method_line_id = False

    @api.depends('journal_id')
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

    @api.depends('advance_payment_ids')
    def _get_advance_payment_total(self):
        for record in self:
            payment_residual = 0.0
            for payment in record.advance_payment_ids:
                payment_currency = payment.currency_id.with_context(date=payment.date)
                if record.currency_id != payment_currency:
                    payment_residual += payment_currency._convert(payment.residual,
                                                                  record.currency_id)
                else:
                    payment_residual += payment.residual
            record.advance_payment_total = payment_residual
            record.advance_payment_residual = (payment_residual > record.invoice_residual
                                               and payment_residual - record.invoice_residual
                                               or 0.0)

    @api.onchange('company_id')
    def _onchange_company(self):
        self.journal_id = self.company_id.advance_payment_journal_id.id

    # @api.model
    # def default_get(self, fields):
    #     rec = super(AccountAdvancePaymentInvoice, self).default_get(fields)
    #     context = dict(self._context or {})
    #     active_model = context.get('active_model')
    #     active_ids = context.get('active_ids')
    #
    #     # Checks on context parameters
    #     if not active_model or not active_ids:
    #         raise UserError(_("Programmation error: wizard action executed without active_model or active_ids in context."))
    #     if active_model != 'account.move':
    #         raise UserError(_("Programmation error: the expected model for this action is 'account.move'. The provided one is '%s'.") % active_model)
    #
    #     # Checks on received invoice records
    #     invoices = self.env[active_model].browse(active_ids)
    #     if any(invoice.state != 'posted' for invoice in invoices):
    #         raise UserError(_("You can only apply advance payments for posted invoices"))
    #     if any(inv.partner_id != invoices[0].partner_id for inv in invoices):
    #         raise UserError(_("In order to pay multiple invoices at once, invoices should have the same partner."))
    #     if any(MAP_INVOICE_TYPE_PARTNER_TYPE[inv.move_type] != MAP_INVOICE_TYPE_PARTNER_TYPE[invoices[0].move_type] for inv in invoices):
    #         raise UserError(_("You cannot mix customer invoices and vendor bills in a single payment."))
    #     if any(inv.currency_id != invoices[0].currency_id for inv in invoices):
    #         raise UserError(_("In order to pay multiple invoices at once, they must use the same currency."))
    #
    #     rec.update({
    #         'company_id': invoices[0].company_id.id,
    #         'currency_id': invoices[0].currency_id.id,
    #         'invoice_residual': sum(inv.amount_residual for inv in invoices),
    #         'partner_id': invoices[0].partner_id.id,
    #         'partner_type': MAP_INVOICE_TYPE_PARTNER_TYPE[invoices[0].move_type]
    #     })
    #     return rec

    def apply_advance_payment(self):
        for record in self:
            if (record.advance_payment_total > record.invoice_residual
                    and len(record.advance_payment_ids) > 1):
                error = ('Multiple application of advance payments that '
                         'exceed the invoice balance is not yet supported')
                raise ValidationError(_(error))

            partner = self.env['res.partner']._find_accounting_partner(record.partner_id)
            invoices = self.env['account.move'].browse(self._context.get('active_ids'))
            invoice_move_lines = invoices.mapped('line_ids').filtered(
                lambda r: not r.reconciled and r.account_id.account_type in ('liability_payable', 'asset_receivable'))
            date_invoice = min(invoices.mapped('invoice_date'))

            advance_payment_accounts = self.env['account.account']
            payment_move_line = {}
            for payment in record.advance_payment_ids:
                payment_account = payment.advance_payment_account_id
                advance_payment_accounts |= payment_account
                if payment.id not in payment_move_line:
                    payment_move_line[payment.id] = self.env['account.move.line']
                payment_move_line[payment.id] |= payment.move_line_ids.filtered(
                    lambda r: not r.reconciled and r.account_id == payment_account)
                # payment.write({'invoice_ids': [(4, x.id, None) for x in invoices]})

            advance_payment_move_lines = []
            advance_payment_residual = record.advance_payment_total - record.advance_payment_residual
            counterpart_balance = currency_exchange_diff = 0.0
            company = record.company_id
            currency_company = company.currency_id
            payment_move_lines = self.env['account.move.line']

            for lines in payment_move_line.values():
                payment_move_lines |= lines
                for line in lines:
                    balance = abs(line.balance)
                    currency = line.currency_id or currency_company
                    currency_invoice = record.currency_id
                    payment_date = line.payment_id.date

                    if currency_company != currency_invoice:
                        advance_payment_residual = currency_invoice.with_context(date=payment_date) \
                            ._convert(advance_payment_residual,
                                      currency_company)

                    balance_now = balance_used = min(balance, advance_payment_residual)
                    if currency != currency_company and balance:
                        if line.amount_currency:
                            amount_currency = abs(line.amount_currency * (balance_used / balance))
                        else:
                            amount_currency = balance_used
                        balance_now = currency.with_context(date=date_invoice) \
                            ._convert(amount_currency, currency_company)

                    if currency != currency_invoice:
                        balance_now = currency.with_context(date=payment_date) \
                            ._convert(balance_now, currency_invoice)
                        balance_now = currency_invoice.with_context(date=date_invoice) \
                            ._convert(balance_now, currency)

                    counterpart_balance += balance_now
                    currency_exchange_diff += balance_now - balance_used

                    if record.partner_type == 'customer':
                        credit = 0.0
                        debit = balance_used
                        advance_payment_residual -= debit
                    else:
                        debit = 0.0
                        credit = balance_used
                        advance_payment_residual -= credit

                    currency_company = currency_company.with_context(date=payment_date)
                    if currency_company != currency_invoice:
                        advance_payment_residual = currency_company._convert(advance_payment_residual,
                                                                             currency_invoice)

                    if credit or debit:
                        advance_payment_move_lines.append((0, 0, {
                            'name': 'Advance Payment: %s' % ', '.join(lines.mapped('move_id').mapped('name')),
                            'account_id': line.account_id.id,
                            'partner_id': partner.id,
                            'debit': debit,
                            'credit': credit,
                            'payment_id': line.payment_id.id,
                            'is_advance_payment_account': True,
                        }))

            if counterpart_balance:
                advance_payment_move_lines.append((0, 0, {
                    'name': 'Advance Payment: %s' % ', '.join(invoices.mapped('name')),
                    'account_id': record.partner_type == 'customer' and partner.property_account_receivable_id.id or partner.property_account_payable_id.id,
                    'partner_id': partner.id,
                    'debit': record.partner_type == 'supplier' and counterpart_balance or 0.0,
                    'credit': record.partner_type == 'customer' and counterpart_balance or 0.0,
                    'is_advance_payment_account': False,
                }))

            if currency_exchange_diff:
                if currency_exchange_diff < 0:
                    if record.partner_type == 'supplier':
                        currency_exchange_account = company.expense_currency_exchange_account_id
                        credit = 0.0
                        debit = abs(currency_exchange_diff)
                    else:
                        currency_exchange_account = company.income_currency_exchange_account_id
                        credit = abs(currency_exchange_diff)
                        debit = 0.0
                else:
                    if record.partner_type == 'supplier':
                        currency_exchange_account = company.income_currency_exchange_account_id
                        credit = currency_exchange_diff
                        debit = 0.0
                    else:
                        currency_exchange_account = company.expense_currency_exchange_account_id
                        credit = 0.0
                        debit = currency_exchange_diff

                advance_payment_move_lines.append((0, 0, {
                    'name': 'Currency Exchange Difference',
                    'account_id': currency_exchange_account.id,
                    'partner_id': partner.id,
                    'debit': debit,
                    'credit': credit,
                    'is_advance_payment_account': False,
                }))

            if advance_payment_move_lines:
                move = self.env['account.move'].with_context(skip_validation=True).create({
                    'date': record.date,
                    'company_id': record.company_id.id,
                    'journal_id': record.journal_id.id,
                    'line_ids': advance_payment_move_lines,
                    'move_type': 'entry',
                })
                move._post()

                invoice_payment_move_lines = move.line_ids.filtered(
                    lambda r: not r.reconciled and r.account_id.account_type in (
                        'liability_payable', 'asset_receivable'))
                advance_payment_move_lines = move.line_ids.filtered(
                    lambda r: not r.reconciled and r.account_id in advance_payment_accounts)

                (invoice_payment_move_lines + invoice_move_lines).reconcile()
                (advance_payment_move_lines + payment_move_lines).reconcile()

    def _create_payment_vals_from_wizard(self):
        advance_journal_id = self.env.company.advance_payment_journal_id.id
        payment_method = self.env['account.payment.method.line'].search([('journal_id', '=', advance_journal_id)], limit=1)
        if self.advance_payment_total > 0 and self.amount_total > 0:
            if self.advance_payment_total > self.amount_total:
                advance_payment_amount = self.advance_payment_total - self.amount_total
                payment_vals = {
                    'date': self.date,
                    'amount': self.amount_total,
                    'payment_type': 'inbound',
                    'partner_type': 'customer',
                    'ref': "Paid From Advance Payment",
                    'journal_id': advance_journal_id,
                    'currency_id': self.currency_id.id,
                    'partner_id': self.partner_id.id,
                    # 'payment_method_line_id': payment_method.id,
                    'booking_id': self.booking.id,
                    'audit_date': self.env.company.audit_date
                }
                advance_payment_vals = {
                    'date': self.date,
                    'amount': advance_payment_amount,
                    'payment_type': 'inbound',
                    'partner_type': 'customer',
                    'is_advance_payment': True,
                    'ref': "Advance Payment",
                    'journal_id': advance_journal_id,
                    'currency_id': self.currency_id.id,
                    'partner_id': self.partner_id.id,
                    # 'payment_method_line_id': payment_method.id,
                    'booking_id': self.booking.id,
                    'audit_date': self.env.company.audit_date,
                    'advance_payment_account_id': self.env.company.advance_payment_account_id.id
                }
                return payment_vals, advance_payment_vals
            elif self.advance_payment_total < self.amount_total:
                payment_vals = {
                    'date': self.date,
                    'amount': self.advance_payment_total,
                    'payment_type': 'inbound',
                    'partner_type': 'customer',
                    'ref': "Paid From Advance Payment",
                    'journal_id': self.journal_id.id,
                    'currency_id': self.currency_id.id,
                    'partner_id': self.partner_id.id,
                    'payment_method_line_id': self.payment_method_line_id.id,
                    'booking_id': self.booking.id,
                    'audit_date': self.env.company.audit_date
                }
                return payment_vals, None
        else:
            raise UserError("There is no amount!")

    def action_create_payments(self):
        self.ensure_one()
        to_process = []
        advance = []

        payment_vals, advance_payment_vals = self._create_payment_vals_from_wizard()
        to_process.append({
            'create_vals': payment_vals,
        })
        payments = self.env['account.payment'].create([x['create_vals'] for x in to_process])
        # payments.move_id.line_ids[0].update({'account_id': self.env.company.advance_payment_account_id.id})
        payments.action_post()

        if advance_payment_vals:
            advance.append({
                'create_vals': advance_payment_vals,
            })
            advance_payment = self.env['account.payment'].create([x['create_vals'] for x in advance])
            # advance_payment.update({'journal_id': journal_id, 'payment_method_line_id': payment_method.id})

            # advance_payment.line_ids[0].update({'account_id': account_id})

            advance_payment.action_post()

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

        for adv in self.advance_payment_ids:
            adv.action_draft()
            adv.unlink()

    def prepare_folio_line(self, payments, particulars):
        vals = {
            'folio_id': self.booking.folio_ids[0].id,
            'day': self.date,
            'amount': -self.advance_payment_total if self.advance_payment_total < self.amount_total else -self.amount_total,
            'description': "Paid From Advanced Payment",
            'payment_id': payments[0].id if payments else False,
            'particulars': particulars,
        }
        return vals
