from odoo import fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    folio_id = fields.Many2one('booking.folio', related='payment_id.folio_id')
    folio_room_id = fields.Many2one('hotel.room', related='folio_id.room_id', store=True)
    booking_folio_id = fields.Many2one('booking.folio')

    def unlink(self):
        for move in self:
            booking = move.booking_id
            if booking:
                folios = booking.folio_ids
                for folio in folios:
                    folio.line_ids.write({'is_invoiced': False})
        return super().unlink()



class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    pos_order_ref = fields.Char('POS Order Ref')
