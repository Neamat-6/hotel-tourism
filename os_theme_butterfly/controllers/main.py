# -*- coding: utf-8 -*-
# Part of Odoo Stars. See LICENSE file for full copyright and licensing details.
from odoo.http import request, route, Controller
from operator import itemgetter
from odoo.addons.web.controllers import main as web

import base64
from odoo.addons.os_theme_butterfly.const import MENU_ITEM_ICONS, MODULE_ICONS
from odoo.modules.module import get_module_resource


class Home(web.Home):
    @route()
    def web_load_menus(self, unique):
        response = super().web_load_menus(unique)
        response.headers['Cache-Control'] = 'no-cache'
        return response


class MainController(Controller):

    def update_icons(self, pack):
        menu_items = request.env['ir.ui.menu'].with_context(lang='en_US').sudo().search([('parent_id', '=', False)])
        modules = request.env['ir.module.module'].with_context(lang='en_US').sudo().search([])

        for menu in menu_items:
            if menu.name in list(MENU_ITEM_ICONS.keys()):
                img_name = MENU_ITEM_ICONS.get(menu.name).get('os_image_icon') if MENU_ITEM_ICONS.get(menu.name) else 'default_image_app.png'
                img_path = get_module_resource('os_theme_butterfly', 'static/src/img/module_icons/%s' % pack, img_name)
                img_content = base64.b64encode(open(img_path, "rb").read())
                menu.os_image_icon = img_content

        for module in modules:
            if module.name in list(MODULE_ICONS.keys()):
                module.os_web_icon_font = MODULE_ICONS.get(module.name).get('os_web_icon_font') if MODULE_ICONS.get(module.name) else 'las la-cubes'
                img_name = MODULE_ICONS.get(module.name).get('os_image_icon') if MODULE_ICONS.get(module.name) else 'default_image_app.png'
                img_path = get_module_resource('os_theme_butterfly', 'static/src/img/module_icons/%s' % pack, img_name)
                img_content = base64.b64encode(open(img_path, "rb").read())
                module.os_image_icon = img_content

    @route(['/get/installed/languages'], type='json', auth='public')
    def get_installed_languages(self):
        """
        Render the list of installed languages
        """
        langs = request.env['res.lang'].with_context(active_test=True).search([])
        return sorted([(lang.code, lang.name, lang.id, (lang.country_id and lang.country_id.code) or False) for lang in langs], key=itemgetter(1))

    @route(['/get/selected/language'], type='json', auth='public')
    def get_selected_language(self, selected_language):
        """
        To switch the user language
        :param selected_language: string of language short code
        """
        request.env.user.lang = selected_language

    @route(['/web/theme/user/save_settings'], type='json', auth='public')
    def userSaveThemeSettings(self, data):
        request.env.user.write(data)

    @route(['/web/theme/user/change_theme_mode'], type='json', auth='public')
    def userSaveThemeMode(self, data):
        request.env.user.write(data)

    @route(['/web/theme/company/save_settings'], type='json', auth='public')
    def companySaveThemeSettings(self, data):
        env_sudo = request.env.company.sudo()
        variables = {
            'accent-color': {'name': 'accent-color', 'value': env_sudo.os_theme_color_primary},
            'custom_color': {'name': 'custom_color', 'value': env_sudo.os_theme_custom_color},
            'separator_style': {'name': 'separator_style', 'value': env_sudo.os_separator_style},
            'separator_color': {'name': 'separator_color', 'value': env_sudo.os_separator_color},
            'breadcrumb_style': {'name': 'breadcrumb_style', 'value': env_sudo.os_breadcrumb_style},
            'tabs_style': {'name': 'tabs_style', 'value': env_sudo.os_tabs_style},
            'tabs_alignment': {'name': 'tabs_alignment', 'value': env_sudo.os_tabs_alignment},
            'buttons_style': {'name': 'buttons_style', 'value': env_sudo.os_buttons_style},
            'buttons_angles': {'name': 'buttons_angles', 'value': env_sudo.os_buttons_angles},
            'buttons_size': {'name': 'buttons_size', 'value': env_sudo.os_buttons_size},
            'radios_style': {'name': 'radios_style', 'value': env_sudo.os_radios_style},
            'checkbox_style': {'name': 'checkbox_style', 'value': env_sudo.os_checkbox_style},
            'shape_none_color_icon': {'name': 'shape_none_color_icon', 'value': env_sudo.os_shape_none_color_icon or False},
            'shape_style_unique_color': {'name': 'shape_style_unique_color', 'value': env_sudo.os_shape_style_unique_color or False},
            'shape_style_unique_color_icon': {'name': 'shape_style_unique_color_icon', 'value': env_sudo.os_shape_style_unique_color_icon or False},
            'shape_shadow': {'name': 'shape_shadow', 'value': env_sudo.os_shape_shadow},
            'list_view_header_fg_color': {'name': 'list_view_header_fg_color', 'value': env_sudo.os_list_view_header_fg_color or False},
            'list_view_header_bg_color': {'name': 'list_view_header_bg_color', 'value': env_sudo.os_list_view_header_bg_color or False},
            'list_view_style_spaced': {'name': 'list_view_style_spaced', 'value': env_sudo.os_list_view_style_spaced},
            'list_view_style_separate': {'name': 'list_view_style_separate', 'value': env_sudo.os_list_view_style_separate},
            'list_view_style_hover': {'name': 'list_view_style_hover', 'value': env_sudo.os_list_view_style_hover},
            'modal_animated_entrance': {'name': 'modal_animated_entrance', 'value': env_sudo.os_modal_animated_entrance},
        }

        if data['os_separator_color'].replace(" ", "") == "":
            os_separator_color = env_sudo.os_theme_color_primary
            env_sudo.os_separator_color = env_sudo.os_theme_color_primary
        else:
            os_separator_color = data['os_separator_color']

        if data['os_theme_color_primary'] and data['os_theme_color_primary'] != env_sudo.os_theme_color_primary:
            variables['accent-color'] = {'name': 'accent-color', 'value': data['os_theme_color_primary']}

        if data['os_theme_custom_color'] != env_sudo.os_theme_custom_color != "":
            variables['custom_color'] = {'name': 'custom_color', 'value': data['os_theme_custom_color']}

        if data['os_separator_style'] != env_sudo.os_separator_style:
            variables['separator_style'] = {'name': 'separator_style', 'value': data['os_separator_style']}

        if data['os_separator_color'] != env_sudo.os_separator_color:
            variables['separator_color'] = {'name': 'separator_color', 'value': os_separator_color}

        if data['os_breadcrumb_style'] != env_sudo.os_breadcrumb_style:
            variables['breadcrumb_style'] = {'name': 'breadcrumb_style', 'value': data['os_breadcrumb_style']}

        if data['os_tabs_style'] != env_sudo.os_tabs_style:
            variables['tabs_style'] = {'name': 'tabs_style', 'value': data['os_tabs_style']}

        if data['os_tabs_alignment'] != env_sudo.os_tabs_alignment:
            variables['tabs_alignment'] = {'name': 'tabs_alignment', 'value': data['os_tabs_alignment']}

        if data['os_buttons_style'] != env_sudo.os_buttons_style:
            variables['buttons_style'] = {'name': 'buttons_style', 'value': data['os_buttons_style']}

        if data['os_buttons_angles'] != env_sudo.os_buttons_angles:
            variables['buttons_angles'] = {'name': 'buttons_angles', 'value': data['os_buttons_angles']}

        if data['os_buttons_size'] != env_sudo.os_buttons_size:
            variables['buttons_size'] = {'name': 'buttons_size', 'value': data['os_buttons_size']}

        if data['os_radios_style'] != env_sudo.os_radios_style:
            variables['radios_style'] = {'name': 'radios_style', 'value': data['os_radios_style']}

        if data['os_checkbox_style'] != env_sudo.os_checkbox_style:
            variables['checkbox_style'] = {'name': 'checkbox_style', 'value': data['os_checkbox_style']}

        if data['os_shape_none_color_icon'] != env_sudo.os_shape_none_color_icon:
            os_shape_none_color_icon = False
            if data['os_shape_none_color_icon'].replace(" ", "") != "":
                os_shape_none_color_icon = data['os_shape_none_color_icon'].replace(" ", "")
            env_sudo.os_shape_none_color_icon = os_shape_none_color_icon
            variables['shape_none_color_icon'] = {'name': 'shape_none_color_icon', 'value': os_shape_none_color_icon}

        if data['os_shape_style_unique_color'] != env_sudo.os_shape_style_unique_color:
            os_shape_style_unique_color = False
            if data['os_shape_style_unique_color'].replace(" ", "") != "":
                os_shape_style_unique_color = data['os_shape_style_unique_color'].replace(" ", "")
            env_sudo.os_shape_style_unique_color = os_shape_style_unique_color
            variables['shape_style_unique_color'] = {'name': 'shape_style_unique_color', 'value': os_shape_style_unique_color}

        if data['os_shape_style_unique_color_icon'] != env_sudo.os_shape_style_unique_color_icon:
            os_shape_style_unique_color_icon = False
            if data['os_shape_style_unique_color_icon'].replace(" ", "") != "":
                os_shape_style_unique_color_icon = data['os_shape_style_unique_color_icon'].replace(" ", "")
            env_sudo.os_shape_style_unique_color_icon = os_shape_style_unique_color_icon
            variables['shape_style_unique_color_icon'] = {'name': 'shape_style_unique_color_icon', 'value': os_shape_style_unique_color_icon}

        if data['os_shape_shadow'] != env_sudo.os_shape_shadow:
            variables['shape_shadow'] = {'name': 'shape_shadow', 'value': data['os_shape_shadow']}

        if data['os_list_view_header_fg_color'] != env_sudo.os_list_view_header_fg_color:
            os_list_view_header_fg_color = False
            if data['os_list_view_header_fg_color'].replace(" ", "") != "":
                os_list_view_header_fg_color = data['os_list_view_header_fg_color'].replace(" ", "")
            env_sudo.os_list_view_header_fg_color = os_list_view_header_fg_color
            variables['list_view_header_fg_color'] = {'name': 'list_view_header_fg_color', 'value': os_list_view_header_fg_color}

        if data['os_list_view_header_bg_color'] != env_sudo.os_list_view_header_bg_color:
            os_list_view_header_bg_color = False
            if data['os_list_view_header_bg_color'].replace(" ", "") != "":
                os_list_view_header_bg_color = data['os_list_view_header_bg_color'].replace(" ", "")
            env_sudo.os_list_view_header_bg_color = os_list_view_header_bg_color
            variables['list_view_header_bg_color'] = {'name': 'list_view_header_bg_color', 'value': os_list_view_header_bg_color}

        if data['os_list_view_style_spaced'] != env_sudo.os_list_view_style_spaced:
            variables['list_view_style_spaced'] = {'name': 'list_view_style_spaced', 'value': data['os_list_view_style_spaced']}

        if data['os_list_view_style_separate'] != env_sudo.os_list_view_style_separate:
            variables['list_view_style_separate'] = {'name': 'list_view_style_separate', 'value': data['os_list_view_style_separate']}

        if data['os_list_view_style_hover'] != env_sudo.os_list_view_style_hover:
            variables['list_view_style_hover'] = {'name': 'list_view_style_hover', 'value': data['os_list_view_style_hover']}

        if data['os_modal_animated_entrance'] != env_sudo.os_modal_animated_entrance:
            variables['modal_animated_entrance'] = {'name': 'modal_animated_entrance', 'value': data['os_modal_animated_entrance']}

        if data['os_apps_icon_style_image_pack'] != env_sudo.os_apps_icon_style_image_pack:
            self.update_icons(data['os_apps_icon_style_image_pack'])

        variables_fonts = []
        use_base_google_font = False
        use_alt_google_font = False

        if data['os_theme_base_font'] != env_sudo.os_theme_base_font:
            default_base = "Roboto"
            os_theme_base_font = default_base
            if data['os_theme_base_font'] != "custom":
                os_theme_base_font = data['os_theme_base_font']
            else:
                if len(data["os_theme_base_custom_google_font"]) > 0:
                    os_theme_base_font = data['os_theme_base_custom_google_font']
            if os_theme_base_font != default_base:
                use_base_google_font = True

            variables_fonts.append({'name': 'use_base_google_font', 'value': use_base_google_font})
            variables_fonts.append({'name': 'base_google_font_family', 'value': os_theme_base_font})

        if data['os_theme_alt_font'] != env_sudo.os_theme_alt_font:
            default_alt = "Nunito"
            os_theme_alt_font = default_alt
            if data['os_theme_alt_font'] != "custom":
                os_theme_alt_font = data['os_theme_alt_font']
            else:
                if len(data["os_theme_alt_custom_google_font"]) > 0:
                    os_theme_alt_font = data['os_theme_alt_custom_google_font']
            if os_theme_alt_font != default_alt:
                use_alt_google_font = True
            variables_fonts.append({'name': 'use_alt_google_font', 'value': use_alt_google_font})
            variables_fonts.append({'name': 'alt_google_font_family', 'value': os_theme_alt_font})

        request.env['web_editor.assets'].sudo().replace_variables_values(
            '/os_theme_butterfly/static/src/theme/scss/os_custom_variables_fonts.scss', 'web.assets_backend', variables_fonts
        )

        request.env['web_editor.assets'].sudo().replace_variables_values(
            '/os_theme_butterfly/static/src/theme/scss/os_custom_variables.scss', 'web.assets_backend', list(variables.values())
        )

        if data['os_login_style'] != env_sudo.os_login_style or data['os_login_background_color'] != env_sudo.os_login_background_color or data['os_theme_color_primary'] != env_sudo.os_theme_color_primary:
            os_login_background_color = False
            if data['os_login_background_color'].replace(" ", "") != "":
                os_login_background_color = data['os_login_background_color'].replace(" ", "")
            env_sudo.os_login_background_color = os_login_background_color
            variables_login = [{'name': 'login_style', 'value': data['os_login_style']}, {'name': 'login_background_color', 'value': os_login_background_color}, {'name': 'accent-color', 'value': data['os_theme_color_primary']}]
            request.env['web_editor.assets'].sudo().replace_variables_values(
                '/os_theme_butterfly/static/src/theme/scss/login/os_custom_variables_login.scss', 'web._assets_login', variables_login
            )
        env_sudo.sudo().write(data)

    @route(['/web/theme/user/reset_settings'], type='json', auth='public')
    def userResetThemeSettings(self):
        request.env.user.os_resetDefaultSettings()

    @route(['/web/theme/company/reset_settings'], type='json', auth='public')
    def companyResetThemeSettings(self):
        env_sudo = request.env.company.sudo()
        env_sudo.os_resetDefaultSettings()
        # Change also color primary because it is also changed
        # TODO see what else to reset
        variables = [
            {'name': 'accent-color', 'value': env_sudo.os_theme_color_primary},
        ]
        request.env['web_editor.assets'].sudo().replace_variables_values(
            '/os_theme_butterfly/static/src/theme/scss/os_custom_variables.scss', 'web.assets_backend', variables
        )

    @route('/theme/upload_image', type='http', auth="user")
    def theme_upload_image(self, field):
        env_sudo = request.env.company.sudo()
        files = request.httprequest.files.getlist('ufile')
        for ufile in files:
            datas = base64.encodebytes(ufile.read())
            env_sudo[field] = datas

    @route('/theme/icons/save_settings', type='json', auth='public')
    def theme_apps_icon_settings(self, app_id, icon_font, icon_color, shape_color):
        if app_id and icon_font:
            menu = request.env['ir.ui.menu'].sudo().search([('id', '=', int(app_id))])
            if menu:
                if menu.os_web_icon_font != icon_font or menu.os_web_icon_color != icon_color or menu.os_shape_color != shape_color:
                    menu.write({
                        'os_web_icon_font': icon_font,
                        'os_web_icon_color': icon_color,
                        'os_shape_color': shape_color,
                        'os_is_changed': True
                    })
                    module_name = menu._get_module_name()
                    module = request.env['ir.module.module'].with_context(lang='en_US').sudo().search([('name', '=', module_name)])
                    if module:
                        module.os_is_changed = True
            return True
        return False

    @route('/theme/icons/reset_settings', type='json', auth='public')
    def theme_apps_icon_reset_settings(self, app_id, type_icon):
        env_sudo = request.env.company.sudo()

        if app_id:
            menu = request.env['ir.ui.menu'].with_context(lang='en_US').sudo().search([('id', '=', int(app_id))])
            if menu:
                if menu.name in list(MENU_ITEM_ICONS.keys()):
                    menu.os_web_icon_font = MENU_ITEM_ICONS.get(menu.name).get('os_web_icon_font')
                    menu.os_web_icon_color = MENU_ITEM_ICONS.get(menu.name).get('os_web_icon_color')
                    menu.os_shape_color = MENU_ITEM_ICONS.get(menu.name).get('os_shape_color')

                    img_name = MENU_ITEM_ICONS.get(menu.name).get('os_image_icon') if MENU_ITEM_ICONS.get(menu.name).get('os_image_icon') else 'default_icon_app.png'
                    img_path = get_module_resource('os_theme_butterfly', 'static/src/img/module_icons/%s' % env_sudo.os_apps_icon_style_image_pack, img_name)
                    img_content = base64.b64encode(open(img_path, "rb").read())
                    menu.os_image_icon = img_content
                    menu.os_is_changed = False
                    module_name = menu._get_module_name()
                    module = request.env['ir.module.module'].with_context(lang='en_US').sudo().search([('name', '=', module_name)])
                    if module:
                        module.os_is_changed = False

        return True

    @route('/theme/icons/image/set_file', methods=['POST'], csrf=False)
    def set_os_image_icon(self, ufile, app_id, jsonp='callback'):
        if app_id and ufile:
            menu = request.env['ir.ui.menu'].sudo().search([('id', '=', int(app_id))])
            if menu:
                menu.write({
                    'os_image_icon': base64.encodebytes(ufile.read()),
                    'os_is_changed': True
                })

                module_name = menu._get_module_name()
                module = request.env['ir.module.module'].sudo().search([('name', '=', module_name)])
                if module:
                    module.sudo().write({
                        'os_is_changed': True
                    })
