from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError


class Payment(models.Model):
    _inherit = 'account.payment'

    journal_partner_id = fields.Many2one(comodel_name="res.partner", string="Journal Partner")
    journal_dis_partner_id = fields.Many2one(comodel_name="res.partner", string="City Ledger Partner",
                                             domain=[('is_city_ledger', '=', True)],
                                             compute='onchange_dis_partner', readonly=False, store=True)
    booking_id = fields.Many2one('hotel.booking', domain=[('amount_due', '>', 0)], context={'ignore_record_rule': True})
    folio_ids = fields.One2many(related='booking_id.folio_ids')
    folio_id = fields.Many2one('booking.folio', string='Folio')
    amount_due = fields.Monetary(related='booking_id.amount_due')
    ref = fields.Char()
    is_city_ledger = fields.Boolean("Is City Ledger")
    booking_ids = fields.Many2many('hotel.booking', store=True, readonly=False, context={'ignore_record_rule': True},
                                   domain="[('id','in',hotel_booking_ids)]")
    hotel_booking_ids = fields.Many2many('hotel.booking', relation='hotel_booking_rel', store=True, readonly=True,
                                         context={'ignore_record_rule': True},
                                         compute='onchange_dis_partner')
    hotel_folios_ids = fields.Many2many('booking.folio', relation='hotel_folio_rel', compute='get_folios',
                                        context={'ignore_record_rule': True},
                                        store=True)
    folios_ids = fields.Many2many('booking.folio', domain="[('id','in',hotel_folios_ids)]", compute='get_folios',
                                  store=True, readonly=False)
    hotel_room_ids = fields.Many2many("hotel.room", string='Rooms', compute='get_rooms')
    partner_amount = fields.Float("Amount Total", readonly=True, store=True)
    partner_amount_due = fields.Float("Amount Due", readonly=True, store=True)
    partner_amount_paid = fields.Float("Amount Paid", readonly=True, store=True)
    audit_date = fields.Date("Audit Date", default=lambda self: self.env.company.audit_date)
    closed_cashier = fields.Boolean()
    extra_amount = fields.Float()
    is_payment = fields.Boolean()
    current_user_id = fields.Many2one("res.users", default=lambda self: self.env.user)
    amount_in_words = fields.Char()
    printed_by = fields.Char(string="Printed By", compute="_compute_printed_by")
    company_type = fields.Selection(string="Type", selection=[('person', 'Person'), ('company', 'Company')],
                                    required=False)

    @api.onchange('company_type')
    def _onchange_type(self):
        if self.company_type == 'company':
            return {'domain': {'partner_id': [('is_company', '=', True)]}}
        else:
            return {'domain': {'partner_id': [('is_company', '!=', True)]}}

    @api.depends('printed_by')
    def _compute_printed_by(self):
        self.printed_by = False
        for record in self:
            record.printed_by = self.env.user.name

    def print_custom_payments(self):
        payment_ids = self.ids
        self.amount_in_words = self.currency_id.with_context(lang=self.user_id.lang or 'es_ES').amount_to_text(
            sum(self.mapped("amount")))
        if payment_ids:
            if self.booking_id.payment_type_id == 'city_ledger':
                raise ValidationError("Nothing To Print")
        return self.env.ref('hotel_booking.action_report_payment_document').report_action(payment_ids)

    def delete_payment(self):
        for record in self:
            record.action_draft()
            folio_id = record.folio_id.line_ids.filtered(lambda l: l.payment_id.id == record.id)
            folio_id.unlink()
            record.unlink()

    # @api.onchange('journal_dis_partner_id', 'folio_ids', 'booking_ids')
    # def onchange_dis_partner(self):
    #     print('callleddddddddd from onchange_dis_partner')
    #     for rec in self:
    #         if self.journal_dis_partner_id:
    #             journal_partner = self.search(
    #                 [('journal_partner_id', '=', self.journal_dis_partner_id.id), ('state', '=', 'posted'),
    #                  ('is_city_ledger', '=', False)])
    #             journal_dis_partner = self.search(
    #                 [('journal_dis_partner_id', '=', self.journal_dis_partner_id.id), ('state', '=', 'posted')])
    #             if rec.is_city_ledger:
    #                 booking_ids = journal_partner.mapped('booking_id')
    #                 folio_ids = journal_partner.filtered(lambda b: b.booking_id in booking_ids).mapped('folio_id')
    #                 partner_amount = sum(journal_partner.mapped('amount'))
    #                 partner_amount_paid = sum(
    #                     journal_dis_partner.filtered(lambda l: l.payment_type == 'outbound').mapped('amount'))
    #                 rec.hotel_booking_ids = booking_ids
    #                 rec.booking_ids = booking_ids
    #                 rec.hotel_folios_ids = folio_ids
    #                 rec.folios_ids = folio_ids
    #                 rec.partner_amount = partner_amount
    #                 rec.partner_amount_paid = partner_amount_paid
    #                 rec.partner_amount_due = rec.partner_amount - rec.partner_amount_paid

    def get_rooms(self):
        if self.folio_id:
            room_ids = self.folio_id.mapped('room_id')
            self.hotel_room_ids = room_ids
        else:
            self.hotel_room_ids = False

    @api.depends()
    def get_folios(self):
        folio_ids = self.search([]).filtered(lambda b: b.booking_id in self.booking_ids).mapped('folio_id')
        self.hotel_folios_ids = folio_ids

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.partner_id:
            if not self.is_advance_payment:
                hotel_booking_objs = self.env['hotel.booking'].with_context(ignore_record_rule=True).search(
                    ['|', ('partner_id', '=', self.partner_id.id), ('company_booking_source', '=', self.partner_id.id)])
                for record in hotel_booking_objs:
                    self.booking_id = record
            else:
                self.booking_id = False

    def _create_paired_internal_transfer_payment(self):
        ''' When an internal transfer is posted, a paired payment is created
        with opposite payment_type and swapped journal_id & destination_journal_id.
        Both payments liquidity transfer lines are then reconciled.
        '''
        for payment in self:
            paired_payment = payment.copy({
                'journal_id': payment.destination_journal_id.id,
                'destination_journal_id': payment.journal_id.id,
                'payment_type': payment.payment_type == 'outbound' and 'inbound' or 'outbound',
                'move_id': None,
                'ref': payment.ref,
                'paired_internal_transfer_payment_id': payment.id
            })
            paired_payment.move_id._post(soft=False)
            payment.paired_internal_transfer_payment_id = paired_payment

            body = _(
                'This payment has been created from <a href=# data-oe-model=account.payment data-oe-id=%d>%s</a>') % (
                       payment.id, payment.name)
            paired_payment.message_post(body=body)
            body = _(
                'A second payment has been created: <a href=# data-oe-model=account.payment data-oe-id=%d>%s</a>') % (
                       paired_payment.id, paired_payment.name)
            payment.message_post(body=body)

            lines = (payment.move_id.line_ids + paired_payment.move_id.line_ids).filtered(
                lambda l: l.account_id == payment.destination_account_id and not l.reconciled)
            lines.reconcile()
            print(paired_payment.move_id)
            current_invoice_lines = paired_payment.move_id.line_ids.filtered(
                lambda line: line.account_id == paired_payment.journal_id.default_account_id)
            print('current_invoice_lines', current_invoice_lines)
            print('self.journal_dis_partner_idddddddddd', self.journal_dis_partner_id)
            current_invoice_lines.partner_id = self.journal_dis_partner_id.id

    def _synchronize_from_moves(self, changed_fields):
        ''' Update the account.payment regarding its related account.move.
        Also, check both models are still consistent.
        :param changed_fields: A set containing all modified fields on account.move.
        '''
        if self._context.get('skip_account_move_synchronization'):
            return

        for pay in self.with_context(skip_account_move_synchronization=True):

            # After the migration to 14.0, the journal entry could be shared between the account.payment and the
            # account.bank.statement.line. In that case, the synchronization will only be made with the statement line.
            if pay.move_id.statement_line_id:
                continue

            move = pay.move_id
            move_vals_to_write = {}
            payment_vals_to_write = {}

            if 'journal_id' in changed_fields:
                if pay.journal_id.type not in ('bank', 'cash'):
                    raise UserError(_("A payment must always belongs to a bank or cash journal."))

            if 'line_ids' in changed_fields:
                all_lines = move.line_ids
                liquidity_lines, counterpart_lines, writeoff_lines = pay._seek_for_lines()

                if len(liquidity_lines) != 1:
                    raise UserError(_(
                        "Journal Entry %s is not valid. In order to proceed, the journal items must "
                        "include one and only one outstanding payments/receipts account.",
                        move.display_name,
                    ))

                if len(counterpart_lines) != 1:
                    raise UserError(_(
                        "Journal Entry %s is not valid. In order to proceed, the journal items must "
                        "include one and only one receivable/payable account (with an exception of "
                        "internal transfers).",
                        move.display_name,
                    ))

                if writeoff_lines and len(writeoff_lines.account_id) != 1:
                    raise UserError(_(
                        "Journal Entry %s is not valid. In order to proceed, "
                        "all optional journal items must share the same account.",
                        move.display_name,
                    ))

                if any(line.currency_id != all_lines[0].currency_id for line in all_lines):
                    raise UserError(_(
                        "Journal Entry %s is not valid. In order to proceed, the journal items must "
                        "share the same currency.",
                        move.display_name,
                    ))

                # if any(line.partner_id != all_lines[0].partner_id for line in all_lines):
                #     raise UserError(_(
                #         "Journal Entry %s is not valid. In order to proceed, the journal items must "
                #         "share the same partner.",
                #         move.display_name,
                #     ))

                if counterpart_lines.account_id.user_type_id.type == 'receivable':
                    partner_type = 'customer'
                else:
                    partner_type = 'supplier'

                liquidity_amount = liquidity_lines.amount_currency

                move_vals_to_write.update({
                    'currency_id': liquidity_lines.currency_id.id,
                    'partner_id': liquidity_lines.partner_id.id,
                })
                payment_vals_to_write.update({
                    'amount': abs(liquidity_amount),
                    'partner_type': partner_type,
                    'currency_id': liquidity_lines.currency_id.id,
                    'destination_account_id': counterpart_lines.account_id.id,
                    # 'partner_id': liquidity_lines.partner_id.id,
                })
                if liquidity_amount > 0.0:
                    payment_vals_to_write.update({'payment_type': 'inbound'})
                elif liquidity_amount < 0.0:
                    payment_vals_to_write.update({'payment_type': 'outbound'})

            move.write(move._cleanup_write_orm_values(move, move_vals_to_write))
            pay.write(move._cleanup_write_orm_values(pay, payment_vals_to_write))

    def action_post(self):
        res = super(Payment, self).action_post()
        if self.journal_id.default_account_id and self.journal_partner_id and self.move_id:
            current_invoice_lines = self.move_id.line_ids.filtered(
                lambda line: line.account_id == self.journal_id.default_account_id)
            current_invoice_lines.partner_id = self.journal_partner_id.id
        if self.destination_journal_id.default_account_id and self.journal_dis_partner_id and self.move_id:
            current_invoice_lines = self.move_id.line_ids.filtered(
                lambda line: line.account_id == self.destination_journal_id.default_account_id)
            current_invoice_lines.partner_id = self.journal_dis_partner_id.id

        # todo field is payment is a hook to not duplicate payment in booking line
        if not self.is_payment:
            all_company_ids = self.env['res.company'].sudo().search([]).ids
            context = dict(self.env.context, allowed_company_ids=all_company_ids, ignore_record_rule=True)
            # rule = self.env.ref('hotel_booking.booking_comp_rule')
            #
            # rule.active = False
            #
            # _logger.info(f"Context before creating booking.folio.line: {context}")
            #
            # folio_vals = {
            #     'folio_id': self.folio_id.id,
            #     'booking_id': self.booking_id.id,
            #     'day': self.date,
            #     'partner_id': self.partner_id.id,
            #     'amount': -self.amount,
            #     'payment_id': self.id,
            #     'particulars': self.journal_id.type,
            #     'description': self.booking_id.name.replace('BK', 'FO') if self.booking_id else ""
            # }
            #
            # self.env['booking.folio.line'].with_context(context).sudo().create(folio_vals)
            #
            # rule.active = True

        return res
