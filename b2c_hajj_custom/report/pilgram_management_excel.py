import logging
from datetime import timedelta
import pytz
from odoo.tools import float_round
from odoo import fields, models, api

logger = logging.getLogger(__name__)


class PilgrimManagementXlsx(models.AbstractModel):
    _name = 'report.b2c_hajj_custom.report_pilgrim_management_excel'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'Pilgrim Management Report Excel'

    def generate_xlsx_report(self, workbook, data, doc):
        style_header = workbook.add_format({'bold': True, 'border': True, 'align': 'center'})
        style_body = workbook.add_format({'border': True, 'align': 'left'})
        date_style_time = workbook.add_format({'text_wrap': True, 'border': True,
                                          'num_format': 'dd/mm/yyyy hh:mm:ss', 'align': 'left'})
        style_body_bold = workbook.add_format({'border': True, 'align': 'left','bold': True})
        date_style = workbook.add_format({'text_wrap': True, 'border': True, 'num_format': 'dd/mm/yyyy', 'align': 'left'})


        sheet = workbook.add_worksheet('Pilgrims')
        print('objs',doc)
        row = 0
        sheet.set_column(0, 23, 20)
        sheet.write(row, 0, 'Hotel Type', style_body_bold)
        sheet.write(row, 1, doc.hotel_type, style_body)
        sheet.write(row, 2, 'Hotel', style_body_bold)
        sheet.write(row, 3, doc.hotel_id.name, style_body)
        row += 1
        sheet.write(row, 0, 'Arrival Date From', style_body_bold)
        sheet.write(row, 2, 'Arrival Date To', style_body_bold)
        if doc.hotel_arrival_date_from:
            sheet.write(row, 1, doc.hotel_arrival_date_from, date_style)
        if doc.hotel_arrival_date_to:
            sheet.write(row, 3, doc.hotel_arrival_date_to, date_style)
        row += 1
        sheet.write(row, 0, 'Departure Date From', style_body_bold)
        sheet.write(row, 2, 'Departure Date To', style_body_bold)
        if doc.hotel_dep_date_from:
            sheet.write(row, 1, doc.hotel_dep_date_from, date_style)
        if doc.hotel_dep_date_to:
            sheet.write(row, 3, doc.hotel_dep_date_to, date_style)
        row +=1
        sheet.write(row, 0, 'Package', style_body_bold)
        sheet.write(row, 1, doc.package_id.package_code, style_body)
        sheet.write(row, 2, 'Gender', style_body_bold)
        sheet.write(row, 3, doc.gender, style_body)
        sheet.write(row, 4, 'Pilgrim Type', style_body_bold)
        sheet.write(row, 5, doc.pilgrim_type, style_body)
        row +=1
        sheet.write(row, 0, 'Flight Contract', style_body_bold)
        sheet.write(row, 1, doc.flight_contract_id.name, style_body)
        sheet.write(row, 2, 'Pilgrims No.', style_body_bold)
        sheet.write(row, 3, doc.pilgrims_no, style_body)
        row += 1
        sheet.write(row, 0, 'Arrival Flight', style_body_bold)
        sheet.write(row, 1, doc.arrival_flight_no, style_body)
        sheet.write(row, 2, 'Arrival Flight Date', style_body_bold)
        if doc.arrival_flight_date:
            sheet.write(row, 3, doc.arrival_flight_date, date_style)
        sheet.write(row, 4, 'Arrival Airport', style_body_bold)
        sheet.write(row, 5, doc.arrival_airport_id.name, style_body)
        sheet.write(row, 6, 'Arrival Hall', style_body_bold)
        sheet.write(row, 7, doc.arrival_hall_no, style_body)
        row += 1
        sheet.write(row, 0, 'Departure Flight', style_body_bold)
        sheet.write(row, 1, doc.departure_flight_no, style_body)
        sheet.write(row, 2, 'Departure Flight Date', style_body_bold)
        if doc.departure_flight_date:
            sheet.write(row, 3, doc.departure_flight_date, date_style)
        sheet.write(row, 4, 'Departure Airport', style_body_bold)
        sheet.write(row, 5, doc.departure_airport_id.name, style_body)
        sheet.write(row, 6, 'Departure Hall', style_body_bold)
        sheet.write(row, 7, doc.departure_hall_no, style_body)
        row += 3
        sheet.write(row, 0, 'Package', style_header)
        sheet.write(row, 1, 'Pilgrim', style_header)
        sheet.write(row, 2, 'Passport No', style_header)
        sheet.write(row, 3, 'Pilgrim Type', style_header)
        sheet.write(row, 4, 'Main Member', style_header)
        sheet.write(row, 5, 'Gender', style_header)
        sheet.write(row, 6, 'Nationality', style_header)
        sheet.write(row, 7, 'Language', style_header)
        sheet.write(row, 8, 'Residence Country', style_header)
        sheet.write(row, 9, 'Visa Status', style_header)
        sheet.write(row, 10, 'Ticket Link', style_header)
        sheet.write(row, 11, 'Source', style_header)
        sheet.write(row, 12, 'Makkah Hotel', style_header)
        sheet.write(row, 13, 'Madinah Hotel', style_header)
        sheet.write(row, 14, 'Arfa Hotel', style_header)
        sheet.write(row, 15, 'Minnah Hotel', style_header)
        sheet.write(row, 16, 'Main Shift Hotel', style_header)
        sheet.write(row, 17, 'Makkah Contract', style_header)
        sheet.write(row, 18, 'Madinah Contract', style_header)
        sheet.write(row, 19, 'Main Hotel Contract', style_header)
        sheet.write(row, 20, 'Flight Contract', style_header)
        sheet.write(row, 21, 'Arrival Flight', style_header)
        sheet.write(row, 22, 'Arrival Airport', style_header)
        sheet.write(row, 23, 'Arrival Date', style_header)
        sheet.write(row, 24, 'Departure Flight', style_header)
        sheet.write(row, 25, 'Departure Airport', style_header)
        sheet.write(row, 26, 'Departure Date', style_header)
        row += 1
        for line in doc.line_ids:
            sheet.write(row, 0, line.package_id.package_code, style_body)
            sheet.write(row, 1, line.partner_id.name, style_body)
            sheet.write(row, 2, line.passport_no, style_body)
            sheet.write(row, 3, line.pilgrim_type, style_body)
            sheet.write(row, 4, line.main_member_id.name, style_body)
            sheet.write(row, 5, line.gender, style_body)
            sheet.write(row, 6, line.nationality, style_body)
            sheet.write(row, 7, line.language.name, style_body)
            sheet.write(row, 8, line.residence_country, style_body)
            sheet.write(row, 9, line.visa_status, style_body)
            sheet.write(row, 10, line.ticket_link, style_body)
            sheet.write(row, 11, line.hajj_source, style_body)
            sheet.write(row, 12, line.main_makkah.name, style_body)
            sheet.write(row, 13, line.main_madinah.name, style_body)
            sheet.write(row, 14, line.main_arfa.name, style_body)
            sheet.write(row, 15, line.main_minnah.name, style_body)
            sheet.write(row, 16, line.main_hotel.name, style_body)
            sheet.write(row, 17, line.makkah_contract_id.name, style_body)
            sheet.write(row, 18, line.madinah_contract_id.name, style_body)
            sheet.write(row, 19, line.main_hotel_contract_id.name, style_body)
            sheet.write(row, 20, line.flight_schedule_id.name, style_body)
            sheet.write(row, 21, line.arrival_flight_no, style_body)
            sheet.write(row, 22, line.arrival_airport_id.name, style_body)
            sheet.write(row, 23, line.flight_arrival_date, date_style_time)
            sheet.write(row, 24, line.departure_flight_no, style_body)
            sheet.write(row, 25, line.dep_airport_id.name, style_body)
            sheet.write(row, 26, line.flight_departure_date, date_style_time)
            row += 1







