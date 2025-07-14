odoo.define('os_theme_butterfly.FormController', function (require) {
    "use strict";
    var FormController = require('web.FormController');

    FormController.include({
        events: _.extend({}, FormController.prototype.events, {
            "click .os_reload_view": "_ReloadView",
        }),
        custom_events: _.extend({}, FormController.prototype.custom_events, {
            edit_mode: '_onTurnOnEditMode',
        }),

        _ReloadView: function () {
            this.reload();
        },
        _onTurnOnEditMode: function (ev) {
            if (this.is_action_enabled("edit")) {
                this._setMode("edit");
            }
        },

    });

});
