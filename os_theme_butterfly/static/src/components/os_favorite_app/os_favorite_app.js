/** @odoo-module **/

import {useService} from "@web/core/utils/hooks";

const {Component, hooks} = owl;
const {useRef} = owl.hooks;
var Dialog = require('web.Dialog');
var rpc = require('web.rpc');

function _make_option(term) {
    return {id: term, text: term};
}

export class OsFavoriteAppMenu extends Component {
    setup() {
        super.setup();
        this.menuService = useService("menu");
        this.action = "list_favorite_apps";
        this.application_input_ref = useRef('application_input');
        this.favorite_app_name_ref = useRef('favorite_app_name');
        this.companyThemeService = useService("os_company_settings");
        this.env.bus.on("FAVORITE_APP:ADD_FAVORITE_APP", this, () => {
                this.action = "add_favorite_app_item";
                this.renderFavoriteApps();
            }
        );
        this.env.bus.on("FAVORITE_APP:EDIT_MODE_ENABLED", this, () => {
                this.action = "edit_mode";
                this.renderFavoriteApps();
            }
        );
        this.env.bus.on("FAVORITE_APP:EDIT_MODE_DISABLED", this, () => {
                this.action = "list_favorite_apps";
                this.renderFavoriteApps();
            }
        );

        this.env.bus.on("FAVORITE_APP:CANCEL_EDIT_FAVORITE_APP", this, (data) => {
                this.action = "list_favorite_apps";
                if (data) {
                    this.records = data;
                }
                this.renderFavoriteApps();
            }
        );
        this.env.bus.on("FAVORITE_APP:EDIT_FAVORITE_APP_ITEM", this, ($el) => {
                this.action = "edit_favorite_app_item";
                this.favorite_app_item = {
                    'id': $el.data('id'),
                    'name': $el.data('name'),
                    'menu_id': $el.data('menu_id'),
                    'menu_name': $el.data('menu_name'),
                    'sequence': $el.data('sequence'),
                }
                this.renderFavoriteApps();
            }
        );
        this.env.bus.on("FAVORITE_APP:CLOSE_DROPDOWN", this, () => {
                this.action = "list_favorite_apps";
                this.renderFavoriteApps();
            }
        );
        hooks.onPatched(() => {
            var self = this;
            if (this.action === "add_favorite_app_item" || this.action === "edit_favorite_app_item") {
                let $input = $(self.application_input_ref.el);
                var domain = []
                if (this.records.length > 0) {
                    domain = [['id', 'not in', this.records[0].menus_ids]]
                }
                this.$select2 = $input.select2({
                    width: '100%',
                    allowClear: true,
                    formatNoMatches: false,
                    multiple: false,
                    fill_data: function (query, data) {
                        var that = this;
                        var tags = {results: []};
                        _.each(data, function (obj) {
                            if (that.matcher(query.term, obj.name)) {
                                tags.results.push({
                                    id: obj.id,
                                    text: obj.name,
                                });
                            }
                        });
                        query.callback(tags);
                    },
                    query: function (query) {
                        var that = this;
                        rpc.query({
                            model: 'ir.ui.menu',
                            method: 'os_load_menus_root_with_domain',
                            args: [],
                            kwargs: {
                                domain: domain
                            },

                        }).then(function (data) {
                            that.fill_data(query, data.children);
                        });

                    },

                    initSelection: function ($e, c) {
                        return c(_make_option($e.val()));

                    }

                });


                this.$select2.change(function () {
                    let data = $input.select2('data');
                    $(self.favorite_app_name_ref.el).val(data.text);
                });

                if (this.action === "edit_favorite_app_item") {
                    $input.select2('val', this.favorite_app_item.menu_name);
                    $input.select2('disable');
                }
            }


        });
    }

    async willStart() {
        this.records = await this.loadRecords("/theme/get/favorite_app");
        return super.willStart();
    }

    async loadRecords(Route) {
        return await this.rpc(Route);
    }

    getInfoMenuItem(menuID) {
        return this.menuService.getMenu(menuID);

    }

    async renderFavoriteApps(menuID) {
        await this.render();
        tippy('[data-tippy-content]', {
            animation: 'shift-away',
        });
    }

