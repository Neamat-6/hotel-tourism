# -*- coding: utf-8 -*-
{
    'name': 'Hotel Booking Dashboard',
    'category': 'Productivity',
    'summary': 'Detailed Dashboard View for Hotel Booking',
    'description': 'Detailed Dashboard View for Hotel Booking',
    'version': '15.0.2.0.1',
    'author': 'Hotels Task',
    'website': "https://www.hotelstask.com",
    'license': 'LGPL-3',
    'depends': [
        'base',
        'hotel_booking',
        'hotel_booking_folio',
        'hotel_room_availability',
    ],
    'data': [
        'views/hotel_booking.xml',

    ],
    'images': [
        'static/description/banner.png',
    ],
    'assets': {
        'web.assets_backend': [
            'hotel_booking_dashboard/static/src/css/lib/nv.d3.css',
            # 'hotel_booking_dashboard/static/src/css/dashboard.css',
            "hotel_booking_dashboard/static/src/js/dashboard.js",
            'hotel_booking_dashboard/static/src/js/lib/d3.min.js',
            'https://cdnjs.cloudflare.com/ajax/libs/Chart.js/2.8.0/Chart.bundle.js',
        ],
        'web.assets_qweb': [
            'hotel_booking_dashboard/static/src/xml/dashboard.xml',

        ],
    },

    'installable': True,
    'application': True,
    'auto_install': False,
}
