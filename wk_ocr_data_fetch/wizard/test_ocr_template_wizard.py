# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# See LICENSE file for full copyright and licensing details.
# License URL : <https://store.webkul.com/license.html/>
##############################################################################
from werkzeug import urls
import random
from odoo import api, fields, models, _
from odoo.tools.translate import html_translate
from odoo.exceptions import UserError
from ..helpers import wk_ocr_tesseract
import logging

_logger = logging.getLogger(__name__)


def create_table(data, max_row, max_column, *args, **kwargs):
    html = "<table style='width:100%;border:1px solid black;'>"
    html += "<tr><th style='border:1px solid black;'></th>"
    for i in range(1, max_column + 1):
        html += "<th style='border:1px solid black;'>" + str(i) + "</th>"
    html += "</tr>"

    for i in range(1, max_row + 1):
        html += "<tr>" \
                "<th style='border:1px solid black;'>" + str(i) + "</th>"
        for j in range(1, max_column + 1):
            html += "<td style='border:1px solid black;'>" + (
                    data.get((i, j)) and data[(i, j)]['text'] or " ") + "</td>"
        html += "</tr>"
    html += "</table>"
    return html


class TestOCRTemplateWizard(models.TransientModel):
    _name = 'test.ocr.template.wizard'
    _description = 'Test OCR Template'

    state = fields.Selection([
        ('upload', 'Upload Image'),
        ('result', 'Result')], string="OCR Process", help="OCR template test state", default='upload')
    image = fields.Image('Image', help='Upload image to process', copy=False, attachment=False)
    ocr_template_id = fields.Many2one(comodel_name='ocr.template', copy=False, string='OCR Template')
    result = fields.Html('Test Result', sanitize_attributes=False, translate=html_translate,
                         sanitize_form=False, help="Shows the last test result")

    def onchange(self, values, field_name, field_onchange):
        _context = self.env.context
        # Set the active ocr template id in the wizard
        values['ocr_template_id'] = _context['active_id']
        results = super(TestOCRTemplateWizard, self).onchange(values, field_name, field_onchange)
        return results

    def process_test_image(self):
        _context = self.env.context
        ocr_template_id = self.env['ocr.template'].browse(_context['active_id'])
        image = self.image
        psm = ocr_template_id.psm
        oem = ocr_template_id.oem
        min_conf = ocr_template_id.min_conf
        lang = ocr_template_id.lang

        if ocr_template_id.restrict_im_size:
            im_pil = wk_ocr_tesseract.b64_to_pil(image)
            wid, hgt = im_pil.size
            if wid != ocr_template_id.image_wid or hgt != ocr_template_id.image_hgt:
                raise UserError(_("The file size is not correct. Please try with the correct size image."))

        result = ""
        if ocr_template_id.process_type == 'words':
            data = wk_ocr_tesseract.get_data_from_image(image, lang=lang, oem=oem, psm=psm)
            words_map, max_row, max_column = wk_ocr_tesseract.words_row_column(data, min_conf)
            
            
            # Render the template for table and update the result
            template = self.env.ref(
                'wk_ocr_data_fetch.ocr_fetched_data_word_table', raise_if_not_found=False
            )
            if template:
                render_template = template._render({
                    'data': words_map,
                    'max_row': max_row,
                    'max_column': max_column
                }, engine='ir.qweb')

                result = render_template
            # Returns a opencv numpy array
            image = wk_ocr_tesseract.draw_words(image, words_map)

            # Need to first convert opencv np_array format to pil format and then to base64
            # TODO Try to find a better approach
            image = wk_ocr_tesseract.opencv_to_pil(image)
            image = wk_ocr_tesseract.pil_to_b64(image)
        elif ocr_template_id.process_type == 'string':
            string = wk_ocr_tesseract.get_string_from_image(image, lang=lang, oem=oem, psm=psm)
            result = string

        self.image = image

        base_url = self.get_base_url()
        url = ""
        if base_url:
            path = '/web/image?model=test.ocr.template.wizard'
            url = urls.url_join(base_url, path)
        sequence = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
        image = "{}&id={}&field=image&unique={}".format(url, self.id,
                                                        "".join(random.sample(sequence, 5)))

        # Render the template for the result to be shown as the test result
        template = self.env.ref(
            'wk_ocr_data_fetch.ocr_process_result', raise_if_not_found=False
        )
        if template:
            render_template = template._render({
                'image_link': image,
                'result': result,
            }, engine='ir.qweb')
            result = render_template
        self.write({
            'ocr_template_id': _context['active_id'],
            'state': 'result',
            'result': result
        })

        return {
            'name': 'Test OCR Template',
            'type': 'ir.actions.act_window',
            'res_model': 'test.ocr.template.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'views': [(False, 'form')],
            'target': 'new',
        }

    def save_result(self):
        ocr_template_id = self.ocr_template_id
        ocr_template_id.write({
            'result': self.result
        })
        return

    def upload_test_image(self):
        # Update the active_id and swap it with the ocr_template_id in context for the process_test_image
        _context = {**self.env.context, 'active_id': self.ocr_template_id.id}
        self.write({
            'state': 'upload',
            'image': False
        })
        return {
            'name': 'Test OCR Template',
            'type': 'ir.actions.act_window',
            'res_model': 'test.ocr.template.wizard',
            'view_mode': 'form',
            'context': _context,
            'res_id': self.id,
            'views': [(False, 'form')],
            'target': 'new',
        }
