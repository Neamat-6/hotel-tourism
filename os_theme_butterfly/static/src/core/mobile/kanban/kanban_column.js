odoo.define('os_theme_butterfly.KanbanColumnMobile', function (require) {
    "use strict";

    const {device} = require('web.config');
    if (!device.isMobile) {
        return;
    }

    const KanbanColumn = require('web.KanbanColumn');

    KanbanColumn.include({
        init() {
            this._super(...arguments);
            this.recordsDraggable = false;
            this.canBeFolded = false;
        },
    });
});
