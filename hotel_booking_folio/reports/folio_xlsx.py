from odoo import models, fields, api
from datetime import date, datetime, timedelta
from odoo.exceptions import UserError


class FolioReportXlsx(models.AbstractModel):
    _name = 'report.hotel_booking_folio.folio_xlsx_report'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, objs):
        header_style = workbook.add_format(
            {'font_name': 'Times', 'bold': True, 'left': 1, 'bottom': 1, 'right': 1, 'top': 1, 'align': 'center'})

        sheet = workbook.add_worksheet('Folio')
        wizard = objs[0]
        sheet.merge_range('A1:H1', 'List of Folios', header_style)

        sheet.write('A2:A2', 'Booking', header_style)
        sheet.write('B2:B2', 'Reference', header_style)
        sheet.write('C2:C2', 'Room Type', header_style)
        sheet.write('D2:D2', 'Room', header_style)
        sheet.write('E2:E2', 'Check In', header_style)
        sheet.write('F2:F2', 'Check Out', header_style)
        sheet.write('G2:G2', 'Total', header_style)
        sheet.write('H2:H2', 'State', header_style)

        row = 2
        for line in wizard.line_ids:
            sheet.write(row, 0, line.booking_id.name or '', header_style)
            sheet.write(row, 1, line.name or '', header_style)
            sheet.write(row, 2, line.room_type_id.name or '', header_style)
            sheet.write(row, 3, line.room_id.name or '', header_style)
            sheet.write(row, 4, str(line.check_in) or '', header_style)
            sheet.write(row, 5, str(line.check_out) or '', header_style)
            sheet.write(row, 6, line.price_total or '', header_style)
            sheet.write(row, 7, line.state, header_style)
            row += 1
        sheet.set_column(0, 7, 15)
