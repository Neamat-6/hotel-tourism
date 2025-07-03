from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def delete_product_tax(self):
        print("Deleting product tax", self)
        for rec in self:
            if rec.taxes_id:
                rec.taxes_id = [(6, 0, [])]
