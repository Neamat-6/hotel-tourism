/** @odoo-module **/

import {customComputeAppsAndMenuItems} from "@os_theme_butterfly/webclient/menus/menu_helpers";
import {useService} from "@web/core/utils/hooks";
import {fuzzyLookup} from "@web/core/utils/search";

const {Component, hooks} = owl;
const {useState, useRef} = hooks;

export class OsSearchMenus extends Component {
    setup() {
        super.setup();
        this.menuService = useService("menu");
        this.companyThemeService = useService("os_company_settings");
        let {apps, menuItems} = customComputeAppsAndMenuItems(this.menuService.getMenuAsTree("root"));
        this._apps = apps;
        this._menuItems = menuItems;
        this.availableApps = [];
        this.displayedMenuItems = [];
        this.inputRef = useRef("input");
        this.state = useState({
            focusedIndex: null,
            isSearching: false,
            query: "",
        });


    }

    async willUpdateProps() {
        this.state.focusedIndex = null;
        this.state.isSearching = false;
        this.state.query = "";
        this.inputRef.el.value = "";
        this.availableApps = [];
        this.displayedMenuItems = [];
    }

    mounted() {
        this.inputRef.el.focus();
    }

    _onInputSearch(ev) {
        this._updateQuery(ev.target.value);
    }

    get displayedApps() {
        return this.availableApps;
    }

    _filter(array) {
        return fuzzyLookup(this.state.query, array, (el) =>
            (el.parents + " / " + el.label).split("/").reverse().join("/")
        );
    }

    get menuIndex() {
        const appLength = this.displayedApps.length;
        const focusedIndex = this.state.focusedIndex;
        return focusedIndex >= appLength ? focusedIndex - appLength : null;
    }

    _updateQuery(query) {
        this.state.query = query;
        this.inputRef.el.value = this.state.query;
        this.state.isSearching = true;

        if (query === "") {
            this.availableApps = [];
            this.displayedMenuItems = [];
        } else {
            this.availableApps = this._filter(this._apps);
            this.displayedMenuItems = this._filter(this._menuItems);
        }
        const total = this.displayedApps.length + this.displayedMenuItems.length;
        this.state.focusedIndex = total ? 0 : null;
    }

    _openMenu(menu) {
        return this.menuService.selectMenu(menu);
    }

    _onItemClick(menu) {
        this._openMenu(menu);
    }

}

OsSearchMenus.template = 'os_theme_butterfly.os_search_menus';

