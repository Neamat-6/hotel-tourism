# -*- coding: utf-8 -*-
#################################################################################
# Author      : CFIS (<https://www.cfis.store/>)
# Copyright(c): 2017-Present CFIS.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://www.cfis.store/>
#################################################################################

{
    "name": "Scan barcode and QR code using mobile camera and webcam | Barcode and QR code scanner widget for many2one and character field | Barcode Scan Widget",
    "summary": """
        This module allows users to quickly Scan barcode and QR code using mobile camera and webcam.
        """,
    "version": "15.0.1",
    "description": """
        This module allows users to quickly Scan barcode and QR code using mobile camera and webcam.
        """,    
    "author": "CFIS",
    "maintainer": "CFIS",
    "license" :  "Other proprietary",
    "website": "https://www.cfis.store",
    "images": ["images/widget_mobile_scan.png"],
    "category": "Extra Tools",
    "depends": [
        "base",
    ],
    "data": [
        
    ],
    "assets": {
        "web.assets_qweb": [
            "/widget_mobile_scan/static/src/xml/*.xml",
        ],
        "web.assets_backend": [
            "/widget_mobile_scan/static/src/libs/ZXing.js",
            "/widget_mobile_scan/static/src/css/style.css",
            "/widget_mobile_scan/static/src/js/scan_code_dialog.js",
            "/widget_mobile_scan/static/src/js/char_field.js",
            "/widget_mobile_scan/static/src/js/relational_fields.js",
        ],
    },
    "installable": True,
    "application": True,
    "price"                 :  35,
    "currency"              :  "EUR",
    "pre_init_hook"         :  "pre_init_check",
}
