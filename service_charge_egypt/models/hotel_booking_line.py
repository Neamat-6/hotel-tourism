from odoo import fields, models, api
import pytz
from dateutil.relativedelta import relativedelta


class BookingLine(models.Model):
    _inherit = 'hotel.booking.line'

    def update_folio(self, number_of_rooms, price=False, room_type=False, check_in=False,
                     check_out=False):
        if not self.env.context.get('ignore_all_update', False):
            timezone = pytz.timezone(self.env.user.tz or 'UTC')
            if check_in:
                check_in = pytz.utc.localize(check_in).astimezone(timezone)
            else:
                check_in = pytz.utc.localize(self.check_in).astimezone(timezone)
            if check_out:
                check_out = pytz.utc.localize(check_out).astimezone(timezone)
            else:
                check_out = pytz.utc.localize(self.check_out).astimezone(timezone)
            date_list = self.get_dates_between_exclude(check_in, check_out + relativedelta(days=1))
            if not self.booking_id.quick_group_booking:
                number_of_rooms = 1
            booking_folios = self.folio_ids
            if self.env.context.get('amend_stay', False):
                iterator = self.env.context.get('folio_id')
            else:
                iterator = range(0, number_of_rooms)
            for i in iterator:
                if self.env.context.get('update_existing_folio', False) or self.env.context.get(
                        'amend_stay', False):
                    if self.env.context.get('amend_stay', False):
                        folio = i
                    else:
                        folio = booking_folios[i]
                else:
                    folio = self.env['booking.folio'].create({
                        'booking_id': self.booking_id.id,
                        'booking_line_id': self.id,
                        'room_type_id': room_type if room_type else self.room_type.id,
                        'check_in': self.check_in,
                        'check_out': self.check_out,
                        'new_check_in': self.booking_id.new_check_in,
                        'new_check_out': self.booking_id.new_check_out,
                        'total_nights': self.booking_id.total_nights,
                        'available_room_ids': [(6, 0, self.available_room_ids.ids)],
                        'number_of_guests': self.number_of_adults,
                    })
                rate_plan = folio.booking_line_id.rate_plan
                rate_type = rate_plan.rate_type_id
                booking_line = folio.booking_line_id

                for day in date_list:
                    prices = self.get_prices(booking_line, day.date())
                    price_untaxed = prices['price_untaxed']
                    price_vat = prices['price_vat']
                    price_municipality = prices['price_municipality']
                    room_charge_deduction = 0
                    total_price = price_untaxed + price_vat + price_municipality
                    if rate_type.is_package:
                        for incl in rate_type.inclusion_ids:
                            vat_taxes = incl.service_id.tax_ids.filtered(lambda t: t.type == 'vat')
                            municipality_taxes = incl.service_id.tax_ids.filtered(
                                lambda t: t.type == 'municipality')
                            total_rate = incl.rate * folio.booking_line_id.number_of_adults
                            if incl.service_id.include_taxes:
                                if vat_taxes and municipality_taxes:
                                    service_net_amount = total_rate / 1.17875
                                    municipality_tax_amount = service_net_amount * 0.025
                                    vat_tax_amount = total_rate - service_net_amount - municipality_tax_amount
                                if vat_taxes and not municipality_taxes:
                                    service_net_amount = total_rate / 1.15
                                    vat_tax_amount = total_rate - service_net_amount
                                    municipality_tax_amount = 0
                            else:
                                service_net_amount = total_rate
                                vat_tax_amount = service_net_amount * 0.15
                                municipality_tax_amount = service_net_amount * 0.025

                            # price_untaxed -= room_charge_deduction
                            if day.date() == check_in.date() and incl.posting_rule in [
                                'everyday_no_check_in',
                                'everyday_no_check_in_out']:
                                room_charge_deduction += incl.rate * folio.booking_line_id.number_of_adults
                                continue
                            if day.date() == check_out.date() and incl.posting_rule in [
                                'everyday_no_check_out',
                                'everyday_no_check_in_out']:
                                room_charge_deduction += incl.rate * folio.booking_line_id.number_of_adults
                                continue
                            if day.date() != check_in.date() and incl.posting_rule in ['check_in',
                                                                                       'check_in_out']:
                                continue
                            if day.date() != check_out.date() and incl.posting_rule in ['check_out',
                                                                                        'check_in_out']:
                                continue
                            room_charge_deduction += incl.rate * folio.booking_line_id.number_of_adults
                            # if incl.service_id.include_taxes:
                            # create line for service
                            service_line = self.env['booking.folio.line'].create({
                                'folio_id': folio.id,
                                'number_of_adults': folio.booking_line_id.number_of_adults,
                                'day': day,
                                'amount': service_net_amount,
                                'particulars': incl.service_id.name,
                                'type': incl.service_id.type,
                            })
                            # create line for service taxes
                            if vat_tax_amount > 0:
                                self.env['booking.folio.line'].create({
                                    'folio_id': folio.id,
                                    'number_of_adults': folio.booking_line_id.number_of_adults,
                                    'day': day,
                                    'amount': vat_tax_amount,
                                    'particulars': 'VAT',
                                    'is_service_tax': True,
                                    'tax_type': 'vat',
                                    'type': 'tax',
                                    'related_line_id': service_line.id
                                })
                            # create line for service municipality
                            if municipality_tax_amount > 0:
                                self.env['booking.folio.line'].create({
                                    'folio_id': folio.id,
                                    'number_of_adults': folio.booking_line_id.number_of_adults,
                                    'day': day,
                                    'amount': municipality_tax_amount,
                                    'particulars': 'Service Charge',
                                    'is_service_tax': True,
                                    'tax_type': 'municipality',
                                    'type': 'tax',
                                    'related_line_id': service_line.id
                                })
                    final_vat = 0
                    final_municipality = 0
                    final_room_charge = 0
                    if self.env.context.get('update_existing_folio', False):
                        room_charge_line = folio.line_ids.filtered(
                            lambda l: l.day == day.date() and l.type == 'room_charge')
                        vat_line = folio.line_ids.filtered(
                            lambda
                                l: l.day == day.date() and l.type == 'tax' and l.tax_type == 'vat' and not l.is_service_tax
                        )
                        municipality_line = folio.line_ids.filtered(
                            lambda
                                l: l.day == day.date() and l.type == 'tax' and l.tax_type == 'municipality' and not l.is_service_tax
                        )
                        if room_charge_line:
                            room_charge_line.write({'amount': price_untaxed})
                            #  create price history
                            self.env['booking.folio.line.price'].create({
                                'folio_id': folio.id,
                                'day': day.date(),
                                'amount': price_untaxed,
                                'vat': price_vat,
                                'municipality': price_municipality,
                            })
                        if vat_line:
                            vat_line.write({'amount': price_vat})
                        if municipality_line:
                            municipality_line.write({'amount': price_municipality})
                    else:
                        final_room_charge = (self.price_unit or total_price) - room_charge_deduction
                        final_municipality = price_municipality
                        final_vat = price_vat

                        if self.price_include_tax:
                            for tax in self.tax_id:
                                final_room_charge = final_room_charge / (1 + tax.amount / 100)

                            for tax in self.tax_id.filtered(lambda t: t.type == 'municipality'):
                                final_municipality = final_room_charge * (tax.amount / 100)

                            final_vat = (self.price_unit or total_price) - room_charge_deduction
                            for tax in self.tax_id.filtered(lambda t: t.type == 'vat'):
                                final_vat = (final_room_charge + final_municipality) * (
                                            tax.amount / 100)

                    # create line for room charge
                    # CHECK IF DAY IS CHECKOUT DAY BUT NOT DAY USE
                    if day.date() != check_out.date() or self.booking_id.day_use:
                        self.env['booking.folio.line'].create({
                            'folio_id': folio.id,
                            'day': day,
                            'amount': final_room_charge,
                            'particulars': 'Room Charge',
                            'type': 'room_charge',
                        })
                        # create line for room charge taxes
                        if final_vat > 0:
                            self.env['booking.folio.line'].create({
                                'folio_id': folio.id,
                                'day': day,
                                'amount': final_vat,
                                'particulars': 'VAT',
                                # 'is_service_tax': True,
                                'type': 'tax',
                                'tax_type': 'vat',
                            })
                        if final_municipality > 0:
                            self.env['booking.folio.line'].create({
                                'folio_id': folio.id,
                                'day': day,
                                'amount': final_municipality,
                                'particulars': 'Service Charge',
                                #  'is_service_tax': True,
                                'type': 'tax',
                                'tax_type': 'municipality',
                            })
                        #  create price history
                        self.env['booking.folio.line.price'].create({
                            'folio_id': folio.id,
                            'day': day,
                            'amount': price_untaxed,
                            'vat': price_vat,
                            'municipality': price_municipality,
                        })
