/* @odoo-module */
import {session} from "@web/session";

if (!session.user_display_bookmarks) {
    return;
}

import {patch} from "@web/core/utils/patch";
import {ClientActionAdapter, ViewAdapter} from "@web/legacy/action_adapters";
import {parseHash} from "@web/core/browser/router_service";

const ajax = require('web.ajax');
patch(ClientActionAdapter.prototype, 'os_theme_butterfly.ClientActionAdapter', {

    setup() {
        const data = this._super(...arguments);
        this.action = {...this.props.widgetArgs[0]};
        return data;

    },
    async loadRecords(Route) {
        return await ajax.jsonRpc(Route);
    },
    parseURL(url) {
        url = url.replace('web#', '')
        return parseHash(url);
    },
    async do_push_state(state) {
        let self = this;
        const data = this._super(...arguments);
        this.bookmark_records = await this.loadRecords("/theme/get/bookmark");
        let links = _.map(this.bookmark_records, 'link');
        let is_res_id = state && state.id
        let action_id = this.action.id;

        let is_bookmarked = _.some(links, function (data) {
            let url = self.parseURL(data);
            if (is_res_id) {
                let res_id = state.id;
                return url.id === res_id && url.action === action_id;
            } else {
                return url.action === action_id;
            }

        });

        if (is_bookmarked) {

            $('#icon_bookmark').addClass("text-warning").removeClass('osi-bookmark').addClass('osi-bookmark-fill');
        } else {
            $('#icon_bookmark').removeClass("text-warning").removeClass('osi-bookmark-fill').addClass('osi-bookmark');
        }
        return data;

    }

});
patch(ViewAdapter.prototype, 'os_theme_butterfly.ViewAdapter', {
    async setup() {
        const data = this._super(...arguments);
        this.action = {...this.props.viewParams.action};
        return data;

    },
    async loadRecords(Route) {
        return await ajax.jsonRpc(Route);
    },
    parseURL(url) {
        url = url.replace('web#', '')
        return parseHash(url);
    },
    async _trigger_up(ev) {
        const data = this._super(...arguments);
        let self = this;

        if (ev.name === "push_state") {
            this.bookmark_records = await this.loadRecords("/theme/get/bookmark");
            let links = _.map(this.bookmark_records, 'link');
            let is_res_id = ev.data.state && ev.data.state.id
            let action_id = this.action.id;

            let is_bookmarked = _.some(links, function (data) {
                let url = self.parseURL(data);
                if (is_res_id) {
                    let res_id = ev.data.state.id;
                    return url.id === res_id && url.action === action_id;
                } else {
                    return url.action === action_id;
                }

            });


            if (is_bookmarked) {

                $('#icon_bookmark').addClass("text-warning").removeClass('osi-bookmark').addClass('osi-bookmark-fill');
            } else {
                $('#icon_bookmark').removeClass("text-warning").removeClass('osi-bookmark-fill').addClass('osi-bookmark');
            }

        }
        return data;

    }

});
