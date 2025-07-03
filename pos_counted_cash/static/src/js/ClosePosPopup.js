odoo.define('pos_counted_cash.ClosePosPopup', function (require) {
    'use strict';

    const ClosePosPopup = require('point_of_sale.ClosePosPopup');
    const Registries = require('point_of_sale.Registries');
    const { useValidateCashInput } = require('point_of_sale.custom_hooks');
    const PosDefaultCounted = (ClosePosPopup) =>
        class extends ClosePosPopup {
            constructor() {
                super(...arguments);
                useValidateCashInput("closingCashInput",this.defaultCashDetails.amount);
            }
        };
    Registries.Component.extend(ClosePosPopup, PosDefaultCounted);
    return ClosePosPopup;
});
