# -*- coding: utf-8 -*-
{
    'name': "Account Journals",
    'summary': """
        Changes the coding sequence of the chart of accounts duplicate function into one step instead of 10 .
        """,
    'description': """
        Long description of module's purpose
    """,
    'author': "Ahmed Elgamal",
    'category': 'account',
    'version': '0.1',
    'depends': ['base', 'account'],
    # always loaded
    'data': [
        'data/action_server.xml',
        'views/account_account.xml',
        'views/res_company.xml',
    ],

}
