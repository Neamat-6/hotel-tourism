/** @odoo-module */

import {patch} from "@web/core/utils/patch";
import {session} from "@web/session";
import {OsSideBar} from "@os_theme_butterfly/components/os_sidebar/os_sidebar";
import {OsTodo} from "@os_theme_butterfly/components/os_todo/os_todo";
import {Os_todo_menu} from "@os_theme_butterfly/components/os_todo/os_todo_menu";
import {OsWebRibbon} from "@os_theme_butterfly/components/os_web_ribbon/os_web_ribbon";
import {OsScrollToTop} from "@os_theme_butterfly/components/os_scroll_top/os_scroll_top";
import {OsZoom, OsZoomContent} from "@os_theme_butterfly/components/os_zoom/os_zoom";
import {OsFullScreenMenu} from "@os_theme_butterfly/components/os_fullscreen_menu/os_fullscreen_menu";
import {OsHeaderToolsBar} from "@os_theme_butterfly/components/os_header_toolsbar/os_header_toolsbar";
import {OsSettingsPanelUser, OsSettingsPanelGeneral} from "@os_theme_butterfly/components/os_settings_panel/os_settings_panel";
import {WebClient} from "@web/webclient/webclient";
import {useService} from "@web/core/utils/hooks";
import {hasTouch} from "@web/core/browser/feature_detection";

const {device} = require('web.config');

const {hooks} = owl;

patch(WebClient, "os_theme_butterfly.WebClient", {
    components: {
        ...WebClient.components,
        OsSideBar,
        OsSettingsPanelUser,
        OsSettingsPanelGeneral,
        OsZoom,
        OsZoomContent,
        OsFullScreenMenu,
        OsTodo,
        Os_todo_menu,
        OsWebRibbon,
        OsScrollToTop,
        OsHeaderToolsBar,
    },
});

function extend(obj, ext) {
    Object.keys(ext).forEach(function (key) {
        obj[key] = ext[key];
    });
    return obj;
}

export class WebClientTheme extends WebClient {
    constructor() {
        super(...arguments);
        this.$win = $(window);
        this.$body = $('body');
        this.$doc = $(document);
        this._break = OsApp.Break;
        this.userThemeService = useService("os_user_settings");
        this.companyThemeService = useService("os_company_settings");
        this.userService = useService("user");
        this.viewAppsService = useService("view_apps");
        this.isMobile = device.isMobile;

    }

    setup() {
        super.setup();
        const title = session.company_web_window_title;
        if (title) {
            this.title.setParts({zopenerp: title});
        }

        hooks.onMounted(() => {
            this.content('.toggle');
            this.expand('.toggle-expand');
            this.expand('.toggle-opt', {toggle: false});
            tippy('[data-tippy-content]', {
                animation: 'shift-away',
            });
            this.el.classList.toggle("o_touch_device", hasTouch());

            $(".os_draggable").each(function () {
                $(this).draggable();
            });

        });
    }


    expand(elm, opt) {
        var toggle = (elm) ? elm : '.expand', def = {toggle: true}, attr = (opt) ? extend(def, opt) : def;

        $(toggle).on('click', function (e) {
            OsApp.Toggle.trigger($(this).data('target'), attr);
            e.preventDefault();
        });
    }

    screen(elm) {
        if ($(elm).exists()) {
            $(elm).each(function () {
                var size = $(this).data('toggle-screen');
                if (size) {
                    $(this).addClass('toggle-screen-' + size);
                }
            });
        }
    }

    content(elm, opt) {
        let self = this;
        var toggle = (elm) ? elm : '.toggle', $toggle = $(toggle), $contentD = $('[data-content]'),
            toggleBreak = true, toggleCurrent = false, def = {active: 'active', content: 'content-active', break: toggleBreak}, attr = (opt) ? extend(def, opt) : def;

        this.screen($contentD);

        $toggle.on('click', function (e) {
            toggleCurrent = this;
            OsApp.Toggle.trigger($(this).data('target'), attr);
            e.preventDefault();
        });

        this.$doc.on('mouseup', function (e) {
            if (toggleCurrent) {
                var $toggleCurrent = $(toggleCurrent), currentTarget = $(toggleCurrent).data('target'), $contentCurrent = $(`[data-content="${currentTarget}"]`), $s2c = $('.select2-container'), $dpd = $('.datepicker-dropdown'), $tpc = $('.ui-timepicker-container'), $mdl = $('.modal');
                if (!$toggleCurrent.is(e.target) && $toggleCurrent.has(e.target).length === 0 && !$contentCurrent.is(e.target) && $contentCurrent.has(e.target).length === 0
                    && !$s2c.is(e.target) && $s2c.has(e.target).length === 0 && !$dpd.is(e.target) && $dpd.has(e.target).length === 0
                    && !$tpc.is(e.target) && $tpc.has(e.target).length === 0 && !$mdl.is(e.target) && $mdl.has(e.target).length === 0) {
                    OsApp.Toggle.removed($toggleCurrent.data('target'), attr);
                    toggleCurrent = false;
                }
            }
        });

        this.$win.on('resize', function () {
            $contentD.each(function () {
                var content = $(this).data('content'), size = $(this).data('toggle-screen'), toggleBreak = self._break[size];
                if (OsApp.Win.width > toggleBreak) {
                    OsApp.Toggle.removed(content, attr);
                }
            });
        });
    }

    _loadDefaultApp() {
        return this.viewAppsService.toggleView(true);
    }
}

WebClientTheme.components = {...WebClient.components};


	