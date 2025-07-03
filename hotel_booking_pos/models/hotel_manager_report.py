from odoo import fields, models, api


class ManagerReport(models.TransientModel):
    _inherit = 'hotel.manager.report'

    def create_payment_lines(self):
        self.payment_line_ids = [(5, 0, 0)]
        payment_ids = self.env['account.payment'].search([
            ('state', '=', 'posted'), ('pos_session_id', '=', False)
        ]).filtered(lambda p: p.audit_date.year == self.date.year)
        date_payment_ids = payment_ids.filtered(lambda p: p.audit_date == self.date)
        ptd_payment_ids = payment_ids.filtered(lambda p: self.date >= p.audit_date >= self.ptd)
        ytd_payment_ids = payment_ids.filtered(lambda p: self.date >= p.audit_date >= self.ytd)
        journals = list(set(payment_ids.mapped('journal_id')))
        for journal in journals:
            total_date_payment = sum(date_payment_ids.filtered(lambda p: p.journal_id.id == journal.id).mapped('amount'))
            total_ptd_payment = sum(ptd_payment_ids.filtered(lambda p: p.journal_id.id == journal.id).mapped('amount'))
            total_ytd_payment = sum(ytd_payment_ids.filtered(lambda p: p.journal_id.id == journal.id).mapped('amount'))
            self.payment_line_ids = [
                (0, 0, {
                    'journal_id': journal.id,
                    'date_total': abs(total_date_payment),
                    'ptd_total': abs(total_ptd_payment),
                    'ytd_total': abs(total_ytd_payment),
                }), ]
