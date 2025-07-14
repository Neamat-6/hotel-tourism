odoo.define("ThemeBackend.Dialog", function (require) {
    "use strict";

    const Dialog = require("web.Dialog");
    const session = require("web.session");
    const config = require("web.config");

    Dialog.include({

        async willStart() {
            const prom = await this._super.apply(this, arguments);

            this.$modal.find(".modal-content")
                .resizable({
                    minWidth: 625,
                    animate: true,
                    animateDuration: "fast",
                    aspectRatio: true,
                    handles: 'n, e, s, w, ne, sw, se, nw',
                }).draggable({
                handle: ".modal-header",
                helper: false,
                cursor: "move",
            });


            return prom;
        },

        opened: function () {
            return this._super.apply(this, arguments).then(
                function () {
                    if (!config.device.isMobile &&  this.$modal && session.company_modal_animated_entrance && session.company_modal_animated_entrance_value) {
                        let animation = "animate__animated animate__" + session.company_modal_animated_entrance_value;
                        this.$modal.find(".modal-content").addClass(animation);
                    }
                }.bind(this)
            );
        },


        destroy() {
            if (this.$modal) {
                var draggable = this.$modal.find(".modal-content").draggable("instance");
                if (draggable) {
                    this.$modal.find(".modal-content").draggable("destroy");
                }
                var resizable = this.$modal.find(".modal-content").resizable("instance");
                if (resizable) {
                    this.$modal.find(".modal-content").resizable("destroy");
                }
            }
            this._super(...arguments);
        },
    });
});
