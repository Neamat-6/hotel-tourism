# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models, tools, _

_logger = logging.getLogger(__name__)


class HtaskAccountType(models.Model):
    _name = "htask.account.type"

    name = fields.Char(string='Name', required=True)
    initial_code = fields.Char(string='Initial Code', required=True)
    htask_ref = fields.Char(string='HTask Reference')


class HtaskAccountConfiguration(models.Model):
    _name = "htask.account.configuration"

    account_id = fields.Many2one('account.account', string='Account')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    branch_id = fields.Many2one('res.branch', string='Company', default=lambda self: self.env.user.branch_id.id)
    product_id = fields.Many2one('product.product', string='Product')
    htask_type_id = fields.Many2one('htask.account.type', string='Type')
    htask_account = fields.Char(string='HTask Account')
    htask_external_id = fields.Char(string='HTask External ID')
    htask_external_ref = fields.Char(string='HTask External Reference')
