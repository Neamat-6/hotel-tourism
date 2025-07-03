odoo.define('htask_connector.models', function (require) {
    'use strict';
const models = require('point_of_sale.models');
var _super_Order = models.Order.prototype;

models.Order = models.Order.extend({

    export_for_printing: function () {
        var res = _super_Order.export_for_printing.apply(this, arguments);
            res.room_no = this.room_no;

        return res;
    },
});
});

