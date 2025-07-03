# -*- coding: utf-8 -*-
{
    'name': "Ezee Api",
    'summary': "Ezee Api",
    'description': """Ezee Api""",
    'author': "Ahmed Gaber",
    'website': "https://www.yourcompany.com",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['base', 'account'],
    'data': [
        'security/ir.model.access.csv',
        # 'data/cron.xml',
        'views/product.xml',
        'views/account_move.xml',
        'wizards/create_ezee_invoice.xml',
    ],
}

