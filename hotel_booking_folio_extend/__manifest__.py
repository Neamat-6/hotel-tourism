# -*- coding: utf-8 -*-
{
    'name': "hotel_booking_folio_extend",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",
    'category': 'Uncategorized',
    'version': '0.1',

    'depends': ['base', 'hotel_booking_folio'],

    'data': [
        'security/ir.model.access.csv',
        'wizards/folio_manual_assign.xml',
    ],
}
