# -*- coding: utf-8 -*-
# Part of Odoo Stars. See LICENSE file for full copyright and licensing details.
from odoo import models, api


class IrAsset(models.Model):
    _inherit = "ir.asset"

    @api.model_create_multi
    def create(self, vals_list):
        for val in vals_list:
            if 'path' in val and 'website_id' in val:
                if self.env.context.get('is_os_asset'):
                    val['website_id'] = False
        return super().create(vals_list)
