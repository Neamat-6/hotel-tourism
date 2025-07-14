/** @odoo-module **/

import {useService} from "@web/core/utils/hooks";

const framework = require('web.framework');

const {getDataURLFromFile} = require('web.utils');
const {Component, hooks} = owl;
const {useRef} = owl.hooks;
var Dialog = require('web.Dialog');
var rpc = require('web.rpc');

function _make_option(term) {
    return {id: term, text: term};
}

export class OsSettingsPanelUser extends Component {
    setup() {
        super.setup();
        this.rpc = useService("rpc");
        this.themeService = useService("os_user_settings");
        this.userService = useService("user");
        this.home_action_input_ref = useRef('home_action_input');
        this.div_same_icons_ref = useRef("div_same_icons");
        this.sidebar_style_ref = useRef("sidebar_style");


    }


    mounted() {
        this.toggle_opt_item('.os-opt-item', '.os-opt-list');
        this.onChangeDivSameIcons();
        let theme_mode_opt = this.el.querySelector('[data-key="mode"].active')
        let theme_mode = $(theme_mode_opt).data("update");
        $(this.sidebar_style_ref.el).toggle($(this.el.querySelector('[data-key="navigation_style"].active')).attr('data-update') === 'vertical');

        if (theme_mode === 'dark-mode') {
            $(".os-opt-item[data-key='header']").addClass('disabled');
            $(".os-opt-item[data-key='aside']").addClass('disabled');
        }

        let $input = $(this.home_action_input_ref.el);

        this.$select2 = $input.select2({
            width: '100%',
            allowClear: true,
            formatNoMatches: false,
            multiple: false,
            selection_data: false,
            placeholder: this.env._t("Home Action"),
            fill_data: function (query, data) {
                var that = this;
                var tags = {results: []};
                _.each(data, function (obj) {
                    if (that.matcher(query.term, obj.display_name)) {
                        tags.results.push({id: obj.id, text: obj.display_name});
                    }
                });
                query.callback(tags);
            },
            query: function (query) {
                var that = this;
                if (!this.selection_data) {
                    rpc.query({
                        model: 'ir.actions.actions',
                        method: 'search_read',
                        args: [[['type', 'in', ["ir.actions.act_url", "ir.actions.act_window", "ir.actions.client"]]], ['display_name']],

                    }).then(function (data) {
                        that.fill_data(query, data);
                        that.selection_data = data;
                    });
                } else {
                    this.fill_data(query, this.selection_data);
                }
            },
            initSelection: function ($e, c) {
                return c(_make_option($e.val()));

            }
        });

    }

    onChangeDivSameIcons() {
        let condition = $(this.el.querySelector('[data-key="navigation_style"].active')).attr('data-update') === 'vertical';
        $(this.div_same_icons_ref.el).toggle(condition);
    }

    toggle_opt_item(elm, parent) {
        var self = this;
        $(elm).on('click', function (e) {
            $(this).parent(parent).find(elm).removeClass("active");
            $(this).addClass("active");
            if ($(this).attr('data-key') === 'mode') {
                if ($(this).attr('data-update') === 'dark-mode') {
                    $(".os-opt-item[data-key='header']").addClass('disabled');
                    $(".os-opt-item[data-key='aside']").addClass('disabled');
                } else {
                    $(".os-opt-item[data-key='header']").removeClass('disabled');
                    $(".os-opt-item[data-key='aside']").removeClass('disabled');
                }
            }
            if ($(this).attr('data-key') === 'navigation_style') {
                $(self.sidebar_style_ref.el).toggle($(this).attr('data-update') === 'vertical');
                self.onChangeDivSameIcons();
            }
            e.preventDefault();
        });
    }

    async confirmUserResetThemeSettings() {
        var self = this;
        return await this.rpc("/web/theme/user/reset_settings",
            {}).then(function (res) {
            self.env.services.action.doAction("reload_context");
        });
    }

    userResetThemeSettings() {
        var self = this;
        Dialog.confirm(this, (this.env._t("Are you sure you want to reset your settings?")), {
            confirm_callback: function () {
                framework.blockUI();
                self.confirmUserResetThemeSettings()
            },
        });

    }

