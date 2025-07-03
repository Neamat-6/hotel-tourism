# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Hotel Room Gantt',
    'description': """
                Hotel Room Gantt chart view     
    """,
    'version': '2.0',
    'depends': ['hotel_booking', 'hotel_booking_folio', 'web_gantt'],
    'date': {
        'views/room_view.xml'
    },
    'auto_install': True,
    'license': 'OEEL-1',
}
