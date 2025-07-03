odoo.define('pos_room_charge.PaymentScreen', function (require) {
  'use strict';

  const PaymentScreen = require('point_of_sale.PaymentScreen');
  const Registries = require('point_of_sale.Registries');
  const { Gui } = require('point_of_sale.Gui');
  const { _t } = require('web.core');
  const PosRoomChargePaymentScreen = (PaymentScreen) =>
    class extends PaymentScreen {
      /**
       * @override
       */
      addNewPaymentLine({ detail: paymentMethod }) {
        if (paymentMethod.use_for_room_charge) {
          Gui.showPopup("RoomChargePopup", {
            title: _t("Room Charge Products"),
            confirmText: _t("Charge"),
          }).then((result) => {
            if (result.confirmed) {
              super.addNewPaymentLine({ detail: paymentMethod });
            }
          }).catch(() => {
            console.error("RoomChargePopup was dismissed or an error occurred.");
          });
        }
        else {
          super.addNewPaymentLine(...arguments);
        }
      }
    };
  Registries.Component.extend(PaymentScreen, PosRoomChargePaymentScreen);
  return PaymentScreen;
});
