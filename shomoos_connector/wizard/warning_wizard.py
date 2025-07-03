from odoo import api, fields, models, _


class WarningWizard(models.TransientModel):
    _name = 'warning.wizard'

    message = fields.Text(readonly=True)
    folio_id = fields.Many2one('booking.folio')

    def action_confirm(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Folio'),
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'booking.folio',
            'res_id': self.folio_id.id,
            'target': 'new'
        }

    def action_cancel(self):
        if self.folio_id:
            self.folio_id.button_undo_check_in()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Folio'),
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'booking.folio',
            'res_id': self.folio_id.id,
            'target': 'new'
        }
