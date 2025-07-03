from dateutil.relativedelta import relativedelta

import toolz as T
import toolz.curried as TC

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class CashierSummarReport(models.TransientModel):
    _name = 'cashier.summary.report'
    _description = 'Cashier Summary Report'

    start_audit_date = fields.Date(string='Start Audit Date', required=True)
    end_audit_date = fields.Date(string='End Audit Date', required=True)

    def prepare_data(self):
        start_audit_date = self.start_audit_date
        end_audit_date = self.end_audit_date
        if start_audit_date > end_audit_date:
            raise ValidationError(_('End Audit Date must be greater than Start Audit Date'))

        payment_ids = self.env['account.payment'].search([
            ('audit_date', '>=', start_audit_date),
            ('audit_date', '<=', end_audit_date),
            ('state', '=', 'posted'),
            ('booking_id', '!=', False)
        ])

        grouped_payments = T.pipe(
            payment_ids,
            TC.groupby(lambda p: p.create_uid.name),
            TC.valmap(TC.groupby(lambda p: p.journal_id.name),),
            TC.valmap(TC.valmap(TC.compose(sum, TC.pluck('amount_signed')))),
        )
        totals = T.pipe(
            payment_ids,
            TC.groupby(lambda p: p.journal_id.name),
            TC.valmap(TC.compose(sum, TC.pluck('amount_signed'))),
        )
        journal_ids = self.env['account.journal'].search([
            ('company_id', '=', self.env.company.id),
            ('type','in', ['bank', 'cash']),
        ]).mapped('name')

        return {
            'grouped_payments': grouped_payments,
            'totals': totals,
            'journal_ids': journal_ids,
        }

    def print_pdf(self):
        structured_date = self.prepare_data()
        data = {
            'date': self.read()[0],
            'grouped_payments': structured_date.get('grouped_payments'),
            'totals': structured_date.get('totals'),
            'journal_ids': structured_date.get('journal_ids'),
        }
        return self.env.ref('hotel_booking_folio.action_cashier_summary_report').report_action(
            None,
            data=data,
        )
