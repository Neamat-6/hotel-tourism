{
    "name":
        "POS Order Sequence Per Config",
    "summary":
        "POS Order Sequence Per Config",
    "description":
        """
        This module allows you to set a different order sequence for each POS configuration.
        Then display it on the POS receipt.
    """,
    "category":
        "Point of Sale",
    "version":
        "15.0.0.0.0",
    "depends": ["point_of_sale",],
    "data": [
        'views/pos_config_views.xml',
    ],
    'assets': {
        'point_of_sale.assets': ['pos_order_sequence_per_config/static/**/*',],
        'web.assets_qweb': ['pos_order_sequence_per_config/static/src/xml/**/*',],
    },
}
