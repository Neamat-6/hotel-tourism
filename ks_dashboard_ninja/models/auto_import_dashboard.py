from odoo import fields, models, api


import base64
from odoo import models, api, tools

class AutoImportDashboard(models.TransientModel):
    _inherit = 'ks_dashboard_ninja.import'  # reuse the existing wizard model

    @api.model
    def auto_import_dashboard_json(self):
        json_path = 'ks_dashboard_ninja/data/default_dashboard.json'
        file_data = tools.file_open(json_path, mode='rb').read()
        encoded_data = base64.b64encode(file_data)

        wizard = self.create({
            'ks_import_dashboard': encoded_data,
            'ks_top_menu_id': self.env.ref('hotel_booking.menu_front_office').id,
        })
        wizard.ks_do_action()
