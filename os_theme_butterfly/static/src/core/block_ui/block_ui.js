/** @odoo-module **/

import {useService} from "@web/core/utils/hooks";
import {patch} from "@web/core/utils/patch";
import {BlockUI} from "@web/core/ui/block_ui";

patch(BlockUI.prototype, "os_theme_butterfly.LoadingIndicator", {
    setup() {
        this._super();
        this.themeService = useService("os_company_settings");

    },
});
BlockUI.template = "os_theme_butterfly.block_ui";