    async userSaveThemeSettings() {
        var self = this;
        framework.blockUI();
        let header_style_opt = this.el.querySelector('[data-key="header"].active');
        let sidebar_style_opt = this.el.querySelector('[data-key="aside"].active');
        let chatter_position_opt = this.el.querySelector('[data-key="os_chatter_position"].active');
        let dbl_click_edit_opt = this.el.querySelector('#user_dbl_click_edit');
        let display_todo_list_opt = this.el.querySelector('#user_display_todo_list');
        let display_bookmarks_opt = this.el.querySelector('#user_display_bookmarks');
        let display_favorite_apps_opt = this.el.querySelector('#user_display_favorite_apps');
        let display_recently_viewed_records_opt = this.el.querySelector('#user_display_recently_viewed_records');
        let display_zoom_in_out_opt = this.el.querySelector('#user_display_zoom_in_out');
        let display_full_screen_opt = this.el.querySelector('#user_display_full_screen');
        let home_action_input_opt = this.el.querySelector('#home_action_input');
        let os_show_sidebar_opt = this.el.querySelector('[data-key="navigation_style"].active');
        let os_show_quick_create_opt = this.el.querySelector('#user_show_quick_create');
        let same_icons_opt = this.el.querySelector('#user_same_icons');
        let user_header_tools_bar_fixed_opt = this.el.querySelector('#user_header_tools_bar_fixed');

        let data_user = {
            'os_header_style': $(header_style_opt).data("update"),
            'os_sidebar_style': $(sidebar_style_opt).data("update"),
            'os_chatter_position': $(chatter_position_opt).data("update"),
            'os_dbl_click_edit': $(dbl_click_edit_opt).is(':checked'),
            'os_display_todo_list': $(display_todo_list_opt).is(':checked'),
            'os_display_bookmarks': $(display_bookmarks_opt).is(':checked'),
            'os_display_favorite_apps': $(display_favorite_apps_opt).is(':checked'),
            'os_display_recently_viewed_records': $(display_recently_viewed_records_opt).is(':checked'),
            'os_display_zoom_in_out': $(display_zoom_in_out_opt).is(':checked'),
            'os_display_full_screen': $(display_full_screen_opt).is(':checked'),
            'action_id': parseInt($(home_action_input_opt).val()),
            'os_show_sidebar': $(os_show_sidebar_opt).attr('data-update') === 'vertical',
            'os_show_quick_create': $(os_show_quick_create_opt).is(':checked'),
            'os_use_same_apps_icons_style_for_sidebar': $(same_icons_opt).is(':checked'),
            'os_header_tools_bar_fixed': $(user_header_tools_bar_fixed_opt).is(':checked'),

        }

        return await this.rpc("/web/theme/user/save_settings", {data: data_user}).then(function (res) {
            self.env.services.action.doAction("reload_context");
        });


    }
}

OsSettingsPanelUser.template = 'os_theme_butterfly.os_settings_panel_user';

export class OsSettingsPanelGeneral extends Component {
    setup() {
        super.setup();
        this.rpc = useService("rpc");
        this.themeService = useService("os_company_settings");
        this.userService = useService("user");
        this.company = useService("company");
        this.http = useService("http");
        this.input_primary_color_ref = useRef('input_primary_color');
        this.opt_custom_color_ref = useRef('opt_custom_color');
        this.div_custom_ref = useRef('div_custom');
        this.ribbon_bloc_ref = useRef('ribbon_bloc');
        this.os_login_background_type_ref = useRef('os_login_background_type');
        this.os_login_background_image_ref = useRef('os_login_background_image');
        this.os_login_background_color_ref = useRef('os_login_background_color');
        this.apps_view_background_type_ref = useRef('os_apps_view_background_type');
        this.apps_view_background_image_ref = useRef('os_apps_view_background_image');
        this.apps_view_background_color_ref = useRef('os_apps_view_background_color');
        this.apps_view_text_color_ref = useRef('os_apps_view_text_color');
        this.Login_fileInputRef = useRef("login-bg-file-input");
        this.LogoWhite_fileInputRef = useRef("os_theme_logo_white-bg-file-input");
        this.LogoDark_fileInputRef = useRef("os_theme_logo_dark-bg-file-input");
        this.LogoSmall_fileInputRef = useRef("os_theme_logo_small-bg-file-input");
        this.os_theme_favicon_inputRef = useRef("os_theme_favicon_input");
        this.AppsView_fileInputRef = useRef("apps_view-bg-file-input");
        this.loginBgImgRef = useRef("login-bg-img");
        this.LogoWhiteImgRef = useRef("os_theme_logo_white-bg-img");
        this.LogoDarkImgRef = useRef("os_theme_logo_dark-bg-img");
        this.LogoSmallImgRef = useRef("os_theme_logo_small-bg-img");
        this.os_theme_faviconRef = useRef("os_theme_favicon");
        this.AppsViewBgImgRef = useRef("apps_view-bg-img");
        this.sidebar_style_ref = useRef("sidebar_style");
        this.div_base_custom_font_ref = useRef("div_base_custom_font");
        this.div_alt_custom_font_ref = useRef("div_alt_custom_font");
        this.shape_style_div_ref = useRef("shape_style_div");
        this.chart_bg_palette_ref = useRef("chart_bg_palette");
        this.shape_style_unique_color_ref = useRef("shape_style_unique_color");
        this.div_same_icons_ref = useRef("div_same_icons");
        this.animations_modal_entrance_div_ref = useRef("animations_modal_entrance_div");
        this.shape_none_color_icon_ref = useRef("shape_none_color_icon");
        this.os_login_title_subtitle_ref = useRef("os_login_title_subtitle");
        this.os_login_background_ref = useRef("os_login_background");
        this.os_login_background_image_ref = useRef("os_login_background_image");
        this.shape_div_ref = useRef("shape_div");
        this.config_style_image_ref = useRef("config_style_image");
        this.os_login_background_image_changed = false;
        this.os_theme_logo_white_changed = false;
        this.os_theme_logo_dark_changed = false;
        this.os_theme_logo_small_changed = false;
        this.os_theme_favicon_changed = false;
        this.apps_view_background_image_changed = false;

    }

