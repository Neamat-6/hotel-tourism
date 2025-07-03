# See LICENSE file for full copyright and licensing details.

import time
from datetime import datetime, timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


def _offset_format_timestamp1(
        src_tstamp_str,
        src_format,
        dst_format,
        ignore_unparsable_time=True,
        context=None,
):
    """
    Convert a source timeStamp string into a destination timeStamp string,
    attempting to apply the correct offset if both the server and local
    timeZone are recognized,or no offset at all if they aren't or if
    tz_offset is false (i.e. assuming they are both in the same TZ).
    @param src_tstamp_str: the STR value containing the timeStamp.
    @param src_format: the format to use when parsing the local timeStamp.
    @param dst_format: the format to use when formatting the resulting
     timeStamp.
    @param server_to_client: specify timeZone offset direction (server=src
                             and client=dest if True, or client=src and
                             server=dest if False)
    @param ignore_unparsable_time: if True, return False if src_tstamp_str
                                   cannot be parsed using src_format or
                                   formatted using dst_format.
    @return: destination formatted timestamp, expressed in the destination
             timezone if possible and if tz_offset is true, or src_tstamp_str
             if timezone offset could not be determined.
    """
    if not src_tstamp_str:
        return False
    res = src_tstamp_str
    if src_format and dst_format:
        try:
            # dt_value needs to be a datetime object\
            # (so notime.struct_time or mx.DateTime.DateTime here!)
            dt_value = datetime.strptime(src_tstamp_str, src_format)
            if context.get("tz", False):
                try:
                    import pytz

                    src_tz = pytz.timezone(context["tz"])
                    dst_tz = pytz.timezone("UTC")
                    src_dt = src_tz.localize(dt_value, is_dst=True)
                    dt_value = src_dt.astimezone(dst_tz)
                except Exception:
                    pass
            res = dt_value.strftime(dst_format)
        except Exception:
            # Normal ways to end up here are if strptime or strftime failed
            if not ignore_unparsable_time:
                return False
            pass
    return res


