# -*- coding: utf-8 -*-
# Part of Odoo Stars. See LICENSE file for full copyright and licensing details.

from odoo import models, fields


class OsQuickCreate(models.Model):
    _name = "os.quick.create"
    _description = "OsQuickCreate"
    _order = "sequence"

    name = fields.Char("Name", required=True)
    icon = fields.Char("Icon", required=True)
    model = fields.Many2one('ir.model', required=True, ondelete='cascade')
    sequence = fields.Integer("Sequence", default=10)
    user_id = fields.Many2one("res.users", string="User", required=True, default=lambda self: self.env.uid)
