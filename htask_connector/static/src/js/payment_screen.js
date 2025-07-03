odoo.define("htask_connector.PaymentScreen", function (require) {
    "use strict";

    const Registries = require("point_of_sale.Registries");
    const PaymentScreen = require("point_of_sale.PaymentScreen");



    const PosPaymentScreen = (PaymentScreen) =>
        class extends PaymentScreen {
              async _finalizeValidation() {
                      var self = this;
                      var order = this.env.pos.get_order();
                const payment_lines = order.get_paymentlines();
                let is_room_post = false;
            if (this.currentOrder.get_due() < 0) {
                this.showPopup('ErrorPopup', {
                    title: this.env._t('Warning'),
                    body: this.env._t(
                        'You exceeded the total amount of receipt.'
                    ),
                });
                return false;
            }
            for (let l=0; l<payment_lines.length; l++){
                if (payment_lines[l].payment_method.name === "Post Charge to Room"){
                    is_room_post = true;
                    break;
                }
            }
               if(is_room_post){
               console.log('zenaaaaaddd'  )
                 const { confirmed,} = await  self.showPopup('PostChargeWidget', {});
                console.log('zenaaaaa' , confirmed )
                if(confirmed){
                     super._finalizeValidation();

                    }
                    else{
                return ;
                }
                        }
                else{
                await super._finalizeValidation();
                }

        }

        };

    Registries.Component.extend(PaymentScreen, PosPaymentScreen);
});