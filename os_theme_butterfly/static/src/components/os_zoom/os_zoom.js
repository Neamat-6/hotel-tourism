/** @odoo-module **/
import {session} from "@web/session";

const {Component} = owl;

if (session.user_display_zoom_in_out) {
    const {useRef} = owl.hooks;

    export class OsZoom extends Component {
    }

    export class OsZoomContent extends Component {
        setup() {
            super.setup();
            this.btn_zoom_inRef = useRef('btn_zoom_in');
            this.btn_zoom_outRef = useRef('btn_zoom_out');
            this.btn_zoom_percentageRef = useRef('btn_zoom_percentage');
        }

        zoom(scale_value) {
            $(this.btn_zoom_percentageRef.el).text(String(scale_value) + "%");

            if (document.querySelector(".o_content").children.length === 1) {
                var o_content_style = document.querySelector(
                    ".o_content div:last-child"
                ).style;
            } else {
                var o_content_style = document.querySelector(
                    ".o_content"
                ).style;
            }

            o_content_style.transform = "scale(" + scale_value / 100 + ")";
            o_content_style.transformOrigin = "left top";
            if ($('body.o_rtl').length) {
                o_content_style.transformOrigin = "right top";
            }
            o_content_style.width = 100 * (100 / scale_value) + "%";
            o_content_style.flex = "0 0 " + 100 * (100 / scale_value) + "%";
        }

        onZoomIn(ev) {
            ev.stopPropagation();
            if ($(".o_content").length) {
                var scale_value =
                    parseInt(
                        $(this.btn_zoom_percentageRef.el).text().replace("%", "")
                    ) + 10;
                this.zoom(scale_value);
                $(this.btn_zoom_outRef.el).removeAttr("disabled");
                if (scale_value >= 500) {
                    ev.currentTarget.setAttribute("disabled", true);
                }
            }
        }

        onZoomOut(ev) {
            ev.stopPropagation();
            if ($(".o_content").length) {
                var scale_value =
                    parseInt(
                        $(this.btn_zoom_percentageRef.el).text().replace("%", "")
                    ) - 10;
                this.zoom(scale_value);
                $(this.btn_zoom_inRef.el).removeAttr("disabled");
                if (scale_value <= 20) {
                    ev.currentTarget.setAttribute("disabled", true);
                }
            }
        }

        onZoomReset(ev) {
            ev.stopPropagation();
            if ($(".o_content").length) {
                if (document.querySelector(".o_content").children.length === 1) {
                    $(".o_content div:last-child").removeAttr("style");
                } else {
                    $(".o_content").removeAttr("style");
                }
                $(this.btn_zoom_percentageRef.el).text("100%");
            }
        }
    }

    OsZoom.template = 'os_theme_butterfly.Zoom';
    OsZoomContent.template = 'os_theme_butterfly.ZoomContent';
} else {

    export class OsZoom extends Component {
    }

    export class OsZoomContent extends Component {
    }
}


