odoo.define('os_theme_butterfly.ListControllerMobile', function (require) {
    "use strict";

    const {device} = require('web.config');
    if (!device.isMobile) {
        return;
    }

    const ListController = require('web.ListController');

    ListController.include({

        renderButtons() {
            this._super(...arguments);
            this.$buttons.find('.o_list_export_xlsx').hide();
        },

        updateButtons() {
            this._super(...arguments);
            this.$buttons.find('.o_list_export_xlsx').hide();
        },

    });
});
