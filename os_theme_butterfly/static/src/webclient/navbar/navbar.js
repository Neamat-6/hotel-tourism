/** @odoo-module */

import {patch} from "@web/core/utils/patch";
import {useService} from "@web/core/utils/hooks";
import {NavBar} from "@web/webclient/navbar/navbar";
import {OsViewAppsMenu} from "@os_theme_butterfly/components/os_view_apps/os_view_apps_menu";

const {device} = require('web.config');
const {hooks} = owl;
const {useRef} = hooks;

patch(NavBar.prototype, "os_theme_butterfly.NavBar", {
    setup() {
        this._super();
        this.companyThemeService = useService("os_company_settings");
        this.themeUserService = useService("os_user_settings");
        this.userService = useService("user");
        this.companyService = useService("company");
        this.menuService = useService("menu");
        this.menuBrand = useRef("menuBrand");
        this.viewApps = useService("view_apps");
        this.isMobile = device.isMobile;
        hooks.onMounted(() => {
            this.env.bus.on("APPS-MENU-TOGGLED", this, () => this._updateNavbar());
            this._updateNavbar();
        });
        hooks.onPatched(() => {
            this._updateNavbar();
        });
    },

    get isAppViewDisplayed() {
        return !this.viewApps.is_displayed;
    },

    _updateNavbar() {
        const menuBrand = this.menuBrand.el;
        if (menuBrand) {
            menuBrand.classList.toggle("o_hidden", !this.isAppViewDisplayed);
        }

        const appSubMenus = this.appSubMenus.el;
        if (appSubMenus) {
            appSubMenus.classList.toggle("o_hidden", !this.isAppViewDisplayed);
        }
    },

    showMenu(ev, opt) {
        ev.preventDefault();
        this._break = OsApp.Break;
        this._sidebar = 'os-sidebar';
        this._header_menu = 'os-header-menu';
        var self = this, $win = $(window), $body = $('body'), $doc = $(document);
        var $toggle = $(ev.currentTarget), $contentD = $('[data-content]'),
            toggleBreak = $contentD.hasClass(this._header_menu) ? self._break.lg : self._break.xl,
            toggleOlay = this._sidebar + '-overlay', toggleClose = {profile: true, menu: false},
            def = {active: 'toggle-active', content: this._sidebar + '-active', body: 'nav-shown', overlay: toggleOlay, break: toggleBreak, close: toggleClose},
            attr = (opt) ? extend(def, opt) : def;

        OsApp.Toggle.trigger($toggle.data('target'), attr);

        $doc.on('mouseup', function (e) {
            if (!$toggle.is(e.target) && $toggle.has(e.target).length === 0 && !$contentD.is(e.target) && $contentD.has(e.target).length === 0 && OsApp.Win.width < toggleBreak) {
                OsApp.Toggle.removed($toggle.data('target'), attr);
            }
        });

        $win.on('resize', function () {
            if ((OsApp.Win.width < self._break.xl || OsApp.Win.width < toggleBreak) && !OsApp.State.isMobile) {
                OsApp.Toggle.removed($toggle.data('target'), attr);
            }
        });
    }

});

patch(NavBar, "os_theme_butterfly.NavBar", {
    components: {
        ...NavBar.components,
        OsViewAppsMenu,
    },
});
	