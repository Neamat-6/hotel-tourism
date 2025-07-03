# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# See LICENSE file for full copyright and licensing details.
# License URL : <https://store.webkul.com/license.html/>
##############################################################################
import re
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from ..helpers import wk_ocr_tesseract
import logging

_logger = logging.getLogger(__name__)


class OCRProcessWizard(models.TransientModel):
    _name = 'ocr.process.wizard'
    _description = 'OCR Process'

    def _get_template_domain(self):
        return [('model_id', '=', self.model_id)]

    state = fields.Selection([
        ('template', 'Select Template'),
        ('upload', 'Upload Image')], string="OCR Process", help="OCR server action state", default='template')
    image = fields.Image('Image', help='Upload image to process', attachment=False)
    model_id = fields.Many2one(comodel_name='ir.model', string='Model')
    ocr_template_id = fields.Many2one(comodel_name='ocr.template', string='OCR Template',
                                      domain=_get_template_domain)

    def _save_data(self, process_type, ocr_template_id, model_name, record_id, data):
        record_data = {}
        fields = ocr_template_id.model_fields_ids
        if process_type == 'words':
            regex = r"\((\d), ?(\d)\)"
            # TODO think for something more optimised
            for f in fields:
                results = re.finditer(regex, f.regex, re.MULTILINE)
                string = f.regex
                for result in results:
                    try:
                        row = int(result.groups()[0])
                        column = int(result.groups()[1])
                    except ValueError:
                        continue
                    value = wk_ocr_tesseract.search(data, 'DICT', row, column)
                    sub_regex = fr"\({row}, ?{column}\)"
                    string = re.sub(sub_regex, value, string, 0, re.MULTILINE)
                    record_data[f.model_fields_id.name] = string
        elif process_type == 'string':
            for f in fields:
                value = wk_ocr_tesseract.search(data, 'STRING', regex=f.regex)
                record_data[f.model_fields_id.name] = value
        record_id = self.env[f"{model_name}"].browse(record_id)
        record_id.write(record_data)

    def process_and_save(self):
        image = self.image
        if not image:
            raise UserError(_("Please provide the image to process."))
        _context = self.env.context
        model_name = _context['static_context']["model_name"]
        record_id = _context['static_context']["record_id"]

        ocr_template_id = self.ocr_template_id
        psm = ocr_template_id.psm
        oem = ocr_template_id.oem
        min_conf = ocr_template_id.min_conf
        process_type = ocr_template_id.process_type
        lang = ocr_template_id.lang

        if ocr_template_id.restrict_im_size:
            im_pil = wk_ocr_tesseract.b64_to_pil(image)
            wid, hgt = im_pil.size
            if wid != ocr_template_id.image_wid or hgt != ocr_template_id.image_hgt:
                raise UserError(_("The file size is not correct. Please try with the correct size image."))

        data = False
        if process_type == 'words':
            data = wk_ocr_tesseract.get_data_from_image(image, lang=lang, oem=oem, psm=psm)
            words_map, max_row, max_column = wk_ocr_tesseract.words_row_column(data, min_conf)
            data = words_map

        elif process_type == 'string':
            string = wk_ocr_tesseract.get_string_from_image(image, lang=lang, oem=oem, psm=psm)
            data = string

        self._save_data(process_type, ocr_template_id, model_name, record_id, data)

    def upload_image(self):
        if not self.ocr_template_id:
            raise UserError(_("Please select the OCR template"))
        self.write({
            'ocr_template_id': self.ocr_template_id,
            'state': 'upload'
        })
        return {
            'name': 'Upload Image',
            'type': 'ir.actions.act_window',
            'res_model': 'ocr.process.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'views': [(False, 'form')],
            'target': 'new',
        }

    def select_template(self):
        self.write({
            'state': 'template',
            'image': False
        })
        return {
            'name': 'Select Template',
            'type': 'ir.actions.act_window',
            'res_model': 'ocr.process.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'views': [(False, 'form')],
            'target': 'new'
        }
