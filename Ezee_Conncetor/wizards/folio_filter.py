from odoo import fields, models, api


class FolioFilter(models.TransientModel):
    _inherit = 'folio.filter'

    def get_online_bookings(self):
        self.env['hotel.booking'].search([], limit=1).fetch_and_create_ezee_bookings()
