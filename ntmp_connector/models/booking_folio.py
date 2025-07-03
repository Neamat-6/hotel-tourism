import json
import traceback
from symbol import lambdef

import requests
from requests.auth import HTTPBasicAuth

from odoo import fields, models, api
from odoo.exceptions import ValidationError,_logger
import logging
logger = logging.getLogger(__name__)


class Folio(models.Model):
    _inherit = 'booking.folio'

    # todo check if should be required!
    apply_ntmp = fields.Boolean(string='Apply NTMP', related='company_id.apply_ntmp', store=True)
    nationality_id = fields.Many2one('ntmp.nationality')
    gender_id = fields.Many2one('ntmp.gender', related='partner_id.gender_id')
    rent_type_id = fields.Many2one('ntmp.rent.type', string='Room Rent Type')
    customer_type_id = fields.Many2one('ntmp.customer.type', related='partner_id.customer_type_id')
    ntmp_room_type_id = fields.Many2one('ntmp.room.type', string='Room Type2')
    visit_purpose_id = fields.Many2one('ntmp.visit.purpose', string='Purpose of Visit',
                                       related='partner_id.visit_purpose_id')
    payment_type_id = fields.Many2one('ntmp.payment.type')
    message = fields.Text()
    ntmp_transaction_id = fields.Char(string='NTMP Transaction ID')
    ntmp_msg_transaction_id = fields.Char(string='NTMP Message Transaction ID')

    @api.model
    def create(self, vals):
        res = super(Folio, self).create(vals)
        if not res['partner_id']:
            res.update({
                'partner_id': res['booking_id'].partner_id.id,
                'gender_id': res['booking_id'].partner_id.gender_id.id,
                'customer_type_id': res['booking_id'].partner_id.customer_type_id.id,
                'visit_purpose_id': res['booking_id'].partner_id.visit_purpose_id.id
            })
        return res


    # @api.model
    # def create(self, vals):
    #     res = super(Folio, self).create(vals)
    #     if res.apply_ntmp:
    #         res.ntmp_connect(mode='booking', new=True)
    #     return res

    def button_confirm(self):
        res = super(Folio, self).button_confirm()
        if self.booking_id.apply_ntmp:
            self.ntmp_connect(mode='booking', new=True)
        return res

    # def write(self, vals):
    #     self = self.with_context(ignore_updates=True)
    #     res = super(Folio, self).write(vals)
    #     if self.apply_ntmp:
    #         folio_fields = self.get_folio_ntmp_fields()
    #         modified = [key for key in folio_fields if key in vals and vals.get(key, False)]
    #         if modified:
    #             self.ntmp_connect(mode='booking', new=False)
    #     return res

    def button_check_in(self, book_by_bed=None, bed_partner=None):
        res = super(Folio, self).button_check_in(book_by_bed=book_by_bed, bed_partner=bed_partner)
        if self.apply_ntmp:
            self.ntmp_connect(mode='check_in', new=False)
        return res

    def button_check_out(self):
        res = super(Folio, self).button_check_out()
        if self.apply_ntmp:
            self.ntmp_connect(mode='check_out', new=False)
            self.ntmp_expense_connect()
        return res

    def ntmp_connect(self, mode, new=False):
        url = "https://api.ntmp.gov.sa/gateway/CreateOrUpdateBooking/1.0/createOrUpdateBooking"
        headers = self.prepare_ntmp_headers()
        data = self.prepare_ntmp_data(mode=mode, new=new)
        response = requests.post(url=url, headers=headers, json=data,
                                 auth=HTTPBasicAuth(self.company_id.ntmp_username, self.company_id.ntmp_password))
        txt = json.loads(response.text)
        if new:
            self.ntmp_transaction_id = txt.get('transactionId', False)
        self.ntmp_msg_transaction_id = txt.get('transactionId', False)

        if txt.get('errorCode', False):
            error_code = txt['errorCode'][0]
            self.message = self.get_response_msg(error_code)
            self.env['audit.trails'].create({
                'booking_id': self.booking_id.id,
                'folio_id': self.id,
                'user_id': self.env.user.id,
                'operation': 'ntmp',
                'datetime': fields.Datetime.now(),
                'notes': f"Transaction ID: {self.ntmp_transaction_id}, Message: {self.message}, {response.text}"
            })

        return self.action_refresh()

    def prepare_ntmp_headers(self):
        return {
            "Content-Type": "application/json",
            "x-Gateway-APIKey": self.company_id.ntmp_key,
        }

    def prepare_ntmp_data(self, mode, new=False):
        if self.total_nights > 0:
            daily_room_rate = str(round((self.room_price_subtotal / self.total_nights), 2))
        else:
            daily_room_rate = "0"
        if mode == 'booking':
            trx_type = "1"
        elif mode == 'check_in':
            trx_type = "2"
        else:
            trx_type = "3"
        return {
            "channel": self.company_id.ntmp_channel if self.company_id.ntmp_channel else "",
            "bookingNo": self.name,
            "nationalityCode": self.nationality_id.code if self.nationality_id else "900",
            "checkInDate": self.check_in_date.strftime('%Y%m%d'),
            "checkOutDate": self.check_out_date.strftime('%Y%m%d'),
            "totalDurationDays": str(self.total_nights),
            "allotedRoomNo": str(self.room_id.name) if self.room_id else "0",
            "roomRentType": self.rent_type_id.code if self.rent_type_id else "1",
            "dailyRoomRate": daily_room_rate,
            "totalRoomRate": str(self.room_price_subtotal) if self.room_price_subtotal else "0",
            "vat": str(round(self.price_vat, 2)) if self.price_vat else "0",
            "municipalityTax": str(round(self.price_municipality, 2)) if self.price_municipality else "0",
            "discount": str(round(abs(self.room_price_discount), 2)) if self.room_price_discount else "0",
            "grandTotal": str(self.room_price_total) if self.room_price_total else "0",
            "transactionTypeId": trx_type,
            "gender": self.gender_id.code if self.gender_id else "0",
            "transactionId": "" if new else self.ntmp_transaction_id,  # todo to be handled
            "checkInTime": "000000",  # todo to be handled
            "checkOutTime": "000000",  # todo to be handled
            "customerType": self.customer_type_id.code if self.customer_type_id else "3",
            "noOfGuest": "1",  # todo to be handled
            "roomType": self.ntmp_room_type_id.code if self.ntmp_room_type_id else "13",
            "purposeOfVisit": self.visit_purpose_id.code if self.visit_purpose_id else "7",
            "dateOfBirth": "0",  # todo to be handled
            "paymentType": "1",
            "noOfRooms": "1",
            "cuFlag": "1" if new else "2"
        }

    def get_response_msg(self, code):
        msg = False
        if code:
            response = self.env['ntmp.response.code'].search([
                ('api_name', '=', 'createOrUpdateBooking'), ('error_code', '=', code)
            ], limit=1)
            if response:
                if response.category == 'success':
                    msg = 'Synced Successfully with NTMP'
                else:
                    msg = response.error_description
        return msg

    # bookingExpense
    def ntmp_expense_connect(self):
        url = "https://api.ntmp.gov.sa/gateway/BookingExpense/1.0/bookingExpense"
        headers = self.prepare_ntmp_headers()
        data = self.prepare_expense_data()
        response = requests.post(url=url, headers=headers, json=data,
                                 auth=HTTPBasicAuth(self.company_id.ntmp_username, self.company_id.ntmp_password))
        txt = json.loads(response.text)
        if txt.get('errorCode', False):
            error_code = txt['errorCode'][0]
            message = self.get_expense_response_msg(error_code)
            # todo error code 13 not exist
            self.env['audit.trails'].create({
                'booking_id': self.booking_id.id,
                'folio_id': self.id,
                'user_id': self.env.user.id,
                'operation': 'ntmp',
                'datetime': fields.Datetime.now(),
                'notes': f"Transaction ID: {self.ntmp_transaction_id}, {response.text}, {message}"
            })

    def prepare_expense_data(self):
        return {
            "transactionId": self.ntmp_transaction_id,
            "userId": self.company_id.ntmp_username or "",
            "channel": self.company_id.ntmp_channel or "",
            "expenseItems": self.prepare_expense_items()
        }

    def prepare_expense_items(self):
        items = []
        for expense in self.line_ids.filtered(lambda l: l.ntmp_service_id and l.ntmp_item_number):
            total = expense.amount
            vat = self.line_ids.filtered(lambda l: l.related_line_id.id == expense.id and l.tax_type == 'vat')
            if vat:
                total += vat.amount
            municipality = self.line_ids.filtered(
                lambda l: l.related_line_id.id == expense.id and l.tax_type == 'municipality')
            if municipality:
                total += municipality.amount
            discount_related_line = self.line_ids.filtered(
                lambda l: l.discount_related_line.id == expense.id and l.type == 'discount'
            )

            items.append({
                "expenseDate": expense.day.strftime('%Y%m%d'),
                "itemNumber": expense.ntmp_item_number,
                "expenseTypeId": expense.ntmp_service_id.code if expense.ntmp_service_id else "0",
                "unitPrice": str(round(expense.amount, 2)),
                "discount": str(round(abs(discount_related_line.amount), 2)) if discount_related_line else "0",
                "vat": str(round(vat.amount, 2)) if vat else "0",
                "municipalityTax": str(round(municipality.amount, 2)) if municipality else "0",
                "grandTotal": str(total),
                "paymentType": "1",
                "cuFlag": "1"
            })
        return items

    # todo refactor
    def get_expense_response_msg(self, code):
        msg = False
        if code:
            response = self.env['ntmp.response.code'].search([
                ('api_name', '=', 'bookingExpense'), ('error_code', '=', code)
            ], limit=1)
            if response:
                if response.category == 'success':
                    msg = 'Synced Successfully with NTMP'
                else:
                    msg = response.error_description
        return msg

    def get_folio_ntmp_fields(self):
        return [
            "check_in", "check_out", "total_nights", "room_id", "rent_type_id", "nationality_id", "visit_purpose",
            "gender_id", "customer_type_id", "price_total"
        ]

    def archive_folio_lines(self):
        lines = self.line_ids.filtered(lambda l: not l.is_cancellation_fee).ids
        # cancellation_fee = sum(self.line_ids.filtered(lambda l: l.is_cancellation_fee).mapped('amount'))
        if lines:
            query_line = """
                UPDATE booking_folio_line
                SET active=False , amount = 0
                WHERE payment_id IS NULL AND id in %s
            """
            params = [tuple(lines)]
            self.env.cr.execute(query_line, params)

        # Update the booking_folio records based on the related lines
        cancel_lines = self.line_ids.filtered(lambda l: l.is_cancellation_fee)
        price_municipality = sum(cancel_lines.filtered(lambda l: l.tax_type == 'municipality').mapped('amount'))
        price_vat = sum(cancel_lines.filtered(lambda l: l.tax_type == 'vat').mapped('amount'))
        room_price_subtotal = sum(cancel_lines.filtered(lambda l: l.type == 'room_charge').mapped('amount'))
        room_price_tax = price_municipality + price_vat
        room_price_total = room_price_tax + room_price_subtotal
        price_paid = abs(sum(self.line_ids.filtered(lambda l: l.payment_id and l.is_cancellation_fee).mapped('amount')))
        price_due = room_price_total - price_paid
        query_folio = """
            UPDATE booking_folio
            SET price_subtotal = %s, price_total = %s, price_due = %s, price_tax = %s,room_price_total = %s , room_price_subtotal = %s,room_price_tax = %s,price_vat = %s,price_municipality = %s
            WHERE id = %s
        """
        self.env.cr.execute(query_folio, (room_price_subtotal, room_price_total, price_due, room_price_tax, room_price_total, room_price_subtotal, room_price_tax, price_vat, price_municipality, self.id,))

        # Invalidate cache
        self.invalidate_cache()

    def button_cancel(self):
        try:
            # set a context for selected folio to get cancel without raise wizard in confirmed folio
            if self.apply_ntmp and self.state != 'draft' and not self.env.context.get('selected_folio'):
                _logger.info("==========================================================================================")
                _logger.info("==========================inside button cancel if================================")
                _logger.info(f"====state {self.apply_ntmp}")
                _logger.info(f"====state {self.state}")
                _logger.info(f"====context {self.env.context.get('selected_folio')}")
                _logger.info("==========================================================================================")
                return {
                    'type': 'ir.actions.act_window',
                    'name': "Cancel Folio",
                    'res_model': 'folio.cancel',
                    'view_mode': 'form',
                    'target': 'new',
                    'context': {
                        'default_folio_id': self.id,
                    }
                }
            else:
                _logger.info("==========================================================================================")
                _logger.info("==========================inside button cancel else================================")
                _logger.info("==========================================================================================")
                paid_amount = sum(self.line_ids.filtered(lambda l: l.payment_id and not l.is_cancellation_fee).mapped('amount'))
                if any(self.line_ids.filtered(lambda l: l.particulars == 'City Ledger')):
                    raise ValidationError(f"Please remove City Ledger line from {self.name} before cancellation!")
                if paid_amount > 0 and not self.booking_id.payment_type_id == 'city_ledger':
                    raise ValidationError(f"Please Refund paid amount for {self.name} before cancellation!")
                cancellation_payments = abs(sum(self.line_ids.filtered(lambda l: l.payment_id and l.is_cancellation_fee).mapped('amount')))
                cancellation_fee = sum(self.line_ids.filtered(lambda l: not l.payment_id and l.is_cancellation_fee).mapped('amount'))
                if self.price_paid > 0:
                    if self.price_paid != cancellation_payments and not self.booking_id.payment_type_id == 'city_ledger':
                        raise ValidationError(f"Please Refund paid amount for {self.name} before cancellation!")
                else:
                    if cancellation_fee > cancellation_payments:
                        raise ValidationError(f"Please register cancellation fee for {self.name} before cancellation!")
                if self.room_id:
                    self.room_id.write({
                        'stay_state': self.env.ref('hotel_booking.hotel_room_stay_status_vacant').id
                    })
                if self.booking_id.payment_type_id == 'city_ledger':
                    payment_ids = self.line_ids.filtered(lambda l: l.amount < 0.0)
                    for line in payment_ids:
                        line.payment_id.action_draft()
                        line.payment_id.unlink()
                        line.unlink()
                self.archive_folio_lines()
                self.state = 'cancelled'

                cancelled_folios = self.booking_id.folio_ids.filtered(lambda l: l.state == 'cancelled')
                if len(cancelled_folios) == len(self.booking_id.folio_ids):
                    self.booking_id.state = 'cancelled'
                audit_trails_obj = self.env['audit.trails'].create({
                    'booking_id': self.booking_id.id,
                    'folio_id': self.id,
                    'user_id': self.env.user.id,
                    'operation': 'cancel_folio',
                    'datetime': fields.Datetime.now(),
                    'notes': f'Folio {self.name} is Cancelled'
                })
        except Exception as e:
            logger.info(f'ntmp connector button_cancel error {e}')
            logger.info(f'ntmp connector button_cancel error {traceback.format_exc()}')
            raise ValidationError(e.name) from e


class FolioLine(models.Model):
    _inherit = 'booking.folio.line'

    ntmp_item_number = fields.Char()
    ntmp_service_id = fields.Many2one('ntmp.expense.type', string='NTMP Expense')
    active = fields.Boolean(default=True, help="If unchecked, this record will be archived and hidden from the views.")
