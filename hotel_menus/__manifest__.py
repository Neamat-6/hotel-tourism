# -*- coding: utf-8 -*-
{
    'name': "Hotel Menus",

    'summary': "Hotel Menus",

    'description': "Hotel Menus",

    'author': "My Company",
    'website': "http://www.yourcompany.com",
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hotel_booking', 'hotel_booking_folio', 'hotel_booking_folio_extend'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/menus.xml',
        'views/views.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
