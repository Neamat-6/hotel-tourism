# -*- coding: utf-8 -*-
# Part of Odoo Stars. See LICENSE file for full copyright and licensing details.

from odoo import models, fields


class Bookmark(models.Model):
    _name = 'os.bookmark'
    _description = "Bookmark"
    _order = "sequence desc"

    name = fields.Char(string="Name", required=True)
    description = fields.Char(string="Description")
    icon = fields.Char(string="Icon")
    type = fields.Selection(
        selection=[
            ('internal', 'Internal'),
            ('external', 'External'),
        ],
        required=True,
        string="type of bookmark",
        default="internal"
    )
    link = fields.Char(string="Link",required=True)
    user_id = fields.Many2one('res.users', string="User", required=True)
    sequence = fields.Integer("Sequence", default=10)
