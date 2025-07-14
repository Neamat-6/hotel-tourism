/** @odoo-module **/

const {Component} = owl;
import {registry} from "@web/core/registry";

export class OsHeaderToolsBarMenu extends Component {
    setup() {
    }

    toggleHeaderToolsBar() {
        $(".os-header-toolsbar").toggleClass('is-fixed');
        $(".os-content").toggleClass('os-header-toolsbar-shown');
        $("body").toggleClass('os-header-toolsbar-shown');
        $(this.el).toggleClass("shown");
    }
}

OsHeaderToolsBarMenu.template = "os_theme_butterfly.OsHeaderToolsBarMenu";

export const systrayItem = {
    Component: OsHeaderToolsBarMenu,
};

registry.category("systray").add("OsHeaderToolsBarMenu", systrayItem, {sequence: -1});