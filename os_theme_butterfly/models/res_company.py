# -*- coding: utf-8 -*-
# Part of Odoo Stars. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api


class ResCompany(models.Model):
    _inherit = 'res.company'

    # -------------------- Login page Styles ----------------------------
    os_login_style = fields.Selection([
        ('default', 'Odoo Standard'),
        ('style_1', 'Style 1'),
        ('style_2', 'Style 2'),
        ('style_3', 'Style 3'),
        ('style_4', 'Style 4'),
        ('style_5', 'Style 5'),
        ('style_6', 'Style 6'),
    ],
        default="style_1",
        string="Login page style"
    )
    os_login_background_type = fields.Selection([
        ('default', 'Default'),
        ('bg_color', 'Color'),
        ('bg_img', 'Image')
    ],
        string="Login Background Type",
        default="default"
    )
    os_login_background_image = fields.Image(string='Login page Background Image', attachment=True)
    os_login_background_color = fields.Char(string='Login Background Color')
    os_login_title = fields.Char(string='Login Title')
    os_login_subtitle = fields.Char(string='Login Subtitle')

    # -------------------- Apps Drawer ----------------------------
    os_apps_icon_style = fields.Selection(
        selection=[
            ('default', 'Default'),
            ('font', 'Font Icon'),
            ('image', 'Image'),
        ],
        required=True,
        string="Apps Icon Type",
        default="font"
    )
    os_apps_icon_style_image_pack = fields.Selection(
        selection=[
            ('pack01', 'Pack 1'),
            ('pack02', 'Pack 2'),
            ('pack03', 'Pack 3'),
            ('pack04', 'Pack 4'),
            ('pack05', 'Pack 5'),
            ('pack06', 'Pack 6'),
            ('pack07', 'Pack 7'),
            ('pack08', 'Pack 8'),
        ],
        required=True,
        string="Icons images pack",
        default="pack01"
    )
    os_shape = fields.Selection(
        selection=[
            ('none', 'None'),
            ('square', 'Square'),
            ('rounded', 'Rounded'),
            ('circle', 'Circle'),
            ('pentagon', 'Pentagon'),
            ('hexagon', 'Hexagon'),
            ('heptagon', 'Heptagon'),
            ('octagon', 'Octagon'),
            ('nonagon', 'Nonagon'),
            ('decagon', 'Decagon'),
            ('rhombus', 'Rhombus'),
        ],
        required=True,
        string="Shape",
        default="rounded"
    )
    os_shape_none_color_icon = fields.Char("Icon color if shape is none", default="#222")
    os_shape_style = fields.Selection(
        selection=[
            ('unique_color', 'Unique Color'),
            ('simple', 'Simple Colored'),
            ('soft', 'Soft'),
            ('gradient', 'Gradient'),
        ],
        required=True,
        string="Shape Style",
        default="simple"
    )
    os_shape_style_unique_color = fields.Char(
        string='Color of shape (unique_color)',
        default="#4f46e5"
    )
    os_shape_style_unique_color_icon = fields.Char(
        string='Color of icons (unique_color)',
        default="#fefefe"
    )
    os_shape_shadow = fields.Boolean(
        string='Enable shadow for shapes icon (Only type os_apps_icon_style= font)',
        default=False
    )
    os_apps_view_background_type = fields.Selection([
        ('default', 'Default'),
        ('bg_color', 'Color'),
        ('bg_img', 'Image')
    ], string="Apps Background Type", default="default")
    os_apps_view_background_image = fields.Image(string='Apps view Background Image', attachment=True)
    os_apps_view_background_color = fields.Char(string='Apps view Background Color')
    os_apps_view_text_color = fields.Char(string='Text Color for apps')

    # -------------------- Theme Logo ----------------------------
    os_theme_logo_white = fields.Image(string='Theme Logo white (260x80)', attachment=True)
    os_theme_logo_dark = fields.Image(string='Theme Logo dark (260x80)', attachment=True)
    os_theme_logo_small = fields.Image(string='Theme Logo small (80x80) ', attachment=True)

    # -------------------- Sidebar Style  ----------------------------
    os_sidebar_style = fields.Selection(
        selection=[
            ('is-light', 'White'),
            ('is-gray-light', 'Light'),
            ('is-dark', 'Dark'),
            ('is-theme', 'Theme')
        ],
        required=True,
        string="Sidebar Style",
        default='is-theme'
    )

    os_use_same_apps_icons_style_for_sidebar = fields.Boolean(string='Use same Apps icon style for sidebar', default=False)

    # -------------------- Header Style  ----------------------------
    os_header_style = fields.Selection(
        selection=[
            ('is-light', 'White'),
            ('is-gray-light', 'Light'),
            ('is-dark', 'Dark'),
            ('is-theme', 'Theme')
        ],
        required=True,
        string="Header Style",
        default='is-light'
    )
    os_header_tools_bar_fixed = fields.Boolean(string='Fixed header Tools bar', default=False)

    # -------------------- General Settings  ----------------------------
    os_theme_mode = fields.Selection(
        selection=[
            ('light-mode', 'Light Mode'),
            ('dark-mode', 'Dark Mode'),
        ],
        required=True,
        help="Select Dark or Light Mode",
        string="Theme Mode",
        default='light-mode'
    )

    os_chatter_position = fields.Selection(
        selection=[
            ('normal', 'Normal'),
            ('sided', 'Sided'),
        ],
        required=True,
        string="Chatter Position",
        default="normal"
    )
    os_web_window_title = fields.Char('Web Window Title', default='Odoo')

    # -------------------- Theme Colors  ----------------------------
    os_theme_color_brand = fields.Char(string='Brand Color: Default Primary Color', default='#4f46e5')
    os_theme_color_primary = fields.Char(string='Theme Primary Color', default='#4f46e5')
    os_theme_custom_color = fields.Char(string='Custom Color', default='#000')

    # -------------------- Enable/Disable Features  ----------------------------
    os_dbl_click_edit = fields.Boolean(string='Double Click to edit form view', default=False)
    os_display_bookmarks = fields.Boolean(string='Display Bookmarks', default=True)
    os_display_favorite_apps = fields.Boolean(string='Display Favorite Apps', default=True)
    os_display_todo_list = fields.Boolean(string='Display TODO', default=True)
    os_display_recently_viewed_records = fields.Boolean(string='Display Recently viewed Records', default=True)
    os_display_zoom_in_out = fields.Boolean(string='Display Zoom In/Out', default=True)
    os_display_full_screen = fields.Boolean(string='Display FullScreen', default=True)
    os_show_user_settings = fields.Boolean(string='Show user Settings', default=True)
    os_show_sidebar = fields.Boolean(string='Show Sidebar menu?', default=True)
    os_show_quick_create = fields.Boolean(string='Show Quick create?', default=True)

    # -------------------- Web Ribbon  ----------------------------
    os_activate_web_ribbon = fields.Boolean(string='Activate web ribbon', default=False)
    os_web_ribbon_text = fields.Char('Web ribbon Text', default=lambda self: self._os_default_web_ribbon_text())
    os_web_ribbon_bg = fields.Char('Web ribbon Background Color', default="#FF0000")
    os_web_ribbon_fg = fields.Char('Web ribbon Color', default="#FFFFFF")

    # -------------------- Theme elements styles  ----------------------------
    os_loader_style = fields.Selection(
        selection=[
            ('default', 'Odoo default'),
            ('style_1', 'Audio'),
            ('style_2', 'Ball triangle'),
            ('style_3', 'Bars'),
            ('style_4', 'Circles'),
            ('style_5', 'Grid'),
            ('style_6', 'Oval'),
            ('style_7', 'Puff'),
            ('style_8', 'Rings'),
            ('style_9', 'Spinning circles'),
            ('style_10', 'Tail spin'),
            ('style_11', 'Three dots'),
        ],
        required=True,
        string="Loader Style",
        default="default"
    )
    os_separator_style = fields.Selection(
        selection=[
            ('default', 'Odoo default'),
            ('style_1', 'Style 1'),
            ('style_2', 'Style 2'),
            ('style_3', 'Style 3'),
            ('style_4', 'Style 4'),
            ('style_5', 'Style 5'),
            ('style_6', 'Style 6'),
            ('style_7', 'Style 7'),
            ('style_8', 'Style 8'),
            ('style_9', 'Style 9'),
            ('style_10', 'Style 10'),
            ('style_11', 'Style 11'),
            ('style_12', 'Style 12'),
            ('style_13', 'Style 13'),
            ('style_14', 'Style 14'),
            ('style_15', 'Style 15'),

        ],
        required=True,
        string="Separator Style",
        default="style_8"
    )
    os_separator_color = fields.Char('Separator Color', default="#526484")
    os_breadcrumb_style = fields.Selection(
        selection=[
            ('default', 'Odoo default'),
            ('style_1', 'Style 1'),
            ('style_2', 'Style 2'),
            ('style_3', 'Style 3'),
            ('style_4', 'Style 4'),
            ('style_5', 'Style 5'),
            ('style_6', 'Style 6'),
            ('style_7', 'Style 7'),
            ('style_8', 'Style 8'),
            ('style_9', 'Style 9'),
            ('style_10', 'Style 10'),
            ('style_11', 'Style 11'),

        ],
        required=True,
        string="Breadcrumb Style",
        default="default"
    )

    os_tabs_style = fields.Selection(
        selection=[
            ('default', 'Odoo default'),
            ('style_1', 'Style 1'),
            ('style_2', 'Style 2'),
            ('style_3', 'Style 3'),
            ('style_4', 'Style 4'),
            ('style_5', 'Style 5'),
            ('style_6', 'Style 6'),
        ],
        required=True,
        string="Tabs Style",
        default="style_5"
    )

    os_tabs_alignment = fields.Selection(
        selection=[
            ('horizontal', 'Horizontal'),
            ('vertical', 'Vertical'),
        ],
        required=True,
        string="Tabs alignment",
        default="horizontal"
    )

    os_buttons_style = fields.Selection(
        selection=[
            ('default', 'Default'),
            ('ddd', '3D'),
            ('inset', 'Inset'),
            ('soft', 'Soft'),
        ],
        required=True,
        string="Buttons Style",
        default="default"
    )

    os_buttons_angles = fields.Selection(
        selection=[
            ('flat', 'Flat'),
            ('rounded', 'Rounded'),
            ('pill', 'Pill'),
            ('skew_flat', 'Skew Flat'),
            ('skew_rounded', 'Skew Rounded'),
        ],
        required=True,
        string="Buttons Angles",
        default="rounded"
    )

    os_buttons_size = fields.Selection(
        selection=[
            ('small', 'Small'),
            ('medium', 'Medium'),
            ('large', 'Large'),
        ],
        required=True,
        string="Buttons size",
        default="medium"
    )

    os_radios_style = fields.Selection(
        selection=[
            ('default', 'Odoo default'),
            ('style_1', 'Style 1'),
            ('style_2', 'Style 2'),
            ('style_3', 'Style 3'),
            ('style_4', 'Style 4'),
            ('style_5', 'Style 5'),
            ('style_6', 'Style 6'),
        ],
        required=True,
        string="Radios Style",
        default="default"
    )

    os_checkbox_style = fields.Selection(
        selection=[
            ('default', 'Odoo default'),
            ('style_1', 'Style 1'),
            ('style_2', 'Style 2'),
            ('style_3', 'Style 3'),
            ('style_4', 'Style 4'),
        ],
        required=True,
        string="Checkbox Style",
        default="default"
    )

    # -------------------- Theme Font  ----------------------------
    os_theme_base_font = fields.Selection([
        ('Roboto', 'Default'),
        ('Raleway', 'Raleway'),
        ('Poppins', 'Poppins'),
        ('Oxygen', 'Oxygen'),
        ('Lato', 'Lato'),
        ('OpenSans', 'OpenSans'),
        ('custom', 'Custom Google Font'),
    ], string="Base Font", default="Roboto")
    os_theme_alt_font = fields.Selection([
        ('Nunito', 'Default'),
        ('Raleway', 'Raleway'),
        ('Poppins', 'Poppins'),
        ('Oxygen', 'Oxygen'),
        ('Lato', 'Lato'),
        ('OpenSans', 'OpenSans'),
        ('custom', 'Custom Google Font'),
    ], string="Alternative Font", default="Nunito", help="For heading etc ...")
    os_theme_base_custom_google_font = fields.Char("Base Custom Google Font")
    os_theme_alt_custom_google_font = fields.Char("ALT Custom Google Font")

    # -------------------- List View Styles ----------------------------
    os_list_view_sticky_header_footer = fields.Boolean(string='Sticky header footer List view', default=False)
    os_list_view_header_bg_color = fields.Char(string='List view header BG Color', default=False)
    os_list_view_header_fg_color = fields.Char(string='List view header FG Color', default=False)
    os_list_view_style_spaced = fields.Boolean(string='Spaced List view?', default=True)
    os_list_view_style_separate = fields.Boolean(string='Separate List view?', default=False)
    os_list_view_style_hover = fields.Selection(
        selection=[
            ('none', 'None'),
            ('normal', 'Normal'),
            ('shadow', 'Shadow'),
        ],
        required=True,
        string="Hover List view",
        default="normal"
    )

    # -------------------- Advanced Settings  ----------------------------
    os_chart_color_palette = fields.Selection(
        selection=[
            ('default', 'Default'),
            ('palette_1', 'Odoo Stars'),
            ('palette_2', 'Happy'),
            ('palette_3', 'Pastel'),
            ('palette_4', 'Spring'),
            ('palette_5', 'Winter'),
            ('palette_6', 'Neon'),
            ('palette_7', 'Retro Metro'),
            ('palette_8', 'Apple iMac'),
            ('palette_9', 'Dracula'),
            ('palette_10', 'Rainbow'),
            ('palette_11', 'Cool'),
            ('palette_12', 'Red Yellow Blue'),
            ('palette_13', 'Spectral'),
            ('palette_14', 'Yellow & Green'),
            ('palette_15', 'Red & Purple'),
        ],
        required=True,
        string="Chart Palette Color",
        default="palette_1"
    )

    os_modal_animated_entrance = fields.Boolean(string='Animate Modal in entrance', default=False)
    os_modal_animated_entrance_value = fields.Char(string='Animate Modal in entrance value')

    @api.model
    def _os_default_web_ribbon_text(self):
        return self.env.cr.dbname

    @api.model
    def os_resetDefaultSettings(self):
        self.update({
            'os_header_style': 'is-light',
            'os_header_tools_bar_fixed': False,
            'os_sidebar_style': 'is-theme',
            'os_theme_mode': 'light-mode',
            'os_chatter_position': 'normal',
            'os_loader_style': 'default',
            'os_dbl_click_edit': False,
            'os_show_user_settings': True,
            'os_web_window_title': "Odoo",
            'os_activate_web_ribbon': False,
            'os_web_ribbon_text': self._os_default_web_ribbon_text(),
            'os_web_ribbon_bg': "#FF0000",
            'os_web_ribbon_fg': "#FFFFFF",
            'os_separator_style': "style_8",
            'os_separator_color': "#526484",
            'os_breadcrumb_style': "default",
            'os_login_style': "style_1",
            'os_theme_base_font': "Roboto",
            'os_theme_alt_font': "Nunito",
            'os_login_background_type': "default",
            'os_apps_view_background_type': "default",
            'os_tabs_style': "style_5",
            'os_buttons_style': "default",
            'os_buttons_angles': "rounded",
            'os_buttons_size': "medium",
            'os_radios_style': "default",
            'os_checkbox_style': "default",
            'os_list_view_style_spaced': True,
            'os_list_view_style_separate': False,
            'os_list_view_style_hover': "normal",
            'os_display_todo_list': True,
            'os_display_bookmarks': True,
            'os_display_favorite_apps': True,
            'os_display_recently_viewed_records': True,
            'os_display_zoom_in_out': True,
            'os_display_full_screen': True,
            'os_apps_icon_style': "font",
            'os_apps_icon_style_image_pack': "pack01",
            'os_shape_shadow': False,
            'os_show_sidebar': True,
            'os_show_quick_create': True,
            'os_modal_animated_entrance': False,
            'os_use_same_apps_icons_style_for_sidebar': False,
            'os_chart_color_palette': 'palette_1',
            'os_theme_color_primary': self.os_theme_color_brand,
        })
