odoo.define('pos_room_charge.models', function (require) {
    var models = require('point_of_sale.models');

    models.load_fields('pos.payment.method', ['use_for_room_charge']);
    models.load_fields('pos.order', ['hotel_room_id']);
    var _super_Order = models.Order.prototype;

    models.Order = models.Order.extend({

        constructor: function (attributes, options) {
            _super_Order.constructor.apply(this, arguments);
            this.hotel_room_id = false || this.hotel_room_id;
        },
        export_for_printing: function () {
            var result = _super_Order.export_for_printing.apply(this, arguments);
            result.hotel_room_id = this.hotel_room_id;
            result.hotel_room_name = this.hotel_room_name;

            return result;
        },

        export_as_JSON: function () {
            var json = _super_Order.export_as_JSON.apply(this, arguments);
            json.hotel_room_id = this.hotel_room_id;
            return json;
        },

        init_from_JSON: function (json) {
            _super_Order.init_from_JSON.apply(this, arguments);
            this.hotel_room_id = json.hotel_room_id;
        },
    });
});


