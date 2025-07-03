from odoo import models, fields, api
from datetime import date, datetime, timedelta
from odoo.exceptions import UserError


class BookingArrivalReportXlsx(models.AbstractModel):
    _name = 'report.hotel_booking.booking_arrival_xlsx_report'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, objs):
        header_style = workbook.add_format(
            {'font_name': 'Times', 'bold': True, 'left': 1, 'bottom': 1, 'right': 1, 'top': 1, 'align': 'center'})

        sheet = workbook.add_worksheet('Booking Arrival')
        wizard = objs[0]
        sheet.merge_range('A1:L1', 'List of Booking Arrivals', header_style)

        sheet.write('A2:A2', 'Booking No', header_style)
        sheet.write('B2:B2', 'Guest Name', header_style)
        sheet.write('C2:C2', 'Check In', header_style)
        sheet.write('D2:D2', 'Check Out', header_style)
        sheet.write('E2:E2', 'NO. Guests', header_style)
        sheet.write('F2:F2', 'Room Type', header_style)
        sheet.write('G2:G2', 'Booking Source', header_style)
        sheet.write('H2:H2', 'Online Booking Source', header_style)
        sheet.write('I2:I2', 'Company Booking Source', header_style)
        sheet.write('J2:J2', 'Total Nights', header_style)
        sheet.write('K2:K2', 'Subtotal', header_style)
        sheet.write('L2:L2', 'Note', header_style)

        row = 2
        for line in wizard.line_ids:
            sheet.write(row, 0, line.ref or '', header_style)
            sheet.write(row, 1, line.partner_id.name or '', header_style)
            sheet.write(row, 2, str(line.check_in) or '', header_style)
            sheet.write(row, 3, str(line.check_out) or '', header_style)
            sheet.write(row, 4, line.no_guests or '', header_style)
            sheet.write(row, 5, line.room_type_id.name or '', header_style)
            sheet.write(row, 6, line.booking_source or '', header_style)
            sheet.write(row, 7, line.online_travel_agent_source.name or '', header_style)
            sheet.write(row, 8, line.company_booking_source.name or '', header_style)
            sheet.write(row, 9, line.total_nights or '', header_style)
            sheet.write(row, 10, line.subtotal or 0, header_style)
            sheet.write(row, 11, line.note or '', header_style)
            row += 1
        sheet.set_column(0, 7, 15)
