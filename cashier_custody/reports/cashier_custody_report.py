import toolz as T
import toolz.curried as TC

from odoo import models, fields, api, _



class CashierCustodyReport(models.AbstractModel):
    _name = 'report.cashier_custody.cashier_custody_report'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['cashier.custody'].browse(docids)
        group_by_journal = T.pipe(
            docs.account_payment_ids,
            TC.groupby(lambda line: line.journal_id.name),
            TC.valmap(lambda lines: sum(T.pluck('amount', lines))),

        )
        return {
            'doc_ids': docids,
            'doc_model': 'cashier.custody',
            'docs': docs,
            'data': data,
            'group_by_journal': group_by_journal,
        }