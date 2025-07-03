odoo.define('hotel_booking.VoucherBarcodeHandler', function (require) {
    "use strict";
    var field_registry = require('web.field_registry');
    var AbstractField = require('web.AbstractField');
    var FormController = require('web.FormController');

    FormController.include({
        _barcodeVoucherAddLine: function (barcode, activeBarcode) {
            var self = this;
            if (!activeBarcode.handle) {
                return $.Deferred().reject();
            }
            var record = this.model.get(activeBarcode.handle);
            return this._barcodeAddX2MQuantity(barcode, activeBarcode);
        }
    })

    var VoucherBarcodeHandler = AbstractField.extend({
        init: function () {
            this._super.apply(this, arguments);

            this.trigger_up('activeBarcode', {
                name: this.name,
                fieldName: 'lines',
                commands: {
                    barcode: '_barcodeVoucherAddLine',
                }
            });
        },
    });
    field_registry.add('voucher_barcode_handler', VoucherBarcodeHandler);
    return VoucherBarcodeHandler;
});