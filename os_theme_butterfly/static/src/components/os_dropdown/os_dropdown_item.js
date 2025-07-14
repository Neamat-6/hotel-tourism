/** @odoo-module */
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
const { QWeb } = owl;

export class OS_DropdownItem extends DropdownItem {
     setup() {
        super.setup(...arguments);
    }
}

OS_DropdownItem.template = "os_theme_butterfly.OS_DropdownItem";
QWeb.registerComponent("OS_DropdownItem", OS_DropdownItem);

