odoo.define('hotel_booking_pos.models', function (require) {
    var models = require('point_of_sale.models');

    models.load_fields('product.product', ['is_discount']);
    models.load_fields('product.product', ['is_service_charge']);
    var _super_Orderline = models.Orderline.prototype;

    models.Orderline = models.Orderline.extend({

        export_for_printing: function () {
            var result = _super_Orderline.export_for_printing.apply(this, arguments);
            result.is_discount = this.get_product().is_discount;
            result.is_service_charge = this.get_product().is_service_charge;

            return result;
        },
        export_as_JSON: function () {
            var json = _super_Orderline.export_as_JSON.apply(this, arguments);
                json.is_discount = this.get_product().is_discount;
                json.is_service_charge = this.get_product().is_service_charge;
            console.log('jsonnnnnnnnnnnnn',json)
            return json;
        },

    });
});


