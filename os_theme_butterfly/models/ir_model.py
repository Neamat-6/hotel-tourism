# -*- coding: utf-8 -*-
# Part of Odoo Stars. See LICENSE file for full copyright and licensing details.
from odoo import models, api


class IrModel(models.Model):
    _inherit = "ir.model"

    @api.model
    def os_get_models(self, domain):
        models = self.sudo().search(domain)
        result = []
        for model in models:
            if self.env[model.model].check_access_rights("write", raise_exception=False):
                result.append(
                    {"id": model.id, "name": model.name, "model": model.model})
        return result
