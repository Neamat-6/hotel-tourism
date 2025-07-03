from odoo import fields, models, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    name = fields.Char()


class ProductVariant(models.Model):
    _inherit = 'product.product'

    name = fields.Char()
