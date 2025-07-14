/** @odoo-module **/
const {Component} = owl;
import {registry} from "@web/core/registry";

export class OsHomeAction extends Component {
    setup() {
        super.setup();
        this.home_action_id = this.env.services.user.home_action_id;

    }

    onClickHomeAction() {
        this.env.services.action.doAction(this.home_action_id);
    }

}

OsHomeAction.template = 'os_theme_butterfly.os_home_action';
export const systrayItem = {
    Component: OsHomeAction,
};

registry.category("systray").add("OsHomeAction", systrayItem, {sequence: 1500});