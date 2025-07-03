odoo.define('hotel_booking_dashboard.Dashboard', function(require) {
    "use strict";

    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var QWeb = core.qweb;
    var ajax = require('web.ajax');
    var rpc = require('web.rpc');
    var _t = core._t;
    var session = require('web.session');
    var web_client = require('web.web_client');
    var abstractView = require('web.AbstractView');
    var flag = 0;
    var tot_check_in_booking = []
    var tot_check_out_booking = []
    var tot_cancel_booking = []
    var tot_stay_booking = []
    var tot_occupancy = []
    var tot_avg_room_price = []
    var tot_not_paid = []
    var tot_customer = []
    var tot_amount_untaxed = []
    var tot_amount_room = []
    var tot_amount_tax = []
    var tot_task = []
    var tot_employee = []
    var tot_hrs = []
    var tot_margin = []
    var HotelBookingDashboard = AbstractAction.extend({
        template: 'HotelBookingDashboard',
        cssLibs: [
            '/hotel_booking_dashboard/static/src/css/lib/nv.d3.css'
        ],
        jsLibs: [
            '/hotel_booking_dashboard/static/src/js/lib/d3.min.js'
        ],

        events: {
            'click .tot_check_in_bookings': 'tot_check_in_bookings',
            'click .tot_check_out_bookings': 'tot_check_out_bookings',
            'click .tot_cancel_bookings': 'tot_cancel_bookings',
            'click .tot_stay_bookings': 'tot_stay_bookings',
            'click .tot_customers': 'tot_customers',
            'click .tots_not_paid': 'tots_not_paid',
            'change #start_date': '_onchangeFilter',
            'change #end_date': '_onchangeFilter',
            'change #employee_selection': '_onchangeFilter',
            'change #project_selection': '_onchangeFilter',
        },

        init: function(parent, context) {
            this._super(parent, context);
            this.dashboards_templates = ['DashboardHotelBooking', 'BookingDashboardChart'];
            this.today_sale = [];
            rpc.query({
                model: 'hotel.booking',
                method: 'get_room_stay_status',
                args: [],
            }).then(function(result) {
                tot_stay_booking = result
            })

        },


        willStart: function() {
            var self = this;
            return $.when(ajax.loadLibs(this), this._super()).then(function() {
                return self.fetch_data();
            });
        },

        start: function() {
            var self = this;
            this.set("title", 'Dashboard');
            return this._super().then(function() {
                self.render_dashboards();
                self.render_graphs();
            });
        },

        render_dashboards: function() {
            var self = this;
            _.each(this.dashboards_templates, function(template) {
                self.$('.o_booking_dashboard').append(QWeb.render(template, {
                    widget: self
                }));
            });
        },

        render_graphs: function() {
            var self = this;
            self.render_top_customers_graph();
        },

        render_top_customers_graph: function() {
            var self = this
            var ctx = self.$(".top_customers");
            rpc.query({
                model: "hotel.booking",
                method: 'get_top_customers',
            }).then(function(arrays) {
                var data = {
                    labels: arrays[1],
                    datasets: [{
                            label: "Amount Spent",
                            data: arrays[0],
                            backgroundColor: [
                                "rgba(190, 27, 75,1)",
                                "rgba(31, 241, 91,1)",
                                "rgba(103, 23, 252,1)",
                                "rgba(158, 106, 198,1)",
                                "rgba(250, 217, 105,1)",
                                "rgba(255, 98, 31,1)",
                                "rgba(255, 31, 188,1)",
                                "rgba(75, 192, 192,1)",
                                "rgba(153, 102, 255,1)",
                                "rgba(10,20,30,1)"
                            ],
                            borderColor: [
                                "rgba(190, 27, 75, 0.2)",
                                "rgba(190, 223, 122, 0.2)",
                                "rgba(103, 23, 252, 0.2)",
                                "rgba(158, 106, 198, 0.2)",
                                "rgba(250, 217, 105, 0.2)",
                                "rgba(255, 98, 31, 0.2)",
                                "rgba(255, 31, 188, 0.2)",
                                "rgba(75, 192, 192, 0.2)",
                                "rgba(153, 102, 255, 0.2)",
                                "rgba(10,20,30,0.3)"
                            ],
                            borderWidth: 1
                        },
                    ]
                };
                //options
                var options = {
                    responsive: true,
                    title: {
                        display: true,
                        position: "top",
                        text: " الايرادات حسب كل شركة",
                        fontSize: 18,
                        fontColor: "#111"
                    },
                    scales: {
                        yAxes: [{
                            ticks: {
                                min: 0
                            }
                        }]
                    }
                };
                //create Chart class object
                var chart = new Chart(ctx, {
                    type: 'bar',
                    data: data,
                    options: options
                });

            });
        },

        on_reverse_breadcrumb: function() {
            var self = this;
            web_client.do_push_state({});
            this.fetch_data().then(function() {
                self.$('.o_booking_dashboard').empty();
                self.render_dashboards();
                self.render_graphs();
            });
        },

        _onchangeFilter: function() {
            flag = 1
            var start_date = $('#start_date').val();
            var end_date = $('#end_date').val();
            if (!start_date) {
                start_date = "null"
            }
            if (!end_date) {
                end_date = "null"
            }
            var employee_selection = $('#employee_selection').val();
            var project_selection = $('#project_selection').val();
            ajax.rpc('/booking/filter-apply', {
                'data': {
                    'start_date': start_date,
                    'end_date': end_date,
                }
            }).then(function(data) {
                tot_check_in_booking = data['check_in_booking']
                tot_check_out_booking = data['check_out_booking']
                tot_cancel_booking = data['cancel_booking']
                tot_stay_booking = data['stay_booking']
                tot_customer = data['customer']
                tot_amount_untaxed = data['amount_untaxed']
                tot_amount_room = data['amount_room']
                tot_amount_tax = data['amount_tax']
                tot_occupancy = data['occupancy']
                tot_avg_room_price = data['avg_room_price']

                document.getElementById("tot_check_in_booking").innerHTML = data['check_in_booking'].length
                document.getElementById("tot_check_out_booking").innerHTML = data['check_out_booking'].length
                document.getElementById("tot_cancel_booking").innerHTML = data['cancel_booking'].length
                document.getElementById("tot_stay_booking").innerHTML = data['stay_booking'].length
                document.getElementById("tot_customer").innerHTML = data['customer'].length
                document.getElementById("tot_amount_untaxed").innerHTML = data['amount_untaxed']
                document.getElementById("tot_amount_room").innerHTML = data['amount_room']
                document.getElementById("tot_amount_tax").innerHTML = data['amount_tax']
                document.getElementById("tot_occupancy").innerHTML = data['occupancy']
                document.getElementById("tot_avg_room_price").innerHTML = data['avg_room_price']
            })
        },

        tot_check_in_bookings: function(e) {
            var self = this;
            e.stopPropagation();
            e.preventDefault();
            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };
            if (flag == 0) {
                const date = new Date();
                this.do_action({
                    name: _t("الوصول"),
                    type: 'ir.actions.act_window',
                    res_model: 'booking.folio',
                    view_mode: 'tree,form',
                    views: [
                        [false, 'list'],
                        [false, 'form']
                    ],
                    domain: [
                            ["check_in_date", "=", date]
                        ],
                    target: 'new'
                }, options)
            } else {
                if (tot_check_in_booking) {
                    this.do_action({
                        name: _t("الوصول"),
                        type: 'ir.actions.act_window',
                        res_model: 'booking.folio',
                        domain: [
                            ["id", "in", tot_check_in_booking]
                        ],
                        view_mode: 'tree,form',
                        views: [
                            [false, 'list'],
                            [false, 'form']
                        ],
                        target: 'new'
                    }, options)
                }
            }
        },

        tots_not_paid: function(e) {
            var self = this;
            e.stopPropagation();
            e.preventDefault();
            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };
            this.do_action({
                name: _t("حجوزات غير مسددة"),
                type: 'ir.actions.act_window',
                res_model: 'booking.folio',
                view_mode: 'tree,form',
                views: [
                    [false, 'list'],
                    [false, 'form']
                ],
                domain: [
                            ["state", "not in", ['cancelled', 'draft']], ["amount_due", ">", 0],
                        ],
                target: 'new'
            }, options)
        },

        tot_check_out_bookings: function(e) {
            var self = this;
            e.stopPropagation();
            e.preventDefault();
            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };
            if (flag == 0) {
                const date = new Date();
                this.do_action({
                    name: _t("مغادرة"),
                    type: 'ir.actions.act_window',
                    res_model: 'booking.folio',
                    view_mode: 'tree,form',
                    views: [
                        [false, 'list'],
                        [false, 'form']
                    ],
                    domain: [
                            ["check_out_date", "=", date]
                        ],
                    target: 'new'
                }, options)
            } else {
                if (tot_check_out_booking) {
                    this.do_action({
                        name: _t("مغادرة"),
                        type: 'ir.actions.act_window',
                        res_model: 'booking.folio',
                        domain: [
                            ["id", "in", tot_check_out_booking]
                        ],
                        view_mode: 'tree,form',
                        views: [
                            [false, 'list'],
                            [false, 'form']
                        ],
                        target: 'new'
                    }, options)
                }
            }
        },

        tot_cancel_bookings: function(e) {
            var self = this;
            e.stopPropagation();
            e.preventDefault();
            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };
            if (flag == 0) {
                const date = new Date();
                this.do_action({
                    name: _t("الحجوزات الملغية"),
                    type: 'ir.actions.act_window',
                    res_model: 'booking.folio',
                    view_mode: 'tree,form',
                    views: [
                        [false, 'list'],
                        [false, 'form']
                    ],
                    domain: [
                            ["state", "=", 'cancelled']
                        ],
                    target: 'new'
                }, options)
            } else {
                if (tot_cancel_booking) {
                    this.do_action({
                        name: _t("الحجوزات الملغية"),
                        type: 'ir.actions.act_window',
                        res_model: 'booking.folio',
                        domain: [
                            ["id", "in", tot_cancel_booking]
                        ],
                        view_mode: 'tree,form',
                        views: [
                            [false, 'list'],
                            [false, 'form']
                        ],
                        target: 'new'
                    }, options)
                }
            }
        },

        tot_stay_bookings: function(e) {
            var self = this;
            var stay_status = []
            e.stopPropagation();
            e.preventDefault();

            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };
            this.do_action({
                name: _t("الغرف الساكنة"),
                type: 'ir.actions.act_window',
                res_model: 'hotel.room',
                view_mode: 'kanban,form',
                views: [
                    [false, 'kanban'],
                    [false, 'form']
                ],
                domain: [
                        ["stay_state", "in", tot_stay_booking]
                    ],
                target: 'new'
            }, options)

        },

        tot_customers: function(e) {
            var self = this;
            e.stopPropagation();
            e.preventDefault();

            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };
            this.do_action({
                name: _t("الشركات"),
                type: 'ir.actions.act_window',
                res_model: 'res.partner',
                view_mode: 'kanban,tree,form',
                views: [
                    [false, 'kanban'],
                    [false, 'list'],
                    [false, 'form']
                ],
                domain: [
                        ["travel_type", "!=", false]
                    ],
                target: 'new'
            }, options)
        },

        fetch_data: function() {
            var self = this;
            var def1 = this._rpc({
                model: 'hotel.booking',
                method: 'get_tiles_data'
            }).then(function(result) {
                self.check_in_bookings = result['check_in_folios']
                self.check_out_bookings = result['check_out_folios']
                self.cancel_bookings = result['cancel_bookings']
                self.stay_bookings = result['stay_bookings']
                self.customers = result['customers']
                self.amount_untaxed = result['amount_untaxed']
                self.amount_room = result['amount_room']
                self.amount_tax = result['amount_tax']
                self.occupancy = result['occupancy']
                self.avg_room_price = result['avg_room_price']
                self.not_paid = result['not_paid']
            });

            return $.when(def1);
        },

    });

    core.action_registry.add('hotel_booking_dashboard', HotelBookingDashboard);

    return HotelBookingDashboard;

});