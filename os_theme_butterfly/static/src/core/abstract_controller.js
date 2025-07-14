odoo.define('os_theme_butterfly.AbstractController', function (require) {
    "use strict";


    var AbstractController = require("web.AbstractController");

    AbstractController.include({
        start: async function () {
            var prom = this._super.apply(this, arguments);
            this.$el.find('.o_content').on("scroll", function () {
                var topPos = $(this).scrollTop();
                if (topPos > 100) {
                    $("#scrollToTop").show('500');

                } else {
                    $("#scrollToTop").hide('500');
                }

            });
            return prom;
        },
    });

});
