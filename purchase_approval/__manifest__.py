# -*- coding: utf-8 -*-
{
    'name': "Purchase Approval",
    'summary': "Need Two Level Approval for Purchase Order to confirm the Purchase Order",
    'description': "Need Two Level Approval for Purchase Order to confirm the Purchase Order",
    'author': 'Hotels Task',
    'website': "https://www.hotelstask.com",
    'category': 'purchase',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'purchase'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'security/data.xml',
        'views/views.xml',
        'views/templates.xml',
    ]
}
