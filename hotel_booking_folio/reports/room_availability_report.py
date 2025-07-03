from odoo import fields, models, api
import datetime


class RoomAvailabilityReportXlsx(models.AbstractModel):
    _name = 'report.hotel_booking_folio.room_availability_xlsx_report'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, doc):
        header_style = workbook.add_format(
            {'font_name': 'Times', 'bold': True, 'border': 2, 'border_color': 'black', 'align': 'center'})

        header = workbook.add_format({'bold': True, 'align': 'center', 'font_name': 'Times'})
        style_body = workbook.add_format({'align': 'center', 'border': 2, 'border_color': 'black'})
        date_style_time = workbook.add_format({'text_wrap': True, 'border': True,
                                          'num_format': 'dd/mm/yyyy hh:mm:ss', 'align': 'left'})
        style_body_bold = workbook.add_format({'border': True, 'align': 'left','bold': True})
        date_style = workbook.add_format({'text_wrap': True,  'num_format': 'dd/mm/yyyy', 'align': 'center', 'bold': True})

        sheet = workbook.add_worksheet('Rooms')
        row = 0
        sheet.set_column(0, 23, 20)
        sheet.merge_range(row, 0, row, 4, 'Room Availability Report', header)
        sheet.merge_range(row+1, 0, row+1, 4, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), header)

        sheet.write(row+3, 0, 'Hotel', header)
        sheet.write(row+3, 1, doc.hotel_id.name, header)
        sheet.write(row+3, 3, 'Audit Date', header)
        sheet.write(row+3, 4, doc.audit_date, date_style)
        row = 5
        sheet.write(row, 0, 'Room', header_style)
        sheet.write(row, 1, 'Room Type', header_style)
        sheet.write(row, 2, 'Total Beds', header_style)
        sheet.write(row, 3, 'Assigned Beds', header_style)
        sheet.write(row, 4, 'Available Beds', header_style)
        row += 1
        for room in doc.line_ids:
            sheet.write(row, 0, room.room_id.name, style_body)
            sheet.write(row, 1, room.room_type_id.name, style_body)
            sheet.write(row, 2, room.total_beds, style_body)
            sheet.write(row, 3, room.assigned_beds, style_body)
            sheet.write(row, 4, room.available_beds, style_body)
            row += 1


