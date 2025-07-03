# -*- coding: utf-8 -*-
{
    'name': "NTMP Connector",

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
    'depends': ['base', 'hotel_booking', 'hotel_booking_folio', 'booking_audit_trails'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/ntmp.nationality.csv',
        'data/ntmp_visit_purpose.xml',
        'data/ntmp_payment_type.xml',
        'data/ntmp_gender.xml',
        'data/ntmp_customer_type.xml',
        'data/ntmp_room_type.xml',
        'data/ntmp_transaction_type.xml',
        'data/ntmp_rent_type.xml',
        'data/ntmp_expense_type.xml',
        'data/ntmp_cancel_reason.xml',
        'data/ntmp_response_code.xml',
        'views/res_company.xml',
        'views/booking_folio.xml',
        'views/ntmp_nationality.xml',
        'views/ntmp_visit_purpose.xml',
        'views/ntmp_payment_type.xml',
        'views/ntmp_gender.xml',
        'views/ntmp_customer_type.xml',
        'views/ntmp_room_type.xml',
        'views/ntmp_transaction_type.xml',
        'views/ntmp_rent_type.xml',
        'views/ntmp_expense_type.xml',
        'views/ntmp_cancel_reason.xml',
        'views/ntmp_response_code.xml',
        'views/room_type.xml',
        'views/hotel_services.xml',
        'wizards/folio_cancel.xml',
        'wizards/folio_service.xml',
    ],
}
