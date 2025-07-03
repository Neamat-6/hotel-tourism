odoo.define('my_dashboard.HotelBookingInternalDashboard', function (require) {
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
var data = []
var tot_so = []
var tot_project = []
var tot_task = []
var tot_employee = []
var tot_hrs = []
var tot_margin = []


var HotelBookingInternalDashboard = AbstractAction.extend({
    contentTemplate: 'InternalDashboard',
    events: {
            'change #start_date': '_onchangeFilter',
            'change #end_date': '_onchangeFilter',
            'click .click-view-total-rooms': 'click_view_total_rooms',
            'click .click-view-total-ooo-rooms': 'click_view_total_ooo_rooms',
            'click .click-view-net-total-rooms': 'click_view_net_total_rooms',
            'click .click-view-stay-over-rooms': 'click_view_stay_over_rooms',
            'click .click-view-due-out-rooms': 'click_view_due_out_rooms',
            'click .click-view-checked-out-vacant-rooms': 'click_view_checked_out_vacant_rooms',
            'click .click-view-dirty-rooms': 'click_view_dirty_rooms',
            'click .click-view-dirty-vacant-rooms': 'click_view_dirty_vacant_rooms',
            'click .click-view-clean-vacant-rooms': 'click_view_clean_vacant_rooms',
            'click .click-view-assigned-rooms': 'click_view_assigned_rooms',
        },
    /**
     * @override
     */
    init: function(parent, action) {
        this._super.apply(this, arguments);
        this.dashboards_templates = ['InternalDashboard'];
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
        return this._super()
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
        ajax.rpc('/internal-dashboard/filter-apply', {
            'data': {
                'start_date': start_date,
                'end_date': end_date,
                'company': company,
            }
        }).then(function(result) {
            data = result['data']
            var table = document.getElementById("nav-tab")
            table.innerHTML = ''
            for(var i = 0; i < data.length; i++){
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
                newAnchor.textContent = data[i][0];
                newAnchor.setAttribute('aria-controls', 'nav-home-'+i);
                newAnchor.setAttribute('aria-selected', 'true');
                var myDiv = document.getElementById("nav-tab");
                myDiv.appendChild(newAnchor);
            }
            var table_tab = document.getElementById("nav-tabContent")
            table_tab.innerHTML = ''

            function createCard(title, value, progress, redirectClass, iconClass, className) {
                progress = progress.toFixed(2)
                var card = document.createElement('div');
                if(className){
                    card.className = `${className} ${redirectClass}`;
                }else{
                    card.className = `col-xl-4 col-lg-4 ${redirectClass}`;
                }

                var innerDiv1 = document.createElement('div');
                innerDiv1.className = 'card l-bg-cherry';

                var innerDiv2 = document.createElement('div');
                innerDiv2.className = 'card-statistic-4 p-4';

                var innerDiv3 = document.createElement('div');
                innerDiv3.className = 'mb-4';
                innerDiv3.appendChild(document.createElement('h5')).className = 'card-title mb-0';
                innerDiv3.querySelector('h5').appendChild(document.createTextNode(title));

                var innerDiv4 = document.createElement('div');
                innerDiv4.className = 'row align-items-center mb-2 d-flex';

                var innerDiv5 = document.createElement('div');
                innerDiv5.className = 'col-8';
                innerDiv5.appendChild(document.createElement('h2')).className = 'd-flex align-items-center mb-0';
                innerDiv5.querySelector('h2').appendChild(document.createTextNode(value.length));

                var innerDiv6 = document.createElement('div');
                innerDiv6.className = 'col-4';

                var innerDiv7 = document.createElement('button');
                innerDiv7.setAttribute('value', value);
                innerDiv7.innerText = 'Open '
                innerDiv7.appendChild(document.createElement('i')).className = iconClass;

                var innerDiv8 = document.createElement('div');
                innerDiv8.className = 'progress mt-1';
                innerDiv8.dataset.height = '8';
                innerDiv8.style.height = '8px;';
                innerDiv8.appendChild(document.createElement('div')).className = 'progress-bar l-bg-cyan';
                innerDiv8.querySelector('.progress-bar').role = 'progressbar';
                innerDiv8.querySelector('.progress-bar').dataset.width = `${progress}%`;
                innerDiv8.querySelector('.progress-bar').ariaValuenow = `${progress}`;
                innerDiv8.querySelector('.progress-bar').ariaValuemin = '0';
                innerDiv8.querySelector('.progress-bar').ariaValuemax = '100';
                innerDiv8.querySelector('.progress-bar').style.width = `${progress}%`;
                innerDiv8.querySelector('.progress-bar').innerText = `${progress}%`;

                innerDiv4.appendChild(innerDiv5);
                innerDiv4.appendChild(innerDiv6.appendChild(innerDiv7));
                innerDiv2.appendChild(innerDiv3);
                innerDiv2.appendChild(innerDiv4);
                innerDiv2.appendChild(innerDiv8);
                innerDiv1.appendChild(innerDiv2);
                card.appendChild(innerDiv1);

                return card;
            }
            for(var i = 0; i < data.length; i++){
                //This is first section
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
                var total_rooms = data[i][1].length
                sub_div.appendChild(createCard('اجمالي عدد الغرف', data[i][1], 100, 'click-view-total-rooms', 'fa fa-arrow-right'));
                sub_div.appendChild(createCard('الغرف خارج الخدمة', data[i][2], 100*(data[i][2].length/total_rooms), 'click-view-total-ooo-rooms', 'fa fa-arrow-right'));
                sub_div.appendChild(createCard('اجمالي الغرف المتاحة', data[i][3], 100*(data[i][3].length/total_rooms), 'click-view-net-total-rooms', 'fa fa-arrow-right'));
                sub_div.appendChild(createCard('الغرف الساكنة', data[i][4], 100*(data[i][4].length/total_rooms), 'click-view-stay-over-rooms', 'fa fa-arrow-right'));
                sub_div.appendChild(createCard('الغرف المتوقع مغادرتها', data[i][5], 100*(data[i][5].length/total_rooms), 'click-view-due-out-rooms', 'fa fa-arrow-right'));
                sub_div.appendChild(createCard('الغرف المغادرة فعليا', data[i][6], 100*(data[i][6].length/total_rooms), 'click-view-checked-out-vacant-rooms', 'fa fa-arrow-right'));
                sub_div.appendChild(createCard('الغرف الساكنة غير نظيفة', data[i][7], 100*(data[i][7].length/total_rooms), 'click-view-dirty-rooms', 'fa fa-arrow-right'));
                sub_div.appendChild(createCard('الغرف الشاغرة غير نظيفة', data[i][8], 100*(data[i][8].length/total_rooms), 'click-view-dirty-vacant-rooms', 'fa fa-arrow-right'));
                sub_div.appendChild(createCard('الغرف الشاغرة النظيفة', data[i][9], 100*(data[i][9].length/total_rooms), 'click-view-clean-vacant-rooms', 'fa fa-arrow-right'));
                sub_div.appendChild(createCard('الغرف المخصصة', data[i][10], 100*(data[i][10].length/total_rooms), 'click-view-assigned-rooms', 'fa fa-arrow-right'));
                // Create the outermost div with class 'row mt-5'
                var outerBookDiv = document.createElement('div');
                outerBookDiv.className = 'row mt-5';
                // Create the outermost div with class 'row mt-5'
                var outerPeopleDiv = document.createElement('div');
                outerPeopleDiv.className = 'row mt-5';
            }
        })
    },
    fetch_data: function() {
        var self = this;
        var result = self._rpc({
            model: "hotel.booking",
            method: "get_availability_company",
        }).then(function(res) {
            self.company = res['company'];
        });
        return $.when(result);
    },
    async redirect_action(e, name){
        e.stopPropagation();
        e.preventDefault();
        var self = this;
        const view_id = await this._rpc({
            model: 'hotel.booking',
            method : 'get_kanban_view',
        });
        var ids = []
        if (e.target.value != null){
            var lst = e.target.value.split(",")
            for(var i = 0; i < lst.length; i++){
                ids.push(parseInt(lst[i]));
            }
            this.do_action({
                type: 'ir.actions.act_window',
                name: name,
                res_model: 'hotel.room',
                domain: [["id", "in", ids]],
                view_id: view_id,
                views: [[view_id, 'kanban']],
                target: 'current'
            });
        }
    },
    click_view_total_rooms: function(e){
        this.redirect_action(e, 'اجمالي عدد الغرف')
    },
    click_view_total_ooo_rooms: function(e){
        this.redirect_action(e, 'الغرف خارج الخدمة')
    },
    click_view_net_total_rooms: function(e){
        this.redirect_action(e, 'اجمالي الغرف المتاحة')
    },
    click_view_stay_over_rooms: function(e){
        this.redirect_action(e, 'الغرف الساكنة')
    },
    click_view_due_out_rooms: function(e){
        this.redirect_action(e, 'الغرف المتوقع مغادرتها')
    },
    click_view_checked_out_vacant_rooms: function(e){
        this.redirect_action(e, 'الغرف المغادرة فعليا')
    },
    click_view_dirty_rooms: function(e){
        this.redirect_action(e, 'الغرف الساكنة غير نظيفة')
    },
    click_view_dirty_vacant_rooms: function(e){
        this.redirect_action(e, 'الغرف الشاغرة غير نظيفة')
    },
    click_view_clean_vacant_rooms: function(e){
        this.redirect_action(e, 'الغرف الشاغرة النظيفة')
    },
    click_view_assigned_rooms: function(e){
        this.redirect_action(e, 'الغرف المخصصة')
    },
});

core.action_registry.add('my_dashboard.hotel_booking_internal_dashboard', HotelBookingInternalDashboard);

return HotelBookingInternalDashboard;

});
