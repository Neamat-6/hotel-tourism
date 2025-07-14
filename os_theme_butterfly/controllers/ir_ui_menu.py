# -*- coding: utf-8 -*-
# Part of Odoo Stars. See LICENSE file for full copyright and licensing details.

from odoo import api, models, tools
from odoo.osv import expression
import re

try:
    import sass as libsass
except ImportError:
    # If the `sass` python library isn't found, we fallback on the
    # `sassc` executable in the path.
    libsass = None


class IrUiMenu(models.Model):
    _inherit = "ir.ui.menu"

    @api.model
    @tools.ormcache_context('self._uid', 'debug', keys=('lang',))
    def load_menus(self, debug):
        """ Loads all menu items (all applications and their sub-menus).

        :return: the menu root
        :rtype: dict('children': menu_nodes)
        """
        fields = ['name', 'sequence', 'parent_id', 'action', 'web_icon', 'web_icon_data', 'os_web_icon_font', 'os_web_icon_color', 'os_shape_color', 'os_image_icon', 'os_is_changed']
        menu_roots = self.get_user_roots()
        menu_roots_data = menu_roots.read(fields) if menu_roots else []
        menu_root = {
            'id': False,
            'name': 'root',
            'parent_id': [-1, ''],
            'children': [menu['id'] for menu in menu_roots_data],
        }

        all_menus = {'root': menu_root}

        if not menu_roots_data:
            return all_menus

        # menus are loaded fully unlike a regular tree view, cause there are a
        # limited number of items (752 when all 6.1 addons are installed)
        menus_domain = [('id', 'child_of', menu_roots.ids)]
        blacklisted_menu_ids = self._load_menus_blacklist()
        if blacklisted_menu_ids:
            menus_domain = expression.AND([menus_domain, [('id', 'not in', blacklisted_menu_ids)]])
        menus = self.search(menus_domain)
        menu_items = menus.read(fields)
        xmlids = (menu_roots + menus)._get_menuitems_xmlids()

        # add roots at the end of the sequence, so that they will overwrite
        # equivalent menu items from full menu read when put into id:item
        # mapping, resulting in children being correctly set on the roots.
        menu_items.extend(menu_roots_data)

        # set children ids and xmlids
        menu_items_map = {menu_item["id"]: menu_item for menu_item in menu_items}
        for menu_item in menu_items:
            menu_item.setdefault('children', [])
            parent = menu_item['parent_id'] and menu_item['parent_id'][0]
            menu_item['xmlid'] = xmlids.get(menu_item['id'], "")
            if parent in menu_items_map:
                menu_items_map[parent].setdefault(
                    'children', []).append(menu_item['id'])
        all_menus.update(menu_items_map)

        # sort by sequence
        for menu_id in all_menus:
            all_menus[menu_id]['children'].sort(key=lambda id: all_menus[id]['sequence'])

        # recursively set app ids to related children
        def _set_app_id(app_id, menu):
            menu['app_id'] = app_id
            for child_id in menu['children']:
                _set_app_id(app_id, all_menus[child_id])

        for app in menu_roots_data:
            app_id = app['id']
            _set_app_id(app_id, all_menus[app_id])

        # filter out menus not related to an app (+ keep root menu)
        all_menus = {menu['id']: menu for menu in all_menus.values() if menu.get('app_id')}
        all_menus['root'] = menu_root

        return all_menus

    def hex_to_rgb(self, hx):
        """Converts an hexadecimal string (starting with '#') to a RGB tuple"""
        # return tuple([int(hx[i:i + 2], 16) for i in range(1, 6, 2)])
        res = [int(hx[i:i + 2], 16) for i in range(1, 6, 2)]
        return ','.join(str(e) for e in res)

    def _set_app_icon_style(self, shape, shape_style, menu_id, shape_color, icon_color):
        compiled_style = ""
        style = ""
        if icon_color and len(icon_color) > 0:
            icon_color = icon_color.replace(" ", "")
        if icon_color == "":
            icon_color = False
        icon_color_set = True if icon_color else False
        dark_mode = self.env.user.os_theme_mode == "dark-mode"

        if shape != "none" and shape_color:
            if shape_style == "simple":
                style = """
                        $icon_color_set : %s;
                        $dark_mode : %s;
                        $shape_color: %s;
                        $icon_color: %s;
                    @if ($dark_mode==True and $shape_color != False) {
                            $shape_color: desaturate(darken($shape_color,20%%),30%%);
                            $shape_color_lightness: lightness($shape_color);
                             @if ($shape_color_lightness <= 20) {
                                    $shape_color: lighten($shape_color,15%%);
                            } 
                        } 
                        $yiq-text-dark: #212529;
                        $yiq-text-light: #fff;
                        $yiq-contrasted-threshold:  200;
                        @function color-yiq($color, $dark: $yiq-text-dark, $light: $yiq-text-light) {
                            $r: red($color);
                            $g: green($color);
                            $b: blue($color);
                            $yiq: (($r * 299) + ($g * 587) + ($b * 114)) / 1000;
                            @if ($yiq >= $yiq-contrasted-threshold) {
                                 @return $dark;
                                } @else {
                                     @return $light;
                                }
                        }
                        .app-icon-%s { 
                             background: $shape_color !important;
                            @if $icon_color_set!=False  {
                                  color: $icon_color !important;
                             } @else {
                                color: color-yiq($shape_color) !important;
                             }
                         }  """ % (icon_color_set, dark_mode, shape_color, icon_color, menu_id)

            if shape_style == "soft":
                style = """
                            $dark_mode : %s;
                            $shape_color: rgba(%s,0.2);
                            $icon_color: %s;
                            
                    @if ($dark_mode==True and $shape_color != False) {
                                $shape_color: desaturate(lighten($shape_color,20%%),30%%);
                                $shape_color_lightness: lightness($shape_color);
                                @if ($shape_color_lightness <= 20) {
                                    $shape_color: lighten($shape_color,15%%);
                                } 
                            } 
                            .app-icon-%s { 
                                background:$shape_color !important;
                                color: $icon_color !important;
                            }  """ % (dark_mode, self.hex_to_rgb(shape_color), shape_color, menu_id)

            if shape_style == "gradient":
                percent1 = "10%"
                percent2 = "20%"
                style = """
                        $dark_mode : %s;
                        $icon_color_set : %s;
                        $shape_color: %s;
                        $icon_color: %s;
                        $yiq-text-dark: #212529;
                        $yiq-text-light: #fff;
                        $yiq-contrasted-threshold:  200;
                        @function color-yiq($color, $dark: $yiq-text-dark, $light: $yiq-text-light) {
                            $r: red($color);
                            $g: green($color);
                            $b: blue($color);
                            $yiq: (($r * 299) + ($g * 587) + ($b * 114)) / 1000;
                            @if ($yiq >= $yiq-contrasted-threshold) {
                                 @return $dark;
                                } @else {
                                     @return $light;
                                }
                             }
                             
                    @if ($dark_mode==True and $shape_color != False) {
                           
                                $shape_color: desaturate(darken($shape_color,20%%),30%%);
                                $shape_color_lightness: lightness($shape_color);
                                @if ($shape_color_lightness <= 20) {
                                    $shape_color: lighten($shape_color,15%%);
                                } 
                            } 
                        
                            .app-icon-%s { 
                                background: linear-gradient(to right, darken($shape_color, %s), lighten($shape_color, %s) ) !important;
                                    @if $icon_color_set!=False  {
                                        color: $icon_color !important;
                                    } @else {
                                        color: color-yiq($shape_color) !important;
                                    }
        
                                }  """ % (dark_mode, icon_color_set, shape_color, icon_color, menu_id, percent1, percent2)

        if shape == "none":
            os_shape_none_color_icon = self.env.company.os_shape_none_color_icon
            os_theme_color_primary = self.env.company.os_theme_color_primary
            if os_shape_none_color_icon and len(os_shape_none_color_icon) > 0:
                os_shape_none_color_icon = os_shape_none_color_icon.replace(" ", "")
            if os_shape_none_color_icon == "":
                os_shape_none_color_icon = False
            if shape_color and len(shape_color) > 0 and shape_color.replace(" ", "") == "":
                shape_color = False
            is_color_set = True if os_shape_none_color_icon else False
            style = """
                    $os_theme_color_primary: %s;
                    $is_color_set: %s;
                    $os_shape_none_color_icon: %s;
                    $dark_mode: %s;
                    $shape_color: %s;
                    @if ($dark_mode==True and $shape_color != False) {
                        $shape_color: desaturate(darken($shape_color,20%%),30%%);
                        $shape_color_lightness: lightness($shape_color);
                         @if ($shape_color_lightness <= 20) {
                                $shape_color: lighten($shape_color,15%%);
                        } 
                    } 
                    $yiq-text-dark: #212529;
                    $yiq-text-light: #fff;
                    $yiq-contrasted-threshold:  200;
                    @function color-yiq($color, $dark: $yiq-text-dark, $light: $yiq-text-light) {
                        $r: red($color);
                        $g: green($color);
                        $b: blue($color);
                        $yiq: (($r * 299) + ($g * 587) + ($b * 114)) / 1000;
                        @if ($yiq >= $yiq-contrasted-threshold) {
                             @return $dark;
                            } @else {
                                 @return $light;
                            }
                    }
                    .app-icon-%s { 
                        @if $is_color_set!=False {
                              color: $os_shape_none_color_icon !important;
                            } @else {
                              color: if($shape_color!=False, $shape_color, $os_theme_color_primary) !important;
                            }
                        
                     }  """ % (os_theme_color_primary, is_color_set, os_shape_none_color_icon, dark_mode, shape_color, menu_id)

        if libsass is not None and style != "":
            compiled_style = libsass.compile(string=style)

        return compiled_style

    def load_web_menus(self, debug):
        menus = self.load_menus(debug)
        shape_style = self.env.company.os_shape_style
        shape = self.env.company.os_shape
        os_apps_icon_style = self.env.company.os_apps_icon_style
        web_menus = {}
        for menu in menus.values():
            if not menu['id']:
                # special root menu case
                web_menus['root'] = {
                    "id": 'root',
                    "name": menu['name'],
                    "children": menu['children'],
                    "appID": False,
                    "xmlid": "",
                    "actionID": False,
                    "actionModel": False,
                    "webIcon": None,
                    "webIconData": None,
                    "backgroundImage": menu.get('backgroundImage'),
                }
            else:
                action = menu['action']
                no_action = "False"
                if not action:
                    no_action = "True"
                if menu['id'] == menu['app_id']:
                    # if it's an app take action of first (sub)child having one defined
                    child = menu
                    while child and not action:
                        action = child['action']
                        child = menus[child['children'][0]] if child['children'] else False

                action_model, action_id = action.split(',') if action else (False, False)
                action_id = int(action_id) if action_id else False
                webIconData = ""
                webImageIcon = ""
                if os_apps_icon_style == 'default':
                    if menu['web_icon_data']:
                        imgtype = menu['web_icon_data'][0] == 80 and 'svg+xml' or 'png'
                        webIconData = re.sub(r'\s/g', "", ('data:image/%s;base64,%s' % (imgtype, menu['web_icon_data'].decode('utf-8'))))
                    else:
                        webIconData = '/os_theme_butterfly/static/src/img/default_icon_app.png'

                if os_apps_icon_style == 'image':
                    if menu['os_image_icon']:
                        imgtype = menu['os_image_icon'][0] == 80 and 'svg+xml' or 'png'
                        webImageIcon = re.sub(r'\s/g', "", ('data:image/%s;base64,%s' % (imgtype, menu['os_image_icon'].decode('utf-8'))))
                    else:
                        webImageIcon = '/os_theme_butterfly/static/src/img/default_image_app.png'

                web_menus[menu['id']] = {
                    "id": menu['id'],
                    "name": menu['name'],
                    "children": menu['children'],
                    "appID": menu['app_id'],
                    "xmlid": menu['xmlid'],
                    "actionID": action_id,
                    "actionModel": action_model,
                    "webIcon": menu['web_icon'],
                    "webIconData": webIconData,
                    "webIconFont": menu['os_web_icon_font'] or "osi osi-box",
                    "hasNoAction": no_action,
                    "webIconColor": menu['os_web_icon_color'] or "",
                    "webIconChanged": menu['os_is_changed'] or False,
                    "webShapeColor": menu['os_shape_color'] or "",
                    "webImageIcon": webImageIcon,
                    "webIconStyle": self._set_app_icon_style(shape, shape_style, menu['id'], menu['os_shape_color'], menu['os_web_icon_color']),
                }

        return web_menus
