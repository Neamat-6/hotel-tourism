odoo.define('room_availability_dashboard.Dashboard', function(require) {
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
    var tot_so = []
    var tot_project = []
    var tot_task = []
    var tot_employee = []
    var tot_hrs = []
    var tot_margin = []
    var RoomAvailabilityDashboard = AbstractAction.extend({
        template: 'RoomAvailabilityDashboard',
        cssLibs: [
            '/room_availability_dashboard/static/src/css/lib/nv.d3.css'
        ],
        jsLibs: [
            '/room_availability_dashboard/static/src/js/lib/d3.min.js'
        ],

        events: {
            'click .click-view-check-in': 'click_view_check_in',
            'click .click-view-arrival': 'click_view_arrival',
            'click .click-view-check-out': 'click_view_check_out',
            'click .click-view-exp-check-out': 'click_view_exp_check_out',
            'click .click-view-booked': 'click_view_booked',
            'click .click-view-exp-booked': 'click_view_exp_booked',
            'click .click-view-cancelled': 'click_view_cancelled',
            'click .click-view-inhouse': 'click_view_inhouse',
            'click .click-view-exp-inhouse': 'click_view_exp_inhouse',
            'click .click-view-allotment1': 'click_view_allotment1',
            'click .click-view-allotment2': 'click_view_allotment2',
            'click #download-availability': 'click_download_availability',
            'click #send-mail': 'click_send_mail',
            'change #start_date': '_onchangeFilter',
            'change #end_date': '_onchangeFilter',
        },

        init: function(parent, context) {
            this._super(parent, context);
            this.dashboards_templates = ['DashboardRoomAvailability', 'RoomAvailabilityDashboardChart'];
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
            });
        },

        _onchangeFilter: function() {
            flag = 1
            var start_date = $('#start_date').val();
            var end_date = $('#end_date').val();
            var company = $('#company_input').val();
            if (!start_date) {
                start_date = "null"
            }
            if (!end_date) {
                end_date = "null"
            }
            ajax.rpc('/availability/filter-apply', {
                'data': {
                    'start_date': start_date,
                    'end_date': end_date,
                    'company': company,
                }
            }).then(function(data) {
                tot_check_in_booking = data['days']
                var table = document.getElementById("availability-tbody")
                table.innerHTML = ''
                //row no. 1
                var row = document.createElement("tr")
                var c1 = document.createElement("td")
                c1.innerText = "التاريخ"
                c1.style.cssText = 'font-weight: bold;'
                row.appendChild(c1);
                for(var i = 0; i < tot_check_in_booking.length; i++){

                    var newAnchor = document.createElement('a');


                    var td = document.createElement("td")
                    var button = document.createElement("button")
                    button.style.cssText = 'cursor:default;border-radius: 8px; background-color: #c4c4f2;width: 50px;height: 35px;';
                    var span = document.createElement("span")
                    span.innerText = tot_check_in_booking[i][0]
                    button.appendChild(span)
                    td.appendChild(button)
                    row.appendChild(td);
                }
                table.appendChild(row)
                //row no. 2
                var row = document.createElement("tr")
                var c1 = document.createElement("td")
                c1.innerText = "اليوم"
                c1.style.cssText = 'font-weight: bold;'
                row.appendChild(c1);
                for(var i = 0; i < tot_check_in_booking.length; i++){
                    var td = document.createElement("td")
                    var button = document.createElement("button")
                    button.style.cssText = 'cursor:default;border-radius: 8px; background-color: #c4c4f2;width: 50px;height: 35px;';
                    var span = document.createElement("span")
                    span.innerText = tot_check_in_booking[i][1]
                    button.appendChild(span)
                    td.appendChild(button)
                    row.appendChild(td);
                }
                table.appendChild(row)
                //row no. 3
                var row = document.createElement("tr")
                var c1 = document.createElement("td")
                c1.innerText = "تسجيل الوصول"
                c1.style.cssText = 'font-weight: bold;'
                row.appendChild(c1);
                for(var i = 0; i < tot_check_in_booking.length; i++){
                    var td = document.createElement("td")
                    var button = document.createElement("button")
                    button.style.cssText = 'border-radius: 8px; background-color: #c4c4f2;width: 50px;height: 35px;';
                    button.setAttribute('value', tot_check_in_booking[i][3]);
                    button.classList.add("click-view-check-in")
                    button.classList.add("bg-success")
                    var span = document.createElement("span")
                    span.innerText = tot_check_in_booking[i][2]
                    button.appendChild(span)
                    td.appendChild(button)
                    row.appendChild(td);
                }
                table.appendChild(row)
                //row no. 4
                var row = document.createElement("tr")
                var c1 = document.createElement("td")
                c1.innerText = "الوصول"
                c1.style.cssText = 'font-weight: bold;'
                row.appendChild(c1);
                for(var i = 0; i < tot_check_in_booking.length; i++){
                    var td = document.createElement("td")
                    var button = document.createElement("button")
                    button.style.cssText = 'border-radius: 8px; background-color: #c4c4f2;width: 50px;height: 35px;';
                    button.setAttribute('value', tot_check_in_booking[i][32]);
                    button.classList.add("click-view-arrival")
                    button.classList.add("bg-success")
                    var span = document.createElement("span")
                    span.innerText = tot_check_in_booking[i][31]
                    button.appendChild(span)
                    td.appendChild(button)
                    row.appendChild(td);
                }
                table.appendChild(row)
                //row no. 5
                var row = document.createElement("tr")
                var c1 = document.createElement("td")
                c1.innerText = "الخروج الفعلي"
                c1.style.cssText = 'font-weight: bold;'
                row.appendChild(c1);
                for(var i = 0; i < tot_check_in_booking.length; i++){
                    var td = document.createElement("td")
                    var button = document.createElement("button")
                    button.style.cssText = 'border-radius: 8px; background-color: #c4c4f2;width: 50px;height: 35px;';
                    button.setAttribute('value', tot_check_in_booking[i][5]);
                    button.classList.add("click-view-check-out")
                    button.classList.add("bg-danger")
                    var span = document.createElement("span")
                    span.innerText = tot_check_in_booking[i][4]
                    button.appendChild(span)
                    td.appendChild(button)
                    row.appendChild(td);
                }
                table.appendChild(row)
                //row no. 6 exp
                var row = document.createElement("tr")
                var c1 = document.createElement("td")
                c1.innerText = "الخروج المتوقع"
                c1.style.cssText = 'font-weight: bold;'
                row.appendChild(c1);
                for(var i = 0; i < tot_check_in_booking.length; i++){
                    var td = document.createElement("td")
                    var button = document.createElement("button")
                    button.style.cssText = 'border-radius: 8px; background-color: #c4c4f2;width: 50px;height: 35px;';
                    button.setAttribute('value', tot_check_in_booking[i][16]);
                    button.classList.add("click-view-exp-check-out")
                    button.classList.add("bg-danger")
                    var span = document.createElement("span")
                    span.innerText = tot_check_in_booking[i][15]
                    button.appendChild(span)
                    td.appendChild(button)
                    row.appendChild(td);
                }
                table.appendChild(row)
                //row no. 7
                var row = document.createElement("tr")
                var c1 = document.createElement("td")
                c1.innerText = "الحجوزات الملغية"
                c1.style.cssText = 'font-weight: bold;'
                row.appendChild(c1);
                for(var i = 0; i < tot_check_in_booking.length; i++){
                    var td = document.createElement("td")
                    var button = document.createElement("button")
                    button.style.cssText = 'border-radius: 8px; background-color: #c4c4f2;width: 50px;height: 35px;';
                    button.classList.add("bg-danger")
                    button.setAttribute('value', tot_check_in_booking[i][11]);
                    button.classList.add("click-view-cancelled")
                    var span = document.createElement("span")
                    span.innerText = tot_check_in_booking[i][10]
                    button.appendChild(span)
                    td.appendChild(button)
                    row.appendChild(td);
                }
                table.appendChild(row)
                //row no. 8
                var row = document.createElement("tr")
                var c1 = document.createElement("td")
                c1.innerText = "الساكن فعليا"
                c1.style.cssText = 'font-weight: bold;'
                row.appendChild(c1);
                for(var i = 0; i < tot_check_in_booking.length; i++){
                    var td = document.createElement("td")
                    var button = document.createElement("button")
                    button.style.cssText = 'border-radius: 8px; background-color: #c4c4f2;width: 50px;height: 35px;';
                    button.setAttribute('value', tot_check_in_booking[i][13]);
                    button.classList.add("click-view-inhouse")
                    button.classList.add("bg-warning")
                    var span = document.createElement("span")
                    span.innerText = tot_check_in_booking[i][12]
                    button.appendChild(span)
                    td.appendChild(button)
                    row.appendChild(td);
                }
                table.appendChild(row)
                //row no. 9 exp
                var row = document.createElement("tr")
                var c1 = document.createElement("td")
                c1.innerText = "المتوقع في الداخل"
                c1.style.cssText = 'font-weight: bold;'
                row.appendChild(c1);
                for(var i = 0; i < tot_check_in_booking.length; i++){
                    var td = document.createElement("td")
                    var button = document.createElement("button")
                    button.style.cssText = 'border-radius: 8px; background-color: #c4c4f2;width: 50px;height: 35px;';
                    button.setAttribute('value', tot_check_in_booking[i][18]);
                    button.classList.add("click-view-exp-inhouse")
                    button.classList.add("bg-warning")
                    var span = document.createElement("span")
                    span.innerText = tot_check_in_booking[i][17]
                    button.appendChild(span)
                    td.appendChild(button)
                    row.appendChild(td);
                }
                table.appendChild(row)
                //row no. 10
                var row = document.createElement("tr")
                var c1 = document.createElement("td")
                c1.innerText = "إجمالي الغرف"
                c1.style.cssText = 'font-weight: bold;'
                row.appendChild(c1);
                for(var i = 0; i < tot_check_in_booking.length; i++){
                    var td = document.createElement("td")
                    var button = document.createElement("button")
                    button.style.cssText = 'cursor:default;border-radius: 8px; background-color: #00cbf5;width: 50px;height: 35px;';
                    var span = document.createElement("span")
                    span.innerText = tot_check_in_booking[i][6]
                    button.appendChild(span)
                    td.appendChild(button)
                    row.appendChild(td);
                }
                table.appendChild(row)
                //row no. 11
                var row = document.createElement("tr")
                var c1 = document.createElement("td")
                c1.innerText = "Unconfirmed Allotment"
                c1.style.cssText = 'font-weight: bold;'
                row.appendChild(c1);
                for(var i = 0; i < tot_check_in_booking.length; i++){
                    var td = document.createElement("td")
                    var button = document.createElement("button")
                    button.style.cssText = 'border-radius: 8px; background-color: #00cbf5;width: 50px;height: 35px;';
                    button.setAttribute('value', tot_check_in_booking[i][34]);
                    button.classList.add("click-view-allotment1")
                    var span = document.createElement("span")
                    span.innerText = tot_check_in_booking[i][33]
                    button.appendChild(span)
                    td.appendChild(button)
                    row.appendChild(td);
                }
                table.appendChild(row)
                //row no. 12
                var row = document.createElement("tr")
                var c1 = document.createElement("td")
                c1.innerText = "Confirmed Allotment"
                c1.style.cssText = 'font-weight: bold;'
                row.appendChild(c1);
                for(var i = 0; i < tot_check_in_booking.length; i++){
                    var td = document.createElement("td")
                    var button = document.createElement("button")
                    button.style.cssText = 'border-radius: 8px; background-color: #00cbf5;width: 50px;height: 35px;';
                    button.setAttribute('value', tot_check_in_booking[i][36]);
                    button.classList.add("click-view-allotment2")
                    var span = document.createElement("span")
                    span.innerText = tot_check_in_booking[i][35]
                    button.appendChild(span)
                    td.appendChild(button)
                    row.appendChild(td);
                }
                table.appendChild(row)
                //row no. 11
                var row = document.createElement("tr")
                var c1 = document.createElement("td")
                c1.innerText = "الغرف المحجوزة فعليا"
                c1.style.cssText = 'font-weight: bold;'
                row.appendChild(c1);
                for(var i = 0; i < tot_check_in_booking.length; i++){
                    var td = document.createElement("td")
                    var button = document.createElement("button")
                    button.style.cssText = 'border-radius: 8px; background-color: #00cbf5;width: 50px;height: 35px;';
                    button.setAttribute('value', tot_check_in_booking[i][14]);
                    button.classList.add("click-view-booked")
                    var span = document.createElement("span")
                    span.innerText = tot_check_in_booking[i][7]
                    button.appendChild(span)
                    td.appendChild(button)
                    row.appendChild(td);
                }
                table.appendChild(row)
                //row no. 12 exp
                var row = document.createElement("tr")
                var c1 = document.createElement("td")
                c1.innerText = "الغرف المحجوزة المتوقعة"
                c1.style.cssText = 'font-weight: bold;'
                row.appendChild(c1);
                for(var i = 0; i < tot_check_in_booking.length; i++){
                    var td = document.createElement("td")
                    var button = document.createElement("button")
                    button.style.cssText = 'border-radius: 8px; background-color: #00cbf5;width: 50px;height: 35px;';
                    button.setAttribute('value', tot_check_in_booking[i][22]);
                    button.classList.add("click-view-exp-booked")
                    var span = document.createElement("span")
                    span.innerText = tot_check_in_booking[i][19]
                    button.appendChild(span)
                    td.appendChild(button)
                    row.appendChild(td);
                }
                table.appendChild(row)
                //row no. 13
                var row = document.createElement("tr")
                var c1 = document.createElement("td")
                c1.innerText = "الغرف المتاحة الفعلية"
                c1.style.cssText = 'font-weight: bold;'
                row.appendChild(c1);
                for(var i = 0; i < tot_check_in_booking.length; i++){
                    var td = document.createElement("td")
                    var button = document.createElement("button")
                    button.style.cssText = 'cursor:default;border-radius: 8px; background-color: #00cbf5;width: 50px;height: 35px;';
                    var span = document.createElement("span")
                    span.innerText = tot_check_in_booking[i][8]
                    button.appendChild(span)
                    td.appendChild(button)
                    row.appendChild(td);
                }
                table.appendChild(row)
                //row no. 14 exp
                var row = document.createElement("tr")
                var c1 = document.createElement("td")
                c1.innerText = "الغرف المتوفرة المتوقعة"
                c1.style.cssText = 'font-weight: bold;'
                row.appendChild(c1);
                for(var i = 0; i < tot_check_in_booking.length; i++){
                    var td = document.createElement("td")
                    var button = document.createElement("button")
                    button.style.cssText = 'cursor:default;border-radius: 8px; background-color: #00cbf5;width: 50px;height: 35px;';
                    var span = document.createElement("span")
                    span.innerText = tot_check_in_booking[i][20]
                    button.appendChild(span)
                    td.appendChild(button)
                    row.appendChild(td);
                }
                table.appendChild(row)
                //row no. 15
                var row = document.createElement("tr")
                var c1 = document.createElement("td")
                c1.innerText = "(%) الإشغال الفعلي"
                c1.style.cssText = 'font-weight: bold;'
                row.appendChild(c1);
                for(var i = 0; i < tot_check_in_booking.length; i++){
                    var td = document.createElement("td")
                    var button = document.createElement("button")
                    button.style.cssText = 'cursor:default;border-radius: 8px; background-color: #00cbf5;width: 50px;height: 35px;';
                    var span = document.createElement("span")
                    span.innerText = tot_check_in_booking[i][9]
                    button.appendChild(span)
                    td.appendChild(button)
                    row.appendChild(td);
                }
                table.appendChild(row)
                //row no. 16 exp
                var row = document.createElement("tr")
                var c1 = document.createElement("td")
                c1.innerText = "(%) الإشغال المتوقع"
                c1.style.cssText = 'font-weight: bold;'
                row.appendChild(c1);
                for(var i = 0; i < tot_check_in_booking.length; i++){
                    var td = document.createElement("td")
                    var button = document.createElement("button")
                    button.style.cssText = 'cursor:default;border-radius: 8px; background-color: #00cbf5;width: 50px;height: 35px;';
                    var span = document.createElement("span")
                    span.innerText = tot_check_in_booking[i][21]
                    button.appendChild(span)
                    td.appendChild(button)
                    row.appendChild(td);
                }
                table.appendChild(row)
            })
        },

        click_send_mail: function(e) {
			e.preventDefault();
			var self = this;
            var start_date = $('#start_date').val();
            var end_date = $('#end_date').val();
            if (!start_date) {
                start_date = "null"
            }
            if (!end_date) {
                end_date = "null"
            }
			self._rpc({
				model: 'room.availability.dashboard',
				method: 'create_wizard_with_attachment',
				args: [start_date, end_date],
			}).then(function(data) {
				var action = {
                    'name': 'Compose Email',
                    'type': 'ir.actions.act_window',
                    'view_mode': 'form',
                    'res_model': 'mail.compose.message',
                    'views': [[false, 'form']],
                    'view_id': false,
                    'target': 'new',
                    'context': {
                        'default_subject': 'Room Availability Report',
                        'default_body': "Dear All<br/>Kindly find attached room availability report.<br/>Do not hesitate to contact us if you have any questions.<br/><br/>Best regards",
                        'default_attachment_ids': [[6, 0, [data[1]]]],
                    },
                };
				return self.do_action(action);
			});

		},
        click_download_availability: function(e) {
			e.preventDefault();
			var self = this;
			var action_title = self._title;
            var start_date = $('#start_date').val();
            var end_date = $('#end_date').val();
            if (!start_date) {
                start_date = "null"
            }
            if (!end_date) {
                end_date = "null"
            }
			self._rpc({
				model: 'room.availability.dashboard',
				method: 'create_wizard',
				args: [start_date, end_date],
			}).then(function(data) {
				var action = {
					'type': 'ir.actions.report',
					'report_type': 'qweb-pdf',
					'report_name': 'room_availability_dashboard.room_availability_report',
					'report_file': 'room_availability_dashboard.room_availability_report',
					'docids': data,
					'data': {
						'report_data': data,
						'docids': data,
					},
					'context': {
						'active_model': 'room.availability.dashboard',
						'active_id': data,
						'landscape': 1,
						'docids': data,

					},
					'display_name': 'test',
				};
				return self.do_action(action);
			});

		},
        click_view_check_in: function(e){
            e.stopPropagation();
            e.preventDefault();
            var ids = []
            if (e.target.value != null){
                var lst = e.target.value.split(",")
                for(var i = 0; i < lst.length; i++){
                    ids.push(parseInt(lst[i]));
                }
                this.do_action({
                    type: 'ir.actions.act_window',
                    name: 'Check In Bookings',
                    res_model: 'booking.folio',
                    domain: [["id", "in", ids]],
                    context: {
                        search_default_booking: 1,
                        group_by_booking: 1,
                    },
                    views: [[false, 'list'], [false, 'form']],
                    view_mode: 'list,form',
                    target: 'current'
                });
            }
        },
        click_view_arrival: function(e){
            e.stopPropagation();
            e.preventDefault();
            var ids = []
            if (e.target.value != null){
                var lst = e.target.value.split(",")
                for(var i = 0; i < lst.length; i++){
                    ids.push(parseInt(lst[i]));
                }
                this.do_action({
                    type: 'ir.actions.act_window',
                    name: 'Arrival Bookings',
                    res_model: 'booking.folio',
                    domain: [["id", "in", ids]],
                    context: {
                        search_default_booking: 1,
                        group_by_booking: 1,
                    },
                    views: [[false, 'list'], [false, 'form']],
                    view_mode: 'list,form',
                    target: 'current'
                });
            }
        },
        click_view_check_out: function(e){
            e.stopPropagation();
            e.preventDefault();
            var ids = []
            if (e.target.value != null){
                var lst = e.target.value.split(",")
                for(var i = 0; i < lst.length; i++){
                    ids.push(parseInt(lst[i]));
                }
                this.do_action({
                    type: 'ir.actions.act_window',
                    name: 'Check Out Bookings',
                    res_model: 'booking.folio',
                    domain: [["id", "in", ids]],
                    context: {
                        search_default_booking: 1,
                        group_by_booking: 1,
                    },
                    views: [[false, 'list'], [false, 'form']],
                    view_mode: 'list,form',
                    target: 'current'
                });
            }
        },
        click_view_exp_check_out: function(e){
            e.stopPropagation();
            e.preventDefault();
            var ids = []
            if (e.target.value != null){
                var lst = e.target.value.split(",")
                for(var i = 0; i < lst.length; i++){
                    ids.push(parseInt(lst[i]));
                }
                this.do_action({
                    type: 'ir.actions.act_window',
                    name: 'Expected Check Out Bookings',
                    res_model: 'booking.folio',
                    domain: [["id", "in", ids]],
                    context: {
                        search_default_booking: 1,
                        group_by_booking: 1,
                    },
                    views: [[false, 'list'], [false, 'form']],
                    view_mode: 'list,form',
                    target: 'current'
                });
            }
        },
        click_view_booked: function(e){
            e.stopPropagation();
            e.preventDefault();
            var ids = []
            if (e.target.value != null){
                var lst = e.target.value.split(",")
                for(var i = 0; i < lst.length; i++){
                    ids.push(parseInt(lst[i]));
                }
                this.do_action({
                    type: 'ir.actions.act_window',
                    name: 'Booked Rooms',
                    res_model: 'booking.folio',
                    domain: [["id", "in", ids]],
                    context: {
                        search_default_booking: 1,
                        group_by_booking: 1,
                    },
                    views: [[false, 'list'], [false, 'form']],
                    view_mode: 'list,form',
                    target: 'current'
                });
            }
        },
        click_view_exp_booked: function(e){
            e.stopPropagation();
            e.preventDefault();
            var ids = []
            if (e.target.value != null){
                var lst = e.target.value.split(",")
                for(var i = 0; i < lst.length; i++){
                    ids.push(parseInt(lst[i]));
                }
                this.do_action({
                    type: 'ir.actions.act_window',
                    name: 'Expected Booked Rooms',
                    res_model: 'booking.folio',
                    domain: [["id", "in", ids]],
                    context: {
                        search_default_booking: 1,
                        group_by_booking: 1,
                    },
                    views: [[false, 'list'], [false, 'form']],
                    view_mode: 'list,form',
                    target: 'current'
                });
            }
        },
        click_view_cancelled: function(e){
            e.stopPropagation();
            e.preventDefault();
            var ids = []
            if (e.target.value != null){
                var lst = e.target.value.split(",")
                for(var i = 0; i < lst.length; i++){
                    ids.push(parseInt(lst[i]));
                }
                this.do_action({
                    type: 'ir.actions.act_window',
                    name: 'Cancelled Bookings',
                    res_model: 'booking.folio',
                    domain: [["id", "in", ids]],
                    context: {
                        search_default_booking: 1,
                        group_by_booking: 1,
                    },
                    views: [[false, 'list'], [false, 'form']],
                    view_mode: 'list,form',
                    target: 'current'
                });
            }
        },
        click_view_inhouse: function(e){
            e.stopPropagation();
            e.preventDefault();
            var ids = []
            if (e.target.value != null){
                var lst = e.target.value.split(",")
                for(var i = 0; i < lst.length; i++){
                    ids.push(parseInt(lst[i]));
                }
                this.do_action({
                    type: 'ir.actions.act_window',
                    name: 'In-House Bookings',
                    res_model: 'booking.folio',
                    domain: [["id", "in", ids]],
                    context: {
                        search_default_booking: 1,
                        group_by_booking: 1,
                    },
                    views: [[false, 'list'], [false, 'form']],
                    view_mode: 'list,form',
                    target: 'current'
                });
            }
        },
        click_view_exp_inhouse: function(e){
            e.stopPropagation();
            e.preventDefault();
            var ids = []
            if (e.target.value != null){
                var lst = e.target.value.split(",")
                for(var i = 0; i < lst.length; i++){
                    ids.push(parseInt(lst[i]));
                }
                this.do_action({
                    type: 'ir.actions.act_window',
                    name: 'Expected In-House Bookings',
                    res_model: 'booking.folio',
                    domain: [["id", "in", ids]],
                    context: {
                        search_default_booking: 1,
                        group_by_booking: 1,
                    },
                    views: [[false, 'list'], [false, 'form']],
                    view_mode: 'list,form',
                    target: 'current'
                });
            }
        },
        click_view_allotment1: function(e){
            e.stopPropagation();
            e.preventDefault();
            var ids = []
            if (e.target.value != null){
                var lst = e.target.value.split(",")
                for(var i = 0; i < lst.length; i++){
                    ids.push(parseInt(lst[i]));
                }
                this.do_action({
                    type: 'ir.actions.act_window',
                    name: 'Unconfirmed Allotments',
                    res_model: 'booking.folio',
                    domain: [["id", "in", ids]],
                    context: {
                        search_default_booking: 1,
                        group_by_booking: 1,
                    },
                    views: [[false, 'list'], [false, 'form']],
                    view_mode: 'list,form',
                    target: 'current'
                });
            }
        },
        click_view_allotment2: function(e){
            e.stopPropagation();
            e.preventDefault();
            var ids = []
            if (e.target.value != null){
                var lst = e.target.value.split(",")
                for(var i = 0; i < lst.length; i++){
                    ids.push(parseInt(lst[i]));
                }
                this.do_action({
                    type: 'ir.actions.act_window',
                    name: 'Confirmed Allotments',
                    res_model: 'booking.folio',
                    domain: [["id", "in", ids]],
                    context: {
                        search_default_booking: 1,
                        group_by_booking: 1,
                    },
                    views: [[false, 'list'], [false, 'form']],
                    view_mode: 'list,form',
                    target: 'current'
                });
            }
        },
        render_dashboards: function() {
            var self = this;
            _.each(this.dashboards_templates, function(template) {
                self.$('.o_availability_dashboard').append(QWeb.render(template, {
                    widget: self
                }));
            });
        },

        on_reverse_breadcrumb: function() {
            var self = this;
            web_client.do_push_state({});
            this.fetch_data().then(function() {
                self.$('.o_pj_dashboard').empty();
                self.render_dashboards();
                self.render_graphs();
            });
        },

        fetch_data: function() {
            var self = this;
            var def4 = self._rpc({
                    model: "hotel.booking",
                    method: "get_availability_data",
                })
                .then(function(res) {
                    self.days = res['days'];
                    self.company = res['company'];
                });
            return $.when(def4);
        },

    });

    core.action_registry.add('room_availability_dashboard', RoomAvailabilityDashboard);

    return RoomAvailabilityDashboard;

});