odoo.define('hotel_booking.signature_form', function(require) {
'use strict';

var SignatureForm = require('portal.signature_form').SignatureForm;
var NameAndSignature = require('web.name_and_signature').NameAndSignature;
var publicWidget = require('web.public.widget');

NameAndSignature.include({
    template: 'hotel_booking.sign_name_and_signature',
    xmlDependencies: (NameAndSignature.prototype.xmlDependencies || []).concat(
        ['/hotel_booking/static/src/xml/signature_form.xml']
    ),
    init: function (parent, options) {
        this._super.apply(this, arguments);
        this.is_hotel = options.hotel || 0;
    },
    start: function(){
        this.$referenceInput = this.$('input[name=booking_reference]');
        this._super.apply(this, arguments);
    },
    validateSignature: function (parent, options) {
        var reference;
        if(!this.is_hotel) {
            reference = true;
        }
        else {
            reference = this.getReference();
            this.$referenceInput.toggleClass('border-danger', !reference);
        }
        return this._super.apply(this, arguments) && reference;
    },
    getReference: function () {
        return this.$referenceInput.val();
    },
});

SignatureForm.include({
    _onClickSignSubmit: function (ev) {
        var self = this;
        ev.preventDefault();

        if (!this.nameAndSignature.validateSignature()) {
            return;
        }
        var name = this.nameAndSignature.getName();
        var reference = this.nameAndSignature.getReference();
        var signature = this.nameAndSignature.getSignatureImage()[1];
        return this._rpc({
            route: this.callUrl,
            params: _.extend(this.rpcParams, {
                'name': name,
                'signature': signature,
                'booking_reference': reference,
            }),
        }).then(function (data) {
            if (data.error) {
                self.$('.o_portal_sign_error_msg').remove();
                self.$controls.prepend(qweb.render('portal.portal_signature_error', {widget: data}));
            } else if (data.success) {
                var $success = qweb.render('portal.portal_signature_success', {widget: data});
                self.$el.empty().append($success);
            }
            if (data.force_refresh) {
                if (data.redirect_url) {
                    window.location = data.redirect_url;
                } else {
                    window.location.reload();
                }
                // no resolve if we reload the page
                return new Promise(function () { });
            }
        });
    },
});

publicWidget.registry.SignatureForm = publicWidget.Widget.extend({
    selector: '.o_portal_signature_form_custom',
    /**
     * @private
     */
    start: function () {
        var hasBeenReset = false;
        var callUrl = this.$el.data('call-url');
        var nameAndSignatureOptions = {
            defaultName: this.$el.data('default-name'),
            hotel: this.$el.data('is-hotel'),
            mode: this.$el.data('mode'),
            displaySignatureRatio: this.$el.data('signature-ratio'),
            signatureType: this.$el.data('signature-type'),
            fontColor: this.$el.data('font-color')  || 'black',
        };
        var sendLabel = this.$el.data('send-label');

        var form = new SignatureForm(this, {
            callUrl: callUrl,
            nameAndSignatureOptions: nameAndSignatureOptions,
            sendLabel: sendLabel,
        });

        // Correctly set up the signature area if it is inside a modal
        this.$el.closest('.modal').on('shown.bs.modal', function (ev) {
            if (!hasBeenReset) {
                // Reset it only the first time it is open to get correct
                // size. After we want to keep its content on reopen.
                hasBeenReset = true;
                form.resetSignature();
            } else {
                form.focusName();
            }
        });

        return Promise.all([
            this._super.apply(this, arguments),
            form.appendTo(this.$el)
        ]);
    },
});

});
