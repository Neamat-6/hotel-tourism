/** @odoo-module **/
import {session} from "@web/session";

const {Component} = owl;

if (session.user_display_full_screen) {
    const {useRef} = owl.hooks;

    export class OsFullScreenMenu extends Component {
        setup() {
            super.setup();
            this.iconRef = useRef('os-icon-fullscreen');
        }

        _onFullScreen(ev) {
            let btn = $(this.iconRef.el);

            if ((document.fullScreenElement !== undefined && document.fullScreenElement === null) || (document.msFullscreenElement !== undefined && document.msFullscreenElement === null) || (document.mozFullScreen !== undefined && !document.mozFullScreen) || (document.webkitIsFullScreen !== undefined && !document.webkitIsFullScreen)) {
                if (document.documentElement.requestFullScreen) {
                    document.documentElement.requestFullScreen();
                } else if (document.documentElement.mozRequestFullScreen) {
                    document.documentElement.mozRequestFullScreen();
                } else if (document.documentElement.webkitRequestFullScreen) {
                    document.documentElement.webkitRequestFullScreen(Element.ALLOW_KEYBOARD_INPUT);
                } else if (document.documentElement.msRequestFullscreen) {
                    document.documentElement.msRequestFullscreen();
                }
            } else {

                if (document.cancelFullScreen) {
                    document.cancelFullScreen();
                } else if (document.mozCancelFullScreen) {
                    document.mozCancelFullScreen();
                } else if (document.webkitCancelFullScreen) {
                    document.webkitCancelFullScreen();
                } else if (document.msExitFullscreen) {
                    document.msExitFullscreen();
                }
            }
            var fullscreenchange = $.browser.mozilla ? "mozfullscreenchange" : $.browser.webkit ? "webkitfullscreenchange" : "fullscreenchange";
            $(document).on(fullscreenchange, function () {
                if ((document.fullScreenElement !== undefined && document.fullScreenElement === null) || (document.msFullscreenElement !== undefined && document.msFullscreenElement === null) || (document.mozFullScreen !== undefined && !document.mozFullScreen) || (document.webkitIsFullScreen !== undefined && !document.webkitIsFullScreen)) {
                    btn.removeClass("osi-shrink");
                    btn.addClass("osi-expand");
                } else {
                    btn.removeClass("osi-expand");
                    btn.addClass("osi-shrink");
                }
            });
        }

    }

    OsFullScreenMenu.template = "os_theme_butterfly.os_fullscreen_menu";
} else {
    export class OsFullScreenMenu extends Component {
    }
}