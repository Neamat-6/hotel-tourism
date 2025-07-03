odoo.define('ks_curved_backend_theme.ks_list_controller', function(require) {
    "use strict";
    var ks_list_controller = require('web.ListController');
    var list_view = require('web.ListView');
    var session = require("web.session");

    ks_list_controller.include({
        events: _.extend({}, ks_list_controller.prototype.events, {
            "click .reload_list_view": "_KsReloadView",
        }),

        init: function (viewInfo, params) {
            this._super.apply(this, arguments);
        },

        _KsReloadView: function() {
            this.reload();
        },

    });

    list_view.include({
        init: function (viewInfo, params) {
            this._super.apply(this, arguments);
            this.list_split_mode = session['ks_split_view'] || false;
            if (this.list_split_mode) {
                this.controllerParams.list_split_mode = this.list_split_mode;
                this.rendererParams.list_split_mode = this.list_split_mode;
            }
        },
    })

});
