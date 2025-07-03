odoo.define('hotel.RoomTypeAvailabilityView', function(require) {
    "use strict";

    var core = require('web.core');
    var FieldOne2Many = require('web.relational_fields').FieldOne2Many;
    var fieldRegistry = require('web.field_registry');
    var ListRenderer = require('web.ListRenderer');
    var rpc = require('web.rpc');

    var _t = core._t;
    var QWeb = core.qweb;

    var RoomTypeAvailabilityListRenderer = ListRenderer.extend({
        events: {
            'click .accordian_btn': '_expand_room_detail',
            'click .booking_number': '_on_booking_number_click',

        },

        init: function(parent, state, params) {
            var self = this;
            this._super.apply(this, arguments);
            this.set({
                sheets: {},
                room_sheet: {},
                line_sheet: {},
                date_from: false,
                date_to: false,
                company_id: false,
                room_id: {},
                hotel: {},
            });
            this.company_id = parent.recordData.company_id.data.id;
            this.date_from = parent.recordData.date_from;
            this.date_to = parent.recordData.date_to;
            this.mode = parent.mode;

            self.rendered = false;
        },

        setRowMode: function(recordID, mode) {
            return $.when();
        },

        _selectCell: function(rowIndex, fieldIndex, options) {
            return $.when();
        },

        _render: function() {
            var self = this;
            rpc.query({
                model: 'room.type',
                method: 'get_room_type_data',
                args: [self.company_id],
            }).then(function(result) {
                self.rooms_types = result;

                self.$widget = $(QWeb.render('hotel_room_availability.RoomTypeAvailability', {
                    widget: self
                }));
                if (!self.rendered) {
                    self.rendered = true;
                    self.$el.html('');
                    self.$widget.appendTo(self.$el);
                    self.$el.parent().find('.o_cp_pager').hide();
                }
            });
        },

        start: function() {
            var self = this;
            this._super.apply(this, arguments);
            var dates = [];
            var start = self.date_from;
            var end = self.date_to;
            while (start <= end) {
                dates.push(start);
                var m_start = moment(start).add(1, 'days');
                start = m_start.toDate();
            }
            self.dates = dates;
        },

        _expand_room_detail: function(event) {
            var self = this;
            var target = event.target;
            if ($(target).hasClass('collapsed')) {
                $(target).removeClass('expanded_row').addClass('closed_row');
            } else if (!$(target).hasClass('collapsed')) {
                $(target).removeClass('closed_row').addClass('expanded_row');
                self.get_room_data($(target).data('room-type'),$(target).data('hotel'));
            }
        },

        get_room_data: async function(room_id,hotel) {
            var self = this;
            var roomTr = document.getElementsByClassName("room_tr");
            if (!$(roomTr).hasClass('rendered')) {
                var day_count = 0;
                var sheet = self.get("sheets");
                const StayViewData = await rpc.query({
                    model: 'room.type',
                    method: 'get_room_type_data_from_daterange',
                    args: [
                        sheet[0], room_id, moment(self.date_from).format('YYYY-MM-DD'),
                        moment(self.date_to).format('YYYY-MM-DD'),hotel
                    ],
                })
                for (const [RoomID, RoomData] of Object.entries(StayViewData)){
                    for (const day in self.dates) {
                        let room_data =  RoomData.filter((data) => {
                            return data.date == moment(self.dates[day]).format('YYYY-MM-DD');
                        });
                        if (room_data) {
                            try {

                                var room_row = document.getElementById("room_tr-" + String(RoomID));
                                var room_cell = room_row.insertCell();
                                var room_cell_data = '';
                                room_cell_data = `<button class="btn booking_number" data-day-count="${day_count}" data-booking-name="${room_data[0].booking_name}" data-room="${RoomID}" data-booking-id="${room_data[0].booking_id}">
                                                    <ul style="list-style-type: none; pointer-events:none;padding:0px !important;">
                                                    <strong><li>${room_data[0].booking_name}</li></strong>
                                                    <li>${room_data[0].room_state}</li>
                                                    <li>${room_data[0].partner_name}</li>
                                                    </ul>
                                                </button>
                                                `;
                                room_cell.innerHTML = room_cell_data;
                                day_count++;
                            } catch (error) {
                                console.log(error);
                                console.log("Error in room data");
                                console.log(RoomID);

                            }
                        }
                    }
                }

                $(roomTr).addClass('rendered');
            }
        },
        _on_booking_number_click: function(event) {
            var target = event.target;
            var hotelBookingId = $(target).data('booking-id');
            var bookingName = $(target).data('booking-name');
            if (bookingName != 'Out of order') {
                // open the form view of the booking
                this.do_action({
                    type: 'ir.actions.act_window',
                    res_model: 'hotel.booking',
                    res_id: hotelBookingId,
                    views: [[false, 'form']],
                    target: 'current',
                });
            }

        },
        _date_changed(date_from, date_to) {
            var self = this;
            self.rendered = false;
            self.date_from = date_from;
            self.date_to = date_to
            self.start();
        }
    });

    var RoomTypeAvailabilityFieldOne2Many = FieldOne2Many.extend({
        /**
         * We want to use our custom renderer for the list.
         *
         * @override
         */
        _getRenderer: function() {
            if (this.view.arch.tag === 'tree') {
                return RoomTypeAvailabilityListRenderer;
            }
            return this._super.apply(this, arguments);
        },

        reset: function(record, ev, fieldChanged) {
            if (!fieldChanged) {
                this.renderer._date_changed(record.data.date_from, record.data.date_to);
            }
            return this._super.apply(this, arguments);
        },

    });

    fieldRegistry.add('RoomTypeAvailabilityView', RoomTypeAvailabilityFieldOne2Many);
});
