/** @odoo-module **/

import {ThreadViewTopbar} from '@mail/components/thread_view_topbar/thread_view_topbar';
import {patch} from "@web/core/utils/patch";

patch(ThreadViewTopbar.prototype, 'os_theme_butterfly.thread_view_topbar', {
    setup() {
        this._super(...arguments);
    },

    onClickToggleSidebar(ev) {
        var $el = $(ev.currentTarget);
        $el.parents(".o_Discuss").toggleClass("os-ibx-aside-shown");
    }
});