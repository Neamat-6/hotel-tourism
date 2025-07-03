# -*- coding: utf-8 -*-

import json
import logging

import requests
# from requests.auth import AuthBase, HTTPBasicAuth

from odoo import _, exceptions

_logger = logging.getLogger(__name__)

_MAX_NUMBER_REQUEST = 30

_BASE_URL = "https://live.ipms247.com/"

_HTASK_TYPE = [
    ("room", "RoomInfo"),
    ("booking", "Bookings"),
]

_HTASK_TYPE_URL = {
    "RoomInfo": "pmsinterface/pms_connectivity.php",
    "Bookings": "pmsinterface/pms_connectivity.php",
}

HTASK_ENDPOINTS = [
    "pmsinterface/pms_connectivity.php",
    "index.php/page/service.posting",
    "index.php/page/service.pos2pms",
    "booking/reservation_api/listing.php",
    "index.php/page/service.PMSAccountAPI",
]

_CODE_602 = 602
_CODE_611 = 611
_CODE_614 = 614
_CODE_612 = 612


class HTASK(object):
    def __init__(self, htask_type, auth_code, hotel_code, max_try):
        super().__init__()
        self.htask_type = htask_type
        self.auth_code = "73286158752462f52b-2f72-11ee-b"
        self.hotel_code = "36150"
        self.max_try = max_try

    def _build_url(self, arguments, url_type=None, page=None):
        arguments = arguments and arguments or {}
        url = _HTASK_TYPE_URL[self.htask_type]
        if self.htask_type not in _HTASK_TYPE_URL.keys():
            raise exceptions.Warning(_("'%s' is not implemented.") % self.htask_type)
        complete_url = _BASE_URL + url % tuple(arguments)
        return complete_url

    def list(self, arguments):
        page = 1
        datas = []
        while True:
            pending_datas = self.get(arguments, False, page)
            datas += pending_datas
            if pending_datas == [] or len(pending_datas) < _MAX_NUMBER_REQUEST:
                break
            page += 1
        return datas

    def get_by_url(self, url, call_type, content_type, data=False):
        _logger.info("------- Calling %s -------" % url)
        self.max_try = 5
        for i in range(self.max_try):
            try:
                if content_type == "json":
                    headers = {'Content-Type': 'application/json'}
                    json_data = json.dumps(data)
                    response = requests.post(url, headers=headers, data=json_data)
                else:
                    headers = {'Content-Type': 'application/xml'}
                    response = requests.post(url, headers=headers, data=data.encode('utf-8'))

                break
            except Exception as err:
                _logger.warning(
                    "URL Call Error. %d/%d. URL: %s", i, self.max_try, err.__str__(),
                )
        else:
            raise exceptions.Warning(_("Maximum attempts reached."))

        auth_err_msg = _("provided auth code and hotel code")

        if response.status_code == _CODE_602:
            raise exceptions.Warning(
                _(
                    "602 - Unable to authenticate to HTASK with the %s.\n"
                    "You should check your credentials in the Odoo configuration file."
                )
                % auth_err_msg
            )
        elif response.status_code == _CODE_611:
            raise exceptions.Warning(
                _("Unauthorized Access. The %s does not have the correct access rights.")
                % auth_err_msg
            )
        elif response.status_code == _CODE_614:
            raise exceptions.Warning(_("Sandbox User Trial Period is expired"))

        elif response.status_code == _CODE_612:
            raise exceptions.Warning(_("Sandbox User Auth Code is inactive"))

        if content_type == "json":
            if self.htask_type == 'bill':  # comes in csv format
                return response.content
            else:
                return response.json()

        else:
            return response.text

    def get_post(self, arguments, data, content_type="json", custom_url=None):
        if custom_url:
            url = custom_url
        else:
            url = self._build_url(arguments)
        res = self.get_by_url(url, "post", content_type, data)
        return res

    def get_htask_connector(self, htask_type):
        auth_code = "73286158752462f52b-2f72-11ee-b"
        hotel_code = "36150"
        max_try = 10
        return HTASK(htask_type, auth_code, hotel_code, max_try)
