# -*- coding: utf-8 -*-
# Part of Odoo Stars. See LICENSE file for full copyright and licensing details.
from odoo import models
from odoo.http import request


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    def os_get_settings_icons(self):
        icons = {}
        modules = self.env['ir.module.module'].sudo().search([])
        if self.env.company.os_apps_icon_style == "default":
            icons = {
                'default': '/os_theme_butterfly/static/src/img/default_icon_app.png',
                'general_settings': '/base/static/description/settings.png',
            }
            for module in modules:
                icons.update({module.name: '/web/image?model=ir.module.module&id=%s&field=icon_image' % module.id})

        if self.env.company.os_apps_icon_style == "font":
            icons = {
                'default': 'osi osi-edit',
                'general_settings': 'osi osi-setting-alt',
            }
            for module in modules:
                icons.update({module.name: module.os_web_icon_font})

        if self.env.company.os_apps_icon_style == "image":
            icons = {
                'default': '/os_theme_butterfly/static/src/img/default_image_app.png',
                'general_settings': '/os_theme_butterfly/static/src/img/module_icons/%s/Settings.png' % request.env.company.os_apps_icon_style_image_pack,
            }
            for module in modules:
                icons.update({module.name: '/web/image?model=ir.module.module&id=%s&field=os_image_icon' % module.id})
        return icons

    def session_info(self):
        info = super().session_info()
        if request.env.user.has_group('base.group_user'):
            info["user_email"] = self.env.user.email
            # User Theme Settings
            info["user_header_style"] = self.env.user.os_header_style
            info["user_sidebar_style"] = self.env.user.os_sidebar_style
            info["user_theme_mode"] = self.env.user.os_theme_mode
            info["user_chatter_position"] = self.env.user.os_chatter_position
            info["user_dbl_click_edit"] = self.env.user.os_dbl_click_edit
            info["user_display_todo_list"] = self.env.user.os_display_todo_list
            info["user_display_recently_viewed_records"] = self.env.user.os_display_recently_viewed_records
            info["user_display_zoom_in_out"] = self.env.user.os_display_zoom_in_out
            info["user_display_full_screen"] = self.env.user.os_display_full_screen
            info["user_display_bookmarks"] = self.env.user.os_display_bookmarks
            info["user_display_favorite_apps"] = self.env.user.os_display_favorite_apps
            info["user_show_sidebar"] = self.env.user.os_show_sidebar
            info["user_header_tools_bar_fixed"] = self.env.user.os_header_tools_bar_fixed
            info["user_show_quick_create"] = self.env.user.os_show_quick_create
            info["home_action_name"] = self.env.user.action_id and self.env.user.action_id.name or False
            info["user_use_same_apps_icons_style_for_sidebar"] = self.env.user.os_use_same_apps_icons_style_for_sidebar
            info["user_has_group_theme_admin"] = self.env.user.has_group('os_theme_butterfly.group_theme_admin') and True or False

            # Company Theme Settings
            info["company_header_style"] = self.env.company.os_header_style
            info["company_show_sidebar"] = self.env.company.os_show_sidebar
            info["company_header_tools_bar_fixed"] = self.env.company.os_header_tools_bar_fixed
            info["company_list_view_header_bg_color"] = self.env.company.os_list_view_header_bg_color
            info["company_list_view_header_fg_color"] = self.env.company.os_list_view_header_fg_color
            info["company_show_quick_create"] = self.env.company.os_show_quick_create
            info["company_sidebar_style"] = self.env.company.os_sidebar_style
            info["company_theme_mode"] = self.env.company.os_theme_mode
            info["company_theme_color_primary"] = self.env.company.os_theme_color_primary
            info["company_theme_custom_color"] = self.env.company.os_theme_custom_color
            info["company_chatter_position"] = self.env.company.os_chatter_position
            info["company_loader_style"] = self.env.company.os_loader_style
            info["company_dbl_click_edit"] = self.env.company.os_dbl_click_edit
            info["company_display_todo_list"] = self.env.company.os_display_todo_list

            info["company_display_bookmarks"] = self.env.company.os_display_bookmarks
            info["company_display_favorite_apps"] = self.env.company.os_display_favorite_apps
            info["company_display_recently_viewed_records"] = self.env.company.os_display_recently_viewed_records
            info["company_display_zoom_in_out"] = self.env.company.os_display_zoom_in_out
            info["company_display_full_screen"] = self.env.company.os_display_full_screen
            info["company_show_user_settings"] = self.env.company.os_show_user_settings
            info["company_chart_color_palette"] = self.env.company.os_chart_color_palette
            info["company_display_favorite_apps"] = self.env.company.os_display_favorite_apps
            info["company_display_recently_viewed_records"] = self.env.company.os_display_recently_viewed_records
            info["company_display_zoom_in_out"] = self.env.company.os_display_zoom_in_out
            info["company_display_full_screen"] = self.env.company.os_display_full_screen
            info["company_web_window_title"] = self.env.company.os_web_window_title
            info["company_activate_web_ribbon"] = self.env.company.os_activate_web_ribbon
            info["company_web_ribbon_text"] = self.env.company.os_web_ribbon_text
            info["company_web_ribbon_bg"] = self.env.company.os_web_ribbon_bg
            info["company_web_ribbon_fg"] = self.env.company.os_web_ribbon_fg
            info["company_separator_style"] = self.env.company.os_separator_style
            info["company_separator_color"] = self.env.company.os_separator_color
            info["company_breadcrumb_style"] = self.env.company.os_breadcrumb_style

            # Login page
            info["company_os_login_style"] = self.env.company.os_login_style
            info["company_os_login_title"] = self.env.company.os_login_title
            info["company_os_login_subtitle"] = self.env.company.os_login_subtitle
            info["company_os_login_background_type"] = self.env.company.os_login_background_type
            info["company_login_background_color"] = self.env.company.os_login_background_color
            info["company_os_login_background_image"] = self.env.company.os_login_background_image and True or False

            # Apps view
            info["company_apps_view_background_type"] = self.env.company.os_apps_view_background_type
            info["company_apps_view_background_color"] = self.env.company.os_apps_view_background_color
            info["company_apps_view_background_image"] = self.env.company.os_apps_view_background_image and True or False
            info["company_apps_view_text_color"] = self.env.company.os_apps_view_text_color

            # Fonts
            info["company_theme_base_font"] = self.env.company.os_theme_base_font
            info["company_theme_alt_font"] = self.env.company.os_theme_alt_font
            info["company_theme_base_custom_google_font"] = self.env.company.os_theme_base_custom_google_font
            info["company_theme_alt_custom_google_font"] = self.env.company.os_theme_alt_custom_google_font

            info["company_tabs_style"] = self.env.company.os_tabs_style
            info["company_tabs_alignment"] = self.env.company.os_tabs_alignment
            info["company_buttons_style"] = self.env.company.os_buttons_style
            info["company_buttons_angles"] = self.env.company.os_buttons_angles
            info["company_buttons_size"] = self.env.company.os_buttons_size
            info["company_radios_style"] = self.env.company.os_radios_style
            info["company_checkbox_style"] = self.env.company.os_checkbox_style
            info["company_list_view_style_spaced"] = self.env.company.os_list_view_style_spaced
            info["company_list_view_style_separate"] = self.env.company.os_list_view_style_separate
            info["company_list_view_style_hover"] = self.env.company.os_list_view_style_hover
            info["company_list_view_sticky_header_footer"] = self.env.company.os_list_view_sticky_header_footer
            info["company_os_shape"] = self.env.company.os_shape
            info["company_os_shape_style"] = self.env.company.os_shape_style
            info["company_os_shape_shadow"] = self.env.company.os_shape_shadow
            info["company_os_shape_none_color_icon"] = self.env.company.os_shape_none_color_icon
            info["company_os_shape_style_unique_color"] = self.env.company.os_shape_style_unique_color
            info["company_os_shape_style_unique_color_icon"] = self.env.company.os_shape_style_unique_color_icon
            info["company_use_same_apps_icons_style_for_sidebar"] = self.env.company.os_use_same_apps_icons_style_for_sidebar
            info["theme_settings_icons"] = self.os_get_settings_icons()
            info["company_os_apps_icon_style"] = self.env.company.os_apps_icon_style
            info["company_apps_icon_style_image_pack"] = self.env.company.os_apps_icon_style_image_pack
            info["company_modal_animated_entrance"] = self.env.company.os_modal_animated_entrance
            info["company_modal_animated_entrance_value"] = self.env.company.os_modal_animated_entrance_value
        return info
