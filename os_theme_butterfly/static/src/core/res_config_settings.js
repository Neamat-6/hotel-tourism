odoo.define('base.settings.inherit', function (require) {
    "use strict";
    const BaseSetting = require('base.settings');
    const session = require('web.session');
    BaseSetting.Renderer.include({
        _getIconUrl: function (module) {
            return session.theme_settings_icons[module] ? session.theme_settings_icons[module] : session.theme_settings_icons["default"];
        },
        _initModules: function () {
            var self = this;
            this.modules = [];
            _.each(this.$('.app_settings_block'), function (settingView, index) {
                var group = !$(settingView).hasClass('o_invisible_modifier');
                var isNotApp = $(settingView).hasClass('o_not_app');
                if (group && !isNotApp) {
                    var data = $(settingView).data();
                    data.string = $(settingView).attr('string') || data.string;
                    self.modules.push({
                        key: data.key,
                        string: data.string,
                        imgurl: self._getAppIconUrl(data.key),
                        iconUrl: self._getIconUrl(data.key),
                        iconType: session.company_os_apps_icon_style,
                    });
                } else {
                    $(settingView).remove();
                }
            });
        },
    });
});
