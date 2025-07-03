# -*- coding: utf-8 -*-
{
    'name': "Hotel Booking Pos",

    'summary': "modify payment report to exclude pos payment transactions",

    'description': "modify payment report to exclude pos payment transactions",
    'author': "My Company",
    'website': "http://www.yourcompany.com",
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'point_of_sale', 'hotel_booking_folio', 'cashier_custody', 'standard_daily_sales',
                'pos_discount', 'om_pos_service_charge'],
    'data': [
        'views/product_template.xml',
        'views/report_saledetails.xml',
    ],
    'assets': {
        'point_of_sale.assets': ['hotel_booking_pos/static/**/*', ],
        'web.assets_qweb': ['hotel_booking_pos/static/src/xml/**/*', ],
    },
    "external_dependencies": {
        "python": ["toolz"],
    }
}
