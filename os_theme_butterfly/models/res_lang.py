# -*- coding: utf-8 -*-
# Part of Odoo Stars. See LICENSE file for full copyright and licensing details.

from odoo import models, fields


class Lang(models.Model):
    _inherit = "res.lang"

    country_id = fields.Many2one('res.country', string="Country")
