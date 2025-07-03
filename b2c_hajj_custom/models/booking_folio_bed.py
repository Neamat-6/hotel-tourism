from odoo import fields, models, api


class FolioBed(models.Model):
    _inherit = 'booking.folio.bed'

    allowed_partner_ids = fields.Many2many('res.partner')
    partner_id = fields.Many2one('res.partner', domain="[('id', 'in', allowed_partner_ids)]")

    def write(self, vals):
        # remove new partner id from all allowed partners in all booking beds
        booking = self.folio_id.booking_id
        if vals.get('partner_id', False):
            guests = booking.guest_ids
            guest_line = guests.filtered(lambda g: g.partner_id.id == vals['partner_id'])
            if guest_line:
                guest_line.folio_id = self.folio_id.id
                if booking.hotel_id.type == 'makkah':
                    guest_line.partner_id.sudo().with_context(skip_assign_to_bookings=True).write({
                        'makkah_room': self.folio_id.room_id.id,})
                elif booking.hotel_id.type == 'madinah':
                    guest_line.partner_id.sudo().with_context(skip_assign_to_bookings=True).write({
                        'madinah_room': self.folio_id.room_id.id,})
                elif booking.hotel_id.type == 'hotel':
                    guest_line.partner_id.sudo().with_context(skip_assign_to_bookings=True).write({
                        'hotel_room': self.folio_id.room_id.id,})
                elif booking.hotel_id.type == 'arfa':
                    guest_line.partner_id.sudo().with_context(skip_assign_to_bookings=True).write({
                        'arfa_room': self.folio_id.room_id.id,})
                elif booking.hotel_id.type == 'minnah':
                    guest_line.partner_id.sudo().with_context(skip_assign_to_bookings=True).write({
                        'minnah_room': self.folio_id.room_id.id,})
                beds = self.env['booking.folio.bed'].search([('folio_id', 'in', booking.folio_ids.ids)])
                for bed in beds:
                    bed.allowed_partner_ids = [(3, vals['partner_id'])]

        # add removed partner to all allowed partners in all booking beds
        old_partner = self.partner_id
        res = super(FolioBed, self).write(vals)
        new_partner = self.partner_id
        if old_partner and not new_partner:
            for bed in booking.folio_ids.mapped('bed_ids'):
                bed.allowed_partner_ids = [(4, old_partner.id)]
        return res