    getMenuItemHref(payload) {
        const parts = [`menu_id=${payload.id}`];
        if (payload.actionID) {
            parts.push(`action=${payload.actionID}`);
        }
        return "#" + parts.join("&");
    }

    onClickFavoriteAppItem(ev) {
        var $el = $(ev.currentTarget);
        this.env.bus.trigger('FAVORITE_APP:EDIT_FAVORITE_APP_ITEM', $el);

    }

    onClickAddFavoriteApp(ev) {
        this.env.bus.trigger('FAVORITE_APP:ADD_FAVORITE_APP');
    }

    enterEditMode() {
        this.env.bus.trigger('FAVORITE_APP:EDIT_MODE_ENABLED');
    }

    exitEditMode() {
        this.env.bus.trigger('FAVORITE_APP:EDIT_MODE_DISABLED');
    }


    cancelEditItem() {
        this.env.bus.trigger('FAVORITE_APP:CANCEL_EDIT_FAVORITE_APP');
    }

    onClickdeleteFavoriteAppItem(ev) {
        var $el = $(ev.currentTarget);
        var self = this;
        Dialog.confirm(this, (this.env._t("Are you sure you want to remove this item?")), {
            confirm_callback: function () {
                self.deleteFavoriteAppItem($el.data('favorite_app-id'))
            },
        });
    }

    deleteFavoriteAppItem(item_id) {
        var self = this;
        let data = {
            'id': item_id,
        }
        return this.rpc("/theme/favorite_app/delete", {data: data}).then(function (data) {
            self.env.bus.trigger('FAVORITE_APP:CANCEL_EDIT_FAVORITE_APP', data);
            self.exitEditMode();
        });
    }

    updateFavoriteAppItem(ev) {
        var self = this;
        var $el = $(ev.currentTarget);
        let name = $(this.el.querySelector('#favorite_app_name')).val().trim();
        let sequence = $(this.el.querySelector('#favorite_app_sequence')).val().trim();
        if (name === '') {
            $(self.el.querySelector('#favorite_app_errors_msg')).html(
                $('<div class="alert alert-danger py-1 fs-14px mb-2" role="alert"/>')
                    .text(this.env._t('Please fill all the required fields first!'))
            );
        } else {
            $(self.el.querySelector('#favorite_app_errors_msg')).html('');
            let data = {
                'id': $el.data('favorite_app-id'),
                'name': name,
                'sequence': sequence !== "" ? sequence : 10,
            }
            return this.rpc("/theme/favorite_app/update", {data: data}).then(function (data) {
                self.env.bus.trigger('FAVORITE_APP:CANCEL_EDIT_FAVORITE_APP', data);
                self.exitEditMode();
            });
        }

    }

    async addFavoriteAppItem() {
        var self = this;
        let name = $(this.el.querySelector('#favorite_app_name')).val().trim();
        let menu_id = $(this.el.querySelector('#application')).val().trim();
        let sequence = $(this.el.querySelector('#favorite_app_sequence')).val().trim();
        if (name === '' || menu_id === '') {
            $(self.el.querySelector('#favorite_app_errors_msg')).html(
                $('<div class="alert alert-danger py-1 fs-14px mb-2" role="alert"/>')
                    .text(this.env._t('Please fill all the required fields first!'))
            );
        } else {
            $(self.el.querySelector('#favorite_app_errors_msg')).html('');
            let data = {
                'name': name,
                'menu_id': menu_id,
                'sequence': sequence !== "" ? sequence : 10,
            }

            return this.rpc("/theme/favorite_app/add", {data: data}).then(function (data) {
                if (data[0]) {
                    $(self.el.querySelector('#favorite_app_errors_msg')).html(
                        $('<div class="alert alert-danger py-1 fs-14px mb-2" role="alert"/>')
                            .text(data[0])
                    );
                } else {
                    self.env.bus.trigger('FAVORITE_APP:CANCEL_EDIT_FAVORITE_APP', data[1]);
                }
            });
        }
    }
}

OsFavoriteAppMenu.template = "os_theme_butterfly.os_favorite_app_menu";
