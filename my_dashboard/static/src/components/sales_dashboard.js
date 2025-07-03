odoo.define('my_dashboard.HotelBookingDashboard', function (require) {
"use strict";

var AbstractAction = require('web.AbstractAction');
var core = require('web.core');
var QWeb = core.qweb;
var ajax = require('web.ajax');
var rpc = require('web.rpc');
var Dialog = require('web.Dialog');
var _t = core._t;
var QWeb = core.qweb;
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


var HotelBookingDashboard = AbstractAction.extend({
    contentTemplate: 'OwlSalesDashboard',


    events: {
            'click .click-view-check-in': 'click_view_check_in',
            'click .click-view-check-out': 'click_view_check_out',
            'click .click-view-exp-check-out': 'click_view_exp_check_out',
            'click .click-view-booked': 'click_view_booked',
            'click .click-view-exp-booked': 'click_view_exp_booked',
            'click .click-view-cancelled': 'click_view_cancelled',
            'click .click-view-inhouse': 'click_view_inhouse',
            'click .click-view-exp-inhouse': 'click_view_exp_inhouse',
            'change #start_date': '_onchangeFilter',
            'change #end_date': '_onchangeFilter',
        },

    /**
     * @override
     */
    init: function(parent, action) {
        this._super.apply(this, arguments);
        this.dashboards_templates = ['OwlSalesDashboard'];
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
            self._onchangeFilter();
            return this._super().then(function() {
                self.render_dashboards();
            });
        },
        _onchangeFilter: function() {
            flag = 1
            var start_date = $('#start_date').val();
            var end_date = $('#end_date').val();
            var company = $('#company_input').val() || this.company;

            if (!start_date && !end_date) {
                start_date = 'null';
                end_date = 'null';
            }

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
                var table = document.getElementById("nav-tab")
                table.innerHTML = ''
                for(var i = 0; i < tot_check_in_booking.length; i++){
                    var newAnchor = document.createElement('a');
                      // Set the class attribute for the anchor
                      if(i == 0){
                        newAnchor.className = 'nav-item nav-link active btn-outline-success me-2';
                      }else{
                        newAnchor.className = 'nav-item nav-link btn-outline-success me-2';
                      }

                      // Set the ID attribute for the anchor
                      newAnchor.id = 'nav-home-tab-'+i;
                      // Set other attributes for the anchor
                      newAnchor.setAttribute('data-toggle', 'tab');
                      newAnchor.href = '#nav-home-'+i;
                      newAnchor.role = 'tab';
                      newAnchor.textContent = tot_check_in_booking[i][0];
                      newAnchor.setAttribute('aria-controls', 'nav-home-'+i);
                      newAnchor.setAttribute('aria-selected', 'true');
                      var myDiv = document.getElementById("nav-tab");
                      myDiv.appendChild(newAnchor);
                }

                var table_tab = document.getElementById("nav-tabContent")
                table_tab.innerHTML = ''

                function createCard(title, value, progress, iconClass, className) {
                    var card = document.createElement('div');
                    if(className){
                        card.className = className;
                    }else{
                        card.className = 'col-xl-3 col-lg-3';
                    }

                    var innerDiv1 = document.createElement('div');
                    innerDiv1.className = 'card l-bg-cherry';

                    var innerDiv2 = document.createElement('div');
                    innerDiv2.className = 'card-statistic-3 p-4';

                    var innerDiv3 = document.createElement('div');
                    innerDiv3.className = 'mb-4';
                    innerDiv3.appendChild(document.createElement('h5')).className = 'card-title mb-0';
                    innerDiv3.querySelector('h5').appendChild(document.createTextNode(title));

                    var innerDiv4 = document.createElement('div');
                    innerDiv4.className = 'row align-items-center mb-2 d-flex';

                    var innerDiv5 = document.createElement('div');
                    innerDiv5.className = 'col-8';
                    innerDiv5.appendChild(document.createElement('h2')).className = 'd-flex align-items-center mb-0';
                    innerDiv5.querySelector('h2').appendChild(document.createTextNode(value));

                    var innerDiv6 = document.createElement('div');
                    innerDiv6.className = 'col-4';

                    var innerDiv7 = document.createElement('div');
                    innerDiv7.className = 'media-body text-right';
                    innerDiv7.appendChild(document.createElement('i')).className = iconClass;

                    var innerDiv8 = document.createElement('div');
                    if (progress == true){
                        innerDiv8.className = 'progress mt-1';
                        innerDiv8.dataset.height = '8';
                        innerDiv8.style.height = '8px;';
                        innerDiv8.appendChild(document.createElement('div')).className = 'progress-bar l-bg-cyan';
                        innerDiv8.querySelector('.progress-bar').role = 'progressbar';
                        innerDiv8.querySelector('.progress-bar').dataset.width = `${value}%`;
                        innerDiv8.querySelector('.progress-bar').ariaValuenow = `${value}`;
                        innerDiv8.querySelector('.progress-bar').ariaValuemin = '0';
                        innerDiv8.querySelector('.progress-bar').ariaValuemax = '100';
                        innerDiv8.querySelector('.progress-bar').style.width = `${value}%`;
                    }
                    innerDiv4.appendChild(innerDiv5);
                    innerDiv4.appendChild(innerDiv6.appendChild(innerDiv7));
                    innerDiv2.appendChild(innerDiv3);
                    innerDiv2.appendChild(innerDiv4);
                    innerDiv2.appendChild(innerDiv8);
                    innerDiv1.appendChild(innerDiv2);
                    card.appendChild(innerDiv1);

                    return card;
                }


                for(var i = 0; i < tot_check_in_booking.length; i++){
//                      This is first section
                      var new_tab_div = document.createElement('div');
                      if (i==0){
                        new_tab_div.className = 'tab-pane fade show active';
                      }else{
                        new_tab_div.className = 'tab-pane fade show';
                      }

                      new_tab_div.id = 'nav-home-'+i;
                      new_tab_div.setAttribute('role', 'tabpanel');
                      new_tab_div.setAttribute('aria-labelledby', 'nav-home-tab-'+i);
                      // Append the div to the document body or any other container
                      table_tab.appendChild(new_tab_div);


                    var sub_div = document.createElement('div');
                    sub_div.className = 'row mt-5';
                    new_tab_div.appendChild(sub_div);

                    sub_div.appendChild(createCard('متوقع وصول اليوم', tot_check_in_booking[i][2], 0, 'fa fa-arrow-down', 'col-xl-6 col-lg-6 mt-5'));
                    sub_div.appendChild(createCard('الوصول الفعلي', tot_check_in_booking[i][25], 0, 'fa fa-arrow-down', 'col-xl-6 col-lg-6 mt-5'));
                    sub_div.appendChild(createCard('متوقع المغادرة', tot_check_in_booking[i][4], 0, 'fa fa-arrow-up', 'col-xl-6 col-lg-6 mt-5'));
                    sub_div.appendChild(createCard('المغادرة الفعلية', tot_check_in_booking[i][26], 0, 'fa fa-arrow-up', 'col-xl-6 col-lg-6 mt-5'));
                    sub_div.appendChild(createCard('الغرف الساكنة', tot_check_in_booking[i][27], 0, 'fa fa-arrow-up', 'col-xl-6 col-lg-6 mt-5'));
                    sub_div.appendChild(createCard('متوقع الغرف الساكنة', tot_check_in_booking[i][28], 0, 'fa fa-arrow-up', 'col-xl-6 col-lg-6 mt-5'));
                    sub_div.appendChild(createCard('Total Cancelled', tot_check_in_booking[i][11].length, 0, 'fa fa-ban', 'col-xl-6 col-lg-6 mt-5'));
                    sub_div.appendChild(createCard('Total Room', tot_check_in_booking[i][6], 0, 'fa fa-window-restore', 'col-xl-6 col-lg-6 mt-5'));
                    sub_div.appendChild(createCard('(%) Actual Occupancy', tot_check_in_booking[i][29], true, 'fa fa-crosshairs','col-xl-6 col-lg-6 mt-5'));
                    sub_div.appendChild(createCard('(%) Expected Occupancy', tot_check_in_booking[i][30], true, 'fa fa-check','col-xl-6 col-lg-6 mt-5'));

                        // Create the outermost div with class 'row mt-5'
                        var outerBookDiv = document.createElement('div');
                        outerBookDiv.className = 'row mt-5';

                        // Function to create individual cards
                        function createBookCard(colClass, id, value, title, imgSrc) {
                          // Create the column div with specified class
                          var colDiv = document.createElement('div');
                          colDiv.className = colClass;

                          // Create the card div
                          var cardDiv = document.createElement('div');
                          cardDiv.className = 'card';

                          // Create the card content div
                          var cardContentDiv = document.createElement('div');
                          cardContentDiv.className = 'card-content';

                          // Create the card body div
                          var cardBodyDiv = document.createElement('div');
                          cardBodyDiv.className = 'card-body';

                          // Create the media div
                          var mediaDiv = document.createElement('div');
                          mediaDiv.className = 'media d-flex';

                          // Create the media body div for text content on the left
                          var mediaBodyLeftDiv = document.createElement('div');
                          mediaBodyLeftDiv.className = 'media-body text-left';

                          // Create the h3 element with the specified id and value
                          var h3Element = document.createElement('h3');
                          h3Element.className = 'warning';
                          h3Element.id = id;
                          h3Element.appendChild(document.createTextNode(value));

                          // Create the span element with the specified title
                          var spanElement = document.createElement('span');
                          spanElement.appendChild(document.createTextNode(title));

                          // Append h3 and span to the media body left div
                          mediaBodyLeftDiv.appendChild(h3Element);
                          mediaBodyLeftDiv.appendChild(spanElement);

                          // Create the media body div for the image on the right
                          var mediaBodyRightDiv = document.createElement('div');
                          mediaBodyRightDiv.className = 'media-body text-right';

                          // Create the image element with the specified source, width, and height
                          var imgElement = document.createElement('img');
                          imgElement.src = imgSrc;
                          imgElement.width = 80;
                          imgElement.height = 80;
                          imgElement.alt = 'Girl in a jacket';

                          // Append the image to the media body right div
                          mediaBodyRightDiv.appendChild(imgElement);

                          // Append media body left and right to the media div
                          mediaDiv.appendChild(mediaBodyLeftDiv);
                          mediaDiv.appendChild(mediaBodyRightDiv);

                          // Append media div to the card body div
                          cardBodyDiv.appendChild(mediaDiv);

                          // Append card body div to the card content div
                          cardContentDiv.appendChild(cardBodyDiv);

                          // Append card content div to the card div
                          cardDiv.appendChild(cardContentDiv);

                          // Append card div to the column div
                          colDiv.appendChild(cardDiv);

                          return colDiv;
                        }
                        new_tab_div.appendChild(outerBookDiv);



                        // Create the outermost div with class 'row mt-5'
                        var outerPeopleDiv = document.createElement('div');
                        outerPeopleDiv.className = 'row mt-5';

                        // Function to create individual cards
                        function createPeopleCard(colClass, id, value, title, imgSrc) {
                          // Create the column div with specified class
                          var colDiv = document.createElement('div');
                          colDiv.className = colClass;

                          // Create the card div
                          var cardDiv = document.createElement('div');
                          cardDiv.className = 'card';

                          // Create the card content div
                          var cardContentDiv = document.createElement('div');
                          cardContentDiv.className = 'card-content';

                          // Create the card body div
                          var cardBodyDiv = document.createElement('div');
                          cardBodyDiv.className = 'card-body';

                          // Create the media div
                          var mediaDiv = document.createElement('div');
                          mediaDiv.className = 'media d-flex';

                          // Create the media body div for text content on the left
                          var mediaBodyLeftDiv = document.createElement('div');
                          mediaBodyLeftDiv.className = 'media-body text-left';

                          // Create the h3 element with the specified id and value
                          var h3Element = document.createElement('h3');
                          h3Element.className = 'warning';
                          h3Element.id = id;
                          h3Element.appendChild(document.createTextNode(value));

                          // Create the span element with the specified title
                          var spanElement = document.createElement('span');
                          spanElement.appendChild(document.createTextNode(title));

                          // Append h3 and span to the media body left div
                          mediaBodyLeftDiv.appendChild(h3Element);
                          mediaBodyLeftDiv.appendChild(spanElement);

                          // Create the media body div for the image on the right
                          var mediaBodyRightDiv = document.createElement('div');
                          mediaBodyRightDiv.className = 'media-body text-right';

                          // Create the image element with the specified source, width, and height
                          var imgElement = document.createElement('img');
                          imgElement.src = imgSrc;
                          imgElement.width = 80;
                          imgElement.height = 80;
                          imgElement.alt = 'Girl in a jacket';

                          // Append the image to the media body right div
                          mediaBodyRightDiv.appendChild(imgElement);

                          // Append media body left and right to the media div
                          mediaDiv.appendChild(mediaBodyLeftDiv);
                          mediaDiv.appendChild(mediaBodyRightDiv);

                          // Append media div to the card body div
                          cardBodyDiv.appendChild(mediaDiv);

                          // Append card body div to the card content div
                          cardContentDiv.appendChild(cardBodyDiv);

                          // Append card content div to the card div
                          cardDiv.appendChild(cardContentDiv);

                          // Append card div to the column div
                          colDiv.appendChild(cardDiv);

                          return colDiv;
                        }

                        new_tab_div.appendChild(outerPeopleDiv);


                        var outerDiv = document.createElement('div');
                        outerDiv.className = 'row mt-5';
                        var innerDiv1 = document.createElement('div');
                        innerDiv1.className = 'col-xl-12 col-md-12';
                        var innerDiv2 = document.createElement('div');
                        innerDiv2.className = 'card overflow-hidden';
                        var innerDiv3 = document.createElement('div');
                        innerDiv3.className = 'card-content';
                        var innerDiv4 = document.createElement('div');
                        innerDiv4.className = 'card-body clearfix';
                        var innerDiv5 = document.createElement('div');
                        innerDiv5.className = 'media align-items-stretch';
                        var innerDiv6 = document.createElement('div');
                        innerDiv6.className = 'text-center';
                        var h1Element = document.createElement('h1');
                        h1Element.appendChild(document.createTextNode('Room Available'));
                        innerDiv6.appendChild(h1Element);
                        innerDiv5.appendChild(innerDiv6);
                        innerDiv4.appendChild(innerDiv5);
                        innerDiv3.appendChild(innerDiv4);
                        innerDiv2.appendChild(innerDiv3);
                        innerDiv1.appendChild(innerDiv2);
                        outerDiv.appendChild(innerDiv1);

                        new_tab_div.appendChild(outerDiv);

                        var outerRoomAvailableDiv = document.createElement('div');
                        outerRoomAvailableDiv.className = 'row mt-5';
                        outerRoomAvailableDiv.appendChild(createBookCard('col-xl-3 col-sm-6 col-12', 'total_rooms_avail', tot_check_in_booking[i][6], 'Total Rooms', '/my_dashboard/static/src/img/13.png'));
                        outerRoomAvailableDiv.appendChild(createBookCard('col-xl-3 col-sm-6 col-12', 'total_actual_booked_rooms', tot_check_in_booking[i][14].length, 'Actual Booked Rooms', '/my_dashboard/static/src/img/14.png'));
                        outerRoomAvailableDiv.appendChild(createBookCard('col-xl-3 col-sm-6 col-12', 'total_exp_booked_rooms', tot_check_in_booking[i][22].length,'Expected Booked Rooms' , '/my_dashboard/static/src/img/17.png'));
                        outerRoomAvailableDiv.appendChild(createBookCard('col-xl-3 col-sm-6 col-12', 'actual_avail_rooms', tot_check_in_booking[i][8], 'Actual Available Rooms', '/my_dashboard/static/src/img/9.png'));
                        outerRoomAvailableDiv.appendChild(createBookCard('col-xl-3 col-sm-6 col-12 mt-5', 'exp_avail_rooms', tot_check_in_booking[i][20], 'Expected Available Rooms', '/my_dashboard/static/src/img/4.png'));

                        new_tab_div.appendChild(outerRoomAvailableDiv);



                }



            })
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
//            var def1 = this._rpc({
//                model: 'project.project',
//                method: 'get_tiles_data'
//            }).then(function(result) {
//                self.total_projects = result['total_projects'],
//                    self.total_tasks = result['total_tasks'],
//                    self.total_hours = result['total_hours'],
//                    self.total_profitability = result['total_profitability'],
//                    self.total_employees = result['total_employees'],
//                    self.total_sale_orders = result['total_sale_orders'],
//                    self.project_stage_list = result['project_stage_list']
//                tot_so = result['sale_list']
//            });
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

core.action_registry.add('my_dashboard.hotel_booking_dashboard', HotelBookingDashboard);

return HotelBookingDashboard;

});
