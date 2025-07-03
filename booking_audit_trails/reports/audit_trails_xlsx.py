from odoo import models, fields, api
from datetime import date, datetime, timedelta
from odoo.exceptions import UserError


class AuditTrailsReportXlsx(models.AbstractModel):
    _name = 'report.booking_audit_trails.audit_trails_xlsx_report'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, objs):
        header_style = workbook.add_format(
            {'font_name': 'Times', 'bold': True, 'left': 1, 'bottom': 1, 'right': 1, 'top': 1, 'align': 'center'})

        sheet = workbook.add_worksheet('Audit Trails')
        wizard = objs[0]
        sheet.merge_range('A1:G1', 'Audit Trails', header_style)

        sheet.write('A2:A2', 'Operation', header_style)
        sheet.write('B2:B2', 'Booking No', header_style)
        sheet.write('C2:C2', 'Folio No', header_style)
        sheet.write('D2:D2', 'Guest', header_style)
        sheet.write('E2:E2', 'User', header_style)
        sheet.write('F2:F2', 'Datetime', header_style)
        sheet.write('G2:G2', 'Particulars', header_style)

        row = 2
        for line in wizard.line_ids:
            sheet.write(row, 0, line.operation or '', header_style)
            sheet.write(row, 1, line.booking_id.name or '' or '', header_style)
            sheet.write(row, 2, line.folio_id.name or '', header_style)
            sheet.write(row, 3, line.folio_id.partner_id.name or line.booking_id.partner_id.name or '', header_style)
            sheet.write(row, 4, line.user_id.name or '', header_style)
            sheet.write(row, 5, str(line.datetime) or '', header_style)
            sheet.write(row, 6, line.notes or '', header_style)
            row += 1
        sheet.set_column(0, 4, 15)
        sheet.set_column(5, 5, 20)
        sheet.set_column(6, 6, 40)