    mounted() {
        var self = this;
        this.toggle_opt_item('.os-opt-item', '.os-opt-list');
        this.toggleShowRibbon();
        this.toggleLoginType();
        this.toggleAppsViewType();
        this.onChangeBaseFont();
        this.onChangeCustomaAltFont();
        this.onChangeAltFont();
        this.onChangeIconStyle();
        this.onChangeShape();
        this.onChangeDivSameIcons();
        this.onChangeShapeStyle();
        this.onChangeLoginStyle();
        this.onChangeAnimationModalEntrance();
        $(self.sidebar_style_ref.el).toggle($(this.el.querySelector('[data-key="navigation_style"].active')).attr('data-update') === 'vertical');

        $('.os-opt-set > div.d-flex').on('click', function () {
            var $ul = $(this).parent().find("> .os-toggle-content");
            if ($ul.length > 0) {
                $ul.slideToggle(600);
                $(".os-toggle-content").not($ul).slideUp(400);
            }
        });

        $(this.el).find('.os_widget_color').each(function () {
            $(this).minicolors({
                control: 'hue',
                inline: false,
                letterCase: 'lowercase',
                opacity: false,
                theme: 'bootstrap'
            });
            $(this).change(function () {
                let action = $(this).attr('data-action');
                if (action && action === "updateColor") {
                    self.changeColor();
                }
            })
        });
    }


    toggle_opt_item(elm, parent) {
        var self = this;
        $(elm).on('click', function (e) {
            $(this).parent(parent).find(elm).removeClass("active");
            $(this).addClass("active");
            if ($(self.opt_custom_color_ref.el).hasClass('active')) {
                $(self.div_custom_ref.el).show(200);
            } else {
                $(self.div_custom_ref.el).hide(200);
            }
            if ($(this).attr('data-key') === 'navigation_style') {
                $(self.sidebar_style_ref.el).toggle($(this).attr('data-update') === 'vertical');
                self.onChangeDivSameIcons();
            }
            e.preventDefault();
        });
    }

    toggleShowRibbon() {
        let selector_val = $(this.el.querySelector('#os_activate_web_ribbon')).is(':checked');
        $(this.ribbon_bloc_ref.el).toggle(selector_val);
    }

    onChangeCustomBaseFont() {
        let condition = $(this.el.querySelector('#os_theme_base_font')).val() === "custom";
        if (condition && $(this.el.querySelector('#os_theme_base_custom_google_font')).val() === "") {
            $(this.el.querySelector('#fonts_base_msg_errors')).html(
                $('<div class="alert alert-warning py-1 fs-14px mb-2" role="alert"/>')
                    .text(this.env._t('Please enter a base google font otherwise we will use default values!'))
            );
        } else {
            $(this.el.querySelector('#fonts_base_msg_errors')).html('');
        }
    }

