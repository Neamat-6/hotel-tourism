# -*- coding: utf-8 -*-
from . import models
from . import controllers
from odoo import api, SUPERUSER_ID
from odoo.addons.os_theme_butterfly.const import MENU_ITEM_ICONS, MODULE_ICONS
import base64
from odoo.modules.module import get_module_resource


def _uninstall_reset_changes(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env['web_editor.assets'].reset_asset('/os_theme_butterfly/static/src/theme/scss/os_custom_variables_fonts.scss', 'web.assets_backend')
    env['web_editor.assets'].reset_asset('/os_theme_butterfly/static/src/theme/scss/os_custom_variables.scss', 'web.assets_backend')
    env['web_editor.assets'].reset_asset('/os_theme_butterfly/static/src/theme/scss/login/os_custom_variables_login.scss', 'web._assets_login')


def icons_post_init_hook(cr, registry):
    """post init hook for changing module icons"""
    env = api.Environment(cr, SUPERUSER_ID, {})
    menu_items = env['ir.ui.menu'].with_context(lang='en_US').sudo().search([('parent_id', '=', False)])

    for menu in menu_items:
        if menu.name in MENU_ITEM_ICONS.keys():
            menu.os_web_icon_font = MENU_ITEM_ICONS.get(menu.name).get('os_web_icon_font')
            menu.os_web_icon_color = MENU_ITEM_ICONS.get(menu.name).get('os_web_icon_color') or ""
            menu.os_shape_color = MENU_ITEM_ICONS.get(menu.name).get('os_shape_color')

            img_name = MENU_ITEM_ICONS.get(menu.name).get('os_image_icon') if MENU_ITEM_ICONS.get(menu.name).get('os_image_icon') else 'default_image_app.png'
            img_path = get_module_resource('os_theme_butterfly', 'static/src/img/module_icons/%s' % env.company.os_apps_icon_style_image_pack, img_name)
            img_content = base64.b64encode(open(img_path, "rb").read())
            menu.os_image_icon = img_content

            module_name = menu._get_module_name()
            module = env['ir.module.module'].with_context(lang='en_US').sudo().search([('name', '=', module_name)])
            if module:
                module.os_web_icon_font = MENU_ITEM_ICONS.get(menu.name).get('os_web_icon_font')
                module.os_image_icon = img_content

    modules = env['ir.module.module'].with_context(lang='en_US').sudo().search([('state', '=', 'installed')])
    for module in modules:
        if module.name != 'os_theme_butterfly':
            if module.name in list(MODULE_ICONS.keys()) and not module.os_is_changed:
                module.os_web_icon_font = MODULE_ICONS.get(module.name).get('os_web_icon_font') if MODULE_ICONS.get(module.name) else 'las la-cubes'
                img_name = MODULE_ICONS.get(module.name).get('os_image_icon') if MODULE_ICONS.get(module.name) else 'default_image_app.png'
                img_path = get_module_resource('os_theme_butterfly', 'static/src/img/module_icons/%s' % env.company.os_apps_icon_style_image_pack, img_name)
                img_content = base64.b64encode(open(img_path, "rb").read())
                module.os_image_icon = img_content
