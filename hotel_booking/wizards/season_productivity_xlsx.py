from odoo import models


class SeasonProdReportXlsx(models.AbstractModel):
    _name = 'report.hotel_booking.season_productivity_report_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, objs):
        header_style = workbook.add_format(
            {'font_name': 'Arial', 'bold': True, 'align': 'center', 'valign': 'vcenter', 'border': 1}
        )
        content_style = workbook.add_format(
            {'font_name': 'Arial', 'align': 'center', 'valign': 'vcenter', 'border': 1}
        )

        sheet = workbook.add_worksheet('Season Productivity')
        wizard = objs[0]

        sheet.merge_range('A1:B1', 'Season Productivity Report', header_style)

        if wizard.company_booking_source:
            source_info = f"Company Booking Source: {wizard.company_booking_source.name}"
        else:
            source_info = "Company Booking Source: ALL Sources"
        sheet.merge_range('A2:B2', source_info, content_style)

        sheet.write('A3', 'Season', header_style)
        sheet.write('B3', 'Total Amount', header_style)

        row = 3
        for line in wizard.line_ids:
            sheet.write(row, 0, line.season_id.name or '', content_style)
            sheet.write(row, 1, line.total_amount or 0.0, content_style)
            row += 1

        row += 1
        sheet.write(row, 0, 'Summary', header_style)
        sheet.write(row + 1, 0, 'Total Amount', header_style)
        sheet.write(row + 1, 1, sum(line.total_amount for line in wizard.line_ids), content_style)

        sheet.set_column(0, 0, 25)  # Season column
        sheet.set_column(1, 1, 15)  # Total Amount column