    onChangeBaseFont() {
        let condition = $(this.el.querySelector('#os_theme_base_font')).val() === "custom";
        $(this.div_base_custom_font_ref.el).toggle(condition);
        if (condition && $(this.el.querySelector('#os_theme_base_custom_google_font')).val() === "") {
            $(this.el.querySelector('#fonts_base_msg_errors')).html(
                $('<div class="alert alert-warning py-1 fs-14px mb-2" role="alert"/>')
                    .text(this.env._t('Please enter a base google font otherwise we will use default values!'))
            );
        } else {
            $(this.el.querySelector('#fonts_base_msg_errors')).html('');
        }
    }

    onChangeCustomaAltFont() {
        let condition = $(this.el.querySelector('#os_theme_alt_font')).val() === "custom";
        if (condition && $(this.el.querySelector('#os_theme_alt_custom_google_font')).val() === "") {
            $(this.el.querySelector('#fonts_alt_msg_errors')).html(
                $('<div class="alert alert-warning py-1 fs-14px mb-2" role="alert"/>')
                    .text(this.env._t('Please enter an alternative google font otherwise we will use default values!'))
            );
        } else {
            $(this.el.querySelector('#fonts_alt_msg_errors')).html('');
        }
    }

    onChangeAltFont() {
        let condition = $(this.el.querySelector('#os_theme_alt_font')).val() === "custom";
        $(this.div_alt_custom_font_ref.el).toggle(condition);
        if (condition && $(this.el.querySelector('#os_theme_alt_custom_google_font')).val() === "") {
            $(this.el.querySelector('#fonts_alt_msg_errors')).html(
                $('<div class="alert alert-warning py-1 fs-14px mb-2" role="alert"/>')
                    .text(this.env._t('Please enter an alternative google font otherwise we will use default values!'))
            );
        } else {
            $(this.el.querySelector('#fonts_alt_msg_errors')).html('');
        }
    }

    onChangeShape() {
        let condition = $(this.el.querySelector('#os_shape')).val() !== "none";
        $(this.shape_style_div_ref.el).toggle(condition);
        $(this.shape_none_color_icon_ref.el).toggle(!condition);
        $(this.shape_style_unique_color_ref.el).toggle(condition);
    }

    onChangeChartPalette() {
        let os_chart_color_palette = $(this.el.querySelector('#os_chart_color_palette')).val();
        $(this.chart_bg_palette_ref.el).attr('class', 'chart_bg_' + os_chart_color_palette);

    }

    onChangeShapeStyle() {
        let condition = $(this.el.querySelector('#os_shape_style')).val() === "unique_color" && $(this.el.querySelector('#os_shape')).val() !== "none";
        $(this.shape_style_unique_color_ref.el).toggle(condition);
    }

    onChangeDivSameIcons() {
        let condition = $(this.el.querySelector('[data-key="navigation_style"].active')).attr('data-update') === 'vertical';
        $(this.div_same_icons_ref.el).toggle(condition);
    }

    onChangeAnimationModalEntrance() {
        let condition = $(this.el.querySelector('#os_modal_animated_entrance')).val() === 'True'
        $(this.animations_modal_entrance_div_ref.el).toggle(condition);
    }

    onChangeLoginStyle() {
        this.toggleLoginType();


        let condition2 = ["default", "style_1", "style_2", "style_3", "style_4", "style_5", "style_6"].indexOf($(this.el.querySelector('#os_login_style')).val()) > -1
        $(this.os_login_background_ref.el).toggle(condition2);
        if (condition2) {
            $(this.os_login_background_type_ref.el).show();

        }

        let condition3 = ["style_6"].indexOf($(this.el.querySelector('#os_login_style')).val()) > -1
        if (condition3) {
            $(this.os_login_background_color_ref.el).show();
            $(this.os_login_background_image_ref.el).hide();
            $(this.os_login_background_type_ref.el).hide();
        }
        let condition = ["style_4", "style_5"].indexOf($(this.el.querySelector('#os_login_style')).val()) > -1
        $(this.os_login_title_subtitle_ref.el).toggle(condition);
        if (condition) {
            $(this.os_login_background_color_ref.el).show();
            $(this.os_login_background_image_ref.el).hide();
            $(this.os_login_background_type_ref.el).hide();
        }
    }

