from odoo import fields, models, api, tools, _
from odoo.exceptions import AccessError, UserError, ValidationError
from collections import defaultdict
from odoo.tools import float_is_zero, float_compare
import psycopg2
import logging
logger = logging.getLogger(__name__)
import traceback

class PosOrder(models.Model):
    _inherit = 'pos.order'

    posted_guest_folio = fields.Boolean(string='Posted To Guest Folio', default=False)


    @api.model
    def _process_order(self, order, draft, existing_order):
        """Create or update an pos.order from a given dictionary.

        :param dict order: dictionary representing the order.
        :param bool draft: Indicate that the pos_order is not validated yet.
        :param existing_order: order to be updated or False.
        :type existing_order: pos.order.
        :returns: id of created/updated pos.order
        :rtype: int
        """
        order = order['data']
        pos_session = self.env['pos.session'].browse(order['pos_session_id'])
        if pos_session.state == 'closing_control' or pos_session.state == 'closed':
            order['pos_session_id'] = self._get_valid_session(order).id

        pos_order = False
        if not existing_order:
            pos_order = self.create(self._order_fields(order))
        else:
            pos_order = existing_order
            pos_order.lines.unlink()
            order['user_id'] = pos_order.user_id.id
            pos_order.write(self._order_fields(order))

        pos_order = pos_order.with_company(pos_order.company_id)
        self = self.with_company(pos_order.company_id)
        self._process_payment_lines(order, pos_order, pos_session, draft)

        if not draft:
            try:
                pos_order.action_pos_order_paid()
            except psycopg2.DatabaseError:
                # do not hide transactional errors, the order(s) won't be saved!
                raise
            except Exception as e:
                logger.error('Could not fully process the POS Order: %s', tools.ustr(e))
            pos_order._create_order_picking()
            pos_order._compute_total_cost_in_real_time()

        if pos_order.to_invoice and pos_order.state == 'paid':
            not_need_invoice = any(pos_order.payment_ids.mapped('payment_method_id').mapped('posted_guest_folio'))
            logger.info(f'not_need_invoice {not_need_invoice}-- order {pos_order}')
            if not not_need_invoice:
                pos_order._generate_pos_order_invoice()

        return pos_order.id

class PosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    posted_guest_folio = fields.Boolean(string='Posted To Guest Folio', default=False)


