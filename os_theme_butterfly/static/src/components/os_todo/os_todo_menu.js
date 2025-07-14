/** @odoo-module **/

const {Component} = owl;
import {useService} from "@web/core/utils/hooks";

export class Os_todo_menu extends Component {
    setup() {
        super.setup();
        this.themeService = useService("os_user_settings");
    }
}

Os_todo_menu.template = "os_theme_butterfly.os_todo_menu";

