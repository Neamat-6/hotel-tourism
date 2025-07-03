# -*- coding: utf-8 -*-
{
    'name': "Ezee Connector",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Ahmed Elgamal",

    'category': 'Uncategorized',
    'version': '0.1',

    'depends': ['base', 'hotel_booking', 'hotel_booking_folio', 'booking_audit_trails', 'ntmp_connector'],

    'data': [
        'security/ir.model.access.csv',
        'security/rules.xml',
        'views/hotel.xml',
        'views/hotel_booking.xml',
        'views/hotel_room_type.xml',
        'views/hotel_rate_plan.xml',
        'views/hotel_rate_type.xml',
        'views/ezee_extra_charge.xml',
        'views/ezee_room_type.xml',
        'views/ezee_rate_type.xml',
        'views/ezee_rate_plan.xml',
        'views/hotel_services.xml',
        'views/audit_trail.xml',
        'wizards/ezee_connector.xml',
        'wizards/folio_filter.xml',
        'wizards/ezee_booking_wizard.xml',
        'data/cron.xml',
    ],
}
