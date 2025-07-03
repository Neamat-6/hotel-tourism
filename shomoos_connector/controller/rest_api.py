from odoo import http
from odoo.http import Response
import requests
import json
from odoo.exceptions import _logger


class ShomoosIntermediaryController(http.Controller):

    @http.route('/shomoos_connect', type='json', auth="public", methods=['POST'], csrf="*")
    def shomoos_connect(self, **post):
        try:

            url = "https://api.shomoos.com.sa/accommodation/accommodationservice.svc/InsertGuest"

            headers = post['Auth']
            _logger.info("+++++++++++++ headers %s ++++++++++++" % headers)

            post.pop('Auth', None)

            response = requests.post(url=url, headers=headers, json=post, verify=False)
            txt = json.loads(response.text)
            _logger.info("------- response %s -------" % txt)
            return txt

        except Exception as e:
            return Response(
                json.dumps({'error': str(e)}),
                status=500,
                content_type='application/json'
            )

    @http.route('/shomoos_checkout', type='json', auth="public", methods=['POST'], csrf="*")
    def shomoos_checkout(self, **post):
        try:
            url = "https://api.shomoos.com.sa/accommodation/accommodationservice.svc/CheckOutAndRatingGuest"
            _logger.info("+++++++++++++ Calling Shomoos Checkout %s ++++++++++++" % url)

            _logger.info("+++++++++++++ post Checkout %s ++++++++++++" % post)

            headers = post['Auth']
            _logger.info("+++++++++++++ headers Checkout %s ++++++++++++" % headers)

            data_without = post.pop('Auth', None)
            _logger.info("+++++++++++++ post %s ++++++++++++" % post)

            response = requests.post(url=url, headers=headers, json=post, verify=False)

            txt = json.loads(response.text)
            _logger.info("------- response Checkout %s -------" % txt)

            return txt

        except Exception as e:
            return Response(
                json.dumps({'error': str(e)}),
                status=500,
                content_type='application/json'
            )
