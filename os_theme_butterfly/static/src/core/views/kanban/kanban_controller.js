odoo.define('os_theme_butterfly.KanbanController', function (require) {
    "use strict";
    var KanbanController = require('web.KanbanController');

    KanbanController.include({
        events: _.extend({}, KanbanController.prototype.events, {
          "click .os_reload_view": "_ReloadView",
        }),

        _ReloadView: function() {
            this.reload();
        },

    });
});