    onChangeIconStyle() {
        let condition = $(this.el.querySelector('#os_apps_icon_style')).val() === "font";
        $(this.shape_div_ref.el).toggle(condition);
        let condition_2 = $(this.el.querySelector('#os_apps_icon_style')).val() === "image";
        $(this.config_style_image_ref.el).toggle(condition_2);
    }

    toggleLoginType() {
        let selector_val = $(this.el.querySelector('#os_login_background_type')).val();
        $(this.os_login_background_color_ref.el).toggle(selector_val === 'bg_color');
        $(this.os_login_background_image_ref.el).toggle(selector_val === 'bg_img');
    }

    toggleAppsViewType() {
        $(this.apps_view_background_color_ref.el).toggle($(this.apps_view_background_type_ref.el).val() === 'bg_color');
        $(this.apps_view_background_image_ref.el).toggle($(this.apps_view_background_type_ref.el).val() === 'bg_img');
        $(this.apps_view_text_color_ref.el).toggle($(this.apps_view_background_type_ref.el).val() !== 'default');
    }

    async changeColor() {
        $(this.opt_custom_color_ref.el).attr("data-update", this.input_primary_color_ref.el.value)

    }

    openLogoWhiteFileInput(ev) {
        $(this.LogoWhite_fileInputRef.el).click();
    }

    openLogoDarkFileInput(ev) {
        $(this.LogoDark_fileInputRef.el).click();
    }

    openLogoSmallFileInput(ev) {
        $(this.LogoSmall_fileInputRef.el).click();
    }

    openFaviconFileInput(ev) {
        $(this.os_theme_favicon_inputRef.el).click();
    }

    openLoginFileInput(ev) {
        $(this.Login_fileInputRef.el).click();
    }

    openAppsViewFileInput(ev) {
        $(this.AppsView_fileInputRef.el).click();
    }

    async LoginBgImageUploaded(ev) {

        this.os_login_background_image_changed = true;
        if (this.Login_fileInputRef.el.files.length === 1) {
            const file = this.Login_fileInputRef.el.files[0];
            const imageUrl = await getDataURLFromFile(file);
            $(this.loginBgImgRef.el).attr("src", imageUrl)
        }


    }

    async LogoWhiteImageUploaded(ev) {
        this.os_theme_logo_white_changed = true;
        if (this.LogoWhite_fileInputRef.el.files.length === 1) {
            const file = this.LogoWhite_fileInputRef.el.files[0];
            const imageUrl = await getDataURLFromFile(file);
            $(this.LogoWhiteImgRef.el).attr("src", imageUrl)
        }
    }

    async LogoDarkImageUploaded(ev) {
        this.os_theme_logo_dark_changed = true;
        if (this.LogoDark_fileInputRef.el.files.length === 1) {
            const file = this.LogoDark_fileInputRef.el.files[0];
            const imageUrl = await getDataURLFromFile(file);
            $(this.LogoDarkImgRef.el).attr("src", imageUrl)
        }
    }

    async LogoSmallImageUploaded(ev) {
        this.os_theme_logo_small_changed = true;
        if (this.LogoSmall_fileInputRef.el.files.length === 1) {
            const file = this.LogoSmall_fileInputRef.el.files[0];
            const imageUrl = await getDataURLFromFile(file);
            $(this.LogoSmallImgRef.el).attr("src", imageUrl)
        }
    }

    async FaviconImageUploaded(ev) {
        this.os_theme_favicon_changed = true;
        if (this.os_theme_favicon_inputRef.el.files.length === 1) {
            const file = this.os_theme_favicon_inputRef.el.files[0];
            const imageUrl = await getDataURLFromFile(file);
            $(this.os_theme_faviconRef.el).attr("src", imageUrl)
        }
    }

    async AppsViewBgImageUploaded(ev) {
        this.apps_view_background_image_changed = true;
        if (this.AppsView_fileInputRef.el.files.length === 1) {
            const file = this.AppsView_fileInputRef.el.files[0];
            const imageUrl = await getDataURLFromFile(file);
            $(this.AppsViewBgImgRef.el).attr("src", imageUrl)
        }


    }

    async companyResetThemeSettings() {
        var self = this;
        Dialog.confirm(this, (this.env._t("Are you sure you want to reset your company settings?")), {
            confirm_callback: function () {
                framework.blockUI();
                self.confirmCompanyResetThemeSettings()
            },
        });

    }

