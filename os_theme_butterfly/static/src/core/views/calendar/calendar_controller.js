odoo.define('os_theme_butterfly.CalendarController', function(require) {
    "use strict";
    var CalendarController = require('web.CalendarController');

    CalendarController.include({
        events: _.extend({}, CalendarController.prototype.events, {
            "click .os_reload_view": "_ReloadView",
        }),

        _ReloadView: function() {
            this.reload();
        },

    });
});