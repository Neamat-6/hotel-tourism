/** @odoo-module */

import {OS_Dropdown} from "@os_theme_butterfly/components/os_dropdown/os_dropdown";
import {Dropdown} from "@web/core/dropdown/dropdown";

const {QWeb} = owl;

export class OsQuickCreate_Dropdown extends Dropdown {
    setup() {
        super.setup(...arguments);
    }

    onDropdownStateChanged(args) {
        if (!this.el.contains(args.emitter.el)) {
            this.env.bus.trigger('QUICK_CREATE:CLOSE_DROPDOWN');
        }
        return super.onDropdownStateChanged(...arguments);
    }

    close() {
        this.env.bus.trigger('QUICK_CREATE:CLOSE_DROPDOWN');
        return super.close(...arguments);
    }
}

OsQuickCreate_Dropdown.template = OS_Dropdown.template;
QWeb.registerComponent("OsQuickCreate_Dropdown", OsQuickCreate_Dropdown);

