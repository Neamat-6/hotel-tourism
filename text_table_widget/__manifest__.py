# -*- coding: utf-8 -*-
{
    'name': 'Text Table Widget',
    'version': '15.0.0.1',
    'summary': """
        Text Table Widget
    """,
    'description': """Text Table Widget""",
    'category': 'Extra Tools',
    'author': 'Bisolv Solutions',
    'website': "www.bisolv.com",
    'license': 'AGPL-3',

    'price': 10.0,
    'currency': 'USD',

    'depends': ['base'],

    'data': [],

    'assets': {

        'web.assets_qweb': [
            'text_table_widget/static/src/xml/*.xml',
        ],

        'web.assets_backend': [
            'text_table_widget/static/src/js/widget.js',
        ],
    },

    'demo': [

    ],
    'images': ['static/description/banner.png'],
    'qweb': [],

    'installable': True,
    'auto_install': False,
    'application': False,
}


