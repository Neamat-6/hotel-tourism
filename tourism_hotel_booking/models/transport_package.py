from odoo import models, fields


class HotelTransportPackage(models.Model):
    _name="hotel.transport.package"
    _description="Transportation Package"


    name = fields.Char(string="Package Name", required=True)
    transport_package_lines = fields.One2many(
        "hotel.transport.package.line", "package_id", string="Transportation Package Line"
    )


class HotelTransportPackageLine(models.Model):
    _name="hotel.transport.package.line"
    _description="Transportation Package Line"


    package_id = fields.Many2one("hotel.transport.package", string="package", required=True, ondelete="cascade")

    # product_id = fields.Many2one("product.product", string="Product", required=True)

    from_destination_id = fields.Many2one("hotel.destination", string="From Destination", required=True)
    to_destination_id = fields.Many2one("hotel.destination", string="To Destination", required=True)