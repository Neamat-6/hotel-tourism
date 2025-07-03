/** @odoo-module **/

import fieldRegistry from 'web.field_registry';
import { FieldMany2One } from 'web.relational_fields';
import { qweb } from 'web.core';
import core from "web.core";
const _t = core._t;
import Dialog from 'web.Dialog';
import session from "web.session";
import framework from 'web.framework';
var ScanBarcodeDialog = require('widget_mobile_scan.scan_barcode_dialog');


var M2OScan = FieldMany2One.extend({
    events: _.extend({}, FieldMany2One.prototype.events, {
        'click .o_product_scan_button': '_onClickScanIcon'
    }),
    init: function () {
        var self = this;
        self._super.apply(self, arguments);
    },
    _render: function () {
        this._super.apply(this, arguments);
        if (this.mode === 'edit' && this.value){
            if (window.location.protocol == 'https:'){
                this._addProductScanButton();
            }
        }else {
            if (window.location.protocol == 'https:'){
                this._addProductScanButton();
            }
        }
    },
    _addProductScanButton: function(){
        var $inputDropdown = this.$('.o_input_dropdown');
        if ($inputDropdown.length !== 0 && this.$('.o_product_scan_button').length === 0) {
            var $productScanButton = $('<button>', {
                type: 'button',
                class: 'fa fa-barcode btn btn-sm o_product_scan_button',
                tabindex: '-1',
                draggable: false,
                'aria-label': _t('Scan'),
                title: _t('Scan')
            });
            $inputDropdown.after($productScanButton).width('92%');
        }
    },

    _onClickScanIcon: _.debounce(function () {
        var self = this;
        var def = $.Deferred();
        if (self.popover_initialized) {
            def.resolve();
        } else {
            if (window.location.protocol == 'https:'){
                navigator.getUserMedia = navigator.getUserMedia 
                    || navigator.webkitGetUserMedia 
                    || navigator.mozGetUserMedia
                    || navigator.msGetUserMedia;
                if (navigator.getUserMedia) {
                    var options = {};
                    var ScanBarcode = new ScanBarcodeDialog(this, options).open();
                    def.resolve();
                }else if(navigator.mediaDevices.getUserMedia){
                    var options = {};
                    var ScanBarcode = new ScanBarcodeDialog(this, options).open();
                    def.resolve();
                }else{
                    self.displayNotification({ message: _t('Please Update or Use Different Browser'), type: 'danger' });
                    return;
                }
            }else{                
                self.displayNotification({ message: _t('Please Update or Use Different Browser'), type: 'danger' });
                return;
            }
        }
    }, 200, true),

    uploadScanCode:  async function(code){
        var self = this;
        if (code != undefined){
            var code_field = self.nodeOptions.code_field || 'default_code';
            var domain = [[code_field, "=", code]];
            return await self._rpc({
                model: self.field.relation,
                method: 'search_read',
                fields: ["id"],
                domain: domain,
                kwargs: {
                    limit: 1,
                }
            }).then(function (record) {
                if (record.length){                
                    var id  = record[0].id;                
                    self._setValue({ 
                        operation: 'UPDATE', 
                        id: id,
                    });
                }else{
                    return self.displayNotification({ message: _t("There were no matching records found.") });
                }
            });
        }
    },

    reset: function () {
        this._super.apply(this, arguments);
    },
});

fieldRegistry.add('m2o_mobile_scan', M2OScan);

