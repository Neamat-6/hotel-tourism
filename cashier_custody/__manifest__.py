# -*- coding: utf-8 -*-
{
    'name': "Hotel Cashier Custody",
    'summary': "Manage cashiers and their custody in a hotel environment",
    'description': "This module allows you to manage cashiers and their custody in a hotel setting. It provides features for tracking cashier transactions and maintaining custody records.",
    'author': "Ahmed Elgamal",
    'version': "1.0",
    'category': "Hotel Management",

    'depends': ['base', 'account', 'hotel_booking', 'hotel_booking_folio'],

    # always loaded
    'data': [
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        'data/server_action.xml',
        'views/account_journal.xml',
        'views/cashier_custody.xml',
        'reports/cashier_custody.xml',
        'wizards/night_audit_helper.xml',
    ],
}
