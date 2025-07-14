/** @odoo-module **/

import {useService} from "@web/core/utils/hooks";
import {registry} from "@web/core/registry";
import {session} from "@web/session";

const {Component} = owl;

export class OsSwitchLanguageMenu extends Component {
    setup() {
        super.setup();
        this.rpc = useService("rpc");
        this.user = useService("user");
        this.current_language = String(session.user_context.lang);

    }

    async willStart() {
        this.languages = await this.loadLanguages("/get/installed/languages");
        return super.willStart();
    }

    async loadLanguages(Route) {
        return await this.rpc(Route, {context: this.user.context});
    }

    toggleLanguageClick(ev) {
        var self = this;
        var selected_language = $(ev.currentTarget).data("language-code");
        self.rpc("get/selected/language", {
            selected_language: selected_language,
        }).then(function () {
            self.env.services.action.doAction("reload_context");

        });
    }

}

OsSwitchLanguageMenu.template = "os_theme_butterfly.os_switch_language";
OsSwitchLanguageMenu.toggleDelay = 1000;

export const systrayItem = {
    Component: OsSwitchLanguageMenu,
};

registry.category("systray").add("OsSwitchLanguageMenu", systrayItem, {sequence: 1});