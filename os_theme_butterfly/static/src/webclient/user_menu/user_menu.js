/** @odoo-module */


import {patch} from "@web/core/utils/patch";
import {useEffect} from "@web/core/utils/hooks";
import {OS_Dropdown} from "@os_theme_butterfly/components/os_dropdown/os_dropdown";
import {OS_DropdownItem} from "@os_theme_butterfly/components/os_dropdown/os_dropdown_item";
import {UserMenu} from "@web/webclient/user_menu/user_menu";


class OS_UserMenuItem extends OS_DropdownItem {
    setup() {
        super.setup();
        useEffect(
            () => {
                if (this.props.payload.id) {
                    this.el.dataset.menu = this.props.payload.id;
                }
            },
            () => []
        );
    }
}

patch(UserMenu, "os_theme_butterfly.UserMenu", {

    components: {
        ...UserMenu.components,
        OS_Dropdown,
        OS_UserMenuItem,

    },
});