/** @odoo-module **/
const {Component} = owl;
const {useRef} = owl.hooks;
var Dialog = require('web.Dialog');

export class OsBookmarkMenu extends Component {
    setup() {
        super.setup();
        this.icon_bookmark_ref = useRef('icon_bookmark');
        this.edit_mode = false;
        this.action = "list_bookmarks";
        this.env.bus.on("BOOKMARK:QUICK_ADD_REMOVE", this, this.update);
        this.env.bus.on("BOOKMARK:EDIT_MODE_ENABLED", this, () => {
                this.edit_mode = true;
                this.render();
                this.enableEditMode();
            }
        );
        this.env.bus.on("BOOKMARK:EDIT_MODE_DISABLED", this, () => {
                this.edit_mode = false;
                this.render();
                this.disableEditMode();
            }
        );
        this.env.bus.on("BOOKMARK:EDIT_BOOKMARK_ITEM", this, ($el) => {
                this.action = "edit_bookmark_item";
                this.bookmark_item = {
                    'id': $el.data('id'),
                    'name': $el.data('name'),
                    'icon': $el.data('icon'),
                    'description': $el.data('description'),
                    'link': $el.data('link'),
                    'type': $el.data('type'),
                }
                this.render();
            }
        );
        this.env.bus.on("BOOKMARK:CANCEL_EDIT_BOOKMARK_ITEM", this, (data) => {
                this.action = "list_bookmarks";
                if (data) {
                    this.records = data;
                }
                this.render();
            }
        );
        this.env.bus.on("BOOKMARK:ADD_BOOKMARK_ITEM", this, () => {
                this.action = "add_bookmark_item";
                this.bookmark_item = {};
                this.render();
            }
        );

        this.env.bus.on("BOOKMARK:CLOSE_DROPDOWN", this, () => {
                this.action = "list_bookmarks";
                this.render();
            }
        );
    }

    async willStart() {
        this.records = await this.loadRecords("/theme/get/bookmark");
        return super.willStart();
    }

    async loadRecords(Route) {
        return await this.rpc(Route);
    }

    async update(data) {
        this.records = data[1];
        this.render();
        this.updateIcon(data[0]);
    }

    updateIcon(action) {
        if (action === "create") {
            $(this.icon_bookmark_ref.el).addClass("text-warning").removeClass('osi-bookmark').addClass('osi-bookmark-fill');
        } else {
            $(this.icon_bookmark_ref.el).removeClass("text-warning").removeClass('osi-bookmark-fill').addClass('osi-bookmark');
        }
    }

    processURL() {
        return window.location.href.replace(/^.*\/\/[^/]+/, '');
    }


    addRemoveBookMark(ev) {
        let self = this;
        var name = "";
        let name_tab = document.title.split("-");
        if (name_tab.length > 1) {
            name = document.title.split("-")[1]
        } else {
            name = document.title;
        }
        let data = {
            'name': name,
            'description': name,
            'icon': "osi osi-bookmark-fill",
            'type': "internal",
            'link': this.processURL(),
        }
        return this.rpc("/theme/bookmark/save", {data: data}).then(function (data) {
            self.env.bus.trigger('BOOKMARK:QUICK_ADD_REMOVE', data);
        });
    }

    // Advanced Bookmark
    enterEditMode() {
        this.env.bus.trigger('BOOKMARK:EDIT_MODE_ENABLED');
    }

    exitEditMode() {
        this.env.bus.trigger('BOOKMARK:EDIT_MODE_DISABLED');
    }

    enableEditMode() {
        $(this.el).addClass("edit_mode");
    }

    disableEditMode() {
        $(this.el).removeClass("edit_mode");
    }

    cancelEditItem() {
        this.env.bus.trigger('BOOKMARK:CANCEL_EDIT_BOOKMARK_ITEM');
    }

    onClickdeleteBookmarkItem(ev) {
        var $el = $(ev.currentTarget);
        var self = this;
        Dialog.confirm(this, (this.env._t("Are you sure you want to remove this item?")), {
            confirm_callback: function () {
                self.deleteBookmarkItem($el.data('bookmark-id'))
            },
        });
    }

