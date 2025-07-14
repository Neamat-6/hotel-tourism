odoo.define('os_theme_butterfly.KanbanViewMobile', function (require) {
"use strict";

const {device} = require('web.config');
if (!device.isMobile) {
    return;
}

const KanbanView = require('web.KanbanView');

KanbanView.include({
    init() {
        this._super(...arguments);
        this.jsLibs.push('/web/static/lib/jquery.touchSwipe/jquery.touchSwipe.js');
    },
});
});
