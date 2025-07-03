import requests
import json
from requests.auth import HTTPBasicAuth
from odoo import fields, models, api
from datetime import datetime


class FolioService(models.TransientModel):
    _inherit = 'folio.service'

    ntmp_service_id = fields.Many2one('ntmp.expense.type', string='NTMP Expense')

    @api.onchange('service_id')
    def onchange_service_id(self):
        if self.service_id:
            self.price = self.service_id.price_include_tax
            self.ntmp_service_id = self.service_id.ntmp_service_id.id

    def create_folio_lines(self):
        lines = super(FolioService, self).create_folio_lines()
        for i, line in enumerate(lines):
            if line.type != 'tax':
                line.write({
                    'ntmp_service_id': self.ntmp_service_id.id,
                    'ntmp_item_number': str(datetime.today().timestamp())[:8] + str(i),
                })
        return lines
