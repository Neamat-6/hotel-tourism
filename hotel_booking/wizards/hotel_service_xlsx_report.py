import json
from odoo import models


class HotelServiceReportXlsx(models.AbstractModel):
    _name = 'report.hotel_booking.hotel_service_xlsx_report'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, objs):
        # Header style
        header_style = workbook.add_format(
            {'font_name': 'Times', 'bold': True, 'left': 1, 'bottom': 1, 'right': 1, 'top': 1, 'align': 'center'})
        content_style = workbook.add_format(
            {'font_name': 'Times', 'left': 1, 'bottom': 1, 'right': 1, 'top': 1})

        # Create a worksheet
        sheet = workbook.add_worksheet('Hotel Service')
        wizard = objs[0]

        # Report Title
        sheet.merge_range('A1:G1', 'Hotel Service Report', header_style)

        # Column headers
        sheet.write('A2', 'Day', header_style)
        sheet.write('B2', 'Particular', header_style)
        sheet.write('C2', 'Description', header_style)
        sheet.write('D2', 'Room', header_style)
        sheet.write('E2', 'Created By', header_style)
        sheet.write('F2', 'Booking ID', header_style)
        sheet.write('G2', 'Amount', header_style)

        row = 2  # Start from the third row (index 2)
        for line in wizard.line_ids:
            sheet.write(row, 0, str(line.day) or '', content_style)
            sheet.write(row, 1, line.particular or '', content_style)
            sheet.write(row, 2, line.description or '', content_style)
            sheet.write(row, 3, line.room_id.name or '', content_style)
            sheet.write(row, 4, line.created_by.name or '', content_style)
            sheet.write(row, 5, line.booking_id.name or '', content_style)
            sheet.write(row, 6, line.amount or 0, content_style)
            row += 1

        # Summary Section
        row += 2  # Add some space before the summary
        sheet.write(row, 0, 'Summary', header_style)
        sheet.write(row + 1, 0, 'Particular', header_style)
        sheet.write(row + 1, 1, 'Total Amount', header_style)

        summary_data = json.loads(wizard.summary_data or "[]")  # Load summary data
        summary_row = row + 2
        for particular, total_amount in summary_data:
            sheet.write(summary_row, 0, particular, content_style)
            sheet.write(summary_row, 1, total_amount, content_style)
            summary_row += 1

        sheet.set_column(0, 6, 15)
        sheet.set_column(1, 1, 25)
