odoo.define('os_theme_butterfly.FormRendererMobile', function (require) {
    "use strict";

    const {device} = require('web.config');
    if (!device.isMobile) {
        return;
    }

    const FormRenderer = require('web.FormRenderer');

    const {qweb} = require('web.core');

    FormRenderer.include({

        updateState: function () {
            this.isStatusbarButtonsOpen = undefined;
            return this._super(...arguments);
        },

        _renderStatusbarButtons: function (buttons) {

            const $visibleButtons = buttons.filter(button => {
                return !($(button).hasClass('o_invisible_modifier') || (this.mode === 'edit' && $(button).hasClass('oe_read_only')));
            });

            if ($visibleButtons.length > 1) {
                const $statusbarButtonsDropdown = $(qweb.render('os_theme_butterfly.StatusbarButtonsMobile', {
                    open: this.isStatusbarButtonsOpen,
                }));
                $statusbarButtonsDropdown.find('.btn-group').on('show.bs.dropdown', () => {
                    this.isStatusbarButtonsOpen = true;
                });
                $statusbarButtonsDropdown.find('.btn-group').on('hide.bs.dropdown', () => {
                    this.isStatusbarButtonsOpen = false;
                });
                const $dropdownMenu = $statusbarButtonsDropdown.find('.dropdown-menu');
                buttons.forEach(button => {
                    const dropdownButton = $(button).addClass('dropdown-item');
                    return $dropdownMenu.append(dropdownButton);
                });
                return $statusbarButtonsDropdown;
            }
            buttons.forEach(button => $(button).removeClass('dropdown-item'));
            return this._super.apply(this, arguments);
        },

        _updateAllModifiers: function () {
            return this._super.apply(this, arguments).then(() => {
                const $statusbarContainer = this.$('.o_statusbar_buttons');
                const $statusbarButtons = $statusbarContainer.find('button.btn').toArray();
                $statusbarContainer.replaceWith(this._renderStatusbarButtons($statusbarButtons));
            });
        },
    });

});
