from odoo import models, fields


class UserTemplate(models.Model):
    _name = 'user.template'

    name = fields.Char(string='Name', required=True)
    groups_ids = fields.Many2many('res.groups', string='Groups')
    hide_menu_access_ids = fields.Many2many('ir.ui.menu', string='Hide Access Menu')
