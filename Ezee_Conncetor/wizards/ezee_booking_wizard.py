import json
from datetime import datetime

import requests

from odoo import fields, models, _
from odoo.exceptions import ValidationError, _logger


class EzeeBookingWizard(models.TransientModel):
    _name = 'ezee.booking.wizard'
    _description = 'Ezee Booking Wizard'

    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, required=True)
    sub_booking_id = fields.Char(required=True)

    def get_booking(self):
        hotel = self.company_id.related_hotel_id
        url = f"{hotel.ezee_base_url}pmsinterface/pms_connectivity.php"
        params = {
            "RES_Request": {
                "Request_Type": "FetchSingleBooking",
                "BookingId": self.sub_booking_id,
                "Authentication": {
                    "HotelCode": hotel.ezee_hotel_code,
                    "AuthCode": hotel.ezee_api_key
                }
            }
        }
        headers = {
            "Content-Type": "application/json"
        }
        response = requests.post(url, headers=headers, json=params)
        res = json.loads(response.content)
        received_bookings = []
        daily_prices = []
        extra_charges = []
        booking_type_objs = None
        source_partner = None
        reservations_dic = res.get('Reservations', False)
        if reservations_dic:
            # cancel reservations
            cancel_reservations = reservations_dic.get('CancelReservation', False)
            if cancel_reservations:
                for cancel_res in cancel_reservations:
                    if cancel_res.get('UniqueID', False):
                        cancel_booking = self.env['hotel.booking'].search(
                            [('sub_booking_id', '=', cancel_res['UniqueID']), ('company_id', '=', self.company_id.id)])
                        if cancel_booking and cancel_booking.state != 'cancelled':
                            cancel_booking.button_cancel()
                            if cancel_booking.state == 'cancelled':
                                received_bookings.append(cancel_booking)
            # active reservations
            reservation_confirmed_dict = list(reservations_dic.keys())[0]
            reservation_confirmed_dict_value = reservations_dic[reservation_confirmed_dict]
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
                        room_type_obj.ezee_room_type_id.sudo().write({
                            'name': rental['RoomTypeName'],
                            'code': rental['RoomTypeCode'],
                        })
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
                        'company_id': self.company_id.id,
                        'apply_daily_price': False,
                        'ezee_apply_daily_price': True,
                        'daily_price_ids': daily_prices,
                    }
                    hotel_booking_obj = self.env['hotel.booking'].sudo().search([
                        ('sub_booking_id', '=', book['UniqueID']), ('state', '!=', 'cancelled'),
                        ('company_id', '=', self.company_id.id)
                    ])
                    if hotel_booking_obj:
                        if hotel_booking_obj.partner_id == booking_vals['partner_id']:
                            booking_vals.pop('partner_id', False)
                        if hotel_booking_obj.booking_source == booking_vals['booking_source']:
                            booking_vals.pop('booking_source', False)
                        if hotel_booking_obj.online_travel_agent_source == booking_vals['online_travel_agent_source']:
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
                                'ezee_reference': booking_vals.get('sub_booking_id', hotel_booking_obj.sub_booking_id)
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
                                'ezee_reference': booking_vals.get('sub_booking_id', hotel_booking_obj.sub_booking_id)
                            })
                            continue
                        try:
                            hotel_booking_obj.sudo().write(booking_vals)
                            received_bookings.append(hotel_booking_obj)
                        except Exception as e:
                            # create audit log
                            self.env['audit.trails'].create({
                                'booking_id': hotel_booking_obj.id,
                                'user_id': self.env.user.id,
                                'operation': 'ezee_error',
                                'datetime': fields.Datetime.now(),
                                'notes': str(e),
                                'ezee_reference': booking_vals.get('sub_booking_id', hotel_booking_obj.sub_booking_id)
                            })
                            continue
                    else:
                        booking_check_in = booking_vals['new_check_in'].date()
                        if booking_check_in and booking_check_in < self.company_id.audit_date:
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
                        if booking_check_out and booking_check_out < self.company_id.audit_date:
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
                                        ('name', '=', charge['ChargeName']), ('short_code', '=', charge['ChargeCode'])
                                    ], limit=1)
                                    service = self.env['hotel.services'].search([('ezee_charge_id', '=', service.id)])
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
            response = requests.post(url, headers=headers, json=r_params)
            res = json.loads(response.content)
            if res.get('Errors', False):
                if res['Errors'].get('ErrorMessage', False):
                    for r_booking in received_bookings:
                        self.env['audit.trails'].create({
                            'user_id': self.env.user.id,
                            'booking_id': r_booking.id,
                            'operation': 'ezee',
                            'datetime': fields.Datetime.now(),
                            'notes': f"Booking Received Notification {res['Errors']['ErrorMessage']}",
                        })
        return {
            'type': 'ir.actions.act_window',
            'name': _('Get Ezee Booking'),
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'ezee.booking.wizard',
            'res_id': self.id,
            'target': 'new'
        }
