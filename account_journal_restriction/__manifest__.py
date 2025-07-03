# -*- coding: utf-8 -*-
{
    'name': "Account Journal Restriction",

    'summary': """
        Per User Account Journal Restrictions.""",

    'description': """
        Long description of module's purpose
    """,
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'security/groups.xml',
        'security/record_rules.xml',
        'views/views.xml',
        'views/templates.xml',
    ],
}
