/** @odoo-module **/
import {useService} from "@web/core/utils/hooks";

const {Component, hooks} = owl;
const {useRef} = owl.hooks;
var rpc = require('web.rpc');
var Dialog = require('web.Dialog');

function _make_option(term) {
    return {id: term, text: term};
}

export class OsQuickCreate extends Component {
    setup() {
        super.setup();
        this.rpc = useService("rpc");
        this.action = "list_quick_create";
        this.model_input_ref = useRef('model_input');
        this.quick_create_name_ref = useRef('quick_create_name');


        this.env.bus.on("QUICK_CREATE:ADD_QUICK_ACTION", this, () => {
                this.action = "add_quick_create_item";
                this.render();
            }
        );
        this.env.bus.on("QUICK_CREATE:CANCEL_EDIT_QUICK_ACTION", this, (data) => {
                this.action = "list_quick_create";
                if (data) {
                    this.records = data;
                }
                this.render();
            }
        );
        this.env.bus.on("QUICK_CREATE:EDIT_MODE_ENABLED", this, () => {
                this.action = "edit_mode";
                this.render();
            }
        );
        this.env.bus.on("QUICK_CREATE:EDIT_MODE_DISABLED", this, () => {
                this.action = "list_quick_create";
                this.render();
            }
        );

        this.env.bus.on("QUICK_CREATE:CLOSE_DROPDOWN", this, () => {
                this.action = "list_quick_create";
                this.render();
            }
        );

        this.env.bus.on("QUICK_CREATE:EDIT_QUICK_ACTION_ITEM", this, ($el) => {
                this.action = "edit_quick_create_item";
                this.quick_create_item = {
                    'id': $el.data('id'),
                    'name': $el.data('name'),
                    'model_id': $el.data('model-id'),
                    'model_name': $el.data('model-name'),
                    'model_model': $el.data('model-model'),
                    'sequence': $el.data('sequence'),
                    'icon': $el.data('icon'),
                }
                this.render();
            }
        );
        hooks.onPatched(() => {
            var self = this;
            if (this.action === "add_quick_create_item" || this.action === "edit_quick_create_item") {
                let $input = $(self.model_input_ref.el);
                var domain = []
                if (this.records.length > 0) {
                    domain = [['id', 'not in', this.records[0].models_ids]]
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
                            model: 'ir.model',
                            method: 'os_get_models',
                            args: [],
                            kwargs: {
                                domain: domain
                            },
                        }).then(function (data) {
                            that.fill_data(query, data);
                        });
                    },

                    initSelection: function ($e, c) {
                        return c(_make_option($e.val()));

                    }

                });

                this.$select2.change(function () {
                    let data = $input.select2('data');
                    $(self.quick_create_name_ref.el).val(data.text);
                });

                if (this.action === "edit_quick_create_item") {
                    $input.select2('val', this.quick_create_item.model_name);
                    $input.select2('disable');
                }
            }


        });


    }

    async willStart() {
        this.records = await this.loadRecords("/theme/get/quick_create");
        return super.willStart();
    }

    async loadRecords(Route) {
        return await this.rpc(Route);
    }

    onClickAddQuickCreate(ev) {
        this.env.bus.trigger('QUICK_CREATE:ADD_QUICK_ACTION');
    }

    enterEditMode() {
        this.env.bus.trigger('QUICK_CREATE:EDIT_MODE_ENABLED');
    }

    exitEditMode() {
        this.env.bus.trigger('QUICK_CREATE:EDIT_MODE_DISABLED');
    }

    cancelEditItem() {
        this.env.bus.trigger('QUICK_CREATE:CANCEL_EDIT_QUICK_ACTION');
    }

    onClickQuickCreateItem(ev) {
        var $el = $(ev.currentTarget);
        if (this.action === "edit_mode") {
            this.env.bus.trigger('QUICK_CREATE:EDIT_QUICK_ACTION_ITEM', $el);

        } else {
            this.env.services.action.doAction({
                type: 'ir.actions.act_window',
                name: $el.data('model-name'),
                res_model: $el.data('model-model'),
                views: [[false, 'form']],
                target: 'new'
            });
        }
    }

    onClickdeleteQuickCreateItem(ev) {
        var $el = $(ev.currentTarget);
        var self = this;
        Dialog.confirm(this, (this.env._t("Are you sure you want to remove this item?")), {
            confirm_callback: function () {
                self.deleteQuickCreateItem($el.data('quick_create_item-id'))
            },
        });
    }

    deleteQuickCreateItem(item_id) {
        var self = this;
        let data = {
            'id': item_id,
        }
        return this.rpc("/theme/quick_create/delete", {data: data}).then(function (data) {
            self.env.bus.trigger('QUICK_CREATE:CANCEL_EDIT_QUICK_ACTION', data);
            self.exitEditMode();
        });
    }

    updateQuickCreateItem(ev) {
        var self = this;
        var $el = $(ev.currentTarget);
        let name = $(this.el.querySelector('#quick_create_name')).val().trim();
        let model = $(this.el.querySelector('#model')).val().trim();
        let sequence = $(this.el.querySelector('#quick_create_sequence')).val().trim();
        let icon = $(this.el.querySelector('#quick_create_icon')).val().trim();
        if (name === '' || model === '' || icon === '') {
            $(self.el.querySelector('#quick_create_errors_msg')).html(
                $('<div class="alert alert-danger py-1 fs-14px mb-2" role="alert"/>')
                    .text(this.env._t('Please fill all the required fields first!'))
            );
        } else {
            $(self.el.querySelector('#quick_create_errors_msg')).html('');
            let data = {
                'id': $el.data('quick_create_item-id'),
                'name': name,
                'icon': icon,
                'sequence': sequence !== "" ? sequence : 10,
            }
            return this.rpc("/theme/quick_create/update", {data: data}).then(function (data) {
                self.env.bus.trigger('QUICK_CREATE:CANCEL_EDIT_QUICK_ACTION', data);
                self.exitEditMode();
            });
        }

    }

    async addQuickCreateItem() {
        var self = this;
        let name = $(this.el.querySelector('#quick_create_name')).val().trim();
        let model = $(this.el.querySelector('#model')).val().trim();
        let sequence = $(this.el.querySelector('#quick_create_sequence')).val().trim();
        let icon = $(this.el.querySelector('#quick_create_icon')).val().trim();
        if (name === '' || model === '' || icon === '') {
            $(self.el.querySelector('#quick_create_errors_msg')).html(
                $('<div class="alert alert-danger py-1 fs-14px mb-2" role="alert"/>')
                    .text(this.env._t('Please fill all the required fields first!'))
            );
        } else {
            $(self.el.querySelector('#quick_create_errors_msg')).html('');
            let data = {
                'name': name,
                'model': model,
                'sequence': sequence !== "" ? sequence : 10,
                'icon': icon,
            }
            return this.rpc("/theme/quick_create/add", {data: data}).then(function (data) {
                if (data[0]) {
                    $(self.el.querySelector('#quick_create_errors_msg')).html(
                        $('<div class="alert alert-danger py-1 fs-14px mb-2" role="alert"/>')
                            .text(data[0])
                    );
                } else {
                    self.env.bus.trigger('QUICK_CREATE:CANCEL_EDIT_QUICK_ACTION', data[1]);
                }
            });
        }
    }

}


OsQuickCreate.template = 'os_theme_butterfly.Os_quick_create';
