/** @odoo-module **/

import {Dialog} from "@web/core/dialog/dialog";
import {patch} from "@web/core/utils/patch";
import {useEffect} from "@web/core/utils/hooks";
import {session} from "@web/session";
import config from "web.config";

patch(Dialog.prototype, "os_theme_butterfly/static/src/core/dialog.js", {
    setup() {
        this._super();
        useEffect(
            () => {
                $(this.el).find('.modal-content')
                    .resizable({
                        minWidth: 625,
                        animate: true,
                        animateDuration: "fast",
                        aspectRatio: true,
                        handles: 'n, e, s, w, ne, sw, se, nw',
                    })
                    .draggable({
                        handle: '.modal-header',
                        helper: false,
                        cursor: "move",
                    });
                if (!config.device.isMobile && session.company_modal_animated_entrance && session.company_modal_animated_entrance_value) {
                    let animation = "animate__animated animate__" + session.company_modal_animated_entrance_value;
                    $(this.el).find('.modal-content').addClass(animation);
                }
                return () => {
                    var draggable = $(this.el).find(".modal-content").draggable("instance");
                    if (draggable) {
                        $(this.el).find(".modal-content").draggable("destroy");
                    }
                    var resizable = $(this.el).find(".modal-content").resizable("instance");
                    if (resizable) {
                        $(this.el).find(".modal-content").resizable("destroy");
                    }
                };
            },
            () => []
        );
    }
});
