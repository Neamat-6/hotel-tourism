odoo.define('os_theme_butterfly.KanbanRendererMobile', function (require) {
    "use strict";

    const {device} = require('web.config');
    if (!device.isMobile) {
        return;
    }
    var core = require('web.core');
    var KanbanRenderer = require('web.KanbanRenderer');
    var KanbanRendererUtilities = require('os_theme_butterfly.KanbanRendererUtilities');

    var _t = core._t;
    var qweb = core.qweb;

    KanbanRenderer.include(Object.assign({}, KanbanRendererUtilities, {
        custom_events: _.extend({}, KanbanRenderer.prototype.custom_events || {}, {
            quick_create_column_created: '_onColumnCreated',
        }),
        events: _.extend({}, KanbanRenderer.prototype.events, {
            'click .o_kanban_mobile_tab': '_onKanbanMobileTabClicked',
            'click .o_kanban_mobile_add_column': '_onKanbanMobileQuickCreateClicked',
        }),
        ANIMATE: true,
        RTL: _t.database.parameters.direction,

        init: function () {
            this._super.apply(this, arguments);
            this.currentColumnIndex = 0;
            this.finalGroupedBy = null;
            this.scrollPosition = null;
        },


        _onColumnCreated: function () {
            this._getTabPosition(this.widgets, this.currentColumnIndex, this.$('.o_kanban_mobile_tabs'));
            if (this._canCreateColumn() && !this.quickCreate.folded) {
                this.quickCreate.toggleFold();
            }
        },

        _onKanbanMobileTabClicked: function (event) {
            if (this._canCreateColumn() && !this.quickCreate.folded) {
                this.quickCreate.toggleFold();
            }
            this._moveToGroup($(event.currentTarget).index(), true);
        },

        _onKanbanMobileQuickCreateClicked: function () {
            this.$('.o_kanban_group').toggle();
            this.quickCreate.toggleFold();
        },

        on_attach_callback: function () {
            if (this.scrollPosition && this.state.groupedBy.length && this.widgets.length) {
                var currentColumnIndex = this.widgets[this.currentColumnIndex].$el;
                currentColumnIndex.scrollLeft(this.scrollPosition.left);
                currentColumnIndex.scrollTop(this.scrollPosition.top);
            }
            this._getTabPosition(this.widgets, this.currentColumnIndex, this.$('.o_kanban_mobile_tabs'));
            this._super.apply(this, arguments);
        },

        on_detach_callback: function () {
            if (this.state.groupedBy.length && this.widgets.length) {
                var currentColumnIndex = this.widgets[this.currentColumnIndex].$el;
                this.scrollPosition = {
                    left: currentColumnIndex.scrollLeft(),
                    top: currentColumnIndex.scrollTop(),
                };
            } else {
                this.scrollPosition = null;
            }
            this._super.apply(this, arguments);
        },


        addQuickCreate: function () {
            if (this._canCreateColumn() && !this.quickCreate.folded) {
                this._onKanbanMobileQuickCreateClicked();
            }
            return this.widgets[this.currentColumnIndex].addQuickCreate();
        },


        updateColumn: function (localID) {
            var index = _.findIndex(this.widgets, {db_id: localID});
            var currentColumnIndex = this.widgets[index].$el;
            var scrollTop = currentColumnIndex.scrollTop();
            return this._super.apply(this, arguments)
                .then(() => this._layoutUpdate(false))
                .then(() => currentColumnIndex.scrollTop(scrollTop));
        },


        _canCreateColumn: function () {
            return this.quickCreateEnabled && this.quickCreate && this.widgets.length;
        },

        _toNode: function (widgets) {
            const css = widgets
                .map(widget => '.o_kanban_group[data-id="' + (widget.id || widget.db_id) + '"]')
                .join(', ');
            return this.$(css);
        },
        _getColumnPosition: function (animate) {
            var self = this;
            if (this.widgets.length) {
                const rtl = self.RTL === 'rtl';

                this.$('.o_kanban_group').show();

                const column_after = this._toNode(this.widgets.filter((widget, index) => index > this.currentColumnIndex));
                const update_after = this._updateColumnCss(column_after, rtl ? {right: '100%'} : {left: '100%'}, animate);

                const column_before = this._toNode(this.widgets.filter((widget, index) => index < this.currentColumnIndex));
                const update_before = this._updateColumnCss(column_before, rtl ? {right: '-100%'} : {left: '-100%'}, animate);

                const $columnCurrent = this._toNode(this.widgets.filter((widget, index) => index === this.currentColumnIndex));
                const update_current = this._updateColumnCss($columnCurrent, rtl ? {right: '0%'} : {left: '0%'}, animate);

                update_after
                    .then(update_before)
                    .then(update_current)
                    .then(() => {
                        column_after.hide();
                        column_before.hide();
                    });
            }
        },


        _getCurrentColumn: function () {
            if (this.widgets.length) {
                var column = this.widgets[this.currentColumnIndex];
                if (!column) {
                    return;
                }
                var column_id = column.id || column.db_id;
                this.$('.o_kanban_mobile_tab.os_active_kanban, .o_kanban_group.os_active_kanban').removeClass('os_active_kanban');
                this.$('.o_kanban_group[data-id="' + column_id + '"], ' +
                    '.o_kanban_mobile_tab[data-id="' + column_id + '"]')
                    .addClass('os_active_kanban');
            }
        },


        activateSwipe: function () {
            var self = this;
            var step = self.RTL === 'rtl' ? -1 : 1;
            this.$el.swipe({
                excludedElements: ".o_kanban_mobile_tabs",
                swipeLeft: function () {
                    var index_to_move = self.currentColumnIndex + step;
                    if (index_to_move < self.widgets.length) {
                        self._moveToGroup(index_to_move, self.ANIMATE);
                    }
                },
                swipeRight: function () {
                    var index_to_move = self.currentColumnIndex - step;
                    if (index_to_move > -1) {
                        self._moveToGroup(index_to_move, self.ANIMATE);
                    }
                }
            });
        },


        _getTabWidth: function (column) {
            var column_id = column.id || column.db_id;
            return this.$('.o_kanban_mobile_tab[data-id="' + column_id + '"]').outerWidth();
        },


        _layoutUpdate: function (animate) {
            this._getCurrentColumn();
            this._getTabPosition(this.widgets, this.currentColumnIndex, this.$('.o_kanban_mobile_tabs'));
            this._getColumnPosition(animate);
        },


        _moveToGroup: function (index_to_move, animate) {
            if (index_to_move < 0 || index_to_move >= this.widgets.length) {
                this._layoutUpdate(animate);
                return Promise.resolve();
            }
            this.currentColumnIndex = index_to_move;
            this.finalGroupedBy = this.columnOptions.groupedBy;
            var column = this.widgets[this.currentColumnIndex];
            if (column.data.isOpen) {
                this._layoutUpdate(animate);
            } else {
                this.trigger_up('column_toggle_fold', {
                    db_id: column.db_id,
                    onSuccess: () => this._layoutUpdate(animate)
                });
            }
            this.activateSwipe();
            return Promise.resolve();
        },

        _renderExampleBackground: function () {
        },

        _renderGrouped: function (fragment) {
            var self = this;
            var documentFragment = document.createDocumentFragment();
            this._super.apply(this, [documentFragment]);
            this.defs.push(Promise.all(this.defs).then(function () {
                var data = [];
                _.each(self.state.data, function (group) {
                    if (!group.value) {
                        group = _.extend({}, group, {value: _t('Undefined')});
                        data.unshift(group);
                    } else {
                        data.push(group);
                    }
                });

                var container = document.createElement('div');
                container.classList.add('os_kanban_columns_container');
                container.appendChild(documentFragment);
                fragment.appendChild(container);
                if (data.length) {
                    $(qweb.render('KanbanView.MobileTabs', {
                        data: data,
                        quickCreateEnabled: self._canCreateColumn()
                    })).prependTo(fragment);
                }
            }));
        },


        _renderView: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                if (self.state.groupedBy.length) {
                    if (self.finalGroupedBy !== self.columnOptions.groupedBy) {
                        self.currentColumnIndex = 0;
                    }
                    return self._moveToGroup(self.currentColumnIndex);
                } else {
                    if (self._canCreateColumn()) {
                        self._onKanbanMobileQuickCreateClicked();
                    }
                    return Promise.resolve();
                }
            });
        },


        _updateColumnCss: function ($column, cssProperties, animate) {
            if (animate) {
                return new Promise(resolve => $column.animate(cssProperties, 'fast', resolve));
            } else {
                $column.css(cssProperties);
                return Promise.resolve();
            }
        },


    }));

});
