odoo.define('pos_order_sequence_per_config.models', function (require) {
    var models = require('point_of_sale.models');
    models.load_fields('pos.order', ['pos_config_sequence']);
    models.load_fields('pos.config', ['pos_sequence_id']);
    var _super_Order = models.Order.prototype;

    models.Order = models.Order.extend({
        initialize: function (attributes, options) {
            _super_Order.initialize.apply(this, arguments);
            this.pos_config_sequence = false || this.pos_config_sequence;
        },

        export_for_printing: function () {
            var result = _super_Order.export_for_printing.apply(this, arguments);
            result.pos_config_sequence = this.pos_config_sequence;
            return result;
        },

        export_as_JSON: function () {
            var json = _super_Order.export_as_JSON.apply(this, arguments);
            json.pos_config_sequence = this.pos_config_sequence;
            return json;
        },

        init_from_JSON: function (json) {
            _super_Order.init_from_JSON.apply(this, arguments);
            this.pos_config_sequence = json.pos_config_sequence;
        },

    });



});
