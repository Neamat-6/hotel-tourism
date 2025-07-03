from odoo import fields, models, api


class CashierCustody(models.Model):
    _inherit = 'cashier.custody'

    def button_search(self):
        self.account_payment_ids = [(5, 0, 0)]
        domain = [('pos_session_id', '=', False)]
        if self.company_ids:
            domain.append(('company_id', 'in', self.company_ids.ids))
        if self.payment_state == 'closed':
            domain.append(('closed_cashier', '=', True))
        if self.payment_state == 'not_closed':
            domain.append(('closed_cashier', '=', False))
        if self.state:
            domain.append(('state', '=', self.state))
        if self.date_from:
            domain.append(('date', '>=', self.date_from))
        if self.date_to:
            domain.append(('date', '<=', self.date_to))
        if self.user_id:
            domain.append(('user_id', '=', self.user_id.id))
        if self.account_journal_id:
            domain.append(('journal_id', '=', self.account_journal_id.id))

        account_payment_objs = self.env['account.payment'].sudo().search(domain)

        account_payment_values = []
        for payment in account_payment_objs:
            vals = {
                'date': payment.date,
                'name': payment.name,
                'journal_id': payment.journal_id.id,
                'booking_id': payment.booking_id.id,
                'folio_id': payment.folio_id.id,
                'payment_method_line_id': payment.payment_method_line_id.id,
                'partner_id': payment.partner_id.id,
                'amount': payment.amount,
                'state': payment.state,
                'closed_cashier': payment.closed_cashier
            }
            account_payment_values.append((4, payment.id, 0))

        self.account_payment_ids = account_payment_values
        self.status = 'closed'
