# -*- coding: utf-8 -*-
import logging
# from datetime import timedelta
# from functools import partial
#
# import psycopg2
# import pytz

from odoo import api, fields, models, tools, _
# from odoo.tools import float_is_zero
# from odoo.exceptions import UserError
# from odoo.http import request
# from odoo.osv.expression import AND
# import base64

_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = "pos.order"
   
    return_ref = fields.Char(string='Return Ref', readonly=True, copy=False)
    return_status = fields.Selection([
        ('nothing_return', 'Nothing Returned'),
        ('partialy_return', 'Partialy Returned'),
        ('fully_return', 'Fully Returned')
    ], string="Return Status", default='nothing_return',
        readonly=True, copy=False, help="Return status of Order")

    post_request_ref = fields.Char(string='Post Request Ref')
    room_no = fields.Char(string='Room No.')
    folio_no = fields.Char(string='Folio No.')
