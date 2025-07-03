# -*- coding: utf-8 -*-
{
    'name': 'Hotel Booking Dashboard',
    'version': '1.0',
    'summary': 'Hotel Booking Dashboard',
    'description': """Hotel Booking Dashboard""",
    'author': "Hardik Dhaduk",
    'category': 'CRM',
    'depends': ['base', 'web', 'hotel_booking', 'hotel_booking_folio', 'room_availability_dashboard'],
    'data': [
        'views/sales_dashboard.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'assets': {
        'web.assets_backend': [
            'my_dashboard/static/src/components/**/*.css',
            'my_dashboard/static/src/components/**/*.js'
        ],
        'web.assets_qweb': [
            'my_dashboard/static/src/components/**/*.xml',
        ],
    },
}