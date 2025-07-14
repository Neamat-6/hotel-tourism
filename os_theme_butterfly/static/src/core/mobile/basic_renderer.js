odoo.define('os_theme_butterfly.BasicRendererMobile', function (require) {
    "use strict";

    const {device} = require('web.config');
    if (!device.isMobile) {
        return;
    }

    const BasicRenderer = require('web.BasicRenderer');

    BasicRenderer.include({
        TIMEOUT: 250,

        init() {
            this._super(...arguments);
            this.showTimer = undefined;
            this.tooltipNodes = [];
            this._onTouchStartTooltipBind = this._onTouchStartTooltip.bind(this);
            this._onTouchEndTooltipBind = this._onTouchEndTooltip.bind(this);
        },

        on_attach_callback() {
            this._super(...arguments);
            this._addListener();
        },

        on_detach_callback() {
            this._removeListeners();
            this._super(...arguments);
        },

        _addListener: function () {
            this.tooltipNodes.forEach((nodeElement) => {
                nodeElement.addEventListener('touchstart', this._onTouchStartTooltipBind);
                nodeElement.addEventListener('touchend', this._onTouchEndTooltipBind);
                nodeElement.classList.add('os_user_no_select');
            });
        },

        _addFieldTooltip: function (widget, $node) {
            this._super(...arguments);
            $node = $node.length ? $node : widget.$el;
            const nodeElement = $node[0];
            if (!this.tooltipNodes.some(node => node === nodeElement)) {
                this.tooltipNodes.push(nodeElement);
            }
        },

        _getTooltipOptions: function () {
            return Object.assign({}, this._super(...arguments), {
                trigger: 'manual',
            });
        },

        _render: function () {
            return this._super(...arguments).then(() => {
                this._addListener();
            });
        },
        _removeListeners: function () {
            while (this.tooltipNodes.length) {
                const node = this.tooltipNodes.shift();
                node.removeEventListener('touchstart', this._onTouchStartTooltipBind);
                node.removeEventListener('touchend', this._onTouchEndTooltipBind);
                node.classList.remove('os_user_no_select');
            }
        },

        _onTouchEndTooltip: function (event) {
            clearTimeout(this.showTimer);
            const $node = $(event.target);
            $node.tooltip('hide');
        },

        _onTouchStartTooltip: function (event) {
            if (!event.target.classList.contains('os_user_no_select')) {
                return;
            }
            const $node = $(event.target);
            clearTimeout(this.showTimer);
            this.showTimer = setTimeout(() => {
                $node.tooltip('show');
            }, this.TIMEOUT);
        },
    });

});
