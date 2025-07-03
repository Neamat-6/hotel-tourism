/** @odoo-module **/

import basicFields from 'web.basic_fields';
import fieldRegistry from 'web.field_registry';
import { makeDeferred } from '@mail/utils/deferred/deferred';

import core from "web.core";
const _t = core._t;

var FieldChar = basicFields.FieldChar;

var ScanBarcodeDialog = require('widget_mobile_scan.scan_barcode_dialog');

var CharScan = FieldChar.extend({
    init: function () {
        var self = this;
        self._super.apply(self, arguments);
    },
    _render: function () {
        if (this.mode === 'edit') {
            return this._renderEdit();
        } else if (this.mode === 'readonly') {
            return this._renderReadonly();
        }
    },
    _renderEdit: function(){
        var def = this._super.apply(this, arguments);
        if (window.location.protocol == 'https:'){
            this._addProductScanButton();
        }
        return def;
    },
    _renderReadonly: function(){
        var def = this._super.apply(this, arguments);
        if (window.location.protocol == 'https:'){
            this._addProductScanButton();
        }
        return def;
    },
    _addProductScanButton: function(){
        var self = this;
        var $productScanButton = $('<a>', {
            title: _t('Scan'),
            href: '',
            class: 'ml-3 d-inline-flex align-items-center o_product_scan_button',
            html: $('<small>', {class: 'font-weight-bold ml-1', html: 'Scan'}),
        });
        $productScanButton.prepend($('<i>', {class: 'fa fa-barcode'}));
        $productScanButton.on('click', this._onEditCharScan.bind(this));
        this.$el = this.$el.width('75%').add($productScanButton);
    },
    _onEditCharScan: function(ev) {
        ev.preventDefault();
        ev.stopPropagation();
        var self = this;
        const def = makeDeferred();
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
                self.displayNotification({ message: _t("Please Update or Use Different Browser."), type: 'danger' });
                return;
            }
        }else{
            def.resolve();  
            self.displayNotification({ message: _t("Please Update or Use Different Browser."), type: 'danger' });     
            return;
        }       
    },
    async uploadScanCode(code){
        var self = this;
        if (code != undefined){
            if (this.mode === 'edit') {
                self.$input.val(code);
            } else if (this.mode === 'readonly') {
                self._setValue(code || false);
            }
        }
        else{
            self.displayNotification({ message: _t("There were no code found."), type: 'danger' });  
            return;
        }
    }
});

fieldRegistry.add('char_mobile_scan', CharScan);
