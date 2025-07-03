import io
import json
import requests
from hijri_converter import convert

from odoo import fields, models, api
from odoo.exceptions import ValidationError, _logger
# import base64
from odoo import models, fields


# import cv2
# import numpy as np
# import pytesseract
# from datetime import datetime
# import imutils
# from PIL import Image


class BookingFolio(models.Model):
    _inherit = 'booking.folio'

    apply_shomoos = fields.Boolean(string='Apply Shomoos', related='company_id.apply_shomoos', store=True)
    shomoos_message = fields.Text()
    guest = fields.Many2one(related='booking_id.partner_id', store=True)
    shomoos_escorts = fields.Boolean("Have Escorts (Shomoos)")
    shomoos_transactionID = fields.Char("Shomoos Transaction ID")
    shomoos_msg_transaction_id = fields.Char(string='Shomoos Message Transaction ID')
    shomoos_rating = fields.Integer("Shomoos Rating", default=3)
    shomoos_nationality_id = fields.Many2one('shomoos.nationality', "Nationality",
                                             readonly=False)
    shomoos_country_id = fields.Many2one('shomoos.country', "Country",
                                         readonly=False)
    shomoos_identity = fields.Many2one("shomoos.identity.type", 'Identity Type',
                                       readonly=False)
    shomoos_identity_code = fields.Char(store=True)
    shomoos_identity_no = fields.Char('Identity Number', readonly=False)
    shomoos_date_of_birth = fields.Date("Date Of Birth", readonly=False)
    date_of_birth_hijri = fields.Date("Date Of Birth (Hijri)", readonly=False)
    shomoos_identity_number = fields.Char("Shomoos Identity Number", readonly=True)
    is_invalid = fields.Boolean(default=False)
    validation_error = fields.Char()
    mrz_image = fields.Binary(string='ID Image')
    mrz_data = fields.Text(string='Extracted MRZ Data')
    check_shomoos_transaction = fields.Boolean(compute='check_about_transaction')
    error_msg = fields.Text()

    # @api.onchange('mrz_image')
    # def extract_mrz_data(self):
    #     """Extract MRZ data from the uploaded image"""
    #     if self.mrz_image:
    #         # Convert the base64 image to an actual image
    #         image_data = base64.b64decode(self.mrz_image)
    #         image = Image.open(io.BytesIO(image_data))
    #
    #         # Enhance image quality (you can experiment with this)
    #         # image = image.convert('L')  # Convert to grayscale
    #         # image = image.point(lambda x: 0 if x < 128 else 255, '1')  # Binarize
    #
    #         # Use Tesseract to extract text (try different configurations)
    #         mrz_text = pytesseract.image_to_string(image, config='--oem 3 --psm 6')
    #         self.mrz_data = self.ocr_passport(image)
    #         if self.mrz_data:
    #             mrz_lines = self.mrz_data.splitlines()
    #             if len(mrz_lines) >= 2:
    #                 mrz_first_line = mrz_lines[0].replace('K', '')
    #                 mrz_second_line = mrz_lines[1].replace('K', '')
    #
    #                 # Extract surname and given names
    #                 name_part = mrz_first_line.split('<<')
    #                 surname = name_part[0][5:].replace('<', ' ').strip()  # Remove 'P<UTO'
    #
    #                 # Extract passport number, nationality, date of birth, gender, expiry date
    #                 passport_number = mrz_second_line[0:8]
    #                 nationality_code = mrz_first_line[2:5]
    #                 dob_raw = mrz_second_line[13:21]  # Date of birth in YYMMDD format
    #                 gender = mrz_lines[7][-1] if len(mrz_lines) > 7 else ''
    #                 expiry_raw = mrz_second_line[21:27]  # Expiry date in YYMMDD format
    #
    #                 # Convert dates from MRZ format (YYMMDD) to standard format
    #                 date_of_birth = self.convert_mrz_date(dob_raw)
    #                 expiry_date = self.convert_mrz_date(expiry_raw)
    #
    #                 # Use nationality and country mappings (you need to adjust these based on your data)
    #                 nationality_id = self.env['shomoos.nationality'].search([('english_title', 'ilike', nationality_code)], limit=1)
    #                 country_id = self.env['shomoos.country'].search([('english_title', '=', nationality_code)], limit=1)
    #
    #                 # Update existing record
    #                 self.write({
    #                     'shomoos_identity_code': passport_number,
    #                     'shomoos_identity_no': passport_number,  # Adjust if needed
    #                     'shomoos_nationality_id': nationality_id.id if nationality_id else False,
    #                     'shomoos_country_id': country_id.id if country_id else False,
    #                     'shomoos_date_of_birth': date_of_birth,
    #                 })
    #
    # def convert_mrz_date(self, mrz_date_str):
    #     """Convert MRZ date (YYMMDD) to a standard date (YYYY-MM-DD)"""
    #     try:
    #         # Parse the date in DDMMYYYY format
    #         return datetime.strptime(mrz_date_str, '%d%m%Y').date()
    #     except ValueError:
    #         return None
    #
    # def ocr_passport(self, image):
    #     """
    #     Extract MRZ data from a passport photo and return it as a string.
    #     """
    #     # Convert PIL image to OpenCV format
    #     image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    #     gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)
    #     (HEIGHT, WIDTH) = gray.shape
    #
    #     rect_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 7))
    #     sq_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (21, 21))
    #
    #     gray = cv2.GaussianBlur(gray, (3, 3), 0)
    #     blackhat = cv2.morphologyEx(gray, cv2.MORPH_BLACKHAT, rect_kernel)
    #
    #     grad = cv2.Sobel(blackhat, ddepth=cv2.CV_32F, dx=1, dy=0, ksize=-1)
    #     grad = np.absolute(grad)
    #     (min_val, max_val) = (np.min(grad), np.max(grad))
    #     grad = (grad - min_val) / (max_val - min_val)
    #     grad = (grad * 255).astype("uint8")
    #
    #     grad = cv2.morphologyEx(grad, cv2.MORPH_CLOSE, rect_kernel)
    #     thresh = cv2.threshold(grad, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    #     thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, sq_kernel)
    #     thresh = cv2.erode(thresh, None, iterations=2)
    #
    #     contours = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    #     contours = imutils.grab_contours(contours)
    #     contours = sorted(contours, key=lambda c: cv2.boundingRect(c)[1], reverse=True)
    #
    #     mrz_box = None
    #     for c in contours:
    #         (x, y, w, h) = cv2.boundingRect(c)
    #         percent_height = h / float(HEIGHT)
    #         percent_width = w / float(WIDTH)
    #         if percent_width > 0.8 and percent_height > 0.04:
    #             mrz_box = (x, y, w, h)
    #             break
    #
    #     if mrz_box is None:
    #         return ""
    #
    #     (x, y, w, h) = mrz_box
    #     pad_x = int((x + w) * 0.03)
    #     pad_y = int((y + h) * 0.03)
    #     (x, y) = (x - pad_x, y - pad_y)
    #     (w, h) = (w + (pad_x * 2), h + (pad_y * 2))
    #
    #     mrz = image_cv[y:y + h, x:x + w]
    #     mrz_text = pytesseract.image_to_string(mrz)
    #     mrz_text = mrz_text.replace(" ", "")
    #
    #     return mrz_text

    def check_about_transaction(self):
        for rec in self:
            folios_without_shomoos = []
            if not rec.shomoos_transactionID:
                rec.check_shomoos_transaction = True
                folios_without_shomoos.append(rec.name)

                if folios_without_shomoos:
                    rec.error_msg = "Folios missing Shomoos transaction ID: " + ', '.join(folios_without_shomoos)
                else:
                    rec.check_shomoos_transaction = False
                    rec.error_msg = "All folios have Shomoos transaction IDs."
            else:
                rec.check_shomoos_transaction = False
                rec.error_msg = "No folios found."

    @api.onchange('shomoos_date_of_birth')
    def compute_hijri_date(self):
        for record in self:
            if record.shomoos_date_of_birth:
                hijri_date = convert.Gregorian(record.shomoos_date_of_birth.year, record.shomoos_date_of_birth.month,
                                               record.shomoos_date_of_birth.day).to_hijri()
                hijri_month = hijri_date.month_name()
                record.date_of_birth_hijri = str(hijri_date)
            else:
                record.date_of_birth_hijri = False

    @api.onchange('date_of_birth_hijri')
    def compute_from_hijri(self):
        for record in self:
            if record.date_of_birth_hijri:
                Gregorian_date = convert.Hijri(record.date_of_birth_hijri.year, record.date_of_birth_hijri.month,
                                               record.date_of_birth_hijri.day).to_gregorian()
                record.shomoos_date_of_birth = str(Gregorian_date)
            else:
                record.shomoos_date_of_birth = False

    def button_undo_check_in(self):
        res = super(BookingFolio, self).button_undo_check_in()
        self.is_invalid = False
        return res

    def button_check_in(self, book_by_bed=None, bed_partner=None):
        res = super(BookingFolio, self).button_check_in(book_by_bed=book_by_bed, bed_partner=bed_partner)
        if self.apply_shomoos:
            if not self.shomoos_date_of_birth or not self.shomoos_identity_no or not self.shomoos_identity:
                message = (
                    "Be careful, the data for the Shomoos platform is not available. Do you want to continue?\n"
                    "انتبه الداتا الخاصة بمنصة شموس غير موجودة. هل تريد الاستمرار ؟"
                )
                return {
                    'name': 'Warning',
                    'type': 'ir.actions.act_window',
                    'res_model': 'warning.wizard',
                    'view_mode': 'form',
                    'view_type': 'form',
                    'target': 'new',
                    'context': {'default_message': message, 'default_folio_id': self.id}
                }
            else:
                self.shomoos_connect(mode='insert_guests', new=False)
        return res

    def button_check_out(self):
        res = super(BookingFolio, self).button_check_out()
        if self.apply_shomoos:
            if self.shomoos_transactionID:
                self.shomoos_checkout_connect()
        return res

    def shomoos_connect(self, mode='', new=False):
        try:
            intermediary_server_url = "http://185.230.210.215:8069/shomoos_connect"
            _logger.info("+++++++++++ Calling %s +++++++++" % intermediary_server_url)
            headers = self.prepare_shomoos_headers()
            data = self.prepare_shomoos_data(mode=mode, new=new)

            response = requests.post(url=intermediary_server_url, json=data, headers=headers)

            if response.status_code == 200:
                txt = json.loads(response.text)

            fault_code = txt.get('result', {}).get('Header', {}).get('ProxyFaults', [{}])[0].get('FaultCode')
            fault_desc = txt.get('result', {}).get('Header', {}).get('ProxyFaults', [{}])[0].get('FaultDescription')

            if fault_code != 201:
                self.is_invalid = True
                # raise ValidationError("Authenticated With Shomoos Failed Because  %s" % fault_desc)
                validation_error = "You have a problem in shomoos data %s" % fault_desc
                self.validation_error = validation_error
            else:
                self.is_invalid = False
                self.shomoos_message = fault_desc

            identity = txt.get('result', {}).get('Body', {}).get('Identity')
            self.shomoos_transactionID = identity
            if self.shomoos_transactionID:
                self.env['audit.trails'].create({
                    'booking_id': self.booking_id.id,
                    'folio_id': self.id,
                    'user_id': self.env.user.id,
                    'operation': 'shomoos',
                    'datetime': fields.Datetime.now(),
                    'notes': f"Transaction ID: {self.shomoos_transactionID}, Message: {self.shomoos_message}"
                })

        except Exception as e:
            _logger.error(f"Unexpected Error: {e}")
            self.is_invalid = True
            # raise ValidationError(e)

    def prepare_shomoos_headers(self):
        return {
            "Content-Type": "application/json",
            "Authorization": str(self.env.company.shomoos_key) or '',
        }

    def prepare_shomoos_data(self, mode='', new=False):
        if not self.shomoos_date_of_birth:
            raise ValidationError("Please Check Date Of Birth")
        data = {
            "params": {
                "Body": {
                    "DateOfCheckIn": self.check_in.strftime('%m/%d/%Y'),
                    "DateOfCheckOut": self.check_out.strftime('%m/%d/%Y'),
                    "IdentityType": str(self.shomoos_identity.code),
                    "IdentityNum": str(self.shomoos_identity_no),
                    "Nationality": str(self.shomoos_nationality_id.code),
                    "DateOfBirth": self.shomoos_date_of_birth.strftime('%m/%d/%Y'),
                    "VersionNumber": "0",  # todo will be handle
                    "RoomNumber": str(self.room_id.name),
                    "HaveEscorts": "false",
                    "EscortDetails": []
                },
                "Header": {
                    "RequestId": "123654",
                    "UserId": str(self.env.company.shomoos_user_id),
                    "BranchCode": str(self.env.company.shomoos_branch_code),
                    "BranchSecret": str(self.env.company.shomoos_branch_secret),
                    "Lang": "en"
                },
                "Auth": {
                    "Content-Type": "application/json",
                    "Authorization": str(self.env.company.shomoos_key) or '',
                }
            }
        }

        return data

    def get_folio_shomoos_fields(self):
        return [
            "check_in", "check_out", "total_nights", "room_id", "shomoos_nationality_id", "shomoos_country_id",
            "shomoos_escorts",
            "shomoos_identity", "price_total"
        ]

    def get_shomoos_response_msg(self, f_code):
        msg = False
        if f_code:
            response = self.env['shomoos.response.code'].search(
                [('api_name', '=', 'InsertGuest'), ('fault_code', '=', f_code)], limit=1)
            if response:
                if response.api_category == 'success':
                    msg = 'Synced Successfully with Shomoos'
                else:
                    msg = response.fault_description
        return msg

    # Shomoos Checkout and Rating
    def shomoos_checkout_connect(self):
        try:
            url = "http://185.230.210.215:8069/shomoos_checkout"
            _logger.info("+++++++++++ Calling %s +++++++++" % url)

            headers = self.prepare_shomoos_headers()
            data = self.prepare_checkout_data()

            response = requests.post(url=url, headers=headers, json=data)

            if response.status_code == 200:
                txt = json.loads(response.text)

                fault_code = txt.get('result', {}).get('Header', {}).get('ProxyFaults', [{}])[0].get('FaultCode')
                fault_desc = txt.get('result', {}).get('Header', {}).get('ProxyFaults', [{}])[0].get('FaultDescription')

                if fault_code != 201:
                    self.is_invalid = True
                    validation_error = "%s (Shomoos)" % fault_desc
                    self.validation_error = validation_error

                    # Log the fault as an audit trail instead of raising a ValidationError
                    self.env['audit.trails'].create({
                        'booking_id': self.booking_id.id,
                        'folio_id': self.id,
                        'user_id': self.env.user.id,
                        'operation': 'shomoos',
                        'datetime': fields.Datetime.now(),
                        'notes': f"Transaction ID: {self.shomoos_transactionID}, Error: {fault_desc}"
                    })
                else:
                    self.update({'shomoos_message': fault_desc})
                    self.env['audit.trails'].create({
                        'booking_id': self.booking_id.id,
                        'folio_id': self.id,
                        'user_id': self.env.user.id,
                        'operation': 'shomoos',
                        'datetime': fields.Datetime.now(),
                        'notes': f"Transaction ID: {self.shomoos_transactionID}, Message: {self.shomoos_message}"
                    })
            else:
                # Handle non-200 status codes here
                error_msg = f"Received unexpected status code: {response.status_code} with response: {response.text}"
                _logger.error(error_msg)

                # Create an audit trail for the error
                self.env['audit.trails'].create({
                    'booking_id': self.booking_id.id,
                    'folio_id': self.id,
                    'user_id': self.env.user.id,
                    'operation': 'shomoos',
                    'datetime': fields.Datetime.now(),
                    'notes': error_msg
                })

        except Exception as e:
            _logger.error(f"Unexpected Error: {e}")

            # Create an audit trail for the unexpected error
            self.env['audit.trails'].create({
                'booking_id': self.booking_id.id,
                'folio_id': self.id,
                'user_id': self.env.user.id,
                'operation': 'shomoos',
                'datetime': fields.Datetime.now(),
                'notes': f"Unexpected Error: {str(e)}"
            })

    def prepare_checkout_data(self):
        if not self.shomoos_rating:
            ValidationError("Please Check Rating Field")
        if not self.shomoos_transactionID:
            ValidationError("Please Check Transaction ID")
        return {
            "params": {
                "Body": {
                    "Accom_Trx_MainId": str(self.shomoos_transactionID),
                    "DateOfCheckOut": self.check_out.strftime('%m/%d/%Y'),
                    "Rating": self.shomoos_rating,
                },
                "Header": {
                    "RequestId": "123654",
                    "UserId": str(self.env.company.shomoos_user_id),
                    "BranchCode": str(self.env.company.shomoos_branch_code),
                    "BranchSecret": str(self.env.company.shomoos_branch_secret),
                    "Lang": "en"
                },
                "Auth": {
                    "Content-Type": "application/json",
                    "Authorization": str(self.env.company.shomoos_key) or '',
                }
            }
        }

    def get_checkout_response_msg(self, code):
        msg = False
        if code:
            response = self.env['shomoos.response.code'].search(
                [('api_name', '=', 'CheckOutAndRating'), ('fault_code', '=', code)], limit=1)
            if response:
                if response.api_category == 'success':
                    msg = 'Synced Successfully with Shomoos'
                else:
                    msg = response.fault_description
        return msg
