/** @odoo-module */

import {OS_Dropdown} from "@os_theme_butterfly/components/os_dropdown/os_dropdown";
import {Dropdown} from "@web/core/dropdown/dropdown";

const {QWeb} = owl;

export class OS_Favorite_Apps_Dropdown extends Dropdown {
    setup() {
        super.setup(...arguments);
    }

    onDropdownStateChanged(args) {
        if (!this.el.contains(args.emitter.el)) {
            this.env.bus.trigger('FAVORITE_APP:CLOSE_DROPDOWN');
        }
        return super.onDropdownStateChanged(...arguments);
    }

    close() {
        this.env.bus.trigger('FAVORITE_APP:CLOSE_DROPDOWN');
        return super.close(...arguments);
    }
}

OS_Favorite_Apps_Dropdown.template = OS_Dropdown.template;
QWeb.registerComponent("OS_Favorite_Apps_Dropdown", OS_Favorite_Apps_Dropdown);