class HotelFolio(models.Model):
    _name = "hotel.folio"
    _description = "hotel folio"
    _order = 'name desc'

    @api.model
    def _get_checkin_date(self):
        if self._context.get("tz"):
            to_zone = self._context.get("tz")
        else:
            to_zone = "UTC"
        return _offset_format_timestamp1(
            time.strftime("%Y-%m-%d 12:00:00"),
            DEFAULT_SERVER_DATETIME_FORMAT,
            DEFAULT_SERVER_DATETIME_FORMAT,
            ignore_unparsable_time=True,
            context={"tz": to_zone},
        )

    @api.model
    def _get_checkout_date(self):
        if self._context.get("tz"):
            to_zone = self._context.get("tz")
        else:
            to_zone = "UTC"
        tm_delta = timedelta(days=1)
        return (
                datetime.strptime(
                    _offset_format_timestamp1(
                        time.strftime("%Y-%m-%d 12:00:00"),
                        DEFAULT_SERVER_DATETIME_FORMAT,
                        DEFAULT_SERVER_DATETIME_FORMAT,
                        ignore_unparsable_time=True,
                        context={"tz": to_zone},
                    ),
                    "%Y-%m-%d %H:%M:%S",
                )
                + tm_delta
        )

    name = fields.Char("Folio Number", readonly=True, index=True, default="New")
    move_ids = fields.One2many('account.move', 'folio_id', string='Invoices')
    account_move_id = fields.Many2one('account.move', string='Invoice')
    ledger_move_id = fields.Many2one('account.move', string='City Ledger Invoice')
    source_name = fields.Char(string='Source')
    reservation_no = fields.Char(string='Reservation No.')
    invoice_no = fields.Char(string='Invoice No.')
    voucher_no = fields.Char(string='Voucher No.')
    currency_id = fields.Many2one('res.currency', readonly=True, tracking=True, string='Currency',
                                  default=lambda self: self.env.user.company_id.currency_id)
    checkin_date = fields.Datetime(
        "Check In",
        # required=True,
        readonly=True,
        # default=_get_checkin_date,
    )
    checkout_date = fields.Datetime(
        "Check Out",
        # required=True,
        readonly=True,
        # default=_get_checkout_date,
    )
    room_line_ids = fields.One2many(
        "hotel.folio.line",
        "folio_id",
        readonly=True,
        help="Room Lines.",
    )
    detail_line_ids = fields.One2many(
        "hotel.folio.detail",
        "folio_id",
        readonly=False,
        help="Folio Details.",
    )
    partner_id = fields.Many2one('res.partner', string='Guest')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    branch_id = fields.Many2one('res.branch', string='Branch', default=lambda self: self.env.user.branch_id.id)
    amount_total = fields.Monetary(string='Total Amount', compute="_compute_amount", store=True)
    detail_amount_total = fields.Monetary(string='Total Amount', compute="_compute_detail_total", store=True)
    detail_total_paid = fields.Monetary(string='Paid Amount', compute="_compute_detail_total", store=True)
    due_amount = fields.Monetary(string='Due Amount', compute="_compute_detail_total", store=True)

    duration = fields.Float(compute='_compute_duration', string='Duration (Days)', store=True,
                            help="Number of days which will automatically count from the check-in and check-out date.")

    def action_generate_invoice(self):
        for rec in self:
            partner_id = rec.partner_id
            account_move = rec.account_move_id
            if not partner_id:
                raise ValidationError(_('You must define hotel customer firstly.'))
            outbound_payment_transactions = []
            inbound_payment_transactions = []
            credit_aml_payment_transactions = []
            aml_groupby_account = {}
            city_ledger_payment = rec.detail_line_ids.filtered(lambda l: l.type == 'City Ledger')
            for line in rec.detail_line_ids.filtered(lambda l: not l.invoiced and l.amount_subtotal != 0.0):
                if line.is_payment or 'Refund' in line.name:
                    name = line.name
                    if 'Refund' in line.name:
                        name = line.name.replace(' [Refund]', '')
                    journal_domain = [('company_id', '=', rec.env.company.id)]
                    if line.is_city_payment:
                        journal_domain += [('type', 'in', ['cash', 'bank'])]
                    elif 'City' in line.type:
                        journal_domain += [('name', '=', 'City Ledger'), ('type', '=', 'bank')]
                    elif 'Bank' in line.type:
                        journal_domain += [('ezee_journal_type', '=', 'Bank'), ('type', '=', 'bank')]
                    elif 'Cash' in line.type:
                        journal_domain += [('ezee_journal_type', '=', 'Cash'), ('type', '=', 'cash')]
                    elif 'Discount' in line.type:
                        journal_domain += [('ezee_journal_type', '=', 'Discount'), ('type', '=', 'bank')]
                    elif 'Deposit' in line.type:
                        if name in 'Cash':
                            journal_domain += [('ezee_journal_type', '=', 'Cash'), ('type', '=', 'cash')]
                        else:
                            journal_domain += [('ezee_journal_type', '=', 'Bank'), ('type', '=', 'bank')]

                    journal_id = rec.env['account.journal'].search(journal_domain, limit=1)
                    if not journal_id:
                        journal_id = self.env['account.journal'].search(
                            [('name', '=', 'City Ledger'), ('type', '=', 'bank')], limit=1)
                    if 'City' in line.type and not line.is_city_payment:
                        credit_aml_payment_transaction = (
                            journal_id, abs(line.amount_subtotal), line.bill_date, line.name)
                        credit_aml_payment_transactions.append(credit_aml_payment_transaction)

                    elif line.amount_subtotal > 0.0:
                        outbound_payment_transaction = (
                            journal_id, abs(line.amount_subtotal), line.bill_date, line.name)
                        outbound_payment_transactions.append(outbound_payment_transaction)
                    else:
                        inbound_payment_transaction = (
                            journal_id, abs(line.amount_subtotal), line.bill_date, line.name)
                        inbound_payment_transactions.append(inbound_payment_transaction)
                else:
                    account_id = self.env['account.account'].search(
                        [('ezee_account_name', '=', line.name), ('company_id', '=', self.env.company.id)], limit=1)
                    if not account_id:
                        raise ValidationError(_('You must define account of type "%s"' % line.name))
                    else:
                        if account_id in aml_groupby_account:
                            aml_groupby_account[account_id] += abs(line.amount_subtotal)
                        else:
                            aml_groupby_account[account_id] = abs(line.amount_subtotal)
                        # aml_groupby_account = (account_id, abs(line.amount_subtotal), line.bill_date, line.name)
                        # aml_groupby_accounts.append(aml_groupby_account)
                line.invoiced = True
            # else:
            #     for line in rec.detail_line_ids.filtered(lambda l: not l.invoiced and l.amount_subtotal != 0.0):
            #         if line.is_payment or 'Refund' in line.name:
            #             name = line.name
            #             journal_domain = [('company_id', '=', rec.env.company.id)]
            #             if 'City' in line.type:
            #                 journal_domain += [('name', '=', 'City Ledger'), ('type', '=', 'bank')]
            #
            #             journal_id = rec.env['account.journal'].search(journal_domain, limit=1)
            #             if not journal_id:
            #                 journal_id = self.env['account.journal'].search(
            #                     [('name', '=', 'City Ledger'), ('type', '=', 'bank')], limit=1)
            #             if 'City' in line.type and not line.is_city_payment:
            #                 credit_aml_payment_transaction = (
            #                     journal_id, abs(line.amount_subtotal), line.bill_date, line.name)
            #                 credit_aml_payment_transactions.append(credit_aml_payment_transaction)
            #
            #             elif line.amount_subtotal > 0.0:
            #                 outbound_payment_transaction = (
            #                     journal_id, abs(line.amount_subtotal), line.bill_date, line.name)
            #                 outbound_payment_transactions.append(outbound_payment_transaction)
            #             else:
            #                 inbound_payment_transaction = (
            #                     journal_id, abs(line.amount_subtotal), line.bill_date, line.name)
            #                 inbound_payment_transactions.append(inbound_payment_transaction)
            #         else:
            #             account_id = self.env['account.account'].search(
            #                 [('ezee_account_name', '=', line.name), ('company_id', '=', self.env.company.id)], limit=1)
            #             if not account_id:
            #                 raise ValidationError(_('You must define account of type "%s"' % line.name))
            #             else:
            #                 if account_id in aml_groupby_account:
            #                     aml_groupby_account[account_id] += abs(line.amount_subtotal)
            #                 else:
            #                     aml_groupby_account[account_id] = abs(line.amount_subtotal)
            #
            #         line.invoiced = True

            # create invoices
            invoice_line_vals = []
            for account, amount in aml_groupby_account.items():
                invoice_line_vals.append((0, 0, {
                    'name': account.name,
                    'account_id': account.id,
                    'quantity': 1,
                    'price_unit': amount,
                }))
            move_id = self.env['account.move']
            if invoice_line_vals:
                res_partner_obj = self.env['res.partner'].search([('name', '=', city_ledger_payment.name)])
                customer_invoice_journal_id = self.env['account.journal'].search(
                    [('type', '=', 'sale'), ('company_id', '=', self.env.company.id)], limit=1)
                ledger_invoice_journal_id = self.env['account.journal'].search(
                    [('type', '=', 'sale'), ('name', '=', 'City Ledger'), ('is_credit_payment', '=', True)],
                    limit=1)
                move_id = rec.env['account.move'].create({
                    'move_type': 'out_invoice',
                    'is_htask_move': True,
                    'partner_id': res_partner_obj.id if city_ledger_payment else partner_id.id,
                    'journal_id': customer_invoice_journal_id.id if not city_ledger_payment else ledger_invoice_journal_id.id,
                    'invoice_date': rec.checkout_date,
                    'folio_id': account_move
                })
                move_id.invoice_line_ids = invoice_line_vals
                move_id.folio_id = rec.id
                if not city_ledger_payment:
                    rec.account_move_id = move_id
                else:
                    rec.ledger_move_id = move_id
                move_id.action_post()

        # create city ledger invoice
        # if city_ledger_payment:
        #     for journal, amount, date, name in credit_aml_payment_transactions:
        #         payment_method = journal.inbound_payment_method_line_ids
        #         res_partner_obj = self.env['res.partner'].search([('name', '=', line.source_name)])
        #         if not res_partner_obj:
        #             res_partner_obj = self.env['res.partner'].create({
        #                 'name': line.source_name,
        #                 'company_type': 'company'
        #             })
        #         ledger_invoice_journal_id = self.env['account.journal'].search(
        #             [('type', '=', 'sale'), ('name', '=', 'City Ledger'), ('is_credit_payment', '=', True)],
        #             limit=1)
        #         credit_invoice_line_vals = [(0, 0, {
        #             'name': journal.default_account_id.name,
        #             'account_id': journal.default_account_id.id,
        #             'quantity': 1,
        #             'price_unit': rec.detail_amount_total
        #         })]
        #         move_id = self.env['account.move'].create({
        #             'move_type': 'out_invoice',
        #             'is_htask_move': True,
        #             'partner_id': res_partner_obj.id,
        #             'journal_id': ledger_invoice_journal_id.id,
        #             # 'invoice_date': rec.detail_line_ids.filtered(lambda l: l.bill_date).mapped('bill_date')[-1].date(),
        #             'invoice_date': rec.checkout_date,
        #             'folio_id': account_move
        #         })
        #         payment_id = rec.env['account.payment'].with_context(default_invoice_ids=[(4, move_id.id)]).create({
        #             'payment_type': 'inbound',
        #             'partner_id': res_partner_obj.id,
        #             'journal_id': journal.id,
        #             'amount': rec.detail_amount_total,
        #             'payment_method_line_id': payment_method[0].id if payment_method else False,
        #             'date': date,
        #             'folio_id': move_id.folio_id.id,
        #             'htask_payment_type': name
        #         })
        #         move_id.invoice_line_ids = credit_invoice_line_vals
        #         move_id.folio_id = rec.id
        #         rec.ledger_move_id = move_id
        #         move_id.action_post()
        #         payment_id.action_post()

        # create inbound payment
        for journal, amount, date, name in inbound_payment_transactions:
            inbound_payment_method = journal.inbound_payment_method_line_ids
            payment_id = rec.env['account.payment'].with_context(default_invoice_ids=[(4, move_id.id)]).create({
                'payment_type': 'inbound',
                'partner_id': res_partner_obj.id if city_ledger_payment else partner_id.id,
                'journal_id': journal.id,
                'amount': amount,
                'payment_method_line_id': inbound_payment_method[0].id if inbound_payment_method else False,
                'date': date,
                'folio_id': move_id.folio_id.id,
                'htask_payment_type': name
            })
            payment_id.action_post()
            # create outbound payment
            for journal, amount, date, name in outbound_payment_transactions:
                outbound_payment_method = journal.outbound_payment_method_line_ids
                payment_id = self.env['account.payment'].with_context(
                    default_invoice_ids=[(4, move_id.id)]).create(
                    {'payment_type': 'outbound',
                     'partner_id': res_partner_obj.id if city_ledger_payment else partner_id.id,
                     'journal_id': journal.id,
                     'amount': amount,
                     'payment_method_line_id': outbound_payment_method[0].id if outbound_payment_method else False,
                     'date': date if date else rec.checkin_date,
                     'folio_id': move_id.folio_id.id,
                     'htask_payment_type': name
                     })
                payment_id.action_post()

    def action_create_payment(self):
        for rec in self:
            partner_id = rec.partner_id
            account_move = rec.account_move_id
            if not partner_id:
                raise ValidationError(_('You must define hotel customer firstly.'))
            outbound_payment_transactions = []
            inbound_payment_transactions = []
            credit_aml_payment_transactions = []
            aml_groupby_accounts = []
            for line in rec.detail_line_ids.filtered(lambda l: not l.invoiced and l.amount_subtotal != 0.0):
                if line.is_payment or 'Refund' in line.name:
                    name = line.name
                    if 'Refund' in line.name:
                        name = line.name.replace(' [Refund]', '')
                    journal_domain = [('company_id', '=', rec.env.company.id)]
                    if line.is_city_payment:
                        journal_domain += [('type', 'in', ['cash', 'bank'])]
                    elif 'City' in line.type:
                        journal_domain += [('name', '=', 'City Ledger'), ('type', '=', 'bank')]
                    elif 'Bank' in line.type:
                        journal_domain += [('ezee_journal_type', '=', 'Bank'), ('type', '=', 'bank')]
                    elif 'Cash' in line.type:
                        journal_domain += [('ezee_journal_type', '=', 'Cash'), ('type', '=', 'cash')]
                    elif 'Discount' in line.type:
                        journal_domain += [('ezee_journal_type', '=', 'Discount'), ('type', '=', 'bank')]
                    elif 'Deposit' in line.type:
                        if name in 'Cash':
                            journal_domain += [('ezee_journal_type', '=', 'Cash'), ('type', '=', 'cash')]
                        else:
                            journal_domain += [('ezee_journal_type', '=', 'Bank'), ('type', '=', 'bank')]

                    journal_id = rec.env['account.journal'].search(journal_domain, limit=1)
                    if not journal_id:
                        journal_id = self.env['account.journal'].search(
                            [('name', '=', 'City Ledger'), ('type', '=', 'bank')], limit=1)
                    if 'City' in line.type and not line.is_city_payment:
                        credit_aml_payment_transaction = (
                            journal_id, abs(line.amount_subtotal), line.bill_date, line.name)
                        credit_aml_payment_transactions.append(credit_aml_payment_transaction)

                    elif line.amount_subtotal > 0.0:
                        outbound_payment_transaction = (
                            journal_id, abs(line.amount_subtotal), line.bill_date, line.name)
                        outbound_payment_transactions.append(outbound_payment_transaction)
                    else:
                        inbound_payment_transaction = (journal_id, abs(line.amount_subtotal), line.bill_date, line.name)
                        inbound_payment_transactions.append(inbound_payment_transaction)
                else:
                    account_id = self.env['account.account'].search(
                        [('ezee_account_name', '=', line.name), ('company_id', '=', self.env.company.id)], limit=1)
                    if not account_id:
                        raise ValidationError(_('You must define account of type "%s"' % line.name))
                    else:
                        aml_groupby_account = (account_id, abs(line.amount_subtotal), line.bill_date, line.name)
                        aml_groupby_accounts.append(aml_groupby_account)

                line.invoiced = True

            # city ledger payment
            for journal, amount, date, name in credit_aml_payment_transactions:
                payment_method = journal.inbound_payment_method_line_ids
                res_partner_obj = self.env['res.partner'].search([('name', '=', line.source_name)])
                if not res_partner_obj:
                    res_partner_obj = self.env['res.partner'].create({
                        'name': line.source_name,
                        'company_type': 'company'
                    })
                ledger_invoice_journal_id = self.env['account.journal'].search(
                    [('type', '=', 'bank'), ('name', '=', 'City Ledger')], limit=1)
                credit_invoice_line_vals = [(0, 0, {
                    'name': journal.default_account_id.name,
                    'account_id': journal.default_account_id.id,
                    'quantity': 1,
                    'price_unit': amount
                })]
                payment_id = rec.env['account.payment'].with_context(
                    default_invoice_ids=[(4, self.ledger_move_id.id)]).create({
                    'payment_type': 'inbound',
                    'partner_id': rec.partner_id.id,
                    'journal_id': journal.id,
                    'amount': amount,
                    'payment_method_line_id': payment_method[0].id if payment_method else False,
                    # 'date': self.detail_line_ids.filtered(lambda l: l.bill_date).mapped('bill_date')[-1].date(),
                    'date': date,
                    'folio_id': self.ledger_move_id.folio_id.id,
                    'htask_payment_type': name
                })
                payment_id.action_post()

            # create inbound payment
            for journal, amount, date, name in inbound_payment_transactions:
                inbound_payment_method = journal.inbound_payment_method_line_ids
                payment_id = rec.env['account.payment'].with_context(
                    default_invoice_ids=[(4, self.account_move_id.id)]).create({
                    'payment_type': 'inbound',
                    'partner_id': rec.partner_id.id,
                    'journal_id': journal.id,
                    'amount': amount,
                    'payment_method_line_id': inbound_payment_method[0].id if inbound_payment_method else False,
                    'date': date,
                    'folio_id': self.account_move_id.folio_id.id,
                    'htask_payment_type': name
                })
                payment_id.action_post()

                # create outbound payment
                for journal, amount, date, name in outbound_payment_transactions:
                    outbound_payment_method = journal.outbound_payment_method_line_ids
                    payment_id = self.env['account.payment'].with_context(
                        default_invoice_ids=[(4, self.account_move_id.id)]).create(
                        {
                            'payment_type': 'outbound',
                            'partner_id': rec.partner_id.id,
                            'journal_id': journal.id,
                            'amount': amount,
                            'payment_method_line_id': outbound_payment_method[
                                0].id if outbound_payment_method else False,
                            'date': date,
                            'folio_id': self.account_move_id.folio_id.id,
                            'htask_payment_type': name
                        })
                    payment_id.action_post()

    def update_htask_payment(self):
        for record in self:
            if record.account_move_id:
                record.account_move_id.folio_id = record.id
                for line in record.account_move_id.invoice_line_ids:
                    line.folio_id = record.id

    def action_invoiced(self):
        for record in self:
            if record.detail_line_ids:
                for line in record.detail_line_ids:
                    line.invoiced = False

    def update_invoice_date(self):
        for record in self:
            record.account_move_id.invoice_date = record.checkout_date
            record.account_move_id.invoice_date_due = record.checkout_date

    @api.depends("checkout_date", "checkin_date")
    def _compute_duration(self):
        """
        This method gives the duration between check in and checkout
        if customer will leave only for some hour it would be considers
        as a whole day.If customer will check in checkout for more or equal
        hours, which configured in company as additional hours than it would
        be consider as full days
        --------------------------------------------------------------------
        @param self: object pointer
        @return: Duration and checkout_date
        """
        for rec in self:
            myduration = 0
            if rec.checkout_date and rec.checkin_date:
                dur = rec.checkout_date - rec.checkin_date
                myduration = dur.days
            rec.duration = myduration

    @api.depends('room_line_ids.amount_subtotal')
    def _compute_amount(self):
        for rec in self:
            rec.amount_total = sum(rec.room_line_ids.mapped(lambda l: l.amount_subtotal))

    @api.depends('detail_line_ids.amount_subtotal')
    def _compute_detail_total(self):
        for rec in self:
            lines = rec.detail_line_ids
            rec.detail_total_paid = abs(sum(lines.filtered(lambda r: r.is_payment).mapped(lambda l: l.amount_subtotal)))
            rec.detail_amount_total = sum(
                lines.filtered(lambda r: not r.is_payment).mapped(lambda l: l.amount_subtotal))
            rec.due_amount = sum(lines.mapped(lambda l: l.amount_subtotal))

    def action_view_partner_invoice(self):
        move_id = self.env['account.move'].search([('folio_id', '=', self.id), ('move_type', '=', 'out_invoice')])[-1]
        if not move_id:
            return False
        return {
            'name': _('Customer Invoice'),
            'view_mode': 'form',
            'view_id': self.env.ref('account.view_move_form').id,
            'res_model': 'account.move',
            'context': "{'move_type':'out_invoice'}",
            'type': 'ir.actions.act_window',
            'res_id': move_id.id
        }


