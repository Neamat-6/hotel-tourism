from odoo import models, api
from odoo.exceptions import UserError


class ReservationConfirmationReport(models.AbstractModel):
    _name = 'report.hotel_booking.reservation_confirmation'

    @api.model
    def _get_report_values(self, docids, data=None):
        bookings = self.env['tourism.hotel.booking'].browse(docids),
        for booking in bookings:
            if booking.state != 'confirmed':
                raise UserError("{} state is not confirmed!".format(booking.name))
        return {
            'doc_ids': docids,
            'doc_model': 'tourism.hotel.booking',
            'docs': self.env['tourism.hotel.booking'].browse(docids),
            'report_type': data.get('report_type') if data else ''
            # 'docs': data,
        }
