odoo.define('hotel.RoomAvailabilityView', function(require) {
    "use strict";

    var core = require('web.core');
    var FieldOne2Many = require('web.relational_fields').FieldOne2Many;
    var fieldRegistry = require('web.field_registry');
    var ListRenderer = require('web.ListRenderer');
    var rpc = require('web.rpc');

    var _t = core._t;
    var QWeb = core.qweb;

    var RoomAvailabilityListRenderer = ListRenderer.extend({
        events: {
//            'click .oe_room_availability_weekly a': 'go_to',
            // 'change input': '_onFieldChanged',
            // 'change .add_avaliable': '_onFieldChangedAVA',
            'click .accordian_btn': '_expand_room_detail',
            'click #search-availability': '_render',
//            'keyup .validate_input': '_onInputKeyUp',
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

        _render: async function() {
            var self = this;
            console.log("render called")
            const occupancy = await rpc.query({
                model: 'hotel.booking.line',
                method: 'get_occupancy_per_day',
                args: [self.get("sheets")[0],self.date_from, self.date_to, self.company_id],
            })
            self.occupancy = occupancy;

            const rooms_types = await rpc.query({
                model: 'hotel.room',
                method: 'get_room_data',
                domain: ['&',
                    ['booking_ok', '=', 'True'],['hotel_id', '=', self.company_id]
                ],
                args: [self.company_id],
            })
            self.rooms_types = rooms_types;
            self.$widget = $(QWeb.render('hotel_room_availability.RoomAvailability', {
                widget: self
            }));
            if (!self.rendered) {
                self.rendered = true;
                self.$el.html('');
                self.$widget.appendTo(self.$el);
                self.$el.parent().find('.o_cp_pager').hide();
            }


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
        get_occupancy_per_day: async function(start_date, end_date, company_id){
            var self = this;
            var occupancy = await rpc.query({
                model: 'hotel.booking.line',
                method: 'get_occupancy_per_day',
                args: [self.get("sheets")[0],start_date, end_date, company_id],
            });
            return occupancy;
        },


        _expand_room_detail: function(event) {
            var self = this;
            var target = event.target;
            if ($(target).hasClass('collapsed')) {
                $(target).removeClass('expanded_row').addClass('closed_row');
            } else if (!$(target).hasClass('collapsed')) {
                $(target).removeClass('closed_row').addClass('expanded_row');
                self.get_room_data($(target).data('room_type'),$(target).data('hotel'));
            }
        },

        get_room_data: function(room_id,hotel) {
            var self = this;
            var contract_row = document.getElementById("contract_tr-" + room_id);
            var price_row = document.getElementById("price_tr-" + room_id);
            var booked_tr = document.getElementById("booked_tr-" + room_id);
            var out_of_order_tr = document.getElementById("out_of_order_tr-" + room_id);
            var avail_room_tr = document.getElementById("avail_room_tr-" + room_id);
            var occupancy_tr = document.getElementById("occupancy_tr-" + room_id);
            if (!$(contract_row).hasClass('rendered')) {
                var day_count = 0;
                var sheet = self.get("sheets");
                rpc.query({
                    model: 'hotel.booking.line',
                    method: 'get_room_value_from_daterange',
                    args: [
                        sheet[0], room_id, moment(self.date_from).format('YYYY-MM-DD'), moment(self.date_to).format('YYYY-MM-DD'),hotel
                    ],
                }).then(function(result) {
                    _.each(self.dates, function(date) {
                        var room_data = _.find(result, function(data) {
                            return data.date == moment(date).format('YYYY-MM-DD');
                        });
                        if (typeof room_data !== "undefined") {
                            // First Row
                            var contract_cell = contract_row.insertCell();
                            var contract_cell_data = '';
                            contract_cell_data =    '<span name="contract_qty" class=" contract_qty" data-day-count="' + 0 + '" data-date="' + room_data.date + '" data-room="' + room_id + '">' + room_data.contract_qty + '</span>'
                            contract_cell.innerHTML = contract_cell_data;

                            // Third row
                            var booked_cell = booked_tr.insertCell();
                            var booked_cell_data = '';
                            booked_cell_data = '<span class="booked_rooms" data-day-count="' + day_count + '" data-room="' + room_id + '">' + room_data.booked + '</span>'
                            booked_cell.innerHTML = booked_cell_data;
                            $(booked_cell).addClass('pricelist_td')

                            var out_of_order_cell = out_of_order_tr.insertCell();
                            var out_of_order_cell_data = '';
                            out_of_order_cell_data = '<span class="out_of_order_rooms" data-day-count="' + day_count + '" data-room="' + room_id + '">' + room_data.out_of_order + '</span>'
                            out_of_order_cell.innerHTML = out_of_order_cell_data;
                            $(out_of_order_cell).addClass('pricelist_td')

                            // Fourth row
                            var avail_room_cell = avail_room_tr.insertCell();
                            var avail_cell_data = '';
                            avail_cell_data = '<span class="avail_rooms" data-day-count="' + day_count + '" data-room="' + room_id + '">' + room_data.avail + '</span>'
                            avail_room_cell.innerHTML = avail_cell_data;
                            // if (room_data.avail > 0) {
                            //     $(avail_room_cell).addClass('bg-success')
                            // } else {
                            //     $(avail_room_cell).addClass('bg-danger')
                            // }

                            // Fifth Row
                            var price_cell = price_row.insertCell();
                            var price_cell_data = '';
                            price_cell_data = '<span name="room_cost_price" data-room="' + room_id + '" data-contract_qty="' + room_data.contract_qty + '"  data-price_qty="' + room_data.price + '" class="price_data add_avaliable" data-qty="' + room_data.total_qty + '" data-date="' + room_data.date + '"     >' + room_data.price + '</span>'
                            price_cell.innerHTML = price_cell_data;
                            $(price_cell).addClass('price_td')

                            // Sixth Row
                            var occupancy_cell = occupancy_tr.insertCell();
                            var occupancy_cell_data = `<span name="occupancy" data-room=${room_id} data-occupancy=${room_data.occupancy}>${Math.round(room_data.occupancy*100,)}%</span>`
                            occupancy_cell.innerHTML = occupancy_cell_data;
                            if (room_data.occupancy == 0) {
                                $(occupancy_cell).addClass('bg-success')
                            }
                            else if (room_data.occupancy > 0 && room_data.occupancy < 1) {
                                $(occupancy_cell).addClass('bg-warning')
                            }
                            else  {
                                $(occupancy_cell).addClass('bg-danger')
                            }


                            $(occupancy_cell).addClass('occupancy_td')


                            self.style_checkbox(day_count, room_id)
                            day_count++;
                        }
                    });
                    self.display_total_qty(room_id)

                    var total_booked_cell = booked_tr.insertCell();
                    $(total_booked_cell).addClass('total_booked_cell bg-default');
                    $(total_booked_cell).attr('data-room', room_id);
                    self.display_booked_qty(room_id)

                    var total_avail_cell = avail_room_tr.insertCell();
                    $(total_avail_cell).addClass('total_avail_cell bg-default');
                    $(total_avail_cell).attr('data-room', room_id);
                    self.display_avail_qty(room_id)



                });

                if (!self.mode == 'readonly') {
                    alert("1")
                    $(document).on('change', '.close_checkbox', function(event) {
                        event.preventDefault();
                        var room_qty = $('.oe_timesheet_weekly_input[data-room="' + $(this).data('room') + '"][data-day-count="' + $(this).data('day-count') + '"]');
                        self.style_checkbox($(this).data('day-count'), $(this).data('room'));
                        if ($(this).data('origin') !== $(this).prop('checked') && !room_qty.hasClass('value_changed')) {
                            $(this).addClass('value_changed');
                        } else {
                            $(this).removeClass('value_changed');
                        }
                    });
                    $(document).on('change', '.oe_timesheet_weekly_input', function(event) {
                    alert("2")
                        event.preventDefault();
                        var close = $('.close_checkbox[data-room="' + $(this).data('room') + '"][data-day-count="' + $(this).data('day-count') + '"]');
                        if ($(this).data('origin') != $(this).val() && !close.hasClass('value_changed')) {
                            $(this).addClass('value_changed');
                        } else {
                            $(this).removeClass('value_changed');
                        }
                        self.display_total_qty($(this).data('room'));
                        self.display_booked_qty($(this).data('room'));
                        self.display_avail_qty($(this).data('room'));
                        var booked = $('.booked_rooms[data-room="' + $(this).data('room') + '"][data-day-count="' + $(this).data('day-count') + '"]').text();
                        var avail = parseInt($(this).val()) - parseInt(booked)
                        $('.avail_rooms[data-room="' + $(this).data('room') + '"][data-day-count="' + $(this).data('day-count') + '"]').text(avail)
                    });
                }

                $(contract_row).addClass('rendered');
            }
        },

        style_checkbox: function(day_count, room_id) {
            var price_td = $('.price_td');
            var input_td = $('.input_td');
            var input = $('.oe_timesheet_weekly_input[data-room="' + room_id + '"][data-day-count="' + day_count + '"]').parent();
            var booked = $('.booked_rooms[data-room="' + room_id + '"][data-day-count="' + day_count + '"]').parent();
            var available = $('.avail_rooms[data-room="' + room_id + '"][data-day-count="' + day_count + '"]').parent();
            var checked = $('.close_checkbox[data-room="' + room_id + '"][data-day-count="' + day_count + '"]').prop('checked');
            // $(price_td).css({
            //         "color": "#fff",
            //         "background-color": "#3f51b5",
            //     });
            $(input_td).css({
                    "padding-left": "2px",
                    "padding-right": "2px",
            });
            if (checked) {
                $('.close_checkbox[data-room="' + room_id + '"][data-day-count="' + day_count + '"]').parent().css({
                    "background-color": "grey",
                    "color": "white"
                });
                $(input).css({
                    "background-color": "grey",
                    "padding-left": "2px",
                    "padding-right": "2px",
                });
                $(booked).css({
                    "background-color": "grey",
                    "color": "white"
                });
                $(available).css({
                    "background-color": "grey",
                    "color": "white"
                });
            } else {
                $('.close_checkbox[data-room="' + room_id + '"][data-day-count="' + day_count + '"]').parent().removeAttr("style");
                $(input).removeAttr("style");
                $(booked).removeAttr("style");
                $(available).removeAttr("style");
            $(input_td).css({
                    "padding-left": "2px",
                    "padding-right": "2px",
            });
            }
        },

        style_caption: function(room_id, name_height, check_height, booked_height, avail_height) {
            var contract_row = $("#contract_caption-" + room_id);
//            var name_row = $("#room_caption-" + room_id);
            // var closed_tr = $("#closed_caption-" + room_id);
            var booked_tr = $("#booked_caption-" + room_id);
            var avail_room_tr = $("#avail_caption-" + room_id);
            $('head').append("<style>#contract_tr-" + room_id + "::before{ content:'Cotract'; overflow: hidden; text-overflow: ellipsis; width: " + (contract_row.outerWidth() + (contract_row.next().outerWidth() * 2)) + "px !important; height: " + name_height + "px !important; }</style>");
//            $('head').append("<style>#room_name-" + room_id + "::before{ content:'Room'; overflow: hidden; text-overflow: ellipsis; width: " + (name_row.outerWidth() + (name_row.next().outerWidth() * 2)) + "px !important; height: " + name_height + "px !important; }</style>");
            $('head').append("<style>#closed_tr-" + room_id + "::before{ content:'Closed'; overflow: hidden; text-overflow: ellipsis; width: " + (closed_tr.outerWidth() + (closed_tr.next().outerWidth() * 2)) + "px !important; height: " + check_height + "px !important; padding: 0.75rem; }</style>");
            $('head').append("<style>#booked_tr-" + room_id + "::before{ content:'Booked'; overflow: hidden; text-overflow: ellipsis; width: " + (booked_tr.outerWidth() + (booked_tr.next().outerWidth() * 2)) + "px !important; height: " + booked_height + "px !important; padding: 0.75rem; }</style>");
            $('head').append("<style>#avail_room_tr-" + room_id + "::before{ content:'Available'; overflow: hidden; text-overflow: ellipsis; width: " + (avail_room_tr.outerWidth() + (avail_room_tr.next().outerWidth() * 2)) + "px !important; height: " + avail_height + "px !important; padding: 0.75rem; }</style>");
        },

        display_total_qty: function(room_id) {

            var self = this;
            var total = 0;
            if (self.mode == 'readonly') {
                _.each($(".oe_timesheet_weekly_input[data-room='" + room_id + "']"), function(input) {
                    total += parseInt($(input).text());
                });
            } else {
                _.each($(".oe_timesheet_weekly_input[data-room='" + room_id + "']"), function(input) {
                    total += parseInt($(input).val());
                });
            }
//            $(".total_qty_cell[data-room='" + room_id + "']").html(total);
        },

        display_booked_qty: function(room_id) {
            var total = 0;
            _.each($(".booked_rooms[data-room='" + room_id + "']"), function(input) {
                total += parseInt($(input).text());
            });
            $(".total_booked_cell[data-room='" + room_id + "']").html(total);
        },

        display_avail_qty: function(room_id) {
            var total = 0;

            _.each($(".avail_rooms[data-room='" + room_id + "']"), function(input) {
                total += parseInt($(input).text());
            });
            $(".total_avail_cell[data-room='" + room_id + "']").html(total);
        },

        _onInputKeyUp: function(ev) {
            if (isNaN(ev.currentTarget.value)) {
                ev.currentTarget.value = ev.currentTarget.defaultValue;
            } else if ((parseInt(ev.currentTarget.value) < 0) || ev.currentTarget.value.length > 3) {
                ev.currentTarget.value = ev.currentTarget.defaultValue;
            }
        },

        _onFieldChangedAVA: function(ev) {
            var self = this;
            var datas = self.state.data;
            var dataset = ev.currentTarget.dataset;
            var checked = ev.target.checked;
            var value = ev.target.value;
            var res_date = dataset.date;
            var res_room_id = parseInt(dataset.room);
            var contract_qty = dataset.contract_qty
            if ((parseInt(ev.currentTarget.value)*-1 > contract_qty) || (parseInt(ev.currentTarget.value) > 0) || ev.currentTarget.value.length > 3) {
                ev.currentTarget.value = 0;
                return;
            }
            alert("asdsd")
        },
        _onFieldChanged: function(ev) {
            alert("_onFieldChanged")
            var self = this;
            var dataset = ev.currentTarget.dataset;
            var contract_qty = dataset.contract_qty
            if (ev.currentTarget.type != 'checkbox') {
                if (isNaN(ev.currentTarget.value)) {
                    ev.currentTarget.value = ev.currentTarget.defaultValue;
                    return;
   } else  if ((parseInt(ev.currentTarget.value)*-1 > contract_qty) || (parseInt(ev.currentTarget.value) > 0) || ev.currentTarget.value.length > 3) {
                ev.currentTarget.value = 0;
                return;
            }
              }


            var datas = self.state.data;

            var checked = ev.target.checked;
            var value = ev.target.value;
            var res_date = dataset.date;
            var res_room_id = parseInt(dataset.room);
            var prev_data = _.find(datas, function(data) {
                return moment(data.data.date).format('YYYY-MM-DD') == res_date && data.data.room_category_id.res_id == res_room_id
            });
            if (ev.currentTarget.type == 'checkbox') {
                var args = {
                    default_close: checked,
                    default_room_category_id: res_room_id,
                    default_date: res_date,
                    default_contract_qty:dataset.contract_qty,
                    default_room_cost_price:dataset.price_qty,
                    // default_room_qty: dataset.qty,
                }
            } else {
                var args = {
                    default_room_qty: value,
                    default_room_category_id: res_room_id,
                    default_date: res_date,
                    default_contract_qty:dataset.contract_qty,
                    default_room_cost_price:dataset.price_qty,
                    // default_close: dataset.close,
                }
            }

            if (prev_data !== undefined) {
                if (ev.currentTarget.type == 'checkbox') {
                    var args = {
                        default_close: checked,
                        default_room_qty: prev_data.data.room_qty,
                        default_room_category_id: res_room_id,
                        default_date: res_date,
                        default_contract_qty:dataset.contract_qty,
                        default_room_cost_price:dataset.price_qty,
                    }
                } else {
                    var args = {
                        default_close: prev_data.data.close,
                        default_room_qty: value,
                        default_room_category_id: res_room_id,
                        default_date: res_date,
                        default_contract_qty: dataset.contract_qty,
                        default_room_cost_price:dataset.price_qty,
                    }
                }
                self.unselectRow().then(function() {
                    self.trigger_up('list_record_remove', {
                        id: prev_data.id
                    });
                    self.trigger_up('add_record', {
                        context: args && [args]
                    });
                });
            } else {
                self.unselectRow().then(function() {
                    self.trigger_up('add_record', {
                        context: args && [args]
                    });
                });
            }

            self.style_checkbox(dataset.dayCount, res_room_id);
            self.display_total_qty(res_room_id);
            self.display_booked_qty(res_room_id);
            self.display_avail_qty(res_room_id);
        },

        // _date_changed(date_from, date_to) {
        //     alert("_date_changed")
        //     var self = this;
        //     self.rendered = false;
        //     self.date_from = date_from;
        //     self.date_to = date_to
        //     self.start();
        // }

    });

    var RoomAvailabilityFieldOne2Many = FieldOne2Many.extend({
        /**
         * We want to use our custom renderer for the list.
         *
         * @override
         */
        _getRenderer: function() {
            if (this.view.arch.tag === 'tree') {
                return RoomAvailabilityListRenderer;
            }
            return this._super.apply(this, arguments);
        },

        // reset: function(record, ev, fieldChanged) {
        //     if (!fieldChanged) {
        //         this.renderer._date_changed(record.data.date_from, record.data.date_to);
        //     }
        //     return this._super.apply(this, arguments);
        // },

    });

    fieldRegistry.add('RoomAvailabilityView', RoomAvailabilityFieldOne2Many);
});
