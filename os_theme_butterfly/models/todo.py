# -*- coding: utf-8 -*-
# Part of Odoo Stars. See LICENSE file for full copyright and licensing details.
from odoo import models, fields


class Todo(models.Model):
    _name = "os.todo"
    _description = "To Do"
    _order = "sequence"

    name = fields.Char("Name")
    is_done = fields.Boolean("Done")
    sequence = fields.Integer("Sequence", default=1)
    user_id = fields.Many2one("res.users", string="User", required=True, default=lambda self: self.env.uid)
