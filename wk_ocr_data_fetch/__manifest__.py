# -*- coding: utf-8 -*-
#################################################################################
# Author : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
#################################################################################
{
  "name": "Odoo OCR Data Fetch",
  "summary": """This module allows you to fetch data from your images which can be used to update or create new
  records in Odoo""",
  "category":  "Extra_Tools",
  "version":  "1.0.1",
  "sequence":  1,
  "author": "Webkul Software Pvt. Ltd.",
  "license":  "Other proprietary",
  "website": "",
  "description": """
  This module will provide the optical charater recognition(OCR) tool for the users to fetch data from the desired
  images and update or create new records in odoo. Tesseract module is used for this project.
  """,
  "live_test_url": "http://odoodemo.webkul.com/?module=wk_ocr_data_fetch&lifetime=90&lout=1&custom_url=/",
  "depends": ["base"],
  "data": [
            'security/wk_ocr_data_fetch_security.xml',
            'security/ir.model.access.csv',

            'data/ir_action_data.xml',
            'data/ocr_test_template_data.xml',

            'views/ocr_template_views.xml',
            'views/ocr_menuitem.xml',

            'wizard/test_ocr_template_wizard_views.xml',
            'wizard/ocr_process_wizard_views.xml',
          ],
  "demo": [],
  "css": [],
  "js": [],
  "images":  ['static/description/banner.png'],
  "application":  True,
  "installable":  True,
  "auto_install":  False,
  "price":  99,
  "currency": "USD",
  "pre_init_hook":  "pre_init_check",
  "external_dependencies": {"python":[
    "pytesseract",
    "opencv-python",
    "numpy",
    "Pillow"
  ],
  "bin":[
    "tesseract"
  ]
  }
}
