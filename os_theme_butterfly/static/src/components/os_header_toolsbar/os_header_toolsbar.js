/** @odoo-module **/
import {OsSearchMenus} from "@os_theme_butterfly/components/os_search_menus/os_search_menus";
import {OsQuickCreate} from "@os_theme_butterfly/components/os_quick_create/os_quick_create";
import {OsFavoriteAppMenu} from "@os_theme_butterfly/components/os_favorite_app/os_favorite_app";
import {OsBookmarkMenu} from "@os_theme_butterfly/components/os_bookmark/os_bookmark";
import {OsRecentlyViewedMenu} from "@os_theme_butterfly/components/os_recently_viewed_menu/os_recently_viewed_menu";
import {Os_todo_menu} from "@os_theme_butterfly/components/os_todo/os_todo_menu";
import {useService} from "@web/core/utils/hooks";

const {Component} = owl;

export class OsHeaderToolsBar extends Component {
    setup() {
        this.themeUserService = useService("os_user_settings");

    }

}

OsHeaderToolsBar.template = "os_theme_butterfly.OsHeaderToolsBar";
OsHeaderToolsBar.components = {
    OsSearchMenus,
    OsQuickCreate,
    OsFavoriteAppMenu,
    OsBookmarkMenu,
    OsRecentlyViewedMenu,
    Os_todo_menu,
}
