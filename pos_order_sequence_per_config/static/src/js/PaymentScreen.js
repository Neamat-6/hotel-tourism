odoo.define('pos_order_sequence_per_config.PaymentScreen', function (require) {
    'use strict';

    const PaymentScreen = require('point_of_sale.PaymentScreen');
    const Registries = require('point_of_sale.Registries');
    const PosOrderSequence = (PaymentScreen) =>
        class extends PaymentScreen {

            /**
             * Finish any pending input before trying to validate.
             *
             * @override
             */
            async validateOrder(isForceValidate) {
                const order = this.env.pos.get_order();
                const resutl = await this.env.pos.rpc({
                    model: 'pos.config',
                    method: 'get_next_pos_config_sequence',
                    args: [this.env.pos.config.id],
                })
                order.pos_config_sequence = resutl;
                return super.validateOrder(...arguments);
            }
        }

    Registries.Component.extend(PaymentScreen, PosOrderSequence);

    return PaymentScreen;
});
