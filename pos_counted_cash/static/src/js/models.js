odoo.define('pos_counted_cash.pos', function (require) {
    "use strict";

    var models = require('point_of_sale.models');
    var _super_pos_model = models.PosModel.prototype;

    models.PosModel = models.PosModel.extend({
        async getClosePosInfo() {
            var result = await _super_pos_model.getClosePosInfo.apply(this, arguments);
            if (result.cashControl) {
                result.state.payments[result.defaultCashDetails.id] = {counted: 0, difference:0 , number: 0};
            }
            return result;
        }
    });

});

