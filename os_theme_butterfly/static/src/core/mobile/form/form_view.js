odoo.define('os_theme_butterfly.FormView', function (require) {
    "use strict";
    const {device} = require('web.config');
    if (!device.isMobile) {
        return;
    }
    var FormView = require('web.FormView');
    var QuickCreateFormView = require('web.QuickCreateFormView');

    FormView.include({

        init: function () {
            this._super.apply(this, arguments);
            this.controllerParams.disableAutofocus = true;
        },
    });

    QuickCreateFormView.include({
        init: function () {
            this._super.apply(this, arguments);
            this.controllerParams.disableAutofocus = false;
        },
    });

});
