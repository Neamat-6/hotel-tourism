odoo.define('os_theme_butterfly.ListController', function (require) {
    "use strict";
    var ListController = require('web.ListController');

    ListController.include({
        events: _.extend({}, ListController.prototype.events, {
          "click .os_reload_view": "_ReloadView",
        }),

        _ReloadView: function() {
            this.reload();
        },
        
    });

});
