# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# See LICENSE file for full copyright and licensing details.
# License URL : <https://store.webkul.com/license.html/>
##############################################################################
import subprocess
import re
from odoo import api, fields, models, _, tools
from odoo.tools.translate import html_translate
from odoo.exceptions import ValidationError

MODELS = ['res.partner']


class OCRTemplate(models.Model):
    _name = "ocr.template"
    _description = "OCR Template"

    def _get_model_domain(self):
        return [('model', 'in', MODELS)]

    def _get_default_model(self):
        return self.env['ir.model'].search([('model', 'in', MODELS)], limit=1).id

    @api.constrains('min_conf')
    def _check_min_conf(self):
        for record in self:
            if record.min_conf < 0 or record.min_conf > 100:
                raise ValidationError("The minimum confidence value should be between 0 - 100")

    @api.constrains('lang')
    def _validate_ocr_languages(self):
        # TODO add the compatibility for windows
        # For linux only
        avl_langs = subprocess.run(["tesseract", "--list-langs"], stdout=subprocess.PIPE, text=True).stdout
        avl_langs = [lang for lang in avl_langs.split("\n")[1:] if lang]
        for record in self:
            regex = r"^([a-z]{3})(\+[a-z]{3})*"
            result = re.match(regex, record.lang).group()
            if len(result) != len(record.lang):
                raise ValidationError("Invalid input is provided for the field language, please provide the input in "
                                      "the correct format. Example: eng+osd or eng")
            elif len(set(avl_langs).union(set(record.lang.split("+")))) != len(avl_langs):
                raise ValidationError("Invalid or unsupported language is provided.\n\n"
                                      "Note: Languages should be in three-letter code format and should be available "
                                      "for OCR")

    @api.onchange('model_id')
    def _onchange_model_id(self):
        self.model_fields_ids = False

    name = fields.Char(string='Name', required=True, translate=True)
    active = fields.Boolean(default=True)
    model_id = fields.Many2one(comodel_name='ir.model', copy=True, string='Model', domain=_get_model_domain,
                               default=_get_default_model)
    # TODO Need to provide create operation in next version with bulk create
    operation_type = fields.Selection([('update', 'Update')], string="Operation",
                                      default='update')
    result = fields.Html('Test Result', sanitize_attributes=False, translate=html_translate,
                         sanitize_form=False, copy=False, help="Shows the last test result")
    restrict_im_size = fields.Boolean("Restrict Image Size", copy=True,
                                      help="Fix image to the required width and height", default=False)
    image_wid = fields.Integer('Image Width', default=600, copy=True, help="Image width")
    image_hgt = fields.Integer('Image Height', default=600, copy=True, help="Image height")
    lang = fields.Char('Language', default='eng', help="Provide language or languages to be detected by OCR\n"
                                                       "Example: eng or eng+osd\n\n"
                                                       "Note: OCR works best with one language")
    process_type = fields.Selection([
        ('words', 'Words'),
        ('string', 'String')], string="Image Process Type", default='words', copy=True,
        help="Words: Process the image and retrieve the words and map them in row and column\n"
             "String: Process the image and retrieve the string out of the image")
    model_fields_ids = fields.Many2many(comodel_name='model.fields.ocr.template', string='Fields')
    preprocess_image = fields.Boolean("Preprocess Image",
                                      help="Get the image preprocess ability", default=False)
    min_conf = fields.Integer("Min Confidence", default=50, copy=True,
                              help="Minimum confidence value for the word detection")

    oem = fields.Selection([('0', '0'), ('1', '1'), ('2', '2'), ('3', '3')], string="OCR Engine Mode", default='3',
                           copy=True,
                           help="OCR engine modes:\n"
                                "0. Legacy engine only.\n"
                                "1. Neural nets LSTM engine only.\n"
                                "2. Legacy + LSTM engines.\n"
                                "3. Default, based on what is available.")

    psm = fields.Selection([('0', '0'), ('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'), ('6', '6'),
                            ('7', '7'), ('8', '8'), ('9', '9'), ('10', '10'), ('11', '11'), ('12', '12'),
                            ('13', '13')],
                           string="Page Segmentation Mode", default='3', copy=True,
                           help="Page segmentation modes:\n"
                                "0. Orientation and script detection (OSD) only.\n"
                                "1. Automatic page segmentation with OSD.\n"
                                "2. Automatic page segmentation, but no OSD, or OCR. (not implemented)\n"
                                "3. Fully automatic page segmentation, but no OSD. (Default)\n"
                                "4. Assume a single column of text of variable sizes.\n"
                                "5. Assume a single uniform block of vertically aligned text.\n"
                                "6. Assume a single uniform block of text.\n"
                                "7. Treat the image as a single text line.\n"
                                "8. Treat the image as a single word.\n"
                                "9. Treat the image as a single word in a circle.\n"
                                "10. Treat the image as a single character.\n"
                                "11. Sparse text. Find as much text as possible in no particular order.\n"
                                "12. Sparse text with OSD.\n"
                                "13. Raw line. Treat the image as a single text line, bypassing hacks that"
                                " are Tesseract-specific.")

