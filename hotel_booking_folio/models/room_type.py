from odoo import fields, models, api
from dateutil.relativedelta import relativedelta


class RoomType(models.Model):
    _inherit = 'room.type'

    def get_inventory(self, date_start, date_end):
        days = []
        if date_start and date_end:
            total_rooms = len(self.room_ids)
            while date_start <= date_end:
                booked_rooms = self.get_booked_inventory(date_start)
                if total_rooms:
                    book_factor = booked_rooms / total_rooms
                else:
                    book_factor = 0

                vals = {
                    'total_rooms': total_rooms,
                    'booked_rooms': booked_rooms,
                    'available_rooms': int(total_rooms - booked_rooms),
                    'occupancy': round(book_factor * 100, 2),
                }
                days.append(vals)
                date_start += relativedelta(days=1)
            return days
        else:
            return []

    def get_booked_inventory(self, date_start,company_id=False):
        """
            get booked qty for a specific day
        """

        query = """
        SELECT COUNT(BFL.*),RT.NAME,RT.ID,BFL.DAY
        FROM BOOKING_FOLIO_LINE AS BFL
        INNER JOIN BOOKING_FOLIO AS BF ON BF.ID = BFL.FOLIO_ID
            AND BF.STATE != 'cancelled'
            AND BF.COMPANY_ID IS NOT NULL
            AND BF.ROOM_TYPE_ID IS NOT NULL
            AND BFL.DAY = %(date_start)s
            AND BF.COMPANY_ID = %(company_id)s
            AND BFL.PARTICULARS = 'Room Charge'
        LEFT JOIN ROOM_TYPE AS RT ON BF.ROOM_TYPE_ID = RT.ID
        WHERE RT.ID = %(room_type_id)s
        GROUP BY GROUPING SETS ( (RT.NAME,BFL.DAY,RT.ID))
        ORDER BY BFL.DAY
        """
        self.env.cr.execute(query, {'date_start': date_start, 'company_id': company_id, 'room_type_id': self.id})
        booked_folios = self.env.cr.dictfetchall()[0]
        return booked_folios.get('count', 0) if booked_folios else 0

    def get_occupancy(self, date_start=False, date_end=False, company_id=False):
        if not date_start:
            date_start = self.env.company.audit_date
        if not date_end:
            date_end = self.env.company.audit_date
        if not company_id:
            company_id = self.env.company.related_hotel_id.id
        constant_date_start = date_start
        types = self.env['room.type'].search([('company_id', '=', company_id)])
        occupancy = 0
        if date_start and date_end:
            total_rooms = len(types.mapped('room_ids'))
            if total_rooms:
                while date_start <= date_end:
                    booked_folios = self.env['booking.folio'].search_count([
                        ('state', 'not in', ['cancelled', 'draft', 'checked_out']), ('room_id', '!=', False),
                        ('check_in', '!=', False), ('check_in_date', '=', date_start), ('room_type_id', 'in', types.ids)
                    ])
                    occupancy += round((booked_folios / total_rooms) * 100, 2)

                    date_start += relativedelta(days=1)
        diff = (date_end - constant_date_start).days
        if not diff:
            diff = 1
        avg_occupancy = occupancy / diff
        return avg_occupancy
