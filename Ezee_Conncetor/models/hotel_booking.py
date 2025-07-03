import json
from datetime import datetime

import requests
from dateutil.relativedelta import relativedelta

from odoo import fields, models, api
from odoo.exceptions import ValidationError, _logger
from .rest_htask import HTASK
import  traceback
import logging
logger = logging.getLogger(__name__)


class HotelBooking(models.Model):
    _inherit = 'hotel.booking'
    _htask_type = "Bookings"

    sub_booking_id = fields.Char(string='Sub Booking ID')
    ezee_apply_daily_price = fields.Boolean()
    ntmp_to_be_cancel = fields.Boolean()

    def button_confirm(self):
        res = super(HotelBooking, self).button_confirm()
        self.cron_update_inventory()
        _logger.info("++++++++++ Update Inv Finished ++++++")
        return res

    def check_cancel_refund(self):
        errors = []
        for folio in self.folio_ids:
            if folio.price_paid > 0 and not self.payment_type_id == 'city_ledger':
                # create audit log
                self.env['audit.trails'].create({
                    'booking_id': self.id,
                    'user_id': self.env.user.id,
                    'operation': 'ezee_error',
                    'datetime': fields.Datetime.now(),
                    'notes': str(f"Please Refund paid amount for {self.name} before cancellation!"),
                    'ezee_reference': self.sub_booking_id
                })
                errors.append(True)
        return errors

    @api.model
    def cron_ntmp_cancel_bookings(self):
        bookings = self.env['hotel.booking'].sudo().search([('ntmp_to_be_cancel', '=', True)])
        if bookings:
            for booking in bookings:
                if booking.company_id.apply_ntmp:
                    wizard = self.env['folio.cancel'].create({
                        'booking_id': booking.id,
                        'reason_id': 1,
                        'cancel_with_charge': '0',
                    })
                    wizard.button_cancel_folio()
                    booking.ntmp_to_be_cancel = False

    def button_cancel(self):
        try:
            res = super(HotelBooking, self).button_cancel()
            if self.hotel_id.enable_ezee:
                self.cancel_ezee_booking()
                self.cron_update_inventory()
            return res
        except Exception as e:
            # create audit log
            self.env['audit.trails'].create({
                'booking_id': self.id,
                'user_id': self.env.user.id,
                'operation': 'ezee_error',
                'datetime': fields.Datetime.now(),
                'notes': str(e),
                'ezee_reference': self.sub_booking_id
            })
            raise ValidationError(e.name) from e

    def cron_update_inventory(self):
        companies = self.env['res.company'].sudo().search([('related_hotel_id.enable_ezee', '=', True)])
        _logger.info(f"++++++++++ companies {companies} ++++++")
        for company in companies:
            _logger.info(f"++++++++++ company {company.name} ++++++")
            if self.id:
                start = self.new_check_in
                end = self.new_check_out
                _logger.info(f"++++++++++ Duration (id) Start {start} End {end} ++++++")

            else:
                start = company.audit_date
                end = start + relativedelta(days=30)
                _logger.info(f"++++++++++ Duration Start {start} End {end} ++++++")

            wizard = self.env['ezee.connector'].create({
                'date_from': start,
                'date_to': end,
                'action_type': 'update_inventory',
                'company_id': company.id,
            })
            wizard.button_search()
            wizard.button_update_inventory()

    def fetch_and_create_ezee_bookings(self):
        companies = self.env['res.company'].sudo().search([('related_hotel_id.enable_ezee', '=', True)])
        _logger.info(f"++++++++++ Get Online Booking companies {companies} ++++++")
        for company in companies:
            _logger.info(f"++++++++++ Online company {company.name} ++++++")
            hotel = company.related_hotel_id
            url = f"{hotel.ezee_base_url}pmsinterface/pms_connectivity.php"

            htask_booking = HTASK.get_htask_connector(self, self._htask_type)

            params = {
                "RES_Request": {
                    "Request_Type": "Bookings",
                    "Authentication": {
                        "HotelCode": hotel.ezee_hotel_code,
                        "AuthCode": hotel.ezee_api_key
                    }
                }
            }
            res = htask_booking.get_post(arguments={}, data=params, custom_url=url)
            _logger.info(f"++++++++++ {res} RES ++++++")
            received_bookings = []
            daily_prices = []
            extra_charges = []
            booking_type_objs = None
            source_partner = None
            reservations_dic = res.get('Reservations', False)
            _logger.info(f"++++++++++ reservations_dic {reservations_dic} ++++++")
            if reservations_dic and isinstance(reservations_dic, dict):
                cancel_reservations = reservations_dic.get('CancelReservation', [])
                if cancel_reservations:
                    for cancel_res in cancel_reservations:
                        if cancel_res.get('UniqueID', False):
                            UniqueID = cancel_res['UniqueID']
                            UniqueID_splitted = UniqueID.split("-")
                            if len(UniqueID_splitted) > 1:
                                UniqueID = UniqueID_splitted[0]
                            cancel_booking = self.env['hotel.booking'].search([('sub_booking_id', '=', UniqueID), ('company_id', '=', company.id)])
                            if cancel_booking:
                                if cancel_booking.state != 'cancelled':
                                    for inv in cancel_booking.invoice_ids:
                                        inv.button_cancel()
                                    cancel_booking.state = 'cancelled'
                                    for folio in cancel_booking.folio_ids:
                                        folio.with_context(selected_folio=True).button_cancel()
                                    if cancel_booking.state == 'cancelled':
                                        received_bookings.append(cancel_booking)
                                        self.env['audit.trails'].create({
                                            'user_id': self.env.user.id,
                                            'operation': 'ezee',
                                            'datetime': fields.Datetime.now(),
                                            'booking_id': cancel_booking.id,
                                            'notes': f"Booking {cancel_booking.name} cancelled via eZee sync.",
                                        })
                                    cancel_booking.ntmp_to_be_cancel = True
                                else:
                                    received_bookings.append(cancel_booking)
                # active reservations
                if reservations_dic != 'No Reservation Found':
                    reservation_confirmed_dict = list(reservations_dic.keys())[0]
                    reservation_confirmed_dict_value = reservations_dic[reservation_confirmed_dict]
                    if reservation_confirmed_dict_value:
                        _logger.info(f"++++++++++ Booking Reservation {reservation_confirmed_dict_value} ++++++")
                        for book in reservation_confirmed_dict_value:
                            lines_list = []
                            partner_name = book['FirstName'] + " " + book['LastName']
                            partner_vals = {
                                'name': partner_name,
                                'mobile': book['Mobile'],
                                'email': book['Email'],
                            }
                            partner = self.env['res.partner'].search([('name', '=', partner_name)], limit=1)
                            if not partner:
                                res_partner_obj = self.env['res.partner'].sudo().create(partner_vals)
                            else:
                                res_partner_obj = self.env['res.partner'].sudo().write(partner_vals)

                            check_in = False
                            new_check_in = False
                            check_out = False
                            new_check_out = False
                            total_nights = False
                            line = False
                            for line in book['BookingTran']:
                                reservation_type = line['CurrentStatus']
                                booking_type_objs = self.env['booking.type'].search([('name', '=', reservation_type)], limit=1)
                                if not booking_type_objs:
                                    booking_type_objs = self.env['booking.type'].sudo().create({'name': reservation_type})
                                room_type_obj = self.env['room.type'].search(
                                    [('ezee_room_type_id.code', '=', line['RoomTypeCode'])], limit=1)
                                if not room_type_obj:
                                    raise ValidationError(f"There is no room type with code {line['RoomTypeCode']}")
                                rate_plan_name = self.env['hotel.rate.plan'].sudo().search(
                                    [('ezee_rate_plan_id.code', '=', line['RateplanCode'])], limit=1)
                                if not rate_plan_name:
                                    raise ValidationError(f"There is no rate plan with code {line['RateplanCode']}")
                                new_check_in = datetime.strptime(f'{line["Start"]}', '%Y-%m-%d')
                                check_in = datetime.combine(new_check_in, datetime.min.time())
                                new_check_out = datetime.strptime(f'{line["End"]}', '%Y-%m-%d')
                                check_out = datetime.combine(new_check_out, datetime.min.time())
                                total_nights = check_out - check_in
                                source_partner = self.env['res.partner'].search([('name', '=', line['Source'])], limit=1)
                                if not source_partner:
                                    source_partner = self.env['res.partner'].sudo().create({'name': line['Source']})
                                for rental in line['RentalInfo']:
                                    try:
                                        room_type_obj.ezee_room_type_id.sudo().write({
                                            'name': rental['RoomTypeName'],
                                            'code': rental['RoomTypeCode'],
                                        })
                                    except Exception as e:
                                        _logger.info(f'error in write ezee room type {e}')
                                        _logger.info(f'error in write ezee room type {traceback.format_exc()}')
                                    # create daily price from ezee response
                                    daily_prices.append((0, 0, {
                                        'rate_plan_id': rate_plan_name.id,
                                        'room_type_id': room_type_obj.id,
                                        'price': rental['RentPreTax'],
                                        'date': rental['EffectiveDate'],
                                    }))
                                # price_include_tax
                                price_include_tax = False
                                if line.get('TotalTax', False):
                                    if float(line['TotalTax']) == 0:
                                        price_include_tax = True
                                lines_list.append((0, 0, {
                                    'ezee_transaction_id': line['TransactionId'],
                                    'room_type': room_type_obj.id,
                                    'rate_plan': rate_plan_name.id,
                                    'tax_id': rate_plan_name.sudo().tax_ids.filtered(lambda t: t.price_include).ids,
                                    'price_include_tax': price_include_tax,
                                    'number_of_rooms': 1,
                                }))
                            if check_in and check_out and total_nights and line:
                                voucher_no = line['VoucherNo']
                                _logger.info(f"++++++++++ REF >>>>> {voucher_no}")
                                booking_vals = {
                                    'partner_id': partner.id if partner else res_partner_obj.id,
                                    'booking_source': 'online_agent',
                                    'online_travel_agent_source': source_partner.id if source_partner else None,
                                    'sub_booking_id': book['UniqueID'],
                                    'ref': voucher_no,
                                    'check_in': check_in,
                                    'new_check_in': new_check_in,
                                    'check_out': check_out,
                                    'new_check_out': new_check_out,
                                    'total_nights': total_nights.days,
                                    'reservation_type': booking_type_objs.id,
                                    'note': line['Comment'],
                                    'company_id': company.id,
                                    'apply_daily_price': False,
                                    'ezee_apply_daily_price': True,
                                    'daily_price_ids': daily_prices,
                                }
                                _logger.info(f"++++++++++ booking_vals {booking_vals} ++++++")
                                hotel_booking_obj = self.env['hotel.booking'].sudo().search([
                                    ('sub_booking_id', '=', book['UniqueID']), ('state', '!=', 'cancelled'),
                                    ('company_id', '=', company.id)
                                ])
                                if hotel_booking_obj:
                                    if hotel_booking_obj.partner_id == booking_vals['partner_id']:
                                        booking_vals.pop('partner_id', False)
                                    if hotel_booking_obj.booking_source == booking_vals['booking_source']:
                                        booking_vals.pop('booking_source', False)
                                    if hotel_booking_obj.online_travel_agent_source == booking_vals[
                                        'online_travel_agent_source']:
                                        booking_vals.pop('online_travel_agent_source', False)
                                    if hotel_booking_obj.sub_booking_id == booking_vals['sub_booking_id']:
                                        booking_vals.pop('sub_booking_id', False)
                                    if hotel_booking_obj.check_in == booking_vals['check_in']:
                                        booking_vals.pop('check_in', False)
                                    if hotel_booking_obj.new_check_in == booking_vals['new_check_in']:
                                        booking_vals.pop('new_check_in', False)
                                    if hotel_booking_obj.check_out == booking_vals['check_out']:
                                        booking_vals.pop('check_out', False)
                                    if hotel_booking_obj.new_check_out == booking_vals['new_check_out']:
                                        booking_vals.pop('new_check_out', False)
                                    if hotel_booking_obj.reservation_type == booking_vals['reservation_type']:
                                        booking_vals.pop('reservation_type', False)
                                    if hotel_booking_obj.note == booking_vals['note']:
                                        booking_vals.pop('note', False)
                                    if hotel_booking_obj.company_id.id == booking_vals['company_id']:
                                        booking_vals.pop('company_id', False)
                                    if hotel_booking_obj.apply_daily_price == booking_vals['apply_daily_price']:
                                        booking_vals.pop('apply_daily_price', False)

                                    if not booking_vals:
                                        self.env['audit.trails'].create({
                                            'user_id': self.env.user.id,
                                            'operation': 'ezee',
                                            'datetime': fields.Datetime.now(),
                                            'notes': f"booking already exist and has no changes to be updated {hotel_booking_obj.name}",
                                            'ezee_reference': booking_vals.get('sub_booking_id', False)
                                        })
                                    # check for check in/out in past
                                    booking_check_in = booking_vals.get('new_check_in', False).date() if booking_vals.get(
                                        'new_check_in', False) else hotel_booking_obj.check_in_date
                                    if booking_check_in and booking_check_in < hotel_booking_obj.company_id.audit_date:
                                        # create audit log
                                        self.env['audit.trails'].create({
                                            'booking_id': hotel_booking_obj.id,
                                            'user_id': self.env.user.id,
                                            'operation': 'ezee_error',
                                            'datetime': fields.Datetime.now(),
                                            'notes': "check in date can't be in past!",
                                            'ezee_reference': booking_vals.get('sub_booking_id',
                                                                               hotel_booking_obj.sub_booking_id)
                                        })
                                        continue
                                    booking_check_out = booking_vals.get('new_check_out', False).date() if booking_vals.get(
                                        'new_check_out', False) else hotel_booking_obj.check_out_date
                                    if booking_check_out and booking_check_out < hotel_booking_obj.company_id.audit_date:
                                        # create audit log
                                        self.env['audit.trails'].create({
                                            'booking_id': hotel_booking_obj.id,
                                            'user_id': self.env.user.id,
                                            'operation': 'ezee_error',
                                            'datetime': fields.Datetime.now(),
                                            'notes': "check out date can't be in past!",
                                            'ezee_reference': booking_vals.get('sub_booking_id',
                                                                               hotel_booking_obj.sub_booking_id)
                                        })
                                        continue
                                    try:
                                        if hotel_booking_obj.state in ["checked_in", "checked_out"]:
                                            self.env['audit.trails'].create({
                                                'user_id': self.env.user.id,
                                                'operation': 'ezee',
                                                'datetime': fields.Datetime.now(),
                                                'booking_id': hotel_booking_obj.id,
                                                'notes': f"Booking {hotel_booking_obj.name} is already checked in or checked out and can't be updated",
                                            })
                                            continue
                                        else:
                                            hotel_booking_obj.sudo().write(booking_vals)
                                            received_bookings.append(hotel_booking_obj)
                                            self.env['audit.trails'].create({
                                                'user_id': self.env.user.id,
                                                'operation': 'ezee',
                                                'datetime': fields.Datetime.now(),
                                                'booking_id': hotel_booking_obj.id,
                                                'notes': f"Booking successfully updated from eZee with sub_booking_id: {booking_vals.get('sub_booking_id', hotel_booking_obj.sub_booking_id)}",
                                            })
                                    except Exception as e:
                                        # create audit log
                                        self.env['audit.trails'].create({
                                            'booking_id': hotel_booking_obj.id,
                                            'user_id': self.env.user.id,
                                            'operation': 'ezee_error',
                                            'datetime': fields.Datetime.now(),
                                            'notes': str(e),
                                            'ezee_reference': booking_vals.get('sub_booking_id',
                                                                               hotel_booking_obj.sub_booking_id)
                                        })
                                        continue
                                else:
                                    booking_check_in = booking_vals['new_check_in'].date()
                                    if booking_check_in and booking_check_in < company.audit_date:
                                        # create audit log
                                        self.env['audit.trails'].create({
                                            'user_id': self.env.user.id,
                                            'operation': 'ezee_error',
                                            'datetime': fields.Datetime.now(),
                                            'notes': "check in date can't be in past!",
                                            'ezee_reference': booking_vals.get('sub_booking_id', False)
                                        })
                                        continue
                                    booking_check_out = booking_vals['new_check_out'].date()
                                    if booking_check_out and booking_check_out < company.audit_date:
                                        # create audit log
                                        self.env['audit.trails'].create({
                                            'user_id': self.env.user.id,
                                            'operation': 'ezee_error',
                                            'datetime': fields.Datetime.now(),
                                            'notes': "check out date can't be in past!",
                                            'ezee_reference': booking_vals.get('sub_booking_id', False)
                                        })
                                        continue
                                    try:
                                        hotel_booking_obj = self.env['hotel.booking'].sudo().create(booking_vals)
                                        hotel_booking_obj.write({
                                            'line_ids': lines_list
                                        })
                                        hotel_booking_obj.button_confirm()
                                        received_bookings.append(hotel_booking_obj)
                                        self.env['audit.trails'].create({
                                        'user_id': self.env.user.id,
                                        'operation': 'ezee',
                                        'datetime': fields.Datetime.now(),
                                        'booking_id': hotel_booking_obj.id,
                                        'notes': f"Booking successfully created from eZee with sub_booking_id: {booking_vals.get('sub_booking_id', False)}",
                                        })
                                        if not hotel_booking_obj.online_travel_agent_source:
                                            self.env['audit.trails'].create({
                                                'user_id': self.env.user.id,
                                                'operation': 'ezee',
                                                'datetime': fields.Datetime.now(),
                                                'booking_id': hotel_booking_obj.id,
                                                'notes': f"case no online_travel_agent_source\nsource_partner:{source_partner},partner:{partner}",
                                                'ezee_reference': booking_vals.get('sub_booking_id', False)
                                            })

                                    except Exception as e:
                                        # create audit log
                                        self.env['audit.trails'].create({
                                            'user_id': self.env.user.id,
                                            'operation': 'ezee_error',
                                            'datetime': fields.Datetime.now(),
                                            'notes': str(e),
                                            'ezee_reference': booking_vals.get('sub_booking_id', False)
                                        })
                                        continue
                                # create extra lines after folios is created
                                for booking_line in book['BookingTran']:
                                    ezee_booking_line = hotel_booking_obj.line_ids.filtered(
                                        lambda l: l.ezee_transaction_id == booking_line['TransactionId'])
                                    if ezee_booking_line:
                                        if ezee_booking_line.folio_ids:
                                            folio = ezee_booking_line.folio_ids[0]
                                            for charge in line.get('ExtraCharge', []):
                                                service = self.env['ezee.extra.charge'].search([
                                                    ('name', '=', charge['ChargeName']),
                                                    ('short_code', '=', charge['ChargeCode'])
                                                ], limit=1)
                                                service = self.env['hotel.services'].search(
                                                    [('ezee_charge_id', '=', service.id)])
                                                if service:
                                                    service_line = self.env['booking.folio.line'].create({
                                                        'folio_id': folio.id,
                                                        'day': charge.get('ChargeDate', False),
                                                        'amount': float(charge['AmountBeforeTax']),
                                                        'particulars': service.name,
                                                        'type': service.type,
                                                    })
                                                    self.env['booking.folio.line'].create({
                                                        'folio_id': folio.id,
                                                        'day': charge.get('ChargeDate', False),
                                                        'amount': float(charge['AmountAfterTax']) - float(
                                                            charge['AmountBeforeTax']),
                                                        'particulars': service.name + ' VAT',
                                                        'type': 'tax',
                                                        'is_service_tax': True,
                                                        'related_line_id': service_line.id,
                                                        'tax_type': 'vat',
                                                    })
                # Booking Received Notification
                if received_bookings:
                    _logger.info(f"++++++++++ Received Booking Done ++++++")
                    bookings = [{"BookingId": b.sub_booking_id, "PMS_BookingId": b.name} for b in received_bookings if
                                b.sub_booking_id]
                    r_params = {
                        "RES_Request": {
                            "Request_Type": "BookingRecdNotification",
                            "Authentication": {
                                "HotelCode": hotel.ezee_hotel_code,
                                "AuthCode": hotel.ezee_api_key
                            },
                            "Bookings": {
                                "Booking": bookings
                            }
                        }
                    }
                    response = htask_booking.get_post(arguments={}, data=r_params, custom_url=url)
                    if response.get('Errors', False):
                        if response['Errors'].get('ErrorMessage', False):
                            for r_booking in received_bookings:
                                self.env['audit.trails'].create({
                                    'user_id': self.env.user.id,
                                    'booking_id': r_booking.id,
                                    'operation': 'ezee',
                                    'datetime': fields.Datetime.now(),
                                    'notes': f"Booking Received Notification {response['Errors']['ErrorMessage']}",
                                })

    def write(self, vals):
        res = super(HotelBooking, self).write(vals)
        logger.info(f'caleeeed writeeeee {self}')
        if self.hotel_id.enable_ezee and self.ezee_apply_daily_price:
            update_inventory = False
            if vals.get('state', False):
                if vals['state'] == 'cancelled':
                    update_inventory = True
                    # cancel ezee booking
                    self.cancel_ezee_booking()
                    self.cron_update_inventory()
            elif vals.get('new_check_in', False) or vals.get('new_check_out', False):
                update_inventory = True
            if update_inventory:
                logger.info(f'caleeeed writeeeee {res}-- {self.check_in_date}--{self.check_out_date}')
                wizard = self.env['ezee.connector'].create({
                    'date_from': self.check_in_date,
                    'date_to': self.check_out_date,
                    'action_type': 'update_inventory',
                    'company_id': self.company_id.id,
                    'room_type_ids': [(6, 0, self.line_ids.mapped('room_type').mapped('id'))],
                })
                wizard.button_search()
                wizard.button_update_inventory()
                self.env['audit.trails'].create({
                    'booking_id': self.id,
                    'user_id': self.env.user.id,
                    'operation': 'ezee',
                    'datetime': fields.Datetime.now(),
                    'notes': wizard.note
                })
        return res

    def cancel_ezee_booking(self):
        base_url = self.hotel_id.ezee_base_url
        url = f"{base_url}booking/reservation_api/listing.php"
        params = {
            "request_type": "CancelBooking",
            "HotelCode": self.hotel_id.ezee_hotel_code,
            "APIKey": self.hotel_id.ezee_api_key,
            "language": "en",
            "ResNo": int(self.sub_booking_id),
            "publishtoweb": "1"
        }
        response = requests.get(url, params=params)
        data = json.loads(response.content)
        _logger.info(f"++++++++++ data response {data}++++++")
        if data:
            notes = ''
            if isinstance(data, list):
                notes = f"Ezee Booking Cancelled {data[0].get('status', '')}"
            elif isinstance(data, dict):
                notes = f"Ezee Booking Cancelled {data.get('status', '')}"
            self.env['audit.trails'].create({
                'booking_id': self.id,
                'user_id': self.env.user.id,
                'operation': 'ezee',
                'datetime': fields.Datetime.now(),
                'notes': notes
            })