class HotelFolioLine(models.Model):
    _name = "hotel.folio.line"
    _description = "Hotel Folio Room Line"

    @api.model
    def _get_checkin_date(self):
        if "checkin" in self._context:
            return self._context["checkin"]
        return time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

    @api.model
    def _get_checkout_date(self):
        if "checkout" in self._context:
            return self._context["checkout"]
        return time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

    move_id = fields.Many2one(
        "account.move",
        "Move",
        required=True,
        delegate=True,
        ondelete="cascade",
    )
    amount_subtotal = fields.Monetary(string='Subtotal', related="move_id.amount_total", store=True)
    folio_id = fields.Many2one("hotel.folio", "Folio", ondelete="cascade")
    room_no = fields.Char(string='Room No.', related="move_id.room_no", store=True)
    room_type = fields.Char(string='Room Type', related="move_id.room_type", store=True)
    rate_type = fields.Char(string='Rate Type', related="move_id.rate_type", store=True)
    market_code = fields.Char(string='Market Code', related="move_id.market_code", store=True)
    currency_id = fields.Many2one('res.currency', readonly=True, tracking=True, string='Currency',
                                  default=lambda self: self.env.user.company_id.currency_id)

    checkin_date = fields.Datetime(
        "Check In",  # required=True#, default=_get_checkin_date
    )
    checkout_date = fields.Datetime(
        "Check Out",  # required=True#, default=_get_checkout_date
    )

    @api.constrains("checkin_date", "checkout_date")
    def check_dates(self):
        """
        This method is used to validate the checkin_date and checkout_date.
        -------------------------------------------------------------------
        @param self: object pointer
        @return: raise warning depending on the validation
        """
        if self.checkin_date > self.checkout_date:
            raise ValidationError(
                _(
                    """Room line Check In Date Should be """
                    """less than the Check Out Date!"""
                    """ %s === %s """
                ) % (self.checkin_date, self.checkout_date)
            )