    updateBookmarkItem(ev) {
        var $el = $(ev.currentTarget);
        var self = this;
        let name = $(this.el.querySelector('#bookmark_name')).val().trim();
        let description = $(this.el.querySelector('#bookmark_description')).val().trim();
        let icon = $(this.el.querySelector('#bookmark_icon')).val().trim();
        let sequence = $(this.el.querySelector('#bookmark_sequence')).val().trim();

        if (name === '' || icon === '') {
            $(this.el.querySelector('#bookmark_item_errors_msg')).html(
                $('<div class="alert alert-danger py-1 fs-14px mb-2" role="alert"/>')
                    .text(this.env._t('Please fill all the required fields first!'))
            );
        } else {
            $(this.el.querySelector('#bookmark_item_errors_msg')).html('');
            let data = {
                'id': $el.data('bookmark-id'),
                'name': name,
                'description': description,
                'icon': icon,
                'sequence': sequence !== "" ? sequence : 10,
            }
            return this.rpc("/theme/bookmark/update", {data: data}).then(function (data) {
                self.env.bus.trigger('BOOKMARK:CANCEL_EDIT_BOOKMARK_ITEM', data);
                self.exitEditMode();
            });
        }

    }

    deleteBookmarkItem(item_id) {
        var self = this;
        let data = {
            'id': item_id,
        }
        return this.rpc("/theme/bookmark/delete", {data: data}).then(function (data) {
            self.env.bus.trigger('BOOKMARK:CANCEL_EDIT_BOOKMARK_ITEM', data);
            self.exitEditMode();
        });
    }

    onClickBookmarkItem(ev) {
        var $el = $(ev.currentTarget);
        if (this.edit_mode) {
            this.env.bus.trigger('BOOKMARK:EDIT_BOOKMARK_ITEM', $el);
        } else {
            if ($el.data('type') === "internal") {
                window.location.href = $el.data('link');

            } else {
                let url = $el.data('link');
                url = url.replace("http://", '');
                url = url.replace("https://", '');
                this.env.services.action.doAction({
                    name: "External URL",
                    target: "new",
                    type: "ir.actions.act_url",
                    url: "http://" + url,
                });
            }
        }

    }

    onClickAddBookmark(ev) {
        this.env.bus.trigger('BOOKMARK:ADD_BOOKMARK_ITEM');
    }

    addBookmarkItem(ev) {
        var self = this;
        let name = $(this.el.querySelector('#bookmark_name')).val().trim();
        let description = $(this.el.querySelector('#bookmark_description')).val().trim();
        let icon = $(this.el.querySelector('#bookmark_icon')).val().trim();
        let link = $(this.el.querySelector('#bookmark_link_external')).val().trim();
        let sequence = $(this.el.querySelector('#bookmark_sequence')).val().trim();

        if (name === '' || icon === '' || link === '') {
            $(this.el.querySelector('#bookmark_item_errors_msg')).html(
                $('<div class="alert alert-danger py-1 fs-14px mb-2" role="alert"/>')
                    .text(this.env._t('Please fill all the required fields first!'))
            );
        } else {
            $(this.el.querySelector('#bookmark_item_errors_msg')).html('');
            let data = {
                'name': name,
                'description': description,
                'icon': icon,
                'type': 'external',
                'link': link,
                'sequence': sequence !== "" ? sequence : 10,

            }
            return this.rpc("/theme/bookmark/add", {data: data}).then(function (data) {
                if (data[0]) {
                    $(self.el.querySelector('#bookmark_item_errors_msg')).html(
                        $('<div class="alert alert-danger py-1 fs-14px mb-2" role="alert"/>')
                            .text(data[0])
                    );
                } else {
                    self.env.bus.trigger('BOOKMARK:CANCEL_EDIT_BOOKMARK_ITEM', data[1]);
                }
            });
        }
    }

}

OsBookmarkMenu.template = "os_theme_butterfly.os_bookmark_menu";