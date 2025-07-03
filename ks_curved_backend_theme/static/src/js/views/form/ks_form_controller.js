odoo.define('ks_curved_backend_theme.ks_form_controller', function(require) {
    "use strict";
    var ks_form_controller = require('web.FormController');
    var form_view = require('web.FormView');
    var session = require("web.session");

    ks_form_controller.include({
        events: _.extend({}, ks_form_controller.prototype.events, {
            "click button.reload_form_view": "_KsReloadView",
        }),

        _KsReloadView: function() {
            this.reload();
        },

    });

    form_view.include({
        init: function (viewInfo, params) {
            this._super.apply(this, arguments);
            this.isKsSplitFormView = params.isKsSplitFormView || false;
            if (this.isKsSplitFormView) {
                    this.controllerParams.activeActions.create = false;
                    this.controllerParams.activeActions.delete = false;
                    this.controllerParams.isKsSplitFormView = true;
              }
        },
    })

});
