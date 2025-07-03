odoo.define('hotel_booking.HousekeepingDiffReportListView', function (require) {
"use strict";

var ListView = require('web.ListView');
var HousekeepingDiffReportListController = require('hotel_booking.HousekeepingDiffReportListController');
var viewRegistry = require('web.view_registry');


var HousekeepingDiffReportListView = ListView.extend({
    config: _.extend({}, ListView.prototype.config, {
        Controller: HousekeepingDiffReportListController,
    }),
});

viewRegistry.add('housekeeping_diff_report_list', HousekeepingDiffReportListView);

return HousekeepingDiffReportListView;

});
