/** @odoo-module **/

const {Component, hooks} = owl;
import {useService} from "@web/core/utils/hooks";
const {useRef} = hooks;

import {registry} from "@web/core/registry";

export class OsDarkAction extends Component {
    setup() {
        super.setup();
        this.themeUserService = useService("os_user_settings");
        this.osMenuDarkIconRef = useRef("osMenuDarkIcon");

    }

    async onClickDarkAction() {
        var self = this;
        let data_user = {
            'os_theme_mode': $(this.osMenuDarkIconRef.el).data("update"),
        }
        return await this.rpc("/web/theme/user/change_theme_mode", {data: data_user}).then(function (res) {
            self.env.services.action.doAction("reload_context");
        });
    }

}

OsDarkAction.template = 'os_theme_butterfly.os_dark_action';
export const systrayItem = {
    Component: OsDarkAction,
};

registry.category("systray").add("OsDarkAction", systrayItem, {sequence: 1400});