from odoo import fields, models, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_discount = fields.Boolean(default=False, string="Discount")
    is_service_charge = fields.Boolean(default=False, string="Service Charge")
