# -*- coding: utf-8 -*-

from . import controllers
from . import models

import os
import firebase_admin
from firebase_admin import credentials

if not firebase_admin._apps:
    module_path = os.path.dirname(__file__)
    cred_path = os.path.join(module_path, 'firebase', 'firebase_credentials.json')

    if os.path.exists(cred_path):
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
    else:
        import logging
        logging.getLogger(__name__).error(f"Firebase credentials not found: {cred_path}")