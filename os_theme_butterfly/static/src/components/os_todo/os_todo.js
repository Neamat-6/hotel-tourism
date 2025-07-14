/** @odoo-module **/
import {useService} from "@web/core/utils/hooks";
import {session} from "@web/session";

const {Component, hooks} = owl;


if (session.user_display_todo_list) {

    const {useRef} = owl.hooks;
    var core = require('web.core');
    var rpc = require('web.rpc');

    export class OsTodo extends Component {
        setup() {
            super.setup();
            this.rpc = useService("rpc");
            this.inputRef = useRef('input');
            core.bus.on('TODO_ACTION_PERFORMED', this, this.update);
            this.is_filter = false;
            hooks.onMounted(() => {
                if (this.not_done > 0) {
                    $('#todo_counter').addClass("os_todo_counter badge badge-navbar").text(this.not_done);
                } else {
                    $('#todo_counter').removeClass("os_todo_counter badge badge-navbar").text('');
                }
                this.bindSortable();
            });

        }

        async willStart() {
            let data = await this.loadRecords("/theme/get/todo", {});
            this.there_is_completed = data[0];
            this.records = data[1];
            this.not_done = _.filter(this.records, function (o) {
                return !o.is_done;
            }).length;

            return super.willStart();
        }

        async update(data) {
            this.there_is_completed = data[0];
            this.records = data[1];
            this.not_done = _.filter(this.records, function (o) {
                return !o.is_done;
            }).length;
            if (this.not_done > 0) {
                $('#todo_counter').addClass("os_todo_counter badge badge-navbar").text(this.not_done);
            } else {
                $('#todo_counter').removeClass("os_todo_counter badge badge-navbar").text('');

            }
            this.render();
        }


        async filter(type) {

            if (type === "pending") {
                let data = await this.loadRecords("/theme/get/todo", {'type': 'pending'});
                this.records = data[1];
            }
            if (type === "completed") {
                let data = await this.loadRecords("/theme/get/todo", {'type': 'completed'});
                this.records = data[1];
            }
            if (type === "all") {
                let data = await this.loadRecords("/theme/get/todo", {});
                this.records = data[1];
            }
            this.is_filter = type;
            this.render();

        }

        async loadRecords(Route, data) {
            return await this.rpc(Route, data);
        }

        clearCompleted(ev) {
            let data = {
                'action': "completed",
            }
            return this.rpc("/theme/todo/delete", {data: data}).then(function (data) {
                core.bus.trigger('TODO_ACTION_PERFORMED', data);
            });
        }

        clearAll(ev) {
            let data = {
                'action': "all",
            }
            return this.rpc("/theme/todo/delete", {data: data}).then(function (data) {
                core.bus.trigger('TODO_ACTION_PERFORMED', data);
            });
        }

        delete_todo(ev) {
            var $el = $(ev.currentTarget);
            let data = {
                'action': "one",
                'id': $el.data('id'),
            }
            return this.rpc("/theme/todo/delete", {data: data}).then(function (data) {
                core.bus.trigger('TODO_ACTION_PERFORMED', data);
            });
        }

        _onFocusout(ev) {
            let data = {
                'id': $(ev.target).parents(".tasks-item-toggle").find(".todo_content").data("id"),
                'name': $(ev.target).parents(".tasks-item-toggle").find(".todo_content").text()
            }
            return this.rpc("/theme/todo/edit", {data: data}).then(function (data) {
                core.bus.trigger('TODO_ACTION_PERFORMED', data);
                $(ev.target).parents(".tasks-item-toggle").find(".todo_content").attr("contenteditable", "false");
                $(ev.target).parents(".tasks-item-toggle").find(".todo_content").addClass("todo_textarea");
            });
        }

        edit_todo(ev) {
            $(ev.target).parents(".tasks-item-toggle").find(".todo_content").attr("contenteditable", true);
            $(ev.target).parents(".tasks-item-toggle").find(".todo_content").removeClass("todo_textarea");
        }

        toggleComplete(ev) {
            let is_done = !ev.target.classList.contains("is_done");
            var $el = $(ev.currentTarget);
            let data = {
                'id': $el.data('id'),
                'is_done': is_done,
            }
            return this.rpc("/theme/todo/toggle/done", {data: data}).then(function (data) {
                core.bus.trigger('TODO_ACTION_PERFORMED', data);

            });
        }

        addTodo(ev) {
            var self = this;
            if ($(this.inputRef.el).val() === "") {
                $(self.el.querySelector('#msg')).html(
                    $('<div class="alert alert-danger py-1 fs-14px" role="alert"/>')
                        .text(this.env._t('Please enter a text first!'))
                );
            } else {
                $(self.el.querySelector('#msg')).html('')
                let data = {
                    'name': $(this.inputRef.el).val(),
                }
                return this.rpc("/theme/todo/save", {data: data}).then(function (data) {
                    if (data[0]) {
                        toastr.error(this.env._t("You already have a TODO item with this content"))
                    } else {
                        $(self.inputRef.el).val('');
                        core.bus.trigger('TODO_ACTION_PERFORMED', data[1]);
                    }
                });
            }
        }

        bindSortable(ev) {
            $(this.el).sortable({
                handle: '.os_js_sequence_handler',
                items: '.tasks-item-toggle',
                cursor: "grabbing",
                stop: this.reorderItems.bind(this),
                placeholder: 'os_sequence_highlight position-relative my-3'
            });
        }

        getItemsIds(ev) {
            return $(this.el).find('.tasks-item-toggle').map(function () {
                return $(this).attr('id');
            }).get();
        }

        reorderItems(ev) {
            var self = this;
            rpc.query({
                route: '/web/dataset/resequence',
                params: {
                    model: "os.todo",
                    ids: self.getItemsIds()
                }
            });
        }

    }

    OsTodo.template = "os_theme_butterfly.os_todo";
} else {
    export class OsTodo extends Component {
    }
}
