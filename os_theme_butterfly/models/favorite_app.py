# -*- coding: utf-8 -*-
# Part of Odoo Stars. See LICENSE file for full copyright and licensing details.
from odoo import models, fields


class FavoriteApp(models.Model):
    _name = 'os.favorite.app'
    _description = "Favorite app"
    _order = "sequence desc"

    name = fields.Char(string="Name", required=True)
    menu_id = fields.Many2one('ir.ui.menu', string="Menu", required=True)
    user_id = fields.Many2one('res.users', string="User", required=True)
    sequence = fields.Integer("Sequence", default=10)