class HotelFolioDetail(models.Model):
    _name = "hotel.folio.detail"
    _description = "Hotel Folio Detail Line"

    name = fields.Char(string='Particular')
    unique_id = fields.Char(string='Unique ID')
    type = fields.Char(string='Type')
    qty = fields.Float(string='Qty')
    folio_id = fields.Many2one("hotel.folio", "Folio", ondelete="cascade")
    source_name = fields.Char(string='Source', related='folio_id.source_name')
    currency_id = fields.Many2one('res.currency', readonly=True, tracking=True, string='Currency',
                                  default=lambda self: self.env.user.company_id.currency_id)
    amount_subtotal = fields.Monetary(string='Subtotal')
    ref_no = fields.Char(string='Reference No.')
    bill_date = fields.Datetime("Date", readonly=False)
    is_payment = fields.Boolean(string='Payment')
    is_city_payment = fields.Boolean(string='City Ledger Payment')
    branch_id = fields.Many2one('res.branch')
    unmapped = fields.Boolean()
    invoiced = fields.Boolean()

    def action_generate_entry(self):
        date = self[0].bill_date.date()
        if any(line.bill_date.date() != date for line in self):
            raise ValidationError(_('All lines must be in the same date.'))

        partner_id = self.env['res.partner'].search([('is_hotel_customer', '=', True)], limit=1)
        if not partner_id:
            raise ValidationError(_('You must define hotel customer firstly.'))

        inbound_payment_transaction = {}
        outbound_payment_transaction = {}
        aml_groupby_account = {}
        credit_aml_groupby_journal = {}
        for line in self.filtered(lambda l: not l.invoiced and l.amount_subtotal != 0.0):
            if line.is_payment or 'Refund' in line.name:
                name = line.name
                if 'Refund' in line.name:
                    name = line.name.replace(' [Refund]', '')

                journal_domain = [('ezee_journal_type', '=', name), ('company_id', '=', self.env.company.id)]
                if line.is_city_payment:
                    journal_domain += [('type', 'in', ['cash', 'bank'])]
                elif 'City' in line.type:
                    journal_domain += [('type', '=', 'sale')]

                journal_id = self.env['account.journal'].search(journal_domain, limit=1)
                if not journal_id:
                    raise ValidationError(_('You must define journal of type "%s"' % name))

                if 'City' in line.type and not line.is_city_payment:
                    if journal_id in credit_aml_groupby_journal:
                        credit_aml_groupby_journal[journal_id] += abs(line.amount_subtotal)
                    else:
                        credit_aml_groupby_journal[journal_id] = abs(line.amount_subtotal)

                elif line.amount_subtotal > 0.0:
                    if journal_id in outbound_payment_transaction:
                        outbound_payment_transaction[journal_id] += abs(line.amount_subtotal)
                    else:
                        outbound_payment_transaction[journal_id] = abs(line.amount_subtotal)
                else:
                    if journal_id in inbound_payment_transaction:
                        inbound_payment_transaction[journal_id] += abs(line.amount_subtotal)
                    else:
                        inbound_payment_transaction[journal_id] = abs(line.amount_subtotal)

            else:
                account_id = self.env['account.account'].search(
                    [('ezee_account_name', '=', line.name), ('company_id', '=', self.env.company.id)], limit=1)
                if not account_id:
                    raise ValidationError(_('You must define account of type "%s"' % line.name))

                if account_id in aml_groupby_account:
                    aml_groupby_account[account_id] += abs(line.amount_subtotal)
                else:
                    aml_groupby_account[account_id] = abs(line.amount_subtotal)

            line.invoiced = True

        # create invoices
        invoice_line_vals = []
        for account, amount in aml_groupby_account.items():
            invoice_line_vals.append((0, 0, {
                'name': account.name,
                'account_id': account.id,
                'quantity': 1,
                'price_unit': amount
            }))

        move_id = self.env['account.move']
        if invoice_line_vals:
            customer_invoice_journal_id = self.env['account.journal'].search(
                [('type', '=', 'sale'), ('company_id', '=', self.env.company.id)], limit=1)
            move_id = self.env['account.move'].create({
                'move_type': 'out_invoice',
                'is_htask_move': True,
                'partner_id': partner_id.id,
                'journal_id': customer_invoice_journal_id.id,
                'invoice_date': date
            })
            move_id.invoice_line_ids = invoice_line_vals
            move_id.action_post()

        # create city ledger invoice
        for journal, amount in credit_aml_groupby_journal.items():
            city_ledger_partner_id = self.env['res.partner'].search([('is_city_ledger_customer', '=', True)], limit=1)
            if not city_ledger_partner_id:
                raise ValidationError(_('You must define city ledger customer firstly.'))

            if journal.type != 'sale':
                raise ValidationError(_('Journal %s must be of type sales.' % journal.name))

            credit_invoice_line_vals = [(0, 0, {
                'name': journal.default_account_id.name,
                'account_id': journal.default_account_id.id,
                'quantity': 1,
                'price_unit': amount
            })]
            move_id = self.env['account.move'].create({
                'move_type': 'out_invoice',
                'is_htask_move': True,
                'partner_id': city_ledger_partner_id.id,
                'journal_id': journal.id,
                'invoice_date': date
            })
            move_id.invoice_line_ids = credit_invoice_line_vals
            move_id.action_post()

        # create inbound payment
        for journal, amount in inbound_payment_transaction.items():
            inbound_payment_method = journal.inbound_payment_method_line_ids
            partner_id = self.env['res.partner'].search([('is_hotel_customer', '=', True)], limit=1)
            if journal.is_credit_payment:
                partner_id = self.env['res.partner'].search([('is_city_ledger_customer', '=', True)], limit=1)

            payment_id = self.env['account.payment'].with_context(default_invoice_ids=[(4, move_id.id)]).create({
                'payment_type': 'inbound',
                'partner_id': partner_id.id,
                'journal_id': journal.id,
                'amount': amount,
                'payment_method_line_id': inbound_payment_method[0].id if inbound_payment_method else False,
                'date': date
            })
            payment_id.action_post()

        # create outbound payment
        for journal, amount in outbound_payment_transaction.items():
            outbound_payment_method = journal.outbound_payment_method_line_ids
            partner_id = self.env['res.partner'].search([('is_hotel_customer', '=', True)], limit=1)
            if journal.is_credit_payment:
                partner_id = self.env['res.partner'].search([('is_city_ledger_customer', '=', True)], limit=1)

            payment_id = self.env['account.payment'].with_context(default_invoice_ids=[(4, move_id.id)]).create({
                'payment_type': 'outbound',
                'partner_id': partner_id.id,
                'journal_id': journal.id,
                'amount': amount,
                'payment_method_line_id': outbound_payment_method[0].id if outbound_payment_method else False,
                'date': date
            })
            payment_id.action_post()

    def unlink(self):
        if not self.env.context.get('force_delete', False):
            for line in self:
                if line.amount_subtotal != 0.0:
                    raise ValidationError(_('Unable to delete record has amount.'))

        return super().unlink()
