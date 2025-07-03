# -*- coding: utf-8 -*-
{
    'name': "Service Charge Egypt",

    'summary': "Service charge instead of Municipality",
    'description': "Service charge instead of Municipality",
    'author': "My Company",
    'website': "http://www.yourcompany.com",
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hotel_booking_folio'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/booking_folio.xml',
        'reports/booking_report.xml',
        'reports/daily_revenue.xml',
        'reports/revenue_summary.xml',
        'wizards/folio_service.xml',
    ],
}
