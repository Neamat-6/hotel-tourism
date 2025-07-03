from odoo import fields, models, api, _
from odoo.tools import float_is_zero, float_compare


class PosSession(models.Model):
    _inherit = 'pos.session'

    def _create_combine_account_payment(self, payment_method, amounts, diff_amount):
        if not payment_method.use_for_room_charge:
            outstanding_account = payment_method.outstanding_account_id or self.company_id.account_journal_payment_debit_account_id
            destination_account = self._get_receivable_account(payment_method)

            if float_compare(amounts['amount'], 0, precision_rounding=self.currency_id.rounding) < 0:
                # revert the accounts because account.payment doesn't accept negative amount.
                outstanding_account, destination_account = destination_account, outstanding_account

            account_payment = self.env['account.payment'].create({
                'amount': abs(amounts['amount']),
                'journal_id': payment_method.journal_id.id,
                'force_outstanding_account_id': outstanding_account.id,
                'destination_account_id':  destination_account.id,
                'ref': _('Combine %s POS payments from %s') % (payment_method.name, self.name),
                'pos_payment_method_id': payment_method.id,
                'pos_session_id': self.id,
            })

            diff_amount_compare_to_zero = self.currency_id.compare_amounts(diff_amount, 0)
            if diff_amount_compare_to_zero != 0:
                self._apply_diff_on_account_payment_move(account_payment, payment_method, diff_amount)

            account_payment.action_post()
            return account_payment.move_id.line_ids.filtered(lambda line: line.account_id == account_payment.destination_account_id)
        else:
            return self.env['account.move.line']


    def _create_split_account_payment(self, payment, amounts):
        payment_method = payment.payment_method_id
        if not payment_method.journal_id or payment_method.use_for_room_charge:
            return self.env['account.move.line']
        outstanding_account = payment_method.outstanding_account_id or self.company_id.account_journal_payment_debit_account_id
        accounting_partner = self.env["res.partner"]._find_accounting_partner(payment.partner_id)
        destination_account = accounting_partner.property_account_receivable_id

        if float_compare(amounts['amount'], 0, precision_rounding=self.currency_id.rounding) < 0:
            # revert the accounts because account.payment doesn't accept negative amount.
            outstanding_account, destination_account = destination_account, outstanding_account

        account_payment = self.env['account.payment'].create({
            'amount': abs(amounts['amount']),
            'partner_id': payment.partner_id.id,
            'journal_id': payment_method.journal_id.id,
            'force_outstanding_account_id': outstanding_account.id,
            'destination_account_id': destination_account.id,
            'ref': _('%s POS payment of %s in %s') % (payment_method.name, payment.partner_id.display_name, self.name),
            'pos_payment_method_id': payment_method.id,
            'pos_session_id': self.id,
        })
        account_payment.action_post()
        return account_payment.move_id.line_ids.filtered(lambda line: line.account_id == account_payment.destination_account_id)


    def reclose_session(self):
        for rec in self:
            if rec.state == 'closed':
                rec.sudo().write({'state': 'closing_control'})
            st = rec.cash_register_id
            if st.state == 'confirm':
                st.button_reprocess()
            if st.state == 'posted':
                st.button_reopen()
            st.line_ids.unlink()
            rec.action_pos_session_validate()
