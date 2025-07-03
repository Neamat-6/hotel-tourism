odoo.define('hotel_booking.HousekeepingDiffReportListController', function (require) {
"use strict";

var ListController = require('web.ListController');

var HousekeepingDiffReportListController = ListController.extend({
    buttons_template: 'DiscrepancyReport.Buttons',

    // -------------------------------------------------------------------------
    // Public
    // -------------------------------------------------------------------------

    init: function (parent, model, renderer, params) {
        this.context = renderer.state.getContext();
        return this._super.apply(this, arguments);
    },

    /**
     * @override
     */
    renderButtons: function ($node) {
        this._super.apply(this, arguments);
        this.$buttons.on('click', '.o_button_diff', this._onOpenWizard.bind(this));
    },

    // -------------------------------------------------------------------------
    // Handlers
    // -------------------------------------------------------------------------

    /**
     * Handler called when the user clicked on the 'Inventory at Date' button.
     * Opens wizard to display, at choice, the products inventory or a computed
     * inventory at a given date.
     */
    _onOpenWizard: function () {
        var state = this.model.get(this.handle, {raw: true});
        var stateContext = state.getContext();
        var context = {
            active_model: this.modelName,
        };
        this.do_action({
            name: 'Discrepancy Report',
            res_model: 'housekeeping.diff',
            views: [[false, 'form']],
            target: 'new',
            type: 'ir.actions.act_window',
            context: context,
        });
    },
});

return HousekeepingDiffReportListController;

});
