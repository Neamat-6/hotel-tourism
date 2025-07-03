# -*- coding: utf-8 -*-
{
    'name': "Room Availability Dashboard",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': 'Hotels Task',
    'website': "https://www.hotelstask.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hotel_booking', 'hotel_room_availability', 'hotel_booking_folio'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/res_groups.xml',
        'views/menu.xml',
        'reports/room_availability.xml',
        'wizards/room_availability.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'room_availability_dashboard/static/src/css/lib/nv.d3.css',
            # 'room_availability_dashboard/static/src/css/dashboard.css',
            "room_availability_dashboard/static/src/js/dashboard.js",
            "room_availability_dashboard/static/src/js/roomGanttDashboard.js",
            'room_availability_dashboard/static/src/js/lib/d3.min.js',
            'https://cdnjs.cloudflare.com/ajax/libs/Chart.js/2.8.0/Chart.bundle.js',
        ],
        'web.assets_qweb': [
            'room_availability_dashboard/static/src/xml/dashboard.xml',
            # 'room_availability_dashboard/static/src/xml/room_gantt_dashboard.xml',

        ],
    },

}
