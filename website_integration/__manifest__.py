{
    'name': 'Website Integration',
    'version': '16.0.0',
    'summary': 'Odoo module for website integration',
    'description': """
        This module provides integration with websites.
    """,
    'author': 'Ahmed Elgamal',
    'category': 'Website',
    'depends': ['base', 'contacts', 'hotel_booking', 'hotel_booking_folio'],
    'data': [
        'views/res_users.xml',
        'views/room_type.xml'
    ],
    'images': [],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
