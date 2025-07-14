odoo.define('os_theme_butterfly.RelationalFields', function (require) {
    "use strict";

    const {device} = require('web.config');
    if (!device.isMobile) {
        return;
    }

    var relational_fields = require('web.relational_fields');

    const {qweb} = require('web.core');

    relational_fields.FieldStatus.include({
        _render: function () {
            this.$el.html(qweb.render("os_theme_butterfly.FieldStatusMobile", {
                selection: this.status_information,
                status: _.findWhere(this.status_information, {selected: true}),
                clickable: this.isClickable,
            }));
        },
        isEmpty: function () {
            return !this.isSet();
        },
    });

    relational_fields.FieldMany2One.include({

        start: function () {
            var res = this._super.apply(this, arguments);
            this.$input.prop('readonly', true);
            return res;
        },

        // No autocomplete in mobile
        _bindAutoComplete: function () {
        },

        // Add selectionMode
        _getSearchCreatePopupOptions: function () {
            var self = this;
            var res = this._super.apply(this, arguments);
            _.extend(res, {
                selectionMode: true,
                on_clear: function () {
                    self.reinitialize(false);
                },
            });
            return res;
        },

        _toggleAutoComplete: function () {
            this._searchCreatePopup("search");
        },
    });


});
