/** @odoo-module **/

import {registry} from "@web/core/registry";
import {session} from "@web/session";

export const userSettingsService = {
    start() {
        return {
            os_sidebar_style: session.user_sidebar_style,
            os_header_style: session.user_header_style,
            os_theme_mode: session.user_theme_mode,
            os_chatter_position: session.user_chatter_position,
            os_dbl_click_edit: session.user_dbl_click_edit,
            os_display_todo_list: session.user_display_todo_list,
            os_display_bookmarks: session.user_display_bookmarks,
            os_display_favorite_apps: session.user_display_favorite_apps,
            os_display_recently_viewed_records: session.user_display_recently_viewed_records,
            os_display_zoom_in_out: session.user_display_zoom_in_out,
            os_display_full_screen: session.user_display_full_screen,
            os_show_sidebar: session.user_show_sidebar,
            os_header_tools_bar_fixed: session.user_header_tools_bar_fixed,
            os_show_quick_create: session.user_show_quick_create,
            os_home_action_name: session.home_action_name,
            same_icons: session.user_use_same_apps_icons_style_for_sidebar,
            os_has_group_theme_admin: session.user_has_group_theme_admin,
        };
    },
};

export const companySettingsService = {
    start() {
        this.default_skins = ['#4f46e5', '#aa4586', '#86bc42', '#7a19ca', '#c60f0f', '#3a3973'];
        return {
            default_skins: this.default_skins,
            os_sidebar_style: session.company_sidebar_style,
            os_show_sidebar: session.company_show_sidebar,
            os_header_tools_bar_fixed: session.company_header_tools_bar_fixed,
            os_show_quick_create: session.company_show_quick_create,
            os_header_style: session.company_header_style,
            os_theme_mode: session.company_theme_mode,
            os_theme_color_primary: session.company_theme_color_primary,
            os_theme_custom_color: session.company_theme_custom_color,
            is_custom_color: session.company_theme_color_primary === session.company_theme_custom_color,
            os_chatter_position: session.company_chatter_position,
            os_loader_style: session.company_loader_style,
            os_dbl_click_edit: session.company_dbl_click_edit,
            os_display_todo_list: session.company_display_todo_list,
            os_display_bookmarks: session.company_display_bookmarks,
            os_display_favorite_apps: session.company_display_favorite_apps,
            os_display_recently_viewed_records: session.company_display_recently_viewed_records,
            os_display_zoom_in_out: session.company_display_zoom_in_out,
            os_display_full_screen: session.company_display_full_screen,
            os_show_user_settings: session.company_show_user_settings,
            os_web_window_title: session.company_web_window_title,
            // #Ribbon
            os_activate_web_ribbon: session.company_activate_web_ribbon,
            os_web_ribbon_text: session.company_web_ribbon_text,
            os_web_ribbon_bg: session.company_web_ribbon_bg,
            os_web_ribbon_fg: session.company_web_ribbon_fg,
            // #Separator
            os_separator_style: session.company_separator_style,
            os_separator_color: session.company_separator_color,
            os_breadcrumb_style: session.company_breadcrumb_style,
            //Login
            os_login_style: session.company_os_login_style,
            os_login_title: session.company_os_login_title,
            os_login_subtitle: session.company_os_login_subtitle,
            os_apps_view_background_type: session.company_apps_view_background_type,
            os_apps_view_background_color: session.company_apps_view_background_color,
            os_apps_view_background_image: session.company_apps_view_background_image,
            os_apps_view_text_color: session.company_apps_view_text_color,

            //Apps view
            os_login_background_type: session.company_os_login_background_type,
            os_login_background_color: session.company_login_background_color,
            os_login_background_image: session.company_os_login_background_image,
            //fonts
            os_theme_base_font: session.company_theme_base_font,
            os_theme_alt_font: session.company_theme_alt_font,
            os_theme_base_custom_google_font: session.company_theme_base_custom_google_font,
            os_theme_alt_custom_google_font: session.company_theme_alt_custom_google_font,

            os_tabs_style: session.company_tabs_style,
            os_tabs_alignment: session.company_tabs_alignment,
            os_buttons_style: session.company_buttons_style,
            os_buttons_angles: session.company_buttons_angles,
            os_buttons_size: session.company_buttons_size,
            os_radios_style: session.company_radios_style,
            os_checkbox_style: session.company_checkbox_style,
            os_shape: session.company_os_shape,
            os_shape_style: session.company_os_shape_style,
            os_shape_shadow: session.company_os_shape_shadow,
            os_shape_none_color_icon: session.company_os_shape_none_color_icon,
            os_shape_style_unique_color: session.company_os_shape_style_unique_color,
            os_shape_style_unique_color_icon: session.company_os_shape_style_unique_color_icon,
            same_icons: session.company_use_same_apps_icons_style_for_sidebar,
            os_apps_icon_style: session.company_os_apps_icon_style,
            os_list_view_style_spaced: session.company_list_view_style_spaced,
            os_list_view_style_separate: session.company_list_view_style_separate,
            os_list_view_style_hover: session.company_list_view_style_hover,
            os_list_view_header_bg_color: session.company_list_view_header_bg_color,
            os_list_view_header_fg_color: session.company_list_view_header_fg_color,
            os_list_view_sticky_header_footer: session.company_list_view_sticky_header_footer,
            os_chart_color_palette: session.company_chart_color_palette,
            os_apps_icon_style_image_pack: session.company_apps_icon_style_image_pack,
            os_modal_animated_entrance: session.company_modal_animated_entrance,
            os_modal_animated_entrance_value: session.company_modal_animated_entrance_value,
        }
    },
};

registry.category("services").add("os_user_settings", userSettingsService);
registry.category("services").add("os_company_settings", companySettingsService);
