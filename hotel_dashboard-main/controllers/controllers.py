from odoo import http
from odoo.http import request

class CustomDashboardController(http.Controller):
    @http.route('/custom_dashboard', type='http', auth='user', website=True)
    def display_dashboard(self):
        dashboard_model = request.env['hotel.dashboard']
        total_sales = dashboard_model.get_total_sales()
        return request.render('hotel_dashboard.custom_dashboard_template', {
            'total_sales': total_sales,
        })
