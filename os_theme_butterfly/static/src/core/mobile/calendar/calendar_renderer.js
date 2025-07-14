odoo.define('os_theme_butterfly.CalendarRendererMobile', function (require) {
    "use strict";

    const {device} = require('web.config');
    if (!device.isMobile) {
        return;
    }
    const {qweb} = require('web.core');
    const CalendarRenderer = require('web.CalendarRenderer');

    CalendarRenderer.include({

        events: _.extend({}, CalendarRenderer.events, {
            'click .os_top_panel_calendar_panel': '_toggleSidedPanel',
        }),


        init: function (parent, state, params) {
            this._super.apply(this, arguments);
            this.sidePanelShown = false;
            this.swipeModeEnabled = true;
            this.mobile_filters = [];
        },


        start: function () {
            var self = this;
            return this._super().then(function () {
                self._topPanelSwipe();
            });
        },


        _topPanelSwipe: function () {
            const self = this;
            let touchStart;
            let touchEnd;
            $(this.calendarElement).on('touchstart', function (event) {
                self.swipeModeEnabled = true;
                touchStart = event.touches[0].pageX;
            });
            $(this.calendarElement).on('touchend', function (event) {
                if (!self.swipeModeEnabled) {
                    return;
                }
                touchEnd = event.changedTouches[0].pageX;
                if (touchStart - touchEnd > 100) {
                    self.trigger_up('next');
                } else if (touchStart - touchEnd < -100) {
                    self.trigger_up('prev');
                }
            });

        },

        _loadFilters: function () {
            const filters = this.state.filters;
            return Object.keys(filters)
                .filter(key => filters[key].filters)
                .map(key => ({
                    label: filters[key].title,
                    values: this.processData(filters[key].filters),
                    countItems: filters[key].filters.length,
                }))
                ;
        },

        _getFullCalendarOptions: function () {
            const res = this._super(...arguments);
            res.views.dayGridMonth.columnHeaderFormat = 'ddd';
            res.weekNumbersWithinDays = false;
            res.views.dayGridMonth.weekLabel = '';
            const eventDragStart = res.eventDragStart;
            const eventPositioned = res.eventPositioned;
            const eventRender = res.eventRender;
            const eventResize = res.eventResize;
            const eventResizeStart = res.eventResizeStart;
            const selectAllow = res.selectAllow;
            const select = res.select;

            res.eventDragStart = (info) => {
                this.swipeModeEnabled = false;
                if (eventDragStart) {
                    eventDragStart.call(this.calendar, info);
                }
            };
            res.eventPositioned = (info) => {
                this.swipeModeEnabled = false;
                if (eventPositioned) {
                    eventPositioned.call(this.calendar, info);
                }
            };
            res.eventRender = (info) => {
                this.swipeModeEnabled = false;
                if (eventRender) {
                    eventRender.call(this.calendar, info);
                }
            };
            res.eventResize = (info) => {
                this.swipeModeEnabled = false;
                if (eventResize) {
                    eventResize.call(this.calendar, info);
                }
            };
            res.eventResizeStart = (info) => {
                this.swipeModeEnabled = false;
                if (eventResizeStart) {
                    eventResizeStart.call(this.calendar, info);
                }
            };
            res.selectAllow = (info) => {
                this.swipeModeEnabled = false;
                if (selectAllow) {
                    return selectAllow.call(this.calendar, info);
                }
                return true;
            };
            res.select = (info) => {
                info.jsEvent.isSelectiong = true;
                if (select) {
                    return select.call(this.calendar, info);
                }
            };
            res.dateClick = (info) => {
                if (info.jsEvent.isSelectiong) {
                    return;
                }
                if (info.view.type === this.scalesInfo.month) {
                    this.trigger_up('changeDate', {
                        date: moment(info.date),
                        scale: 'day',
                    });
                    return;
                }
                const data = {start: info.date, allDay: info.allDay};
                this._preOpenCreate(data);
            };
            res.yearDateClick = (info) => {
                this.trigger_up('changeDate', {
                    date: moment(info.date),
                    scale: 'day',
                });
            };

            return res;
        },

        _getPopoverParams: function (eventData) {
            const res = this._super.apply(this, arguments);
            res.container = 'body';
            return res;
        },

        _onPopoverShown: function ($popoverElement, calendarPopover) {
            this._super.apply(this, arguments);
            const $popover = $($popoverElement.data('bs.popover').tip);
            setTimeout(() => {
                $popover.toggleClass([
                    'bs-popover-left',
                    'bs-popover-right',
                ], false);
                $popover.find('.arrow').remove();
                $popover.css({
                    display: 'flex',
                    bottom: 0,
                    right: 0,
                    borderWidth: 0,
                    maxWidth: '100%',
                    transform: 'translate3d(0px, 0px, 0px)',
                });
                $popover.find('.o_cw_body').css({
                    display: 'flex',
                    flex: '1 0 auto',
                    flexDirection: 'column',
                });
                $popover.find('.o_cw_popover_fields_secondary')
                    .toggleClass('o_cw_popover_fields_secondary', false)
                    .css({
                            flexGrow: 1,
                        }
                    );
                $popover.on('touchmove', (event) => {
                    event.preventDefault();
                });
                $popover.on('mousewheel', (event) => {
                    event.preventDefault();
                });
                $popover.on('wheel', (event) => {
                    event.preventDefault();
                });
                $popover
                    .find('a.o_field_widget[href]')
                    .on('click', (event) => {
                        $('.o_cw_popover').popover('dispose');
                    });
            }, 0);
        },

        processData: function (array) {
            const self = this;
            return array
                .filter(element => element.active)
                .map(function (element) {
                    return Object.assign({}, element, {
                        color: self.getColor(element.color_index),
                    });
                });
        },

        async _renderView() {
            return this._super(...arguments).then(() => {
                this.$('.o_calendar_mini').toggleClass('d-none', true);
                this._renderTopPanelCalendar();
            });
        },

        _renderFilters: function () {
            return this._super(...arguments).then(() => {
                this.mobile_filters = this._loadFilters();
                const test = !!this.mobile_filters.reduce((visible, filter) => visible | (filter.countItems > 0), false);
                this.$('.o_calendar_sidebar .os_no_filters').toggleClass('d-none', test);
            });
        },

        _renderTopPanelCalendar: function () {
            this.$('.os_top_panel_calendar_panel').remove();
            this.topPanelCalendarMobile = $(qweb.render('CalendarView.TopPanelCalendarMobile', {
                filters: this.mobile_filters,
                sidePanelShown: this.sidePanelShown,
            }));
            this.$el.prepend(this.topPanelCalendarMobile);
        },

        _toggleSidedPanel: async function () {
            this.sidePanelShown = !this.sidePanelShown;
            this.$('.o_calendar_view').toggleClass('d-none', this.sidePanelShown);
            this.$('.o_calendar_sidebar_container').toggleClass('d-none', !this.sidePanelShown);
            this._renderTopPanelCalendar();
        },

        _unselectEvent: function () {
            this._super.apply(this, arguments);
            $('.o_cw_popover').popover('dispose');
        },

        on_attach_callback: function () {
            this.$el.height($(window).height() - this.$el.offset().top);
            this._super(...arguments);
        },
    });

});
