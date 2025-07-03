odoo.define('htask_connector.post_charge',function(require) {
    "use strict";

var models = require('point_of_sale.models');
var screens = require('point_of_sale.screens');
var ScreenWidget = screens.ScreenWidget;
var gui = require('point_of_sale.Gui');
var core = require('web.core');
var QWeb = core.qweb;
var PopupWidget = require('point_of_sale.popups');
var ajax = require('web.ajax');
var rpc = require('web.rpc');
var _t  = core._t;
var session = require('web.session');


var PostChargeWidget = PopupWidget.extend({
    template:'PostChargeWidget',

    init: function(parent, options){
        this._super(parent, options);
        this.options = {
            room_no: "",
            folio_no: "",
        };

    },
    show: function(options){
        this._super(options);

    },
    events: {
        'click .button.cancel':  'click_cancel',
        'click .button.confirm': 'click_post',
        'click .get_room': 'get_room_info',
    },

    get_room_info:function(event){
        var self = this;
        const room_no = $(".room_no").val();
        console.log('romezz' , room_no )
        ajax.jsonRpc('/htask/roominfo', 'call', {
            'room_no': room_no,
        }).then(function (result) {
            result = result['response'];

            if (result['status'] == 'ok'){ //success
                const entries = result['roomrows']['row'];
                console.log('self.options ' , self.options , arg)
                self.options.room_no = room_no;
                self.options.folio_no = entries['Folio No.'];

                $('#room-status').html("Room Information");
                let table = $('#room-info-table');
                table.css('display', 'inline-grid');

                let rows = "";
                for (const [key, value] of Object.entries(entries)) {
                    if (!value) { continue;}
                    let tr = "<tr>";
                    tr += "<th>" + key + " :" + "</th>" + "<td>" + value.toString() + "</td></tr>";
                    rows += tr;
                }
                table.html(_t(rows))
            }
            else { // Show error msg
                $('#room-info-table').hide()
                $('#room-status').html(_t(result['msg']));
            }
        }).guardedCatch(function () {
            $('#room-info-table').hide()
            $('#room-status').html(_t('An error occured. Please try again later or contact the hotel management.'));
        });


    },
    click_post: function(options){
        const self = this;

        if (!self.options.room_no){
            alert(_t('Please select a room first!'));
            return;
        }
        const order = this.pos.get_order();
        const cashier = this.pos.get_cashier();
        const pos_config = this.pos.config;
        const tax_details = order.get_tax_details();
        let tax_amount = 0.0;
        if (tax_details.length){
            tax_amount = order.get_tax_details()[0].tax.amount;
        }
        const order_date = new Date();
        const datestring = order_date.getFullYear() + '-' + ((order_date.getMonth() > 8) ? (order_date.getMonth() + 1) : ('0' + (order_date.getMonth() + 1))) + '-' + ((order_date.getDate() > 9) ? order_date.getDate() : ('0' + order_date.getDate()));

        const charge_desc = $('.charge_desc').val();
        const post_comment = $('.post_comment').val();

        if (!charge_desc){
            alert(_t(
                'Please write a description!'
            ));
            return;
        }

        // let table_no = '';
        // if (order.table){
        //     table_no = order.table.name;
        // }
        //
        // ajax.jsonRpc('/htask/postcharge', 'call', {
        //     'room_no': self.options.room_no,
        //     'folio_no': self.options.folio_no,
        //     'table_no': table_no,
        //     'outlet_name': pos_config.name,
        //     'charge_desc': charge_desc,
        //     'post_date': datestring,
        //     'trans_date': datestring,
        //     'total_amount': order.get_total_with_tax(),
        //     'tax_amount': tax_amount,
        //     'gross_amount': order.get_total_without_tax(),
        //     'receipt_no': order.uid,
        //     'comment': post_comment,
        //     'pos_user_name': cashier.name,
        //     'pos_order_id': order.name,
        // }).then(function (result) {
        //     result = result['response'];
        //     if (result['status'] == 'ok'){
        //         alert(_t('Successfully Posted!'));
        //         self.gui.close_popup();
        //     } else {
        //         alert(_t(result['msg']));
        //     }
        // });

    },

    click_cancel: function(){
        this.trigger('close-popup');;
    }

});
gui.define_popup({name:'PostChargeWidget', widget: PostChargeWidget});

screens.PaymentScreenWidget.include({
    finalize_validation: function() {
        var self = this;
        var order = this.pos.get_order();

        const payment_lines = order.get_paymentlines();
        let is_room_post = false;

        for (let l=0; l<payment_lines.length; l++){
            if (payment_lines[l].payment_method.name === "Post Charge to Room"){
                is_room_post = true;
                break;
            }
        }

        if ((order.is_paid_with_cash() || order.get_change()) && this.pos.config.iface_cashdrawer) {

                this.pos.proxy.printer.open_cashbox();
        }

        order.initialize_validation_date();
        order.finalized = true;

        if (order.is_to_invoice()) {
            var invoiced = this.pos.push_and_invoice_order(order);
            this.invoicing = true;

            invoiced.catch(this._handleFailedPushForInvoice.bind(this, order, false));

            invoiced.then(function (server_ids) {
                self.invoicing = false;
                var post_push_promise = [];
                post_push_promise = self.post_push_order_resolve(order, server_ids);
                post_push_promise.then(function () {
                        self.gui.show_screen('receipt');
                        if(is_room_post){
                            self.gui.show_popup('PostChargeWidget', {});
                        }
                }).catch(function (error) {
                    self.gui.show_screen('receipt');
                    if(is_room_post){
                        self.gui.show_popup('PostChargeWidget', {});
                    }
                    if (error) {
                        self.gui.show_popup('error',{
                            'title': "Error: no internet connection",
                            'body':  error,
                        });
                    }
                });
            });
        } else {
            var ordered = this.pos.push_order(order);
            if (order.wait_for_push_order()){
                var server_ids = [];
                ordered.then(function (ids) {
                  server_ids = ids;
                }).finally(function() {
                    var post_push_promise = [];
                    post_push_promise = self.post_push_order_resolve(order, server_ids);
                    post_push_promise.then(function () {
                            self.gui.show_screen('receipt');
                            if(is_room_post){
                                self.gui.show_popup('PostChargeWidget', {});
                            }
                        }).catch(function (error) {
                          self.gui.show_screen('receipt');
                          if(is_room_post){
                            self.gui.show_popup('PostChargeWidget', {});
                            }
                          if (error) {
                              self.gui.show_popup('error',{
                                  'title': "Error: no internet connection",
                                  'body':  error,
                              });
                          }
                        });
                  });
            }
            else {
              self.gui.show_screen('receipt');
              if(is_room_post){
                this.gui.show_popup('PostChargeWidget', {});
                }
            }

        }

    },
});

});
