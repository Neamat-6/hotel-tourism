/** @odoo-module **/
import {useService} from "@web/core/utils/hooks";
const {Component} = owl;
var core = require('web.core');

export class OsRecentlyViewedMenu extends Component {
    setup() {
        super.setup();
        this.rpc = useService("rpc");
        core.bus.on('RECENTLY_ACTION_PERFORMED', this, this.update);
    }

    async willStart() {
        this.records = await this.loadRecords("/theme/get/recently/viewed/records");
        return super.willStart();
    }

    async loadRecords(Route) {
        return await this.rpc(Route);
    }

    async update(data) {
        this.records = data;
        this.render();
    }

    _onClickRecord(ev) {
        let res_model = $(ev.currentTarget).data("res_model");
        let res_id = $(ev.currentTarget).data("res_id");
        let name = $(ev.currentTarget).data("name");

        this.env.services.action.doAction({
            type: 'ir.actions.act_window',
            name: name,
            res_model: res_model,
            res_id: res_id,
            views: [[false, 'form']],
            target: 'current'
        });
    }

}

OsRecentlyViewedMenu.template = "os_theme_butterfly.os_recently_viewed_menu";

