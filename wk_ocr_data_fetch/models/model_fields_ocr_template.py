# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# See LICENSE file for full copyright and licensing details.
# License URL : <https://store.webkul.com/license.html/>
##############################################################################
from odoo import api, fields, models


class ModelFieldsOCRTemplate(models.Model):
    _name = "model.fields.ocr.template"
    _description = "Map model fields to ocr template"

    def _get_ocr_template(self):
        _context = self.env.context
        id = False
        if _context.get('ocr_template_id', False):
            id = _context['ocr_template_id']
        return id

    def _get_field_domain(self):
        _context = self.env.context
        domain = []
        if _context.get('ocr_template_id', False):
            ocr_template_id = self.env['ocr.template'].browse(_context['ocr_template_id'])
            model_id = ocr_template_id.model_id
            domain = [('model_id', '=', model_id.id), ('store', '=', True), ('ttype', 'in', ['char'])]
        return domain

    model_fields_id = fields.Many2one('ir.model.fields', string='Fields', domain=_get_field_domain)
    ocr_template_id = fields.Many2one('ocr.template', string='OCR Template', default=_get_ocr_template)
    model_id = fields.Many2one(comodel_name='ir.model', string='Model', compute='_compute_model_id')
    regex = fields.Char(help="Provide the regex according to the process type:\n"
                             "Words: All the row and column value combinations would be replaced with the respective "
                             "word. Format: (row,column)\n"
                             "Example:\n"
                             "(1,2) (2,2) OR Mr. (1,1) (1,2)\n"
                             "String: Complete string would be considered as a regular expression and would provide "
                             "all the matches available.\n"
                             "Example:\n"
                             "[A-Z]{3}[0-9]{4}\w")
    process_type = fields.Selection([
        ('words', 'Words'),
        ('string', 'String')], string="Image Process Type", related='ocr_template_id.process_type')

    @api.depends('model_fields_id')
    def _compute_model_id(self):
        _context = self.env.context
        for record in self:
            record.model_id = _context.get('parent_model_id', False) or record.ocr_template_id.model_id
