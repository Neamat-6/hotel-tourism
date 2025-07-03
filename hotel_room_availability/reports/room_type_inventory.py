from odoo import fields, models, api
from dateutil.relativedelta import relativedelta


class RoomTypeInventoryReport(models.AbstractModel):
    _name = 'report.hotel_room_availability.room_type_inventory_report'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['room.availability'].browse(docids)
        doc = docs[0]
        room_types = self.env['room.type'].search([('company_id', '=', doc.company_id.id)])
        days = []
        date_from = doc.date_from
        date_to = doc.date_to
        date_start = doc.date_from
        date_end = doc.date_to
        while date_start <= date_end:
            vals = {
                'month': date_start.strftime('%b'),
                'date': date_start.strftime('%d'),
                'day': date_start.strftime('%a'),
            }

            days.append(vals)
            date_start += relativedelta(days=1)
        return {
            'doc_ids': docs.ids,
            'doc_model': 'room.availability',
            'docs': docs,
            'days': days,
            'room_types': room_types,
            'date_start': date_from,
            'date_end': date_to,
        }
