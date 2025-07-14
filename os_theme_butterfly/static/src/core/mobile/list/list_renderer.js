odoo.define('os_theme_butterfly.ListRendererMobile', function (require) {
    "use strict";

    const {device} = require('web.config');
    if (!device.isMobile) {
        return;
    }

    const ListRenderer = require('web.ListRenderer');

    ListRenderer.include({
        isEditable() {
            return this.editable;
        },
        _isRecordEditable() {
            return this.editable;
        },
    });
});
