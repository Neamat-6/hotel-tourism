from odoo import models, fields, api
from dateutil.relativedelta import relativedelta


class RTAvailabilityReportXlsx(models.AbstractModel):
    _name = 'report.hotel_booking_folio.rt_availability_xlsx_report'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, objs):
        header_style = workbook.add_format(
            {'font_name': 'Times', 'bold': True, 'left': 1, 'bottom': 1, 'right': 1, 'top': 1, 'align': 'center'})

        sheet = workbook.add_worksheet('Folio')
        wizard = objs[0]
        start = wizard.date_from
        end = wizard.date_to
        col = 1
        while start <= end:
            sheet.write(1, col, str(start) or '', header_style)
            start += relativedelta(days=1)
            col += 1
        row = 2
        room_types = list(set(wizard.line_ids.mapped('room_type_id')))
        for room_type in room_types:
            sheet.write(row, 0, room_type.name or '', header_style)
            start = wizard.date_from
            end = wizard.date_to
            col = 1
            while start <= end:
                line = wizard.line_ids.filtered(lambda l: l.date == start and l.room_type_id.id == room_type.id)
                qty_available = line.qty_available if line else 0
                # If the quantity is None, set it to 0
                sheet.write(row, col, qty_available if qty_available is not None else 0, header_style)

                start += relativedelta(days=1)
                col += 1
            row += 1
        sheet.set_column(0, 0, 30)
        sheet.set_column(1, col - 1, 15)
        sheet.merge_range(0, 0, 0, col - 1, 'Availability by Room Type', header_style)
