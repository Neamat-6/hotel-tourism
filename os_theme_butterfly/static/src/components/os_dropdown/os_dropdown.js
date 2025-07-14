/** @odoo-module */
import {Dropdown} from "@web/core/dropdown/dropdown";
const {QWeb} = owl;

export class OS_Dropdown extends Dropdown {
    setup() {
        super.setup(...arguments);
    }
}

OS_Dropdown.template = "os_theme_butterfly.OS_Dropdown";
QWeb.registerComponent("OS_Dropdown", OS_Dropdown);

