odoo.define('os_theme_butterfly.ControlPanel', function (require) {
    "use strict";
    const {device} = require('web.config');
    const ControlPanel = require('web.ControlPanel');
    const {patch} = require('web.utils');
    const {Portal} = owl.misc;
    const {useState} = owl.hooks;
    const CLASS = 'os_sticky_cp';

    patch(ControlPanel.prototype, 'os_theme_butterfly.ControlPanel', {
        setup() {
            this._super(...arguments);
            this.header_class = '.os-header';
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
            this._super(...arguments);
            this.bestScrollTop = 80;
            this.el.style.top = $(this.header_class).height() + 'px';
            if (device.isMobile) {
                window.addEventListener('click', this._closeSwitcher.bind(this));
            }
            document.addEventListener('scroll', this._onScroll.bind(this));
            var $target = $('[data-search]');
            $target.toggleClass("active", $target.find('.o_searchview_facet').length > 0);
            $target.find('.o_searchview_icon').on({
                click: function (e) {
                    $target.removeClass("active");
                }
            });
        },

        willUnmount() {
            if (device.isMobile) {
                window.removeEventListener('click', this._closeSwitcher.bind(this));
            }
            document.removeEventListener('scroll', this._onScroll.bind(this));
        },


        _onScroll() {
            if (this.windowScrolling || !this.el) {
                return;
            }
            this.windowScrolling = true;
            requestAnimationFrame(() => this.windowScrolling = false);

            const scrollTop = document.documentElement.scrollTop;
            if (this.el) {
                if (scrollTop > this.bestScrollTop) {
                    this.el.classList.add(CLASS);
                } else {
                    this.el.classList.remove(CLASS);
                }
            }
        },


        _onSwitchView() {
            Object.assign(this.state, {
                showSearchBar: false,
                showMobileSearch: false,
                showViewSwitcher: false,
            });
        },

        _closeSwitcher(ev) {
            if (
                this.state.showViewSwitcher &&
                !ev.target.closest('.o_cp_switch_buttons')
            ) {
                this.state.showViewSwitcher = false;
            }
        },
        openSearch(ev) {
            var def = {active: 'active', timeout: 400, target: '[data-search]'}, attr = def;
            var $doc = $(document), $target = $(attr.target);
            var $elem = $(ev.currentTarget);
            ev.preventDefault();
            var $self = $elem, the_target = $self.data('target'),
                $self_st = $('[data-search=' + the_target + ']'),
                $self_tg = $('[data-target=' + the_target + ']');

            if (!$self_st.hasClass(attr.active)) {
                $self_tg.add($self_st).addClass(attr.active);
                $self_st.find('input').focus();
            } else {
                $self_tg.add($self_st).removeClass(attr.active);
                setTimeout(function () {
                    $self_st.find('input').val('');
                }, attr.timeout);
            }


            $doc.on({
                keyup: function (e) {
                    if (e.key === "Escape") {
                        $elem.add($target).removeClass(attr.active);
                    }
                },
            });


        }

    });

    patch(ControlPanel, 'os_theme_butterfly.ControlPanelMobile', {
        components: {
            ...ControlPanel.components,
            Portal,
        },
    });
});