class PosSession(models.Model):
    _inherit = 'pos.session'

    # def _accumulate_amounts(self, data):
    #     # Accumulate the amounts for each accounting lines group
    #     # Each dict maps `key` -> `amounts`, where `key` is the group key.
    #     # E.g. `combine_receivables_bank` is derived from pos.payment records
    #     # in the self.order_ids with group key of the `payment_method_id`
    #     # field of the pos.payment record.
    #     amounts = lambda: {'amount': 0.0, 'amount_converted': 0.0}
    #     tax_amounts = lambda: {'amount': 0.0, 'amount_converted': 0.0, 'base_amount': 0.0, 'base_amount_converted': 0.0}
    #     split_receivables_bank = defaultdict(amounts)
    #     split_receivables_cash = defaultdict(amounts)
    #     split_receivables_pay_later = defaultdict(amounts)
    #     combine_receivables_bank = defaultdict(amounts)
    #     combine_receivables_cash = defaultdict(amounts)
    #     combine_receivables_pay_later = defaultdict(amounts)
    #     combine_invoice_receivables = defaultdict(amounts)
    #     split_invoice_receivables = defaultdict(amounts)
    #     sales = defaultdict(amounts)
    #     taxes = defaultdict(tax_amounts)
    #     stock_expense = defaultdict(amounts)
    #     stock_return = defaultdict(amounts)
    #     stock_output = defaultdict(amounts)
    #     rounding_difference = {'amount': 0.0, 'amount_converted': 0.0}
    #     # Track the receivable lines of the order's invoice payment moves for reconciliation
    #     # These receivable lines are reconciled to the corresponding invoice receivable lines
    #     # of this session's move_id.
    #     combine_inv_payment_receivable_lines = defaultdict(lambda: self.env['account.move.line'])
    #     split_inv_payment_receivable_lines = defaultdict(lambda: self.env['account.move.line'])
    #     rounded_globally = self.company_id.tax_calculation_rounding_method == 'round_globally'
    #     pos_receivable_account = self.company_id.account_default_pos_receivable_account_id
    #     currency_rounding = self.currency_id.rounding
    #     logger.info(f'order_ids {self.order_ids}')
    #     logger.info(f"order_ids {self.order_ids.filtered(lambda o: o.state != 'cancel')}")
    #     logger.info(f'order_ids {self.order_ids.filtered(lambda o: not o.posted_guest_folio)}')
    #     for order in self.order_ids.filtered(lambda o: not o.posted_guest_folio):
    #         order_is_invoiced = order.is_invoiced
    #         for payment in order.payment_ids:
    #             amount = payment.amount
    #             if float_is_zero(amount, precision_rounding=currency_rounding):
    #                 continue
    #             date = payment.payment_date
    #             payment_method = payment.payment_method_id
    #             is_split_payment = payment.payment_method_id.split_transactions
    #             payment_type = payment_method.type
    #
    #             # If not pay_later, we create the receivable vals for both invoiced and uninvoiced orders.
    #             #   Separate the split and aggregated payments.
    #             # Moreover, if the order is invoiced, we create the pos receivable vals that will balance the
    #             # pos receivable lines from the invoice payments.
    #             if payment_type != 'pay_later':
    #                 if is_split_payment and payment_type == 'cash':
    #                     split_receivables_cash[payment] = self._update_amounts(split_receivables_cash[payment], {'amount': amount}, date)
    #                 elif not is_split_payment and payment_type == 'cash':
    #                     combine_receivables_cash[payment_method] = self._update_amounts(combine_receivables_cash[payment_method], {'amount': amount}, date)
    #                 elif is_split_payment and payment_type == 'bank':
    #                     split_receivables_bank[payment] = self._update_amounts(split_receivables_bank[payment], {'amount': amount}, date)
    #                 elif not is_split_payment and payment_type == 'bank':
    #                     combine_receivables_bank[payment_method] = self._update_amounts(combine_receivables_bank[payment_method], {'amount': amount}, date)
    #
    #                 # Create the vals to create the pos receivables that will balance the pos receivables from invoice payment moves.
    #                 if order_is_invoiced:
    #                     if is_split_payment:
    #                         split_inv_payment_receivable_lines[payment] |= payment.account_move_id.line_ids.filtered(lambda line: line.account_id == pos_receivable_account)
    #                         split_invoice_receivables[payment] = self._update_amounts(split_invoice_receivables[payment], {'amount': payment.amount}, order.date_order)
    #                     else:
    #                         combine_inv_payment_receivable_lines[payment_method] |= payment.account_move_id.line_ids.filtered(lambda line: line.account_id == pos_receivable_account)
    #                         combine_invoice_receivables[payment_method] = self._update_amounts(combine_invoice_receivables[payment_method], {'amount': payment.amount}, order.date_order)
    #
    #             # If pay_later, we create the receivable lines.
    #             #   if split, with partner
    #             #   Otherwise, it's aggregated (combined)
    #             # But only do if order is *not* invoiced because no account move is created for pay later invoice payments.
    #             if payment_type == 'pay_later' and not order_is_invoiced:
    #                 if is_split_payment:
    #                     split_receivables_pay_later[payment] = self._update_amounts(split_receivables_pay_later[payment], {'amount': amount}, date)
    #                 elif not is_split_payment:
    #                     combine_receivables_pay_later[payment_method] = self._update_amounts(combine_receivables_pay_later[payment_method], {'amount': amount}, date)
    #
    #         if not order_is_invoiced:
    #             order_taxes = defaultdict(tax_amounts)
    #             for order_line in order.lines:
    #                 line = self._prepare_line(order_line)
    #                 # Combine sales/refund lines
    #                 sale_key = (
    #                     # account
    #                     line['income_account_id'],
    #                     # sign
    #                     -1 if line['amount'] < 0 else 1,
    #                     # for taxes
    #                     tuple((tax['id'], tax['account_id'], tax['tax_repartition_line_id']) for tax in line['taxes']),
    #                     line['base_tags'],
    #                 )
    #                 sales[sale_key] = self._update_amounts(sales[sale_key], {'amount': line['amount']}, line['date_order'])
    #                 # Combine tax lines
    #                 for tax in line['taxes']:
    #                     tax_key = (tax['account_id'] or line['income_account_id'], tax['tax_repartition_line_id'], tax['id'], tuple(tax['tag_ids']))
    #                     order_taxes[tax_key] = self._update_amounts(
    #                         order_taxes[tax_key],
    #                         {'amount': tax['amount'], 'base_amount': tax['base']},
    #                         tax['date_order'],
    #                         round=not rounded_globally
    #                     )
    #             for tax_key, amounts in order_taxes.items():
    #                 if rounded_globally:
    #                     amounts = self._round_amounts(amounts)
    #                 for amount_key, amount in amounts.items():
    #                     taxes[tax_key][amount_key] += amount
    #
    #             if self.company_id.anglo_saxon_accounting and order.picking_ids.ids:
    #                 # Combine stock lines
    #                 stock_moves = self.env['stock.move'].sudo().search([
    #                     ('picking_id', 'in', order.picking_ids.ids),
    #                     ('company_id.anglo_saxon_accounting', '=', True),
    #                     ('product_id.categ_id.property_valuation', '=', 'real_time')
    #                 ])
    #                 for move in stock_moves:
    #                     exp_key = move.product_id._get_product_accounts()['expense']
    #                     out_key = move.product_id.categ_id.property_stock_account_output_categ_id
    #                     amount = -sum(move.sudo().stock_valuation_layer_ids.mapped('value'))
    #                     stock_expense[exp_key] = self._update_amounts(stock_expense[exp_key], {'amount': amount}, move.picking_id.date, force_company_currency=True)
    #                     if move.location_id.usage == 'customer':
    #                         stock_return[out_key] = self._update_amounts(stock_return[out_key], {'amount': amount}, move.picking_id.date, force_company_currency=True)
    #                     else:
    #                         stock_output[out_key] = self._update_amounts(stock_output[out_key], {'amount': amount}, move.picking_id.date, force_company_currency=True)
    #
    #             if self.config_id.cash_rounding:
    #                 diff = order.amount_paid - order.amount_total
    #                 rounding_difference = self._update_amounts(rounding_difference, {'amount': diff}, order.date_order)
    #
    #             # Increasing current partner's customer_rank
    #             partners = (order.partner_id | order.partner_id.commercial_partner_id)
    #             partners._increase_rank('customer_rank')
    #
    #     if self.company_id.anglo_saxon_accounting:
    #         global_session_pickings = self.picking_ids.filtered(lambda p: not p.pos_order_id)
    #         if global_session_pickings:
    #             stock_moves = self.env['stock.move'].sudo().search([
    #                 ('picking_id', 'in', global_session_pickings.ids),
    #                 ('company_id.anglo_saxon_accounting', '=', True),
    #                 ('product_id.categ_id.property_valuation', '=', 'real_time'),
    #             ])
    #             for move in stock_moves:
    #                 exp_key = move.product_id._get_product_accounts()['expense']
    #                 out_key = move.product_id.categ_id.property_stock_account_output_categ_id
    #                 amount = -sum(move.stock_valuation_layer_ids.mapped('value'))
    #                 stock_expense[exp_key] = self._update_amounts(stock_expense[exp_key], {'amount': amount}, move.picking_id.date, force_company_currency=True)
    #                 if move.location_id.usage == 'customer':
    #                     stock_return[out_key] = self._update_amounts(stock_return[out_key], {'amount': amount}, move.picking_id.date, force_company_currency=True)
    #                 else:
    #                     stock_output[out_key] = self._update_amounts(stock_output[out_key], {'amount': amount}, move.picking_id.date, force_company_currency=True)
    #     MoveLine = self.env['account.move.line'].with_context(check_move_validity=False)
    #
    #     data.update({
    #         'taxes':                               taxes,
    #         'sales':                               sales,
    #         'stock_expense':                       stock_expense,
    #         'split_receivables_bank':              split_receivables_bank,
    #         'combine_receivables_bank':            combine_receivables_bank,
    #         'split_receivables_cash':              split_receivables_cash,
    #         'combine_receivables_cash':            combine_receivables_cash,
    #         'combine_invoice_receivables':         combine_invoice_receivables,
    #         'split_receivables_pay_later':         split_receivables_pay_later,
    #         'combine_receivables_pay_later':       combine_receivables_pay_later,
    #         'stock_return':                        stock_return,
    #         'stock_output':                        stock_output,
    #         'combine_inv_payment_receivable_lines': combine_inv_payment_receivable_lines,
    #         'rounding_difference':                 rounding_difference,
    #         'MoveLine':                            MoveLine,
    #         'split_invoice_receivables': split_invoice_receivables,
    #         'split_inv_payment_receivable_lines': split_inv_payment_receivable_lines,
    #     })
    #     return data


    def _accumulate_amounts(self, data):
        # Accumulate the amounts for each accounting lines group
        # Each dict maps `key` -> `amounts`, where `key` is the group key.
        # E.g. `combine_receivables_bank` is derived from pos.payment records
        # in the self.order_ids with group key of the `payment_method_id`
        # field of the pos.payment record.
        amounts = lambda: {'amount': 0.0, 'amount_converted': 0.0}
        tax_amounts = lambda: {'amount': 0.0, 'amount_converted': 0.0, 'base_amount': 0.0, 'base_amount_converted': 0.0}
        split_receivables_bank = defaultdict(amounts)
        split_receivables_cash = defaultdict(amounts)
        split_receivables_pay_later = defaultdict(amounts)
        combine_receivables_bank = defaultdict(amounts)
        combine_receivables_cash = defaultdict(amounts)
        combine_receivables_pay_later = defaultdict(amounts)
        combine_invoice_receivables = defaultdict(amounts)
        split_invoice_receivables = defaultdict(amounts)
        sales = defaultdict(amounts)
        taxes = defaultdict(tax_amounts)
        stock_expense = defaultdict(amounts)
        stock_return = defaultdict(amounts)
        stock_output = defaultdict(amounts)
        rounding_difference = {'amount': 0.0, 'amount_converted': 0.0}
        # Track the receivable lines of the order's invoice payment moves for reconciliation
        # These receivable lines are reconciled to the corresponding invoice receivable lines
        # of this session's move_id.
        combine_inv_payment_receivable_lines = defaultdict(lambda: self.env['account.move.line'])
        split_inv_payment_receivable_lines = defaultdict(lambda: self.env['account.move.line'])
        rounded_globally = self.company_id.tax_calculation_rounding_method == 'round_globally'
        pos_receivable_account = self.company_id.account_default_pos_receivable_account_id
        currency_rounding = self.currency_id.rounding
        for order in self.order_ids.filtered(lambda o: not o.posted_guest_folio):
            order_is_invoiced = order.is_invoiced
            for payment in order.payment_ids:
                amount = payment.amount
                if float_is_zero(amount, precision_rounding=currency_rounding):
                    continue
                date = payment.payment_date
                payment_method = payment.payment_method_id
                is_split_payment = payment.payment_method_id.split_transactions
                payment_type = payment_method.type

                # If not pay_later, we create the receivable vals for both invoiced and uninvoiced orders.
                #   Separate the split and aggregated payments.
                # Moreover, if the order is invoiced, we create the pos receivable vals that will balance the
                # pos receivable lines from the invoice payments.
                if payment_type != 'pay_later':
                    if is_split_payment and payment_type == 'cash':
                        split_receivables_cash[payment] = self._update_amounts(split_receivables_cash[payment], {'amount': amount}, date)
                    elif not is_split_payment and payment_type == 'cash':
                        combine_receivables_cash[payment_method] = self._update_amounts(combine_receivables_cash[payment_method], {'amount': amount}, date)
                    elif is_split_payment and payment_type == 'bank':
                        split_receivables_bank[payment] = self._update_amounts(split_receivables_bank[payment], {'amount': amount}, date)
                    elif not is_split_payment and payment_type == 'bank':
                        combine_receivables_bank[payment_method] = self._update_amounts(combine_receivables_bank[payment_method], {'amount': amount}, date)

                    # Create the vals to create the pos receivables that will balance the pos receivables from invoice payment moves.
                    if order_is_invoiced:
                        if is_split_payment:
                            split_inv_payment_receivable_lines[payment] |= payment.account_move_id.line_ids.filtered(lambda line: line.account_id == pos_receivable_account)
                            split_invoice_receivables[payment] = self._update_amounts(split_invoice_receivables[payment], {'amount': payment.amount}, order.date_order)
                        else:
                            combine_inv_payment_receivable_lines[payment_method] |= payment.account_move_id.line_ids.filtered(lambda line: line.account_id == pos_receivable_account)
                            combine_invoice_receivables[payment_method] = self._update_amounts(combine_invoice_receivables[payment_method], {'amount': payment.amount}, order.date_order)

                # If pay_later, we create the receivable lines.
                #   if split, with partner
                #   Otherwise, it's aggregated (combined)
                # But only do if order is *not* invoiced because no account move is created for pay later invoice payments.
                if payment_type == 'pay_later' and not order_is_invoiced:
                    if is_split_payment:
                        split_receivables_pay_later[payment] = self._update_amounts(split_receivables_pay_later[payment], {'amount': amount}, date)
                    elif not is_split_payment:
                        combine_receivables_pay_later[payment_method] = self._update_amounts(combine_receivables_pay_later[payment_method], {'amount': amount}, date)

            if not order_is_invoiced:
                order_taxes = defaultdict(tax_amounts)
                for order_line in order.lines:
                    line = self._prepare_line(order_line)
                    # Combine sales/refund lines
                    sale_key = (
                        # account
                        line['income_account_id'],
                        # sign
                        -1 if line['amount'] < 0 else 1,
                        # for taxes
                        tuple((tax['id'], tax['account_id'], tax['tax_repartition_line_id']) for tax in line['taxes']),
                        line['base_tags'],
                    )
                    sales[sale_key] = self._update_amounts(sales[sale_key], {'amount': line['amount']}, line['date_order'])
                    sales[sale_key].setdefault('tax_amount', 0.0)
                    # Combine tax lines
                    for tax in line['taxes']:
                        tax_key = (tax['account_id'] or line['income_account_id'], tax['tax_repartition_line_id'], tax['id'], tuple(tax['tag_ids']))
                        sales[sale_key]['tax_amount'] += tax['amount']
                        order_taxes[tax_key] = self._update_amounts(
                            order_taxes[tax_key],
                            {'amount': tax['amount'], 'base_amount': tax['base']},
                            tax['date_order'],
                            round=not rounded_globally
                        )
                for tax_key, amounts in order_taxes.items():
                    if rounded_globally:
                        amounts = self._round_amounts(amounts)
                    for amount_key, amount in amounts.items():
                        taxes[tax_key][amount_key] += amount

                if self.company_id.anglo_saxon_accounting and order.picking_ids.ids:
                    # Combine stock lines
                    stock_moves = self.env['stock.move'].sudo().search([
                        ('picking_id', 'in', order.picking_ids.ids),
                        ('company_id.anglo_saxon_accounting', '=', True),
                        ('product_id.categ_id.property_valuation', '=', 'real_time')
                    ])
                    for move in stock_moves:
                        exp_key = move.product_id._get_product_accounts()['expense']
                        out_key = move.product_id.categ_id.property_stock_account_output_categ_id
                        signed_product_qty = move.product_qty
                        if move._is_in():
                            signed_product_qty *= -1
                        amount = signed_product_qty * move.product_id._compute_average_price(0, move.quantity_done, move)
                        stock_expense[exp_key] = self._update_amounts(stock_expense[exp_key], {'amount': amount}, move.picking_id.date, force_company_currency=True)
                        if move._is_in():
                            stock_return[out_key] = self._update_amounts(stock_return[out_key], {'amount': amount}, move.picking_id.date, force_company_currency=True)
                        else:
                            stock_output[out_key] = self._update_amounts(stock_output[out_key], {'amount': amount}, move.picking_id.date, force_company_currency=True)

                if self.config_id.cash_rounding:
                    diff = order.amount_paid - order.amount_total
                    rounding_difference = self._update_amounts(rounding_difference, {'amount': diff}, order.date_order)

                # Increasing current partner's customer_rank
                partners = (order.partner_id | order.partner_id.commercial_partner_id)
                partners._increase_rank('customer_rank')

        if self.company_id.anglo_saxon_accounting:
            global_session_pickings = self.picking_ids.filtered(lambda p: not p.pos_order_id)
            if global_session_pickings:
                stock_moves = self.env['stock.move'].sudo().search([
                    ('picking_id', 'in', global_session_pickings.ids),
                    ('company_id.anglo_saxon_accounting', '=', True),
                    ('product_id.categ_id.property_valuation', '=', 'real_time'),
                ])
                for move in stock_moves:
                    exp_key = move.product_id._get_product_accounts()['expense']
                    out_key = move.product_id.categ_id.property_stock_account_output_categ_id
                    signed_product_qty = move.product_qty
                    if move._is_in():
                        signed_product_qty *= -1
                    amount = signed_product_qty * move.product_id._compute_average_price(0, move.quantity_done, move)
                    stock_expense[exp_key] = self._update_amounts(stock_expense[exp_key], {'amount': amount}, move.picking_id.date, force_company_currency=True)
                    if move._is_in():
                        stock_return[out_key] = self._update_amounts(stock_return[out_key], {'amount': amount}, move.picking_id.date, force_company_currency=True)
                    else:
                        stock_output[out_key] = self._update_amounts(stock_output[out_key], {'amount': amount}, move.picking_id.date, force_company_currency=True)
        MoveLine = self.env['account.move.line'].with_context(check_move_validity=False)

        data.update({
            'taxes':                               taxes,
            'sales':                               sales,
            'stock_expense':                       stock_expense,
            'split_receivables_bank':              split_receivables_bank,
            'combine_receivables_bank':            combine_receivables_bank,
            'split_receivables_cash':              split_receivables_cash,
            'combine_receivables_cash':            combine_receivables_cash,
            'combine_invoice_receivables':         combine_invoice_receivables,
            'split_receivables_pay_later':         split_receivables_pay_later,
            'combine_receivables_pay_later':       combine_receivables_pay_later,
            'stock_return':                        stock_return,
            'stock_output':                        stock_output,
            'combine_inv_payment_receivable_lines': combine_inv_payment_receivable_lines,
            'rounding_difference':                 rounding_difference,
            'MoveLine':                            MoveLine,
            'split_invoice_receivables': split_invoice_receivables,
            'split_inv_payment_receivable_lines': split_inv_payment_receivable_lines,
        })
        return data

    def action_pos_session_closing_control(self, balancing_account=False, amount_to_balance=0, bank_payment_method_diffs=None):
        print('inherit called {amount_to_balance}', amount_to_balance)
        for session in self:
            logger.info(f'closing control {balancing_account} {amount_to_balance} {bank_payment_method_diffs}')
            guest_folio_orders = session.order_ids.filtered(
                lambda o: any(p.payment_method_id.posted_guest_folio for p in o.payment_ids)
            )
            print('guest_folio_orders',guest_folio_orders)
            if guest_folio_orders:
                for order in guest_folio_orders:
                    order.payment_ids.unlink()
                    order.write({"state": "cancel", "amount_paid": 0.0, "posted_guest_folio": True})

            return super().action_pos_session_closing_control(balancing_account, amount_to_balance, bank_payment_method_diffs)



