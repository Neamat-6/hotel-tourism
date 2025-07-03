from odoo import fields, models, api
import pytz


class HotelRoom(models.Model):
    _inherit = 'hotel.room'

    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
    ], string="Gender")
    package_id = fields.Many2one('booking.package')
    is_camp = fields.Boolean(related='room_type.is_camp')


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
                folio = self.env['booking.folio'].search([
                    ('room_id', '=', rec.id),
                    ('check_in_date', '<=', audit_date),
                    ('check_out_date', '>=', audit_date),
                    ('state', 'in', ['part_checked_in', 'checked_in', 'confirmed'])
                ])
                if folio:
                    if rec.hotel_id.type in ['arfa', 'minnah']:
                        rec.number_of_guests = sum(folio.mapped('hajj_count'))
                        rec.total_beds = folio[0].total_beds
                        rec.available_beds = rec.total_beds - rec.number_of_guests
                        rec.booking_total_amount = sum(folio.mapped('price_total'))
                        rec.booking_paid_amount = sum(folio.mapped('price_paid'))
                        rec.booking_due_amount = sum(folio.mapped('price_due'))
                    else:
                        folio = folio[0]
                        rec.number_of_guests = folio.number_of_guests
                        rec.total_beds = folio.total_beds
                        rec.available_beds = folio.available_beds
                        rec.booking_total_amount = folio.price_total
                        rec.booking_paid_amount = folio.price_paid
                        rec.booking_due_amount = folio.price_due
                    folio = folio[0]
                    rec.folio_id = folio.id
                    rec.booking_id = folio.booking_id.id
                    rec.booking_date = folio.create_date
                    rec.booking_guest_name = folio.partner_id.name
                    rec.booking_checkin = folio.check_in
                    rec.booking_checkout = folio.check_out
                    rec.booking_total_nights = folio.total_nights

