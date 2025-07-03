import pytz
from odoo import fields, models, api, _


class HotelRoom(models.Model):
    _inherit = 'hotel.room'

    folio_id = fields.Many2one('booking.folio', compute='compute_booking_id')
    total_beds = fields.Integer(compute='compute_booking_id')
    available_beds = fields.Integer(compute='compute_booking_id')
    number_of_guests = fields.Integer(compute='compute_booking_id')

    def _compute_display_name(self):
        for record in self:
            record.display_name = f'{record.name} - {record.state.name}'

    def compute_booking_id(self):
        for rec in self:
            rec.folio_id = False
            rec.booking_id = False
            rec.booking_date = False
            rec.booking_guest_name = False
            rec.booking_checkin = False
            rec.booking_checkout = False
            rec.booking_total_nights = False
            rec.booking_total_amount = False
            rec.booking_paid_amount = False
            rec.booking_due_amount = False
            rec.total_beds = False
            rec.available_beds = False
            rec.number_of_guests = False

            if rec.hotel_id:
                timezone = pytz.timezone(self.env.user.tz or 'UTC')
                audit_date = self.env.company.audit_date
                folio = self.env['booking.folio'].search([('room_id', '=', rec.id)]).filtered(
                    lambda f: f.check_in_date <= audit_date <= f.check_out_date and f.state in ['part_checked_in',
                                                                                                'checked_in',
                                                                                                'confirmed']
                )
                if folio:
                    folio = folio[0]
                    rec.folio_id = folio.id
                    rec.booking_id = folio.booking_id.id
                    rec.booking_date = folio.create_date
                    rec.booking_guest_name = folio.partner_id.name
                    rec.booking_checkin = folio.check_in
                    rec.booking_checkout = folio.check_out
                    rec.booking_total_nights = folio.total_nights
                    rec.booking_total_amount = folio.price_total
                    rec.booking_paid_amount = folio.price_paid
                    rec.booking_due_amount = folio.price_due
                    rec.hotel_booking_date = folio.check_in_date
                    rec.hotel_booking_date_out = folio.check_out_date
                    rec.total_beds = folio.total_beds
                    rec.available_beds = folio.available_beds
                    rec.number_of_guests = folio.number_of_guests

    def action_view_reservations(self):
        if self.folio_id:
            return {
                'name': _('Folios'),
                'type': 'ir.actions.act_window',
                'view_mode': 'tree,form',
                'view_type': 'form',
                'res_model': 'booking.folio',
                'domain': [('id', '=', self.folio_id.id)],
                'target': 'current',
            }
        else:
            return {
                'name': _('Reservations'),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'view_type': 'form',
                'res_model': 'hotel.booking',
                'target': 'current',
                'context': {
                    'default_hotel_room_id': self.id,
                    'default_is_hotel_room': True
                }
            }
