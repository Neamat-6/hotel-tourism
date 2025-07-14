# -*- coding: utf-8 -*-
# Part of Odoo Stars. See LICENSE file for full copyright and licensing details.
from odoo import fields, models
from odoo.addons.os_theme_butterfly.const import MENU_ITEM_ICONS, MODULE_ICONS
import base64
from odoo.modules.module import get_module_resource


class IrModuleModule(models.Model):
    _name = "ir.module.module"
    _description = 'Module'
    _inherit = _name

    os_web_icon_font = fields.Char("Web Icon Font")
    os_image_icon = fields.Image(string='Image Icon')
    os_is_changed = fields.Boolean(string='Is changed')

    def _button_immediate_function(self, function):
        res = super(IrModuleModule, self)._button_immediate_function(function)

        if function.__name__ != "button_uninstall":
            menu_items = self.env['ir.ui.menu'].with_context(lang='en_US').sudo().search([('parent_id', '=', False)])

            for menu in menu_items:
                # if self.name != 'os_theme_butterfly':

                if menu.name in list(MENU_ITEM_ICONS.keys()) and not menu.os_is_changed:
                    menu.os_web_icon_font = MENU_ITEM_ICONS.get(menu.name).get('os_web_icon_font') if MENU_ITEM_ICONS.get(menu.name) else 'las la-cubes'
                    menu.os_web_icon_color = MENU_ITEM_ICONS.get(menu.name).get('os_web_icon_color') if MENU_ITEM_ICONS.get(menu.name) else ''
                    menu.os_shape_color = MENU_ITEM_ICONS.get(menu.name).get('os_shape_color') if MENU_ITEM_ICONS.get(menu.name) else ''
                    img_name = MENU_ITEM_ICONS.get(menu.name).get('os_image_icon') if MENU_ITEM_ICONS.get(menu.name) else 'default_image_app.png'
                    img_path = get_module_resource('os_theme_butterfly', 'static/src/img/module_icons/%s' % self.env.company.os_apps_icon_style_image_pack, img_name)
                    img_content = base64.b64encode(open(img_path, "rb").read())
                    menu.os_image_icon = img_content

                    # self.os_web_icon_font = MENU_ITEM_ICONS.get(menu.name).get('os_web_icon_font')
                    # self.os_image_icon = img_content

            for module in self.search([]):
                if module.name in list(MODULE_ICONS.keys()) and not module.os_is_changed:
                    module.os_web_icon_font = MODULE_ICONS.get(module.name).get('os_web_icon_font') if MODULE_ICONS.get(module.name) else 'las la-cubes'
                    img_name = MODULE_ICONS.get(module.name).get('os_image_icon') if MODULE_ICONS.get(module.name) else 'default_image_app.png'
                    img_path = get_module_resource('os_theme_butterfly', 'static/src/img/module_icons/%s' % self.env.company.os_apps_icon_style_image_pack, img_name)
                    img_content = base64.b64encode(open(img_path, "rb").read())
                    module.os_image_icon = img_content

        return res
