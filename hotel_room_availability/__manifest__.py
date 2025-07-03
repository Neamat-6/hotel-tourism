{
    'name': 'Hotel Room Availability and Rate Plan',
    'summary': 'Manage Hotel available room',
    'version': '15.0.0.0',
    'description': '''This module helps Hotel to manage  available rooms''',
    'author': 'Hotels Task',
    'website': "https://www.hotelstask.com",
    'license': 'AGPL-3',
    'depends': ['hotel_booking', 'hotel_booking_folio'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/hotel_room_availability_current.xml',
        'wizard/update_available_room_view.xml',
        'wizard/update_room_pricelist_view.xml',
        'wizard/update_rate_plan.xml',
        'wizard/update_room_state.xml',
        'views/hotel_room_availability_view.xml',
        'reports/room_type_inventory.xml',
    ],
    "assets": {
        "web.assets_backend": [
            '/hotel_room_availability/static/src/js/room_availability.js',
            '/hotel_room_availability/static/src/js/room_type_availability.js',
            # '/hotel_room_availability/static/src/js/room_pricelist.js',
             # '/hotel_room_availability/static/src/less/room_availability.less',

            ],
        "web.assets_qweb": [
            '/hotel_room_availability/static/src/xml/room_availability.xml',
            '/hotel_room_availability/static/src/xml/room_type_availability.xml',
            # '/hotel_room_availability/static/src/xml/room_pricelist.xml',
        ],
    },
    'installable': True,
}
