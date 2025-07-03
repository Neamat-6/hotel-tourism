# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ResBranch(models.Model):
    _inherit = 'res.branch'

    auth_code = fields.Char(string='Authentication Code')
    hotel_code = fields.Char(string='Hotel Code')
    max_try = fields.Char(string='Max Try')


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    branch_id = fields.Many2one(comodel_name="res.branch", default=lambda self: self.env.user.branch_id.id)
    auth_code = fields.Char(string='Authentication Code', related="branch_id.auth_code")
    hotel_code = fields.Char(string='Hotel Code', related="branch_id.hotel_code")
    max_try = fields.Char(string='Max Try', related="branch_id.max_try")

    # def set_values(self):
    #     super(ResConfigSettings, self).set_values()
    #     ConfigParameter = self.env['ir.config_parameter']
    #     ConfigParameter.sudo().set_param('htask.auth_code', self.auth_code)
    #     ConfigParameter.sudo().set_param('htask.hotel_code', self.hotel_code)
    #     ConfigParameter.sudo().set_param('htask.max_try', self.max_try)
    #
    # @api.model
    # def get_values(self):
    #     res = super(ResConfigSettings, self).get_values()
    #     ConfigParameter = self.env['ir.config_parameter']
    #     res.update(
    #         auth_code=ConfigParameter.sudo().get_param('htask.auth_code'),
    #         hotel_code=ConfigParameter.sudo().get_param('htask.hotel_code'),
    #         max_try=int(ConfigParameter.sudo().get_param('htask.max_try')),
    #     )
    #     return res
