# -*- coding: utf-8 -*-

import base64
import logging
from datetime import datetime
# from urllib.request import urlopen

from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError

from .htask import HTASK

_logger = logging.getLogger(__name__)


class HTaskAbstractModel(models.AbstractModel):
    """
    This abstract model is used to share all features related to htask model.
    Note that some fields and function have to be defined in the inherited
    model. (htask_type for instance)
    """

    _name = "abstract.htask.model"
    _description = "htask abstract model"
    _htask_type = None
    _field_list_prevent_overwrite = []
    _field_list_required = []
    _field_list_many2one = {}


    htask_id_external = fields.Char(string="HTask Id", readonly=True, index=True)
    htask_last_sync_date = fields.Datetime(
        string="Last Sync Date with HTask", readonly=True
    )

    def get_record_id_from_name(self, name, model):
        """
            Search for record in odoo by name fetched from htask record
            :return: record_id or False if none or multiple records
        """
        rec_id = self.env[model].search([('name', '=ilike', name)])
        if not rec_id or len(rec_id) > 1:
            return False
        return rec_id.id

    def htask_type(self):
        if self._htask_type is None:
            raise UserError(
                _(
                    "Feature not Implemented : Please define 'htask_type'"
                    " function in child model."
                )
            )
        else:
            return self._htask_type

    @api.model
    def get_conversion_dict(self):
        return {
            "htask_id_external": "Id",
        }

    def process_timezone_fields(self, res):
        for k, v in res.items():
            if self._fields[k].type == "datetime" and isinstance(v, str):
                res[k] = datetime.strptime(v, "%Y-%m-%dT%H:%M:%SZ")

    @api.model
    def get_odoo_data_from_htask(self, data):
        """Prepare function that map HTask data (dict) to create in Odoo"""
        map_dict = self.get_conversion_dict()
        res = {}
        for k, v in map_dict.items():
            if hasattr(self, k) and data.get(v, False):
                # Get Record if many2one
                data_val = data[v]
                if k in self._field_list_many2one.keys():
                    data_val = self.get_record_id_from_name(data_val, self._field_list_many2one[k])
                res.update({k: data_val})
        res.update({"htask_last_sync_date": fields.Datetime.now()})
        print(res)
        self.process_timezone_fields(res)
        return res

    def full_update(self):
        """Override this function in models that inherit this abstract
        to mention which items should be synchronized from htask when the
        user click on 'Full Update' Button"""
        pass

    def _update_from_htask_data(self, data):
        for item in self:
            vals = self.get_odoo_data_from_htask(data)
            to_write = {}
            for k, v in vals.items():
                if hasattr(item[k], "id"):
                    to_compare = item[k].id
                else:
                    to_compare = item[k]

                if to_compare != v and (
                    k not in self._field_list_prevent_overwrite or to_compare is False
                ):
                    to_write[k] = v
            if to_write:
                item.write(to_write)

    @api.model
    def get_from_id_or_create(self, id_field_name, data, extra_data=None):
        extra_data = extra_data and extra_data or {}
        existing_object = False
        if self._htask_type != 'revenue_line':
            if self._htask_type == 'revenue':
                # Search invoice by folio
                existing_object = self.with_context(active_test=False).search([("folio_id", "=", data[id_field_name]), ('branch_id', '=', self.env.user.branch_id.id)])
            else:
                existing_object = self.with_context(active_test=False).search([("htask_id_external", "=", data[id_field_name]), ('branch_id', '=', self.env.user.branch_id.id)])
        elif self._htask_type == 'revenue_line':
            existing_object = self.with_context(active_test=False).search([("htask_id_external", "=", data[id_field_name]), ('branch_id', '=', self.env.user.branch_id.id)])

        if existing_object:
            existing_object._update_from_htask_data(data)
            return existing_object
        print(existing_object)
        return self._create_from_htask_data(data, extra_data)

    @api.model
    def create_from_name(self, name):
        htask_connector = self.get_htask_connector(self.htask_type())
        res = htask_connector.get([name])
        # search if ID doesn't exist in database
        current_object = self.with_context(active_test=False).search(
            [("htask_id_external", "=", res["id"])]
        )
        if not current_object:
            # Create the object
            return self._create_from_htask_data(res)
        else:
            return current_object

    def button_update_from_htask_light(self):
        return self.update_from_htask(False)

    def button_update_from_htask_full(self):
        return self.update_from_htask(True)

    def update_from_htask(self, child_update):
        """Call HTask API, using a URL using htask id. Load data and
            update Odoo object accordingly, if the odoo object is obsolete.
            (Based on last write dates)

            :param child_update: set to True if you want to reload childs
                Objects linked to this object. (like members for teams)
        """
        htask_connector = self.get_htask_connector(self.htask_type())
        for item in self:
            res = htask_connector.get([item.htask_id_external], by_id=True)
            item._update_from_htask_data(res)

    @api.model
    def _create_from_htask_data(self, data, extra_data=None):
        extra_data = extra_data and extra_data or {}
        vals = self.get_odoo_data_from_htask(data)
        for field in self._field_list_required:
            if field not in vals.keys():
                return False
        vals.update(extra_data)
        print(vals)
        return self.create(vals)

    def get_htask_connector(self, htask_type):
        ConfigParams = self.sudo().env["ir.config_parameter"]
        auth_code = ConfigParams.sudo().get_param("htask.auth_code")
        hotel_code = ConfigParams.sudo().get_param("htask.hotel_code")
        max_try = int(ConfigParams.sudo().get_param("htask.max_try"))
        if not auth_code:
            auth_code = self.env.user.branch_id.auth_code
        if not hotel_code:
            hotel_code = self.env.user.branch_id.hotel_code
        if not auth_code or not hotel_code:
            raise UserError(
                _(
                    "Please specify 'auth_code' and 'hotel_code'"
                    " in the config settings."
                )
            )

        return HTASK(htask_type, auth_code, hotel_code, max_try)
