# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# See LICENSE file for full copyright and licensing details.
# License URL : <https://store.webkul.com/license.html/>
##############################################################################
from dataclasses import field
import string
from odoo import models, fields, api


class Partner(models.Model):
    _inherit = 'res.partner'
    # Set the description same to the inherited model
    _description = models.Model._description
    
    
    @api.model
    def action_process_image(self):
        """
        Default ocr server action for any model

        Override this function as per the requirement
        """
        _context = self.env.context
        _context = {**self.env.context, 'static_context': {
            'model_name': _context['active_model'],
            'record_id': _context['active_id']
        }}
        active_model_id = self.env['ir.model'].search([('model', '=', _context['active_model'])])
        ocr_process_wizard_id = self.env['ocr.process.wizard'].create({
            'model_id': active_model_id.id
        })
        return {
            'name': 'Select Template',
            'type': 'ir.actions.act_window',
            'res_model': 'ocr.process.wizard',
            'res_id': ocr_process_wizard_id.id,
            'context': _context,
            'view_mode': 'form',
            'views': [(False, 'form')],
            'target': 'new',
        }