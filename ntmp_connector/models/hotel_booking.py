from odoo import models


class Booking(models.Model):
    _inherit = 'hotel.booking'

    def button_cancel(self):
        # res = super(Booking, self).button_cancel()
        if self.company_id.apply_ntmp and self.state != 'draft':
            # wizard = self.env['folio.cancel'].create({
            #     'booking_id': self.id,
            #     'reason_id': 1,
            #     'cancel_with_charge': '0',
            # })
            # wizard.button_cancel_folio()
            return {
                'type': 'ir.actions.act_window',
                'name': "Cancel Booking",
                'res_model': 'folio.cancel',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_booking_id': self.id,
                }
            }
        else:
            # for inv in self.invoice_ids:
            #     inv.button_cancel()
            self.state = 'cancelled'
            for folio in self.folio_ids:
                folio.button_cancel()
        # return res
