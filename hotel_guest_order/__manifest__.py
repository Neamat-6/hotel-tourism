# -*- coding: utf-8 -*-
{
    'name': "Hotel Guest Order",

    'summary': "Hotel Guest Order",

    'description': "Hotel Guest Order",

    'author': "My Company",
    'website': "http://www.yourcompany.com",
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hotel_booking'],
    'external_dependencies': {
        'python': ['firebase-admin'],
    },

    # always loaded
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/product_template.xml',
        'views/res_users.xml',
        'views/guest_order.xml',
        'data/cron.xml',
        'data/ir_sequence.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
