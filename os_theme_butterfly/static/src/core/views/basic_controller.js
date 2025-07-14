odoo.define('os_theme_butterfly.BasicController', function (require) {
    "use strict";
    var BasicController = require('web.BasicController');

    BasicController.include({
        events: _.extend({}, BasicController.prototype.events, {
           "click .os_reload_view": "_ReloadView",
        }),

        _ReloadView: function() {
            this.reload();
        },
    });
});