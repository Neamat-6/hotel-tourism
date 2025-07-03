from odoo import fields, models, api
import pytz


class BookingLine(models.Model):
    _inherit = 'hotel.booking.line'

    def get_prices(self, booking_line, day):
        price_unit = self.get_price_unit(booking_line, day)
        price_vat = 0
        price_service_tax = 0
        price_municipality = 0
        price_untaxed = 0
        if booking_line.price_include_tax:
            municipality = booking_line.tax_id.filtered(lambda t: t.type == 'municipality')
            if municipality:
                municipality = municipality[0]
                municipality_percentage = municipality.amount / 100  # Convert percentage to decimal
                price_untaxed = price_unit / (1 + municipality_percentage)
                price_municipality = price_unit * (municipality.amount / 100)

            service_tax = booking_line.tax_id.filtered(lambda t: t.type == 'service')
            if service_tax:
                service_tax = service_tax[0]
                price_before_service_tax = price_unit
                price_untaxed = (price_before_service_tax / (100 + service_tax.amount)) * 100
                price_service_tax = price_unit * (service_tax.amount / 100)
            vat = booking_line.tax_id.filtered(lambda t: t.type == 'vat')
            if vat:
                vat = vat[0]
                price_before_vat = price_unit
                price_untaxed = (price_before_vat / (100 + vat.amount)) * 100
                price_vat = (price_service_tax + price_unit) * vat.amount / 100
        else:
            price_untaxed = price_unit
            vat = booking_line.tax_id.filtered(lambda t: t.type == 'vat')
            if vat:
                vat = vat[0]
                price_vat = price_untaxed * (vat.amount / 100)
            service_tax = booking_line.tax_id.filtered(lambda t: t.type == 'service')
            if service_tax:
                service_tax = service_tax[0]
                price_service_tax = (price_untaxed + price_vat) * (service_tax.amount / 100)
            municipality = booking_line.tax_id.filtered(lambda t: t.type == 'municipality')
            if municipality:
                municipality = municipality[0]
                price_municipality = (price_untaxed + price_vat + price_service_tax) * (municipality.amount / 100)

        return {
            'price_untaxed': price_unit,
            'price_vat': price_vat,
            'price_service_tax': price_service_tax,
            'price_municipality': price_municipality
        }

    def update_folio(self, number_of_rooms, price=False, room_type=False,check_in=False,check_out=False):
        if not self.env.context.get('ignore_all_update', False):
            date_list = self.get_dates_between_exclude(self.check_in, self.check_out)
            timezone = pytz.timezone(self.env.user.tz or 'UTC')
            check_in = pytz.utc.localize(self.check_in).astimezone(timezone)
            check_out = pytz.utc.localize(self.check_out).astimezone(timezone)
            if not self.booking_id.quick_group_booking:
                number_of_rooms = 1
            booking_folios = self.folio_ids
            for i in range(number_of_rooms):
                if self.env.context.get('update_existing_folio', False):
                    folio = booking_folios[i]
                else:
                    if room_type:
                        number_of_guests = self.env['room.type'].browse(room_type).max_adults
                    else:
                        number_of_guests = self.room_type.max_adults
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
                        'number_of_guests': number_of_guests
                    })
                rate_plan = folio.booking_line_id.rate_plan
                rate_type = rate_plan.rate_type_id
                booking_line = folio.booking_line_id

                for day in date_list:
                    prices = self.get_prices(booking_line, day.date())
                    price_untaxed = prices['price_untaxed']
                    price_vat = prices['price_vat']
                    price_service_tax = prices['price_service_tax']
                    price_municipality = prices['price_municipality']
                    if rate_type.is_package:
                        for incl in rate_type.inclusion_ids:
                            if day.date() == check_in.date() and incl.posting_rule in ['everyday_no_check_in',
                                                                                       'everyday_no_check_in_out']:
                                continue
                            if day.date() == check_out.date() and incl.posting_rule in ['everyday_no_check_out',
                                                                                        'everyday_no_check_in_out']:
                                continue
                            if day.date() != check_in.date() and incl.posting_rule in ['check_in', 'check_in_out']:
                                continue
                            if day.date() != check_out.date() and incl.posting_rule in ['check_out', 'check_in_out']:
                                continue
                            # create line for service
                            service_amount = incl.rate * folio.booking_line_id.number_of_adults
                            self.env['booking.folio.line'].create({
                                'folio_id': folio.id,
                                'day': day,
                                'amount': service_amount,
                                'particulars': incl.service_id.name,
                                'type': incl.service_id.type,
                            })
                            price_untaxed -= incl.rate
                            # create line for service taxes
                            # TODO loop thru all taxes
                            taxes = folio.booking_line_id.tax_id.compute_all(service_amount,
                                                                             partner=self.env['res.partner'])
                            price_tax = sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))
                            if price_tax > 0:
                                self.env['booking.folio.line'].create({
                                    'folio_id': folio.id,
                                    'day': day,
                                    'amount': price_tax,
                                    'particulars': 'VAT',
                                    'type': 'tax',
                                })
                    if self.env.context.get('update_existing_folio', False):
                        room_charge_line = folio.line_ids.filtered(
                            lambda l: l.day == day.date() and l.type == 'room_charge')
                        vat_line = folio.line_ids.filtered(
                            lambda
                                l: l.day == day.date() and l.type == 'tax' and l.tax_type == 'vat' and not l.is_service_tax
                        )
                        service_tax_line = folio.line_ids.filtered(
                            lambda
                                l: l.day == day.date() and l.type == 'tax' and l.tax_type == 'service' and not l.is_service_tax
                        )
                        municipality_line = folio.line_ids.filtered(
                            lambda
                                l: l.day == day.date() and l.type == 'tax' and l.tax_type == 'municipality' and not l.is_service_tax
                        )
                        if room_charge_line:
                            room_charge_line.write({'amount': price_untaxed})
                        if vat_line:
                            vat_line.write({'amount': price_vat})
                        if service_tax_line:
                            service_tax_line.write({'amount': price_service_tax})
                        if municipality_line:
                            municipality_line.write({'amount': price_municipality})
                    else:
                        # create line for room charge
                        self.env['booking.folio.line'].create({
                            'folio_id': folio.id,
                            'day': day,
                            'amount': price_untaxed,
                            'particulars': 'Room Charge',
                            'type': 'room_charge',
                        })
                        # create line for room charge taxes
                        if price_vat > 0:
                            self.env['booking.folio.line'].create({
                                'folio_id': folio.id,
                                'day': day,
                                'amount': price_vat,
                                'particulars': 'VAT',
                                'type': 'tax',
                                'tax_type': 'vat',
                            })
                        if price_service_tax > 0:
                            self.env['booking.folio.line'].create({
                                'folio_id': folio.id,
                                'day': day,
                                'amount': price_service_tax,
                                'particulars': 'Service Tax',
                                'type': 'tax',
                                'tax_type': 'service',
                            })
                        # mun = booking_line.tax_id.filtered(lambda t: t.type == 'municipality')
                        if price_municipality > 0:
                            self.env['booking.folio.line'].create({
                                'folio_id': folio.id,
                                'day': day,
                                'amount': price_municipality,
                                'particulars': "City Tax",
                                'type': 'tax',
                                'tax_type': 'municipality',
                            })
