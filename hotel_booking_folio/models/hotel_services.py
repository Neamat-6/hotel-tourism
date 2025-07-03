from odoo import models, fields, api

class HotelServices(models.Model):
    _inherit = 'hotel.services'

    include_taxes = fields.Boolean('Include Taxes')
    tax_ids = fields.Many2many('account.tax', string='Taxes')
    price_include_tax = fields.Float('Price Include Tax',compute='_compute_price_include_tax')

    @api.depends('include_taxes','price','tax_ids')
    def _compute_price_include_tax(self):
        for service in self:
            if service.include_taxes:
                service.price_include_tax = self.price
            else:
                tax_percentage = sum(service.tax_ids.mapped('amount'))/100
                service.price_include_tax = service.price + (service.price * tax_percentage)