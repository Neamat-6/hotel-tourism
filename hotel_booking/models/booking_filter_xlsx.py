from odoo import models


class BookingFilterReportXlsx(models.AbstractModel):
    _name = 'report.hotel_booking.booking_filter_xlsx_report'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, objs):
        header_style = workbook.add_format({
            'font_name': 'Times',
            'bold': True,
            'left': 1,
            'bottom': 1,
            'right': 1,
            'top': 1,
            'align': 'center',
            'bg_color': '#D7E4BC'  # Light green background
        })

        data_style = workbook.add_format({
            'font_name': 'Times',
            'left': 1,
            'bottom': 1,
            'right': 1,
            'top': 1,
            'align': 'center'
        })

        total_style = workbook.add_format({
            'font_name': 'Times',
            'bold': True,
            'left': 1,
            'bottom': 1,
            'right': 1,
            'top': 1,
            'align': 'center',
            'bg_color': '#F4B084'  # Light orange background
        })

        sheet = workbook.add_worksheet('Dynamic Reservation Booking')
        wizard = objs[0]
        if wizard.grouped_company_source:
            sheet.merge_range('A1:D1', 'List of Reservation Booking', header_style)
        else:
            sheet.merge_range('A1:S1', 'List of Reservation Booking', header_style)

        # Define headers based on grouped_company
        if wizard.grouped_company_source:
            headers = ['Company Source', 'Price Paid', 'Price Total', 'Price Due']
        else:
            headers = [
                '#', 'Folio #', 'Booking #', 'Guest', 'Company Source', 'Room No.', 'Hotel ', 'Check In',
                'Check Out', 'Booked By', 'State', 'NO Night', 'No Room', 'Price Night',
                'Price Tax', 'Price Subtotal', 'Price Paid', 'Price Total', 'Price Due'
            ]

        for col, header in enumerate(headers):
            sheet.write(1, col, header, header_style)

        # Initialize the row and counter
        row = 2
        counter = 1

        # Initialize totals
        total_no_nights = 0
        total_no_rooms = 0
        total_price_night = 0.0
        total_price_tax = 0.0
        total_price_subtotal = 0.0
        total_price_paid = 0.0
        total_price_total = 0.0
        total_price_due = 0.0

        total_direct = 0.0
        total_online = 0.0

        # Write data rows
        for line in wizard.line_ids:
            if wizard.grouped_company_source:
                sheet.write(row, 0, line.company_booking_source.name or '', data_style)
                sheet.write(row, 1, line.price_paid or '', data_style)
                sheet.write(row, 2, line.price_total or '', data_style)
                sheet.write(row, 3, line.price_due or '', data_style)
            else:
                sheet.write(row, 0, counter, data_style)  # Seq
                sheet.write(row, 1, line.folio_id.name or '', data_style)
                sheet.write(row, 2, line.booking_id.name or '', data_style)
                sheet.write(row, 3, line.partner_id.name or '', data_style)
                sheet.write(row, 4, line.company_booking_source.name or '', data_style)
                sheet.write(row, 5, line.room_id.name or '', data_style)
                sheet.write(row, 6, line.related_hotel.name or '', data_style)
                sheet.write(row, 7, str(line.check_in) or '', data_style)
                sheet.write(row, 8, str(line.check_out) or '', data_style)
                sheet.write(row, 9, line.user_id.name or '', data_style)
                sheet.write(row, 10, line.state or '', data_style)
                sheet.write(row, 11, line.no_nights or '', data_style)
                sheet.write(row, 12, line.no_rooms or 0, data_style)
                sheet.write(row, 13, line.price_night or '', data_style)
                sheet.write(row, 14, line.price_tax or '', data_style)
                sheet.write(row, 15, line.price_subtotal or '', data_style)
                sheet.write(row, 16, line.price_paid or '', data_style)
                sheet.write(row, 17, line.price_total or '', data_style)
                sheet.write(row, 18, line.price_due or '', data_style)

            # Update totals
            total_no_nights += line.no_nights or 0
            total_no_rooms += line.no_rooms or 0
            total_price_night += line.price_night or 0.0
            total_price_tax += line.price_tax or 0.0
            total_price_subtotal += line.price_subtotal or 0.0
            total_price_paid += line.price_paid or 0.0
            total_price_total += line.price_total or 0.0
            total_price_due += line.price_due or 0.0

            if line.company_booking_source.name == 'Direct':
                total_direct += line.price_total or 0.0
            elif line.company_booking_source.name == 'Online':
                total_online += line.price_total or 0.0

            row += 1
            counter += 1

        # Write totals row
        if wizard.grouped_company_source:
            sheet.write(row, 0, 'Total', total_style)
            sheet.write(row, 1, total_price_paid, total_style)
            sheet.write(row, 2, total_price_total, total_style)
            sheet.write(row, 3, total_price_due, total_style)
        else:
            sheet.write(row, 0, 'Total', total_style)
            sheet.write(row, 11, total_no_nights, total_style)
            sheet.write(row, 12, total_no_rooms, total_style)
            sheet.write(row, 13, total_price_night, total_style)
            sheet.write(row, 14, total_price_tax, total_style)
            sheet.write(row, 15, total_price_subtotal, total_style)
            sheet.write(row, 16, total_price_paid, total_style)
            sheet.write(row, 17, total_price_total, total_style)
            sheet.write(row, 18, total_price_due, total_style)

        if wizard.grouped_company_source:
            row += 2
            sheet.write(row, 0, 'Total Company', header_style)
            sheet.write(row, 1, wizard.total_amount, data_style)
            row += 1
            sheet.write(row, 0, 'Total Direct', header_style)
            sheet.write(row, 1, wizard.total_amount_direct, data_style)
            row += 1
            sheet.write(row, 0, 'Total Online', header_style)
            sheet.write(row, 1, wizard.total_amount_online, data_style)
            row += 1
            sheet.write(row, 0, 'Grand Total Sources', header_style)
            sheet.write(row, 1, wizard.total_amount_direct + wizard.total_amount_online + wizard.total_amount,
                        data_style)

            # Set column widths
            sheet.set_column(0, len(headers) - 1, 15)
