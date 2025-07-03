from odoo import fields, models, api


class PosOrder(models.Model):
    _inherit = "pos.order"

    pos_config_sequence = fields.Char(
        string="POS Sequence",
        help="This field stores the sequence number of the order.",
    )


    @api.model
    def _order_fields(self, ui_order):
        order_fields = super(PosOrder, self)._order_fields(ui_order)
        order_fields['pos_config_sequence'] = ui_order.get('pos_config_sequence', False)
        return order_fields
