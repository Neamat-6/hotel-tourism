import requests
import json
from requests.auth import HTTPBasicAuth
from odoo import fields, models, api
from odoo.exceptions import ValidationError


class ModelName(models.TransientModel):
    _name = 'folio.cancel'
    _description = 'Folio Cancel'

    folio_id = fields.Many2one('booking.folio')
    booking_id = fields.Many2one('hotel.booking')
    reason_id = fields.Many2one('ntmp.cancel.reason', required=True)
    cancel_with_charge = fields.Selection(selection=[
        ('1', 'Yes'), ('0', 'No')
    ], required=True)
    chargeable_days = fields.Integer(default=0)

    def button_cancel_folio(self):
        folios = [self.folio_id]
        if self.booking_id:
            folios = self.booking_id.folio_ids
        for folio in folios:
            # todo check paid amount and chargeable_days are matching!
            if self.cancel_with_charge == '1' and self.chargeable_days <= 0:
                raise ValidationError("chargeable days must be more than 0!")
            if folio.state != 'draft':
                if self.env.company.apply_ntmp:
                    url = "https://api.ntmp.gov.sa/gateway/CancelBooking/1.0/cancelBooking"
                    headers = folio.prepare_ntmp_headers()
                    data = self.prepare_data()
                    response = requests.post(url=url, headers=headers, json=data,
                                             auth=HTTPBasicAuth(folio.company_id.ntmp_username, folio.company_id.ntmp_password))
                    if response.status_code == 524:
                        self.env['audit.trails'].create({
                            'booking_id': folio.booking_id.id or self.booking_id.id,
                            'folio_id': folio.id,
                            'user_id': self.env.user.id,
                            'operation': 'ntmp',
                            'datetime': fields.Datetime.now(),
                            'notes': "Time out"
                        })
                    else:
                        txt = json.loads(response.text)
                        if txt.get('errorCode', False):
                            error_code = txt['errorCode'][0]
                            message = self.get_response_msg(error_code)
                            self.env['audit.trails'].create({
                                'booking_id': folio.booking_id.id or self.booking_id.id,
                                'folio_id': folio.id,
                                'user_id': self.env.user.id,
                                'operation': 'ntmp',
                                'datetime': fields.Datetime.now(),
                                'notes': f"Transaction ID: {folio.ntmp_transaction_id}, {response.text}, {message}"
                            })
            if folio.room_id:
                folio.room_id.write({
                    'stay_state': self.env.ref('hotel_booking.hotel_room_stay_status_vacant').id
                })

            # folio.line_ids.filtered(lambda l: not l.payment_id).unlink()
            # todo we try to reduce time cancel
            lines_to_update = folio.line_ids.filtered(lambda l: not l.payment_id)
            if lines_to_update:
                lines_to_update.write({'amount': 0})

            folio.state = 'cancelled'
            cancelled_folios = folio.booking_id.folio_ids.filtered(lambda l: l.state == 'cancelled')
            folios = len(folio.booking_id.folio_ids)
            if len(cancelled_folios) == folios:
                folio.booking_id.update({'state': 'cancelled'})
        if self.booking_id:
            for inv in self.booking_id.invoice_ids:
                inv.button_cancel()
            self.booking_id.state = 'cancelled'
            return {'type': 'ir.actions.client', 'tag': 'reload'}
        else:
            return {
                'type': 'ir.actions.act_window',
                'name': "Folio",
                'res_model': 'booking.folio',
                'view_mode': 'form',
                'target': 'new',
                'res_id': self.folio_id.id
            }

    def prepare_data(self):
        folio = self.folio_id
        if self.cancel_with_charge == '1' and folio.total_nights > 0:
            daily_room_rate = str(folio.price_total / folio.total_nights)
        else:
            daily_room_rate = "0"
        return {
            "transactionId": self.folio_id.ntmp_transaction_id,
            "cancelReason": self.reason_id.code,
            "cancelWithCharges": self.cancel_with_charge,
            "chargeableDays": str(
                self.chargeable_days) if self.chargeable_days and self.cancel_with_charge == '1' else "0",
            "roomRentType": self.folio_id.rent_type_id.code if self.folio_id.rent_type_id else "1",
            "dailyRoomRate": daily_room_rate,
            "totalRoomRate": str(folio.price_total) if folio.price_total and self.cancel_with_charge == '1' else "0",
            "vat": "0",  # todo to be handled
            "municipalityTax": "0",  # todo to be handled
            "discount": "0",  # todo to be handled
            "grandTotal": str(folio.price_total) if folio.price_total and self.cancel_with_charge == '1' else "0",
            "userId": folio.company_id.ntmp_username or "",
            "paymentType": "4",
            "cuFlag": "2",
            "esbRefNo": "",
            "channel": folio.company_id.ntmp_channel
        }

    def get_response_msg(self, code):
        msg = False
        if code:
            response = self.env['ntmp.response.code'].search([
                ('api_name', '=', 'cancelBooking'), ('error_code', '=', code)
            ], limit=1)
            if response:
                if response.category == 'success':
                    msg = 'Synced Successfully with NTMP'
                else:
                    msg = response.error_description
        return msg
