from odoo import models, fields, api
from datetime import date, datetime, timedelta
from odoo.exceptions import UserError


class DailyRevenueReportXlsx(models.AbstractModel):
    _name = 'report.hotel_booking_folio.daily_revenue_xlsx_report'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, objs):
        header_style = workbook.add_format(
            {'font_name': 'Times', 'bold': True, 'left': 1, 'bottom': 1, 'right': 1, 'top': 1, 'align': 'center'})

        sheet = workbook.add_worksheet('Daily Revenue')
        wizard = objs[0]
        sheet.merge_range('A1:J1', f'Daily Revenue From {wizard.date_from} To {wizard.date_to}', header_style)

        sheet.write('A2:A2', 'Guest Name', header_style)
        sheet.write('B2:B2', 'Day', header_style)
        sheet.write('C2:C2', 'Bookings', header_style)
        sheet.write('D2:D2', 'Folios', header_style)
        if wizard.tax_revenue_mode:
            sheet.write('E2:E2', 'Total Vat', header_style)
            sheet.write('F2:F2', 'Total Municipality', header_style)
            sheet.write('G2:G2', 'Total', header_style)
        else:
            sheet.write('E2:E2', 'Total Room Charge', header_style)
            sheet.write('F2:F2', 'Total Services', header_style)
            sheet.write('G2:G2', 'Total Vat', header_style)
            sheet.write('H2:H2', 'Total Municipality', header_style)
            sheet.write('I2:I2', 'Total', header_style)

        row = 2
        for line in wizard.line_ids:
            bookings = [b.name for b in line.booking_ids]
            folios = [f.name for f in line.folio_ids]

            sheet.write(row, 0, line.partner_id.name or '', header_style)
            sheet.write(row, 1, str(line.day) or '', header_style)
            sheet.write(row, 2, ','.join(bookings) or '', header_style)
            sheet.write(row, 3, ','.join(folios) or '', header_style)
            if wizard.tax_revenue_mode:
                sheet.write(row, 4, line.total_vat, header_style)
                sheet.write(row, 5, line.total_municipality, header_style)
                sheet.write(row, 6, line.total, header_style)
            else:
                sheet.write(row, 4, line.total_room_charge, header_style)
                sheet.write(row, 5, line.total_service, header_style)
                sheet.write(row, 6, line.total_vat, header_style)
                sheet.write(row, 7, line.total_municipality, header_style)
                sheet.write(row, 8, line.total, header_style)
            row += 1
        total_room_charge = round(sum(wizard.line_ids.mapped('total_room_charge')),2)
        total_service = round(sum(wizard.line_ids.mapped('total_service')),2)
        total_vat = round(sum(wizard.line_ids.mapped('total_vat')),2)
        total_municipality = round(sum(wizard.line_ids.mapped('total_municipality')),2)
        # total_payment = round(sum(wizard.line_ids.mapped('total_payment')),2)
        total = round(sum(wizard.line_ids.mapped('total')),2)
        sheet.merge_range(f'A{row+1}:D{row+1}', 'Total', header_style)
        if wizard.tax_revenue_mode:
            sheet.write(row, 4, total_vat, header_style)
            sheet.write(row, 5, total_municipality, header_style)
            sheet.write(row, 6, total, header_style)
        else:
            sheet.write(row, 4, total_room_charge, header_style)
            sheet.write(row, 5, total_service, header_style)
            sheet.write(row, 6, total_vat, header_style)
            sheet.write(row, 7, total_municipality, header_style)
            sheet.write(row, 8, total, header_style)
        sheet.set_column(0, 9, 15)
