from odoo import models,api

class CashierSummaryReport(models.AbstractModel):
    _name = 'report.hotel_booking_folio.cashier_summary_report'
    _description = 'Cashier Summary Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['cashier.summary.report'].browse(docids)
        return {
            'doc_ids': docs.ids,
            'doc_model': 'cashier.summary.report',
            'grouped_payments': data['grouped_payments'],
            'totals': data['totals'],
            'journal_ids': data['journal_ids'],
            'docs': docs,
            'start_audit_date': data['date']['start_audit_date'],
            'end_audit_date': data['date']['end_audit_date'],
            'data': data,
        }