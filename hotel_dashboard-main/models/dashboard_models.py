from odoo import models, fields, api

class HotelDashboard(models.Model):
    _name = 'hotel.dashboard'
    _description = 'Hotel Dashboard'

    @api.model
    def get_total_sales(self):
        # Example: Calculate total sales (adjust the domain as needed)
        sale_orders = self.env['sale.order'].search([('state', '=', 'sale')])
        total_sales = sum(order.amount_total for order in sale_orders)
        return total_sales
