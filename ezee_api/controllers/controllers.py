import json
import logging
from odoo import http
from odoo.http import request
logger = logging.getLogger(__name__)


class EziController(http.Controller):


    @http.route('/ezee_invoice', type='json', auth='public', methods=['POST'], csrf=False)
    def create_ezee_invoice_webhook(self):
        try:
            kw = request.jsonrequest
            logger.info('create_ezee_invoice_webhook %s', kw)
            return request.env['create.ezee.invoice'].sudo().create_ezee_invoice(kw)
        except Exception as e:
            logger.info('create_ezee_invoice_webhook error %s', e)
            return {'status': 'success'}
