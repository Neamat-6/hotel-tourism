from odoo import fields, models, api


class PosOrder(models.Model):
    _inherit = "pos.order"

    hotel_room_id = fields.Many2one(
        'hotel.room',
        string='Room No.',
        help="Room number to which the order is linked. "
        "This field is used for room charge functionality.",
    )

    @api.model
    def _order_fields(self, ui_order):
        order_fields = super(PosOrder, self)._order_fields(ui_order)
        order_fields['hotel_room_id'] = ui_order.get('hotel_room_id', False)
        return order_fields


    def force_delete_order(self):
        for order in self:
            order.mapped("payment_ids").unlink()
            order.mapped("lines").unlink()
            order.write({"state": "cancel"})
            for picking in order.picking_ids:
                if picking.has_scrap_move:
                    scraps = self.env["stock.scrap"].search(
                        [("picking_id", "=", picking.id)]
                    )
                    for scrap in scraps:
                        scrap.write({"state": "draft"})
                        lines = self.env["stock.move.line"].search(
                            [("move_id", "=", scrap.move_id.id)]
                        )
                        lines.write({"state": "draft"})
                        lines.unlink()
                        scrap.unlink()
                picking.mapped("move_ids_without_package").write({"state": "draft"})
                picking.mapped("move_ids_without_package").unlink()
                picking.mapped("move_line_ids_without_package").write(
                    {"state": "draft"}
                )
                picking.mapped("move_line_ids_without_package").unlink()
                picking.write({"state": "draft"})
                picking.unlink()
        self.unlink()