    async confirmCompanyResetThemeSettings() {
        var self = this;
        return await this.rpc("/web/theme/company/reset_settings",
            {}).then(function (res) {
            self.env.services.action.doAction("reload_context");
        });

    }


    async companySaveThemeSettings() {
        var self = this;
        framework.blockUI();
        let header_style_opt = this.el.querySelector('[data-key="header"].active');
        let sidebar_style_opt = this.el.querySelector('[data-key="aside"].active');
        let theme_mode_opt = this.el.querySelector('[data-key="mode"].active');
        let theme_color_primary_opt = this.el.querySelector('[data-key="skin"].active');
        let theme_custom_color_opt = this.el.querySelector('[data-custom="true"]');
        let chatter_position_opt = this.el.querySelector('[data-key="os_chatter_position"].active');
        let loader_style_opt = this.el.querySelector('[data-key="os_loader_style"].active');
        let show_user_settings_opt = this.el.querySelector('#os_show_user_settings');
        let dbl_click_edit_opt = this.el.querySelector('#os_dbl_click_edit');
        let display_todo_list_opt = this.el.querySelector('#os_display_todo_list');
        let display_bookmarks_opt = this.el.querySelector('#os_display_bookmarks');
        let display_favorite_apps_opt = this.el.querySelector('#os_display_favorite_apps');
        let display_recently_viewed_records_opt = this.el.querySelector('#os_display_recently_viewed_records');
        let display_zoom_in_out_opt = this.el.querySelector('#os_display_zoom_in_out');
        let display_full_screen_opt = this.el.querySelector('#os_display_full_screen');
        let web_window_title_opt = this.el.querySelector('[data-key="os_web_window_title"] input');
        let activate_web_ribbon_opt = this.el.querySelector('#os_activate_web_ribbon');
        let separator_style_opt = this.el.querySelector('#os_separator_style');
        let separator_color_opt = this.el.querySelector('#os_separator_color');
        let breadcrumb_style_opt = this.el.querySelector('[data-key="os_breadcrumb_style"].active');
        //login page
        let os_login_style_opt = this.el.querySelector('#os_login_style');
        let os_login_title_opt = this.el.querySelector('#os_login_title');
        let os_login_subtitle_opt = this.el.querySelector('#os_login_subtitle');
        let os_login_background_type_opt = this.el.querySelector('#os_login_background_type');
        let login_background_color_opt = this.el.querySelector('#os_login_background_color');
        // Apps view
        let apps_view_background_type_opt = this.el.querySelector('#os_apps_view_background_type');
        let apps_view_background_color_opt = this.el.querySelector('#os_apps_view_background_color');
        let apps_view_text_color_opt = this.el.querySelector('#os_apps_view_text_color');
        let os_header_tools_bar_fixed_opt = this.el.querySelector('#os_header_tools_bar_fixed');

        // Fonts
        let theme_base_font_opt = this.el.querySelector('#os_theme_base_font');
        let theme_alt_font_opt = this.el.querySelector('#os_theme_alt_font');
        let tabs_style_opt = this.el.querySelector('#os_tabs_style');
        let tabs_alignment_opt = this.el.querySelector('#os_tabs_alignment');
        let buttons_style_opt = this.el.querySelector('#os_buttons_style');
        let buttons_angles_opt = this.el.querySelector('#os_buttons_angles');
        let buttons_size_opt = this.el.querySelector('#os_buttons_size');
        let radios_style_opt = this.el.querySelector('#os_radios_style');
        let checkbox_style_opt = this.el.querySelector('#os_checkbox_style');
        let list_view_style_opt = this.el.querySelector('#os_list_view_style');
        let os_list_view_header_fg_color_opt = this.el.querySelector('#os_list_view_header_fg_color');
        let os_list_view_header_bg_color_opt = this.el.querySelector('#os_list_view_header_bg_color');
        let os_shape_opt = this.el.querySelector('#os_shape');
        let os_shape_style_opt = this.el.querySelector('#os_shape_style');
        let os_shape_none_color_icon_opt = this.el.querySelector('#os_shape_none_color_icon');
        let os_shape_shadow_opt = this.el.querySelector('#os_shape_shadow');
        let os_shape_style_unique_color_opt = this.el.querySelector('#os_shape_style_unique_color');
        let os_shape_style_unique_color_icon_opt = this.el.querySelector('#os_shape_style_unique_color_icon');
        let same_icons_opt = this.el.querySelector('#same_icons');
        let os_apps_icon_style_opt = this.el.querySelector('#os_apps_icon_style');
        let os_show_sidebar_opt = this.el.querySelector('[data-key="navigation_style"].active');
        let os_show_quick_create_opt = this.el.querySelector('#os_show_quick_create');
        let os_chart_color_palette_opt = this.el.querySelector('#os_chart_color_palette');
        let os_apps_icon_style_image_pack_opt = this.el.querySelector('#os_apps_icon_style_image_pack');
        let os_list_view_style_spaced_opt = this.el.querySelector('#os_list_view_style_spaced');
        let os_list_view_style_separate_opt = this.el.querySelector('#os_list_view_style_separate');
        let os_list_view_style_hover_opt = this.el.querySelector('#os_list_view_style_hover');
        let os_modal_animated_entrance_opt = this.el.querySelector('#os_modal_animated_entrance');
        let os_modal_animated_entrance_value_opt = this.el.querySelector('#os_modal_animated_entrance_value');
        let os_list_view_sticky_header_footer_opt = this.el.querySelector('#os_list_view_sticky_header_footer');


        let data_company = {
            'os_header_style': $(header_style_opt).data("update"),
            'os_sidebar_style': $(sidebar_style_opt).data("update"),
            'os_theme_mode': $(theme_mode_opt).data("update"),
            'os_theme_color_primary': $(theme_color_primary_opt).data("update") || false,
            'os_theme_custom_color': $(theme_custom_color_opt).data("update"),
            'os_chatter_position': $(chatter_position_opt).data("update"),
            'os_loader_style': $(loader_style_opt).data("update"),
            'os_dbl_click_edit': $(dbl_click_edit_opt).is(':checked'),
            'os_show_user_settings': $(show_user_settings_opt).is(':checked'),
            'os_display_todo_list': $(display_todo_list_opt).is(':checked'),
            'os_display_bookmarks': $(display_bookmarks_opt).is(':checked'),
            'os_display_favorite_apps': $(display_favorite_apps_opt).is(':checked'),
            'os_display_recently_viewed_records': $(display_recently_viewed_records_opt).is(':checked'),
            'os_display_zoom_in_out': $(display_zoom_in_out_opt).is(':checked'),
            'os_show_sidebar': $(os_show_sidebar_opt).attr('data-update') === 'vertical',
            'os_show_quick_create': $(os_show_quick_create_opt).is(':checked'),
            'os_display_full_screen': $(display_full_screen_opt).is(':checked'),
            'os_web_window_title': $(web_window_title_opt).val(),
            'os_activate_web_ribbon': $(activate_web_ribbon_opt).is(':checked'),
            'os_separator_style': $(separator_style_opt).val(),
            'os_separator_color': $(separator_color_opt).val(),
            'os_breadcrumb_style': $(breadcrumb_style_opt).data("update"),
            'os_login_style': $(os_login_style_opt).val(),
            'os_login_title': $(os_login_title_opt).val(),
            'os_login_subtitle': $(os_login_subtitle_opt).val(),
            'os_login_background_type': $(os_login_background_type_opt).val(),
            'os_login_background_color': $(login_background_color_opt).val(),
            'os_apps_view_background_type': $(apps_view_background_type_opt).val(),
            'os_apps_view_background_color': $(apps_view_background_color_opt).val(),
            'os_apps_view_text_color': $(apps_view_text_color_opt).val(),
            'os_theme_base_font': $(theme_base_font_opt).val(),
            'os_theme_alt_font': $(theme_alt_font_opt).val(),
            'os_tabs_style': $(tabs_style_opt).val(),
            'os_tabs_alignment': $(tabs_alignment_opt).val(),
            'os_buttons_style': $(buttons_style_opt).val(),
            'os_buttons_angles': $(buttons_angles_opt).val(),
            'os_buttons_size': $(buttons_size_opt).val(),
            'os_radios_style': $(radios_style_opt).val(),
            'os_checkbox_style': $(checkbox_style_opt).val(),
            'os_list_view_style': $(list_view_style_opt).val(),
            'os_list_view_header_fg_color': $(os_list_view_header_fg_color_opt).val(),
            'os_list_view_header_bg_color': $(os_list_view_header_bg_color_opt).val(),
            'os_shape': $(os_shape_opt).val(),
            'os_shape_style': $(os_shape_style_opt).val(),
            'os_shape_none_color_icon': $(os_shape_none_color_icon_opt).val(),
            'os_shape_style_unique_color': $(os_shape_style_unique_color_opt).val(),
            'os_shape_style_unique_color_icon': $(os_shape_style_unique_color_icon_opt).val(),
            'os_use_same_apps_icons_style_for_sidebar': $(same_icons_opt).is(':checked'),
            'os_header_tools_bar_fixed': $(os_header_tools_bar_fixed_opt).is(':checked'),
            'os_shape_shadow': $(os_shape_shadow_opt).val() === "True",
            'os_apps_icon_style': $(os_apps_icon_style_opt).val(),
            'os_chart_color_palette': $(os_chart_color_palette_opt).val(),
            'os_apps_icon_style_image_pack': $(os_apps_icon_style_image_pack_opt).val(),
            'os_list_view_style_spaced': $(os_list_view_style_spaced_opt).val() === "True",
            'os_list_view_style_separate': $(os_list_view_style_separate_opt).val() === "True",
            'os_list_view_style_hover': $(os_list_view_style_hover_opt).val(),
            'os_modal_animated_entrance_value': $(os_modal_animated_entrance_value_opt).val(),
            'os_modal_animated_entrance': $(os_modal_animated_entrance_opt).val() === "True",
            'os_list_view_sticky_header_footer': $(os_list_view_sticky_header_footer_opt).val() === "True",


        }
        if ($(theme_base_font_opt).val() === "custom") {
            data_company['os_theme_base_custom_google_font'] = $(this.el.querySelector('#os_theme_base_custom_google_font')).val();
        }
        if ($(theme_alt_font_opt).val() === "custom") {
            data_company['os_theme_alt_custom_google_font'] = $(this.el.querySelector('#os_theme_alt_custom_google_font')).val();
        }
        if ($(activate_web_ribbon_opt).is(':checked')) {
            data_company['os_web_ribbon_text'] = $(this.el.querySelector('#os_web_ribbon_text')).val();
            data_company['os_web_ribbon_bg'] = $(this.el.querySelector('#os_web_ribbon_bg')).val();
            data_company['os_web_ribbon_fg'] = $(this.el.querySelector('#os_web_ribbon_fg')).val();
        }
        if (this.os_login_background_image_changed) {
            let params =
                {
                    csrf_token: odoo.csrf_token,
                    ufile: [...this.Login_fileInputRef.el.files],
                    field: 'os_login_background_image'
                }
            await this.http.post("/theme/upload_image", params, "text");

        }

        if (this.apps_view_background_image_changed) {
            let params = {
                csrf_token: odoo.csrf_token,
                ufile: [...this.AppsView_fileInputRef.el.files],
                field: 'os_apps_view_background_image'

            };
            await this.http.post("/theme/upload_image", params, "text");

        }

        if (this.os_theme_logo_white_changed) {
            let params =
                {
                    csrf_token: odoo.csrf_token,
                    ufile: [...this.LogoWhite_fileInputRef.el.files],
                    field: 'os_theme_logo_white'
                }
            await this.http.post("/theme/upload_image", params, "text");
        }

        if (this.os_theme_logo_dark_changed) {
            let params =
                {
                    csrf_token: odoo.csrf_token,
                    ufile: [...this.LogoDark_fileInputRef.el.files],
                    field: 'os_theme_logo_dark'
                }
            await this.http.post("/theme/upload_image", params, "text");
        }

        if (this.os_theme_logo_small_changed) {
            let params =
                {
                    csrf_token: odoo.csrf_token,
                    ufile: [...this.LogoSmall_fileInputRef.el.files],
                    field: 'os_theme_logo_small'
                }
            await this.http.post("/theme/upload_image", params, "text");
        }

        if (this.os_theme_favicon_changed) {
            let params =
                {
                    csrf_token: odoo.csrf_token,
                    ufile: [...this.os_theme_favicon_inputRef.el.files],
                    field: 'favicon'
                }
            await this.http.post("/theme/upload_image", params, "text");
        }


        return this.rpc("/web/theme/company/save_settings",
            {
                data: data_company
            }).then(function (res) {
            self.env.services.action.doAction("reload_context");
        });

    }


}

OsSettingsPanelGeneral.template = 'os_theme_butterfly.os_settings_panel_general';
