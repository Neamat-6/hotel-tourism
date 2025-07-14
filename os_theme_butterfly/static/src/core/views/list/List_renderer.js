odoo.define('ThemeBackend.ListRenderer', function (require) {
    "use strict";

    var ListRenderer = require("web.ListRenderer");

    ListRenderer.include({

        _onSelectRecord: function (event) {
            this._super.apply(this, arguments);
            var $selectedRecord = $(event.target).closest('tr')
            if ($(event.target).prop('checked')) {
                $selectedRecord.addClass('selected_item');
            } else {
                $selectedRecord.removeClass('selected_item')
            }
        },

        // List Number
        _getNumberOfCols: function () {
            var columns = this._super();
            if (this.hasSelectors && !this.isGrouped) {
                columns += 1;
            }
            return columns;
        },

        _onToggleSelection: function (ev) {
            this._super.apply(this, arguments);
            var checked = $(ev.currentTarget).prop('checked') || false;
            if (checked) {

                this.$('tbody .o_list_record_selector input:not(":disabled"):checked').parents('tr').addClass('selected_item');

            } else {

                this.$('tbody .selected_item').removeClass('selected_item');

            }
        },


        _renderFooter: function () {
            const $footer = this._super.apply(this, arguments);
            if (this.hasSelectors && !this.isGrouped) {
                $footer.find('tr').prepend($('<td>'));
            }
            return $footer;
        },

        _renderHeader: function () {
            var $thead = this._super.apply(this, arguments);
            if (this.hasSelectors && !this.isGrouped) {
                $thead.find('th.o_list_record_selector').before($('<th>', {class: 'o_list_record_number'}).html('#'));
            }
            return $thead;
        },
        _renderRow: function (record) {
            var $rows = this._super(record);
            var index = this.state.data.indexOf(record)
            if (this.hasSelectors && !this.isGrouped) {
                $rows.prepend($("<td class='o_list_serial_number'>").html(index + 1));
            }
            return $rows;
        },

    });


});
