odoo.define('htask_connector.post_charge', function (require) {
    "use strict";
    const PosComponent = require('point_of_sale.PosComponent');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const {useListener} = require('web.custom_hooks');
    const Registries = require('point_of_sale.Registries');
    var ajax = require('web.ajax');
    var core = require('web.core');
    var _t = core._t;


    class PostChargeWidget extends PosComponent {
        constructor() {
            super(...arguments);
            useListener('click-post', this.confirm);
            useListener('click-get_room', this.get_room_info);
            useListener('close-this-popup', this.cancel);
        }

        get_room_info() {
            var self = this;
            const room_no = $(".room_no").val();
            console.log('romezz', room_no)

            ajax.jsonRpc('/htask/roominfo', 'call', {
                'room_no': room_no,
            }).then(function (result) {
                result = result['response'];

                if (result['status'] == 'ok') { //success
                    const entries = result['roomrows']['row'];

                    self.room_no = room_no;

                    self.folio_no = entries['Folio No.'];
                    console.log(' self.options', self.room_no, self.options, arguments, entries['Folio No.'])


                    $('#room-status').html("Room Information");
                    let table = $('#room-info-table');
                    table.css('display', 'inline-grid');

                    let rows = "";
                    for (const [key, value] of Object.entries(entries)) {
                        if (!value) {
                            continue;
                        }
                        let tr = "<tr>";
                        tr += "<th>" + key + " :" + "</th>" + "<td>" + value.toString() + "</td></tr>";
                        rows += tr;
                    }
                    table.html(_t(rows))
                } else { // Show error msg
                    $('#room-info-table').hide()
                    $('#room-status').html(_t(result['msg']));
                }
            }).guardedCatch(function () {
                $('#room-info-table').hide()
                $('#room-status').html(_t('An error occured. Please try again later or contact the hotel management.'));
            });


        }

        cancel() {
            var self = this;
            this.trigger('close-popup');
        }

        confirm(event) {
            var self = this;
            if (!self.room_no) {
                alert(_t('Please select a room first!'));
                return;
            }
            const order = this.env.pos.get_order();
            const cashier = this.env.pos.get_cashier();
            const pos_config = this.env.pos.config;
            const tax_details = order.get_tax_details();
            let tax_amount = 0.0;
            if (tax_details.length) {
                tax_amount = order.get_tax_details()[0].amount;
            }
            const order_date = new Date();
            const datestring = order_date.getFullYear() + '-' + ((order_date.getMonth() > 8) ? (order_date.getMonth() + 1) : ('0' + (order_date.getMonth() + 1))) + '-' + ((order_date.getDate() > 9) ? order_date.getDate() : ('0' + order_date.getDate()));

            const charge_desc = $('.charge_desc').val();
            const post_comment = $('.post_comment').val();

            if (!charge_desc) {
                alert(_t(
                    'Please write a description!'
                ));
                return;
            }

            let table_no = '';
            if (order.table) {
                table_no = order.table.name;
            }
            order.room_no = self.room_no
            document.getElementById('btn-post').style.display = 'none'
            ajax.jsonRpc('/htask/postcharge', 'call', {
                'room_no': self.room_no,
                'folio_no': self.folio_no,
                'table_no': table_no,
                'outlet_name': pos_config.name,
                'charge_desc': charge_desc,
                'post_date': datestring,
                'trans_date': datestring,
                'total_amount': order.get_total_with_tax(),
                'tax_amount': tax_amount,
                'gross_amount': order.get_total_without_tax(),
                'receipt_no': order.uid,
                'comment': post_comment,
                'pos_user_name': cashier.name,
                'pos_order_id': order.name,
            }).then(function (result) {
                result = result['response'];
                if (result['status'] == 'ok') {
                    self.trigger('close-popup');
                    alert(_t('Successfully Posted!'));
                } else {
                    alert(_t(result['msg']));
                    document.getElementById('btn-post').style.display = 'block'
                }
            });
            this.props.resolve({confirmed: true,})

        }


    }


    PostChargeWidget.template = 'PostChargeWidget';


//confirmText: 'Return',
//        cancelText: 'Cancel',
//        title: 'Confirm ?',
//

//    ProductScreen.addControlButton({
//    component: PostChargeWidget,
//    condition: function() {
//            return true;
//        },
//    });
    Registries.Component.add(PostChargeWidget);

//    return PostChargeWidget;


});
