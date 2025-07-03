from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class BookingFolio(models.Model):
    _name = 'booking.folio.wizard'

    check_in = fields.Date('Check In')
    check_out = fields.Date('Check Out')
    partner_id = fields.Many2one("res.partner")
    day = fields.Date("Day", required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed Waiting Payment'),
        ('part_checked_in', 'Partially Checked In'),
        ('checked_in', 'Checked In'),
        ('part_checked_out', 'Partially Checked Out'),
        ('checked_out', 'Checked Out'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled')], string='State')
    room_id = fields.Many2one('hotel.room', "Room No")

    def print_report(self):
        data = {
            'model': 'booking.folio.wizard',
            'form': self.read()[0]
        }
        return self.env.ref('hotel_booking.booking_folio_report').report_action(self, data=data)


class StudentsReportData(models.AbstractModel):
    _name = "report.hotel_booking.booking_folio_report_template"

    @api.model
    def _get_report_values(self, docids, data=None):
        partner_id = data['form']['partner_id']
        room_id = data['form']['room_id']
        day = data['form']['day']

        domain = []

        if day:
            domain.append(('day', '=', day))
            date_from_in_report = day
        else:
            date_from_in_report = ""

        if partner_id:
            domain.append(('partner_id', '=', partner_id[0]))
            user_in_report = partner_id[1]
        else:
            user_in_report = ""

        if room_id:
            domain.append(('room_id', '=', room_id[0]))

        domain.append(('folio_id.state', '!=', 'cancelled'))

        booking_folio_obj = self.env['booking.folio.line'].search(domain)
        total_amount = sum(booking_line.amount for booking_line in booking_folio_obj)
        total_discount = sum(booking_line.discount for booking_line in booking_folio_obj.booking_line_id)
        total_tax = sum(booking_line.tax_amount for booking_line in booking_folio_obj.booking_line_id)
        total_vat = sum(booking_folio_obj.booking_line_id.tax_id.filtered(lambda l: l.type == 'vat').mapped('amount'))
        total_municipality = sum(
            booking_folio_obj.booking_line_id.tax_id.filtered(lambda l: l.type == 'municipality').mapped('amount'))
        total_room_charge = sum(booking_folio_obj.filtered(lambda l: l.type == 'room_charge').mapped('amount'))
        total_food = sum(booking_folio_obj.filtered(lambda l: l.type == 'food').mapped('amount'))
        total_laundry = sum(booking_folio_obj.filtered(lambda l: l.type == 'laundry').mapped('amount'))
        total_rent = sum(booking_folio_obj.filtered(lambda l: l.type == 'rent').mapped('amount'))
        total_discount = sum(booking_folio_obj.filtered(lambda l: l.type == 'discount').mapped('amount'))

        return {
            'doc_model': 'account.payment.wizard',
            'docs': booking_folio_obj,
            'partner_id': user_in_report,
            'day': day,
            'total_vat': total_vat,
            'total_municipality': total_municipality,
            'total_room_charge': total_room_charge,
            'total_food': total_food,
            'total_laundry': total_laundry,
            'total_rent': total_rent,
            'total_discount': total_discount,
        }
