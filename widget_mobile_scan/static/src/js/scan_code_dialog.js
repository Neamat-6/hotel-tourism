/** @odoo-module alias=widget_mobile_scan.scan_barcode_dialog **/

import core from 'web.core';
import Dialog from 'web.Dialog';

var _t = core._t;

const ZXingReader = new ZXing.BrowserMultiFormatReader();
let $selectedDeviceId;

var ScanBarcodeDialog = Dialog.extend({
    template: "ScanBarcodeDialog",
    jsLibs: [
        '/widget_mobile_scan/static/src/libs/ZXing.js',
    ],
    events: {
        'click .close': '_onDestroy',
        'click .startButton': '_onClickStartButton',
        'click .resetButton': '_onClickResetButton',
    },
    init: function (parent, options) {
        options = _.defaults(options || {}, {
            title: _t("Scan Barcode / QR Code"),
            size: 'medium',
        });
        this.is_update_code = false;
        this.parent = parent;
        this._super.apply(this, arguments);
    },
    start: function () {
        var self = this;
        self.initZXing();
        return this._super.apply(this, arguments);
    },
    initZXing: function(){
        var self = this;
        
        ZXingReader
        .listVideoInputDevices()
        .then(function (videoInputDevices) {
            function pruneText(text) {
                return text.length > 30 ? text.substr(0, 30) : text;
            }
            var $sourceSelect = document.getElementById("deviceSelection");
            while ($sourceSelect && $sourceSelect.firstChild) {
                $sourceSelect.removeChild($sourceSelect.firstChild);
            }
            videoInputDevices.forEach(function(device) {
                var $sourceOption = document.createElement("option");
                $sourceOption.value = device.deviceId || device.id;
                $sourceOption.appendChild(document.createTextNode(pruneText(device.label || device.deviceId || device.id)));
                $sourceOption.selected = device.label;
                if($sourceSelect){
                    $sourceSelect.appendChild($sourceOption);
                }
            });
            $sourceSelect.onchange = () => {
                $selectedDeviceId = $sourceSelect.value;
            };
            
            $(".startButton").trigger("click");
        });
    },
    _onClickStartButton: function (ev) {
        var self = this;
        $(".resetButton").show();
        this.decodeOnce(ZXingReader, $selectedDeviceId);
    },
    _onClickResetButton: function (ev) {
        var self = this;
        ZXingReader.reset();
        $(".resetButton").hide();
    },
    decodeOnce: function (ZXingReader, $selectedDeviceId) {
        var self = this;
        ZXingReader.decodeFromVideoDevice($selectedDeviceId, 'scan_video', (result, err) => {
            if (result) {
                console.log(result);   
                self.update_code(result.text);
            }
            if (err && !(err instanceof ZXing.NotFoundException)) {
                // console.log(err);                
            }
        });        
    },
    detachListeners: function() {    
        var self = this;        
        $(".controls .reader-config-group").off("change", "input, select");
    },
    _onDestroy: function () {
        this.destroy();
    },
    destroy: function () {
        if (this.isDestroyed()) {
            return;
        }
        this._super.apply(this, arguments);
    },

    update_code: function (code) {
        var self = this;
        if (!self.is_update_code) {
            if (!self.is_update_code) {
                ZXingReader.reset();
                self.detachListeners();
                self.is_update_code = true;
                self.parent.uploadScanCode(code);
                self._onDestroy();
            }
        }
    },
});

export default ScanBarcodeDialog;
