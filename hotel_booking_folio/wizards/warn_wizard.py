from odoo import api, fields, models, _


class WarnWizard(models.TransientModel):
    _name = 'warn.wizard'

    message = fields.Text(readonly=True)
    folio_id = fields.Many2one('booking.folio')
    booking_id = fields.Many2one('hotel.booking')

    def action_confirm(self):
        if self.booking_id:
            return {
                'type': 'ir.actions.act_window',
                'name': _('Booking'),
                'view_mode': 'form',
                'res_model': 'hotel.booking',
                'res_id': self.booking_id.id,
                'target': 'current'
            }
        elif self.folio_id:
            return {
                'type': 'ir.actions.act_window',
                'name': _('Folio'),
                'view_mode': 'form',
                'res_model': 'booking.folio',
                'res_id': self.folio_id.id,
                'target': 'current'
            }
        else:
            return {
                "type": "ir.actions.client",
                "tag": "reload"
            }

    def action_cancel(self):
        pass
