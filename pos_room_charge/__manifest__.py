{
    "name": "POS Room Charge",
    "summary": "Room Charge for POS",
    "version": "15.0.0.0.0",
    "category": "Point of Sale",
    "depends": ["point_of_sale","hotel_booking","hotel_booking_folio"],
    "data": ["views/pos_payment_method_views.xml",
             'data/actions.xml',],
    'assets': {
        'point_of_sale.assets': ['pos_room_charge/static/**/*',],
        'web.assets_qweb': ['pos_room_charge/static/src/xml/**/*',],
    },
    "installable": True,
    "application": True,
    "auto_install": True,
}
