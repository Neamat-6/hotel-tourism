# -*- coding: utf-8 -*-
{
    'name': "Umraheasy Connector",

    'summary': """Umraheasy Connector""",

    'description': """
        Umraheasy Connector
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['hotel_booking', 'hotel_booking_folio', 'ntmp_connector', 'booking_audit_trails'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/hotel.xml',
        'views/hotel_booking.xml',
        'views/rate_plan.xml',
        'views/room_type.xml',
        'wizards/umraheasy_connector.xml',
    ],
}
