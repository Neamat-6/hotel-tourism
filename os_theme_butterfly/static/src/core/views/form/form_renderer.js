odoo.define('os_theme_butterfly.FormRenderer', function (require) {
    "use strict";
    var FormRenderer = require('web.FormRenderer');
    var session = require('web.session');
    const config = require('web.config');

    FormRenderer.include({
        events: _.extend({}, FormRenderer.prototype.events, {
            'dblclick .o_form_sheet_bg': '_onDblClick',
        }),

        _onDblClick: function (ev) {
            // Test if double click is enabled first
            if (session.user_dbl_click_edit) {
                var $target = $(ev.target);
                if ($target.parents('.modal').length || $target.parents('.o_chatter').length || $target.is('.o_chatter')) {
                    return;
                }
                this.trigger_up('edit_mode');
            }
        },

        _renderView: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                if (self.$('.ribbon-top-right:not(.o_invisible_modifier)').length) {
                    self.$('.oe_button_box').addClass('mr-8');
                }
            });
        },

        _renderTagNotebook: function (node) {
            var $notebook = this._super.apply(this, arguments);
            var $headers = $notebook.find('.o_notebook_headers');
            if (session.company_tabs_alignment === 'vertical') {
                $notebook.addClass('d-flex align-items-start');
                $notebook.find('ul.nav').addClass('flex-column nav-tabs-vertical w-100').removeClass('nav-tabs');
                $headers.addClass("col-md-3 pl-md-0");
                $notebook = $('<div>').append($('<hr/>'), $notebook)
            }

            if (!config.device.isMobile && session.company_tabs_alignment === 'horizontal') {
                var svg_right = '<svg xmlns="http://www.w3.org/2000/svg"  x="0" y="0" viewBox="0 0 128 128" xml:space="preserve" class="" width="30" height="30" style="enable-background:new 0 0 30 30"><g><path id="Right_Arrow_4_" d="m44 108c-1.023 0-2.047-.391-2.828-1.172-1.563-1.563-1.563-4.094 0-5.656l37.172-37.172-37.172-37.172c-1.563-1.563-1.563-4.094 0-5.656s4.094-1.563 5.656 0l40 40c1.563 1.563 1.563 4.094 0 5.656l-40 40c-.781.781-1.805 1.172-2.828 1.172z" data-original="#000000" class="" fill="currentColor"></path></g></svg>';
                var svg_left = '<svg xmlns="http://www.w3.org/2000/svg"  x="0" y="0" viewBox="0 0 128 128" style="enable-background:new 0 0 512 512" xml:space="preserve" class="" height="30" width="30"><g><path id="Left_Arrow_4_" d="m84 108c-1.023 0-2.047-.391-2.828-1.172l-40-40c-1.563-1.563-1.563-4.094 0-5.656l40-40c1.563-1.563 4.094-1.563 5.656 0s1.563 4.094 0 5.656l-37.172 37.172 37.172 37.172c1.563 1.563 1.563 4.094 0 5.656-.781.781-1.805 1.172-2.828 1.172z" data-original="#000000" class="" fill="currentColor"></path></g></svg>';
                var $scroller = $('<div class="scroller scroller-left">' + svg_left + '</div>\n' +
                    '  <div class="scroller scroller-right">' + svg_right + '</div>')
                $notebook.addClass('os-horizontal-notebook');
                $notebook.find('ul.nav').addClass('notebook-list');
                $notebook.prepend($scroller);
                $headers.addClass("wrapper");
                var scrollBarWidths = 40;

                var widthOfList = function () {
                    var itemsWidth = 0;
                    $notebook.find('.notebook-list li').each(function () {
                        var itemWidth = $(this).outerWidth();
                        itemsWidth += itemWidth;
                    });
                    return itemsWidth;
                };

                var widthOfHidden = function () {
                    return (($headers.outerWidth()) - widthOfList() - getLeftPosi()) - scrollBarWidths;
                };
                var getLeftPosi = function () {
                    return $notebook.find('.notebook-list').position().left;
                };
                var reAdjust = function () {
                    if (($headers.outerWidth()) < widthOfList()) {
                        $notebook.find('.scroller-right').show(300);
                    } else {
                        $notebook.find('.scroller-right').hide(300);
                    }

                    if (getLeftPosi() < 0) {
                        $notebook.find('.scroller-left').show(300);
                    } else {
                        $notebook.find('.notebook-list').animate({left: "-=" + getLeftPosi() + "px"}, 'slow');
                        $notebook.find('.scroller-left').hide(300);
                    }
                }
                // Our custom Js code
                setTimeout(function () {
                    reAdjust();
                }, 500);
                $(window).on('resize', function (e) {
                    reAdjust();
                });

                $notebook.find('.scroller-right').click(function () {
                    $notebook.find('.scroller-left').fadeIn('slow');
                    $notebook.find('.scroller-right').fadeOut('slow');
                    $notebook.find('.notebook-list').animate({left: "+=" + widthOfHidden() + "px"}, 'slow', function () {
                    });
                });

                $notebook.find('.scroller-left').click(function () {
                    $notebook.find('.scroller-right').fadeIn('slow');
                    $notebook.find('.scroller-left').fadeOut('slow');
                    $notebook.find('.notebook-list').animate({left: "-=" + getLeftPosi() + "px"}, 'slow', function () {
                    });
                });
            }

            return $notebook
        }
    });

});
