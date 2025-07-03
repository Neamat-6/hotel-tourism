# -*- coding: utf-8 -*-
{
    'name': "Aiosell Connector",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['hotel_booking', 'hotel_booking_folio', 'ntmp_connector', 'booking_audit_trails'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/res_company.xml',
        'views/hotel.xml',
        'views/room_type.xml',
        'views/rate_plan.xml',
        'views/hotel_booking.xml',
        'wizards/aiosell_connector.xml',
    ],
}
