odoo.define('os_theme_butterfly.KanbanColumnQuickCreateMobile', function (require) {
    "use strict";

    const {device} = require('web.config');
    if (!device.isMobile) {
        return;
    }

    const ColumnQuickCreate = require('web.kanban_column_quick_create');

    ColumnQuickCreate.include({
        init() {
            this._super(...arguments);
            this.isMobile = true;
        },
        _cancel() {
            if (!this.folded) {
                this.$input.val('');
            }
        },
    });
});
