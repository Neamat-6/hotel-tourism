/** @odoo-module **/

import {useService} from "@web/core/utils/hooks";
import {_t} from 'web.core';
import {OsSideBar} from "@os_theme_butterfly/components/os_sidebar/os_sidebar";

const {Component} = owl;
var Dialog = require('web.Dialog');
var rpc = require('web.rpc');
var ajax = require('web.ajax');

var appsSettingDialog = Dialog.extend({
    template: 'os_theme_butterfly.OsViewApp.Settings',
    init: function (parent, options) {
        options = _.defaults(options || {}, {
            title: _t((options.app.label || options.app.name) + ' icon Settings'),
            size: 'medium',
            buttons: [{
                text: _t('Save'),
                classes: 'btn-primary',
                click: this._onClickFormSubmit.bind(this, {app: options.app})
            }, {
                text: _t('Reset'),
                classes: 'btn-danger',
                click: this._onClickFormReset.bind(this, {app: options.app})
            }, {
                text: _t('Discard'),
                close: true
            }]
        });

        this.app = options.app;
        this.apps_icon_style = options.apps_icon_style;
        this.os_shape_style = options.os_shape_style;
        this.onClick
        this._super(parent, options);
    },


    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    _formValidate: function ($form) {
        $form.addClass('was-validated');
        return $form[0].checkValidity();
    },

    _onClickFormSubmit: function (data) {
        var $form = this.$('#apps_icon_settings_form');
        if (this._formValidate($form)) {
            if (this.apps_icon_style === "font") {
                let params = {
                    app_id: data.app.id,
                    icon_font: $form.find('#os_web_icon_font').val(),
                    icon_color: $form.find('#os_web_icon_color').val(),
                    shape_color: $form.find('#os_shape_color').val(),
                }
                rpc.query({
                    route: '/theme/icons/save_settings',
                    params: params
                }).then(function (data) {
                    window.location.reload();
                });
            }

            if (this.apps_icon_style === "image") {
                let params = {
                    app_id: data.app.id,
                    ufile: $form.find('#os_image_icon')[0].files[0]
                }
                ajax.post('/theme/icons/image/set_file', params).then(function (res) {
                    window.location.reload();

                })
            }


        }
    },

    _onClickFormReset: function (data) {
        let params = {
            app_id: data.app.id,
            type_icon: "font",
        }
        rpc.query({
            route: '/theme/icons/reset_settings',
            params: params
        }).then(function (data) {
            window.location.reload();
        });

    },
});

export class OsViewApps extends Component {

    setup() {
        super.setup();
        this.menus = useService("menu");
        this.edit_mode = false
        this.viewAppsService = useService("view_apps");
        this.uiService = useService("ui");
        this.availableApps = this.props.apps;
        this.companyThemeService = useService("os_company_settings");
        this.userService = useService("user");
        this.env.bus.on("APPS_VIEW:EDIT_MODE_ENABLED", this, () => {
                this.edit_mode = true;
                $(this.el).addClass("edit_mode");
                this.render();
            }
        );
        this.env.bus.on("APPS_VIEW:EDIT_MODE_DISABLED", this, () => {
                this.edit_mode = false;
                $(this.el).removeClass("edit_mode");
                this.render();
            }
        );
    }

    async willUpdateProps() {
        this.availableApps = this.props.apps;
    }

    get displayedApps() {
        return this.availableApps;
    }

    openDialog(app, apps_icon_style, os_shape_style) {
        new appsSettingDialog(this, {app: app, apps_icon_style: apps_icon_style, os_shape_style: os_shape_style}).open();
    }

    _openMenu(menu) {
        OsSideBar.prototype.openDropDownMenu(menu.id);
        return this.menus.selectMenu(menu);
    }

    enterEditMode() {
        this.env.bus.trigger('APPS_VIEW:EDIT_MODE_ENABLED');
    }

    exitEditMode() {
        this.env.bus.trigger('APPS_VIEW:EDIT_MODE_DISABLED');
    }

    _onAppClick(app) {
        if (this.edit_mode) {
            this.openDialog(app, this.companyThemeService.os_apps_icon_style, this.companyThemeService.os_shape_style)
        } else {
            this._openMenu(app);

        }
    }

}

OsViewApps.props = {
    apps: {
        type: Array,
        element: {
            type: Object,
            shape: {
                actionID: Number,
                appID: Number,
                id: Number,
                label: String,
                parents: String,
                webIcon: [
                    Boolean,
                    String,
                    {
                        type: Object,
                        optional: 1,
                        shape: {
                            iconClass: String,
                            color: String,
                            backgroundColor: String,
                        },
                    },
                ],
                webIconData: {type: String, optional: 1},
                webIconFont: String,
                webIconStyle: String,
                webIconColor: String,
                webShapeColor: String,
                webIconChanged: Boolean,
                webImageIcon: String,
                xmlid: String,
                hasNoAction: String,
            },
        },
    },
    menuItems: {
        type: Array,
        element: {
            type: Object,
            shape: {
                actionID: Number,
                appID: Number,
                id: Number,
                label: String,
                menuID: Number,
                parents: String,
                xmlid: String,
            },
        },
    },
};
OsViewApps.template = "os_theme_butterfly.OsViewApps";
