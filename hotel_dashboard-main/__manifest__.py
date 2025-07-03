# -*- coding: utf-8 -*-
{
    'name': 'Hotel Dashboard',
    'version': '1.0',
    'summary': 'Custom Dashboard for Hotel Management',

    'author': "Majid Saqr",
    'website': "http://www.yourcompany.com",

    'category': 'Tools',
    'sequence': '-500',

    # any module necessary for this one to work correctly
    'depends': ['base', 'web'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/menu.xml',
        'views/dashboard_views.xml',
        'views/views.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],

    'assets': {
        'web.assets_frontend': [
            '/hotel_dashboard/static/src/xml/custom_dashboard_assets.xml',
        ],
    },

    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
