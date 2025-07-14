/** @odoo-module **/
const {device} = require('web.config');

import {ControlPanel} from "@web/search/control_panel/control_panel";
import {patch} from "@web/core/utils/patch";

const {useState} = owl.hooks;
const {Portal} = owl.misc;
const CLASS = "os_sticky_cp";

patch(ControlPanel.prototype, "os_theme_butterfly.SearchControlPanelMobile", {
    setup() {
        this._super();
        this.isMobile = device.isMobile;
        if (device.isMobile) {
            this.state = useState({
                showSearchBar: false,
                showMobileSearch: false,
                showViewSwitcher: false,
            });
        }

    },
    mounted() {
        this.bestScrollTop = 80;
        this.el.style.top = $(this.header_class).height() + 'px';
        if (device.isMobile) {
            window.addEventListener('click', this._closeSwitcher.bind(this));
        }
        document.addEventListener('scroll', this._onScroll.bind(this));

        this._super();
    },


    _onScroll() {
        if (this.windowScrolling) {
            return;
        }
        this.windowScrolling = true;
        requestAnimationFrame(() => (this.windowScrolling = false));

        const scrollTop = document.documentElement.scrollTop;
        if (this.el) {
            if (scrollTop > this.bestScrollTop) {
                this.el.classList.add(CLASS);
            } else {
                this.el.classList.remove(CLASS);
            }
        }

    },

    onViewClicked() {
        if (device.isMobile) {
            Object.assign(this.state, {
                showSearchBar: false,
                showMobileSearch: false,
                showViewSwitcher: false,
            });
        }
        this._super(...arguments);
    },

    _closeSwitcher(ev) {
        if (this.state.showViewSwitcher && !ev.target.closest(".o_cp_switch_buttons")) {
            this.state.showViewSwitcher = false;
        }
    },
});

patch(ControlPanel, "os_theme_butterfly.SearchControlPanelMobile", {
    components: {
        ...ControlPanel.components,
        Portal,
    },
});
