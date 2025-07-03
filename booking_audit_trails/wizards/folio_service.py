from odoo import fields, models, api


class FolioService(models.TransientModel):
    _inherit = 'folio.service'


    def button_add_service(self):
        result = super().button_add_service()
        self.env['audit.trails'].create({
            'booking_id': self.folio_id.booking_id.id,
            'folio_id': self.folio_id.id,
            'user_id': self.env.user.id,
            'operation': 'add_service',
            'datetime': fields.Datetime.now(),
            'notes': f'Add Service {self.service_id.name}'
        })
        return result