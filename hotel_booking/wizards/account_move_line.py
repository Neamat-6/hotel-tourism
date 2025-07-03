from odoo import models, fields, api


class AccountMoveLineReport(models.AbstractModel):
    _name = 'report.hotel_booking.account_move_line_report'
    _description = 'Account Move Line Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        move_lines = self.env['account.move.line'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': 'account.move.line',
            'docs': move_lines,
        }
