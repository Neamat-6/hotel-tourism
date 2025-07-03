# -*- coding: utf-8 -*-
{
    'name': "Hotel User Role",

    'summary': "Hotel User Role",

    'description': "Hotel User Role",

    'author': "My Company",
    'website': "http://www.yourcompany.com",
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hotel_booking', 'hotel_booking_folio', 'sh_whatsapp_integration_api', 'account',
                'point_of_sale', 'hr', 'sales_team', 'stock', 'purchase', 'om_fiscal_year', 'analytic',
                'product', 'mail', 'ks_curved_backend_theme', 'room_availability_dashboard'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/res_users.xml',
    ],
}
