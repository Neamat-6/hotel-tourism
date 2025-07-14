/** @odoo-module **/

import {useService} from "@web/core/utils/hooks";

const {device} = require('web.config');

const {Component, hooks} = owl;
const {useRef} = hooks;

export class OsSideBar extends Component {
    setup() {
        super.setup();
        var self = this;
        this.menuService = useService("menu");
        this.userThemeService = useService("os_user_settings");
        this.companyThemeService = useService("os_company_settings");
        this.companyService = useService("company");
        this.appSubMenus = useRef("appSubMenus");
        this.hideSidebar = useRef("hideSidebar");
        this._header_menu = 'os-header-menu';
        this._break = OsApp.Break;
        this._sidebar = 'os-sidebar';

        hooks.onMounted(() => {
            if (device.isMobile) {
                $(this.el).find(".os-menu-link:not(.os-menu-toggle)").click(function () {
                    self.hideMenu(false)
                });
            }
        });
    }


    hideMenu(ev, opt) {
        var $toggle;
        if (ev) {
            ev.preventDefault();
            $toggle = $(ev.currentTarget);
        } else {
            $toggle = $(this.hideSidebar.el);

        }
        var self = this, $win = $(window), $body = $('body'), $doc = $(document);
        var $contentD = $('[data-content]'),
            toggleBreak = $contentD.hasClass(this._header_menu) ? self._break.lg : self._break.xl,
            toggleOlay = this._sidebar + '-overlay', toggleClose = {profile: true, menu: false},
            def = {
                active: 'toggle-active',
                content: this._sidebar + '-active',
                body: 'nav-shown',
                overlay: toggleOlay,
                break: toggleBreak,
                close: toggleClose
            },
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

    dropDownMenu(ev) {
        var
            def = {active: 'active', self: 'os-menu-toggle', child: 'os-menu-sub'},
            attr = def;
        var $this = $(ev.currentTarget);
        if ((OsApp.Win.width < this._break.lg) || ($this.parents().hasClass(this._sidebar))) {
            OsApp.Toggle.dropMenu($this, attr);
        }
        ev.preventDefault();
    }

    openDropDownMenu(menu_id) {
        var
            def = {active: 'active', self: 'os-menu-toggle', child: 'os-menu-sub'},
            attr = def;

        $(".os-menu-link.os-menu-toggle").each(function (index) {
            if ($(this).attr("href").includes("menu_id=" + menu_id)) {
                OsApp.Toggle.dropMenu($(this), attr);
            }
        });

    }

    toggle_sidebar(ev) {
        ev.preventDefault();
        var $sidebar = $('.' + this._sidebar), $sidebar_body = $('.' + this._sidebar + '-body');

        var $self = $(ev.currentTarget), get_target = $self.data('target'),
            $self_content = $('[data-content=' + get_target + ']');


        $self.toggleClass('compact-active');
        $self_content.toggleClass('is-compact');
        if (!$self_content.hasClass('is-compact')) {
            $self_content.removeClass('has-hover');
        }
        $sidebar_body.on('mouseenter', function (e) {
            if ($sidebar.hasClass('is-compact')) {
                $sidebar.addClass('has-hover');
            }
        });
        $sidebar_body.on('mouseleave', function (e) {
            if ($sidebar.hasClass('is-compact')) {
                $sidebar.removeClass('has-hover');
            }
        });
    }

    close_open_sidebar(action) {

        var $self = $(".os-nav-compact"), get_target = $self.data('target'),
            $self_content = $('[data-content=' + get_target + ']');

        if (action === "open") {
            $self.removeClass('compact-active');
            $self_content.removeClass('is-compact');
        } else if (action === "close") {
            $self.addClass('compact-active');
            $self_content.addClass('is-compact');
        } else {
            $self.toggleClass('compact-active');
            $self_content.toggleClass('is-compact');
        }

        if (!$self_content.hasClass('is-compact')) {
            $self_content.removeClass('has-hover');
        }

    }

    AppSections(menu_id) {
        return (
            (menu_id && this.menuService.getMenuAsTree(menu_id).childrenTree) ||
            []
        );
    }

    getMenuItemHref(payload) {
        const parts = [`menu_id=${payload.id}`];
        if (payload.actionID) {
            parts.push(`action=${payload.actionID}`);
        }
        return "#" + parts.join("&");
    }

    onSidebarBarItemSelection(menu) {
        if (menu) {
            this.menuService.selectMenu(menu);
        }
    }

    getMenuSection(payload) {
        return payload.id;
    }

    getMenuXmlId(payload) {
        return payload.xmlid;
    }

}


OsSideBar.template = "os_theme_butterfly.OsSideBar";
