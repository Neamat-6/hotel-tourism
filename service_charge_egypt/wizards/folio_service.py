from odoo import fields, models, api


class FolioService(models.TransientModel):
    _inherit = 'folio.service'

    def create_folio_lines(self):
        lines = super(FolioService, self).create_folio_lines()
        for i, line in enumerate(lines):
            if line.particulars and 'Municipality' in line.particulars:
                line.particulars = line.particulars.replace('Municipality', 'Service Charge')
        return lines
