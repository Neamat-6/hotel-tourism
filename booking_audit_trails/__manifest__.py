# -*- coding: utf-8 -*-
{
    'name': "Booking Audit Trails",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': 'Hotels Task',
    'website': "https://www.hotelstask.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hotel_booking_folio'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/hotel_booking.xml',
        'views/hotel_room.xml',
        'views/audit_trails.xml',
        'wizards/audit_trails_report.xml',
        'reports/audit_trails.xml',
        'reports/audit_trails_xlsx.xml',
        'reports/folio_report.xml',
    ],
}
