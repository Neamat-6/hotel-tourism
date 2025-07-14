# -*- coding: utf-8 -*-
# Part of Odoo Stars. See LICENSE file for full copyright and licensing details.


from odoo import models, fields


class RecentlyViewedRecord(models.Model):
    _name = 'os.recently.viewed.record'
    _description = "Recently Viewed Records"
    _order = "create_date desc"

    name = fields.Char(string="Name", required=True)
    user_id = fields.Many2one('res.users', string="User", required=True)
    res_id = fields.Char(string="Record Id", required=True)
    model = fields.Char(string="Model", required=True)
    action = fields.Char(string="Action", required=False)
