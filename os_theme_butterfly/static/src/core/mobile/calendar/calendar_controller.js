odoo.define('os_theme_butterfly.CalendarControllerMobile', function (require) {
    "use strict";

    const {device} = require('web.config');

    if (!device.isMobile) {
        return;
    }

    const CalendarController = require('web.CalendarController');

    CalendarController.include({
        _renderButtonsParameters: function () {
            return _.extend({}, this._super.apply(this, arguments), {
                isMobile: device.isMobile,
            });
        },

    });

});
