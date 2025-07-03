# -*- coding: utf-8 -*-
{
    'name': "Shomoos Connector",

    'version': '15.0.0',

    'description': "Shomoos Connector enables seamless integration between your hotel management system and Shomoos platform, "
                   "providing streamlined operations and enhanced guest experiences. This module facilitates efficient data synchronization, "
                   "enabling real-time updates of reservations, guest information, and billing details. "
                   "Improve operational efficiency and guest satisfaction with Shomoos Connector.",

    'category': 'Base',

    'author': 'Hotels Task',

    'website': "https://www.hotelstask.com",

    'license': 'AGPL-3',

    'depends': ['base', 'hotel_booking', 'hotel_booking_folio'],

    'data': [
        'security/ir.model.access.csv',
        'data/shomoos.nationality.csv',
        'data/shomoos.country.csv',
        'data/shomoos_identity.xml',
        'data/shomoos_response_code.xml',
        'views/hotel_booking.xml',
        'views/booking_folio.xml',
        'views/shomoos_country.xml',
        'views/shomoos_identity_type.xml',
        'views/res_company.xml',
        'views/res_partner.xml',
        'views/shomoos_nationality.xml',
        'wizard/warning_wizard.xml',
    ],
}
