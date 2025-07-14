# -*- coding: utf-8 -*-
# Part of Odoo Stars. See LICENSE file for full copyright and licensing details.


from odoo import api, fields, models
from odoo.osv import expression


class IrUiMenu(models.Model):
    _name = 'ir.ui.menu'
    _description = 'Menu'
    _inherit = _name

    os_web_icon_font = fields.Char(string='Web Icon Font')
    os_web_icon_color = fields.Char(string='Web Icon Color')
    os_shape_color = fields.Char(string='Shape Color')
    os_image_icon = fields.Image(string='Image Icon')
    os_is_changed = fields.Boolean(string='Is changed')

    @api.model
    def os_load_menus_root_with_domain(self, domain):
        fields = ['name', 'sequence', 'parent_id', 'action', 'web_icon_data']
        domain = expression.AND([domain, [('parent_id', '=', False)]])
        menu_roots = self.with_context(lang=self.env.user.lang).search(domain)
        menu_roots_data = menu_roots.read(fields) if menu_roots else []

        menu_root = {
            'id': False,
            'name': 'root',
            'parent_id': [-1, ''],
            'children': menu_roots_data,
            'all_menu_ids': menu_roots.ids,
        }

        xmlids = menu_roots._get_menuitems_xmlids()
        for menu in menu_roots_data:
            menu['xmlid'] = xmlids[menu['id']]

        return menu_root

    def _get_module_name(self):
        return str(self.web_icon).split(",")[0]

    def write(self, vals):
        res = super(IrUiMenu, self).write(vals)
        if 'os_web_icon_font' in vals or 'os_image_icon' in vals:
            module = self.env['ir.module.module'].sudo().search([('name', '=', self._get_module_name())])
            module.os_web_icon_font = module.os_web_icon_font
            module.os_image_icon = self.os_image_icon
        return res
