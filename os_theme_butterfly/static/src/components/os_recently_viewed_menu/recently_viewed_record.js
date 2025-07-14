odoo.define('os_theme_butterfly.recently_viewed_record', function (require) {
    "use strict";
    var session = require('web.session');
    if (!session.user_display_recently_viewed_records) return;


    var FormRenderer = require('web.FormRenderer');
    var core = require('web.core');
    FormRenderer.include({
        _updateView: function (e) {
            this._super.apply(this, arguments);
            if (this.state.res_id && this.state.context.params) {
                var data = {
                    'name': this.state.data.display_name,
                    'res_id': this.state.res_id,
                    'model': this.state.model,
                    'action': this.state.context.params.action || "",
                }

                this._rpc({
                    route: "/theme/recently/viewed/records",
                    params: {data: data}
                }).then(function (data) {
                    core.bus.trigger('RECENTLY_ACTION_PERFORMED', data);
                });

            }

        },

    });
})
