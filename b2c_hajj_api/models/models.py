from odoo import fields, models, api
import json
from datetime import datetime, date

def fix_dates(vals):
    for val in vals:
        for key, value in val.items():
            if isinstance(value, (datetime, date)):
                val[key] = str(value) if value else False
    return vals

class FlightSchedule(models.Model):
    _inherit = 'flight.schedule'


    def get_contract_data(self):
        vals = self.read(['id', 'name', 'contract_type', 'partner_id', 'unit_price', 'purchase_id', 'pilgrims_no', 'booked_no', 'available_no',
                          'arrival_date', 'departure_date', 'arrival_airport_id', 'departure_airport_id','arrival_hall_no', 'departure_hall_no',
                          'arrival_flight_no', 'departure_flight_no', 'state'])
        return fix_dates(vals)


class Partner(models.Model):
    _inherit = 'res.partner'

    def fix_dates(self,obj):
        if isinstance(obj, list):
            return [self.fix_dates(item) for item in obj]
        if isinstance(obj, dict):
            return {k: (v.isoformat() if isinstance(v, (datetime, date)) else v) for k, v in
                    obj.items()}
        return obj

    def get_pilgrim_data(self):
        vals = self.read(['id', 'name', 'pilgrim_id', 'phone', 'mobile', 'email', 'website', 'title',
                          'residence_country', 'hajj_source', 'nationality', 'region', 'language',
                           'gender', 'ticket_number', 'passport_no', 'passport_expiry_date', 'visa_status', 'ticket_link',
                          'pilgrim_type', 'main_member_id', 'is_guide', 'tour_guide_id', 'booking_details', 'package_contract_id',
                          'main_makkah', 'makkah_arrival_date', 'makkah_departure_date', 'makkah_room_type', 'makkah_room',
                          'main_madinah', 'madinah_arrival_date', 'madinah_departure_date', 'madinah_room_type', 'madinah_room',
                           'main_hotel', 'hotel_arrival_date', 'hotel_departure_date', 'hotel_room_type', 'hotel_room',
                           'main_arfa', 'arfa_arrival_date', 'arfa_departure_date', 'arfa_room',
                          'main_minnah', 'minnah_arrival_date', 'minnah_departure_date', 'minnah_room',
                          'status', 'is_hastened', 'tarwiyah', 'ziarat_al_rawdah', 'tawaf_al_qudum', 'jamarat_day1',
                          'jamarat_day2', 'jamarat_day3', 'jamarat_day4', 'tawaf_al_ifada_sai', 'tawaf_al_wada'
                          ])
        for val in vals:
            partner = self.browse(val['id'])
            flight_contract = partner.flight_schedule_id.get_contract_data()
            val['flight_contract'] = flight_contract[0] if flight_contract else {}
        return fix_dates(vals)
        # return vals
