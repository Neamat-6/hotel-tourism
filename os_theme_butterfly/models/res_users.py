# -*- coding: utf-8 -*-
# Part of Odoo Stars. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api


class ResUsers(models.Model):
    _inherit = 'res.users'

    os_sidebar_style = fields.Selection(
        selection=[
            ('is-light', 'White'),
            ('is-gray-light', 'Light'),
            ('is-dark', 'Dark'),
            ('is-theme', 'Theme')
        ],
        required=True,
        string="Sidebar Style",
        default=lambda self: self._os_default_sidebar_style()
    )

    os_show_sidebar = fields.Boolean(
        string='Show Sidebar menu?',
        default=lambda self: self._os_default_show_sidebar()
    )
    os_header_tools_bar_fixed = fields.Boolean(
        string='Fixed header Tools bar',
        default=lambda self: self._os_default_header_tools_bar_fixed()
    )

    os_show_quick_create = fields.Boolean(
        string='Show Quick create?',
        default=lambda self: self._os_default_show_quick_create()
    )

    os_header_style = fields.Selection(
        selection=[
            ('is-light', 'White'),
            ('is-gray-light', 'Light'),
            ('is-dark', 'Dark'),
            ('is-theme', 'Theme')
        ],
        required=True,
        string="Header Style",
        default=lambda self: self._os_default_header_style()
    )

    os_theme_mode = fields.Selection(
        selection=[
            ('light-mode', 'Light Mode'),
            ('dark-mode', 'Dark Mode'),
        ],
        required=True,
        help="Select Dark or Light Mode",
        string="Theme Mode",
        default=lambda self: self._os_default_theme_mode()
    )

    os_chatter_position = fields.Selection(
        selection=[
            ('normal', 'Normal'),
            ('sided', 'Sided'),
        ],
        required=True,
        string="Chatter Position",
        default=lambda self: self._os_default_chatter_position()
    )

    os_dbl_click_edit = fields.Boolean(
        string='Double Click to edit form view',
        default=lambda self: self._os_default_dbl_click_edit()
    )

    os_display_todo_list = fields.Boolean(
        string='Display TODO',
        default=lambda self: self._os_default_display_todo_list()
    )

    os_display_bookmarks = fields.Boolean(
        string='Display Bookmarks',
        default=lambda self: self._os_default_display_bookmarks()
    )

    os_display_favorite_apps = fields.Boolean(
        string='Display Favorite Apps',
        default=lambda self: self._os_default_display_favorite_apps()
    )

    os_display_recently_viewed_records = fields.Boolean(
        string='Display Recently viewed Records',
        default=lambda self: self._os_default_display_recently_viewed_records()

    )

    os_display_zoom_in_out = fields.Boolean(
        string='Display Zoom In/Out',
        default=lambda self: self._os_default_display_zoom_in_out()
    )

    os_display_full_screen = fields.Boolean(
        string='Display FullScreen',
        default=lambda self: self._os_default_display_full_screen()
    )
    os_use_same_apps_icons_style_for_sidebar = fields.Boolean(string='Use same Apps icon style for sidebar',
                                                              default=lambda self: self._os_default_use_same_apps_icons_style_for_sidebar())

    recently_viewed_record_ids = fields.One2many(
        'os.recently.viewed.record', 'user_id', string="Recently Viewed Records")

    todo_ids = fields.One2many('os.todo', 'user_id', string="Todo Records")

    bookmark_ids = fields.One2many('os.bookmark', 'user_id', string="Bookmarks Records")

    favorite_app_ids = fields.One2many('os.favorite.app', 'user_id', string="Favorite apps Records")

    quick_create_ids = fields.One2many('os.quick.create', 'user_id', string="Quick Create")

    @api.model
    def _os_default_sidebar_style(self):
        return self.env.user.company_id.os_sidebar_style

    @api.model
    def _os_default_use_same_apps_icons_style_for_sidebar(self):
        return self.env.user.company_id.os_use_same_apps_icons_style_for_sidebar

    @api.model
    def _os_default_header_style(self):
        return self.env.user.company_id.os_header_style

    @api.model
    def _os_default_show_sidebar(self):
        return self.env.user.company_id.os_show_sidebar

    @api.model
    def _os_default_header_tools_bar_fixed(self):
        return self.env.user.company_id.os_header_tools_bar_fixed

    @api.model
    def _os_default_show_quick_create(self):
        return self.env.user.company_id.os_show_quick_create

    @api.model
    def _os_default_theme_mode(self):
        return self.env.user.company_id.os_theme_mode

    @api.model
    def _os_default_chatter_position(self):
        return self.env.user.company_id.os_chatter_position

    @api.model
    def _os_default_dbl_click_edit(self):
        return self.env.user.company_id.os_dbl_click_edit

    @api.model
    def _os_default_display_full_screen(self):
        return self.env.user.company_id.os_display_full_screen

    @api.model
    def _os_default_display_zoom_in_out(self):
        return self.env.user.company_id.os_display_zoom_in_out

    @api.model
    def _os_default_display_recently_viewed_records(self):
        return self.env.user.company_id.os_display_recently_viewed_records

    @api.model
    def _os_default_display_todo_list(self):
        return self.env.user.company_id.os_display_todo_list

    @api.model
    def _os_default_display_favorite_apps(self):
        return self.env.user.company_id.os_display_favorite_apps

    @api.model
    def _os_default_display_bookmarks(self):
        return self.env.user.company_id.os_display_bookmarks

    @api.model
    def os_resetDefaultSettings(self):
        self.update({
            'os_header_style': self._os_default_header_style(),
            'os_sidebar_style': self._os_default_sidebar_style(),
            'os_show_sidebar': self._os_default_show_sidebar(),
            'os_header_tools_bar_fixed': self._os_default_header_tools_bar_fixed(),
            'os_show_quick_create': self._os_default_show_quick_create(),
            'os_theme_mode': self._os_default_theme_mode(),
            'os_chatter_position': self._os_default_chatter_position(),
            'os_dbl_click_edit': self._os_default_dbl_click_edit(),
            'os_display_todo_list': self._os_default_display_todo_list(),
            'os_display_bookmarks': self._os_default_display_bookmarks(),
            'os_display_favorite_apps': self._os_default_display_favorite_apps(),
            'os_display_recently_viewed_records': self._os_default_display_recently_viewed_records(),
            'os_display_zoom_in_out': self._os_default_display_zoom_in_out(),
            'os_display_full_screen': self._os_default_display_full_screen(),
        })

    @api.model
    def systray_get_activities(self):
        activities = super(ResUsers, self).systray_get_activities()
        for activity in activities:
            module = self.env['ir.module.module'].sudo().search([('name', '=', self.env[activity['model']]._original_module)])
            if self.env.company.os_apps_icon_style == "default":
                activity['type_icon'] = 'default'
                activity['icon'] = '/web/image?model=ir.module.module&id=%s&field=icon_image' % module.id
            if self.env.company.os_apps_icon_style == "font":
                activity['type_icon'] = 'font'
                activity['icon'] = module.os_web_icon_font or "osi osi-box"
            if self.env.company.os_apps_icon_style == "image":
                activity['type_icon'] = 'image'
                activity['icon'] = '/web/image?model=ir.module.module&id=%s&field=os_image_icon' % module.id
        return activities

    # ----------------------------------------------------------
    # Setup
    # ----------------------------------------------------------

    @property
    def SELF_READABLE_FIELDS(self):
        return super().SELF_READABLE_FIELDS + ["os_theme_mode"]

    @property
    def SELF_WRITEABLE_FIELDS(self):
        return super().SELF_WRITEABLE_FIELDS + ["os_theme_mode"]
