odoo.define("os_theme_butterfly.WebDialogMobile", function (require) {
    "use strict";

    const {device} = require('web.config');
    if (!device.isMobile) {
        return;
    }

    const Dialog = require("web.Dialog");

    Dialog.include({
        init(parent, {headerButtons}) {
            this._super.apply(this, arguments);
            this.headerButtons = headerButtons || [];
        },

        willStart() {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                if (self.renderHeader && self.fullscreen) {
                    const $header = self.$modal.find(".modal-header");
                    $header.find("button.close").remove();
                    const $back_btn = $("<button>", {
                        class: "btn osi osi-back-ios", "data-dismiss": "modal", "aria-label": "close",
                    });
                    $header.prepend($back_btn);
                    const $container = $("<div>");
                    self._setButtonsTo($container, self.headerButtons);
                    $header.append($container);
                }
                self.scrollTo = {
                    top: window.scrollY || document.documentElement.scrollTop,
                    left: window.scrollX || document.documentElement.scrollLeft,
                };
            });
        },

        destroy() {
            if (this.$modal && $('.modal[role="dialog"]').filter(":visible").length <= 1) {
                this.$modal.closest("body").removeClass("modal-open");
                window.scrollTo(this.scrollTo);
            }
            this._super(...arguments);
        },
    });
});
