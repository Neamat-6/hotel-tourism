from odoo import fields, models, api
import pytz


class Folio(models.Model):
    _inherit = 'booking.folio'

    price_service_tax = fields.Monetary(compute='compute_amount_total', store=True, string='Room Charge Service Tax')
    service_price_service_tax = fields.Monetary(compute='compute_amount_total', store=True, string='Service Total Service Tax')

    @api.depends('line_ids', 'line_ids.amount')
    def compute_amount_total(self):
        res = super(Folio, self).compute_amount_total()
        for folio in self:
            price_service_tax = sum(folio.line_ids.filtered(lambda l: l.tax_type == 'service' and not l.is_service_tax).mapped('amount')) or 0
            if price_service_tax:
                folio.update({
                    'price_service_tax': price_service_tax,
                    'room_price_tax': folio.room_price_tax + price_service_tax,
                    'room_price_total': folio.room_price_total + price_service_tax,
                    'price_tax': folio.price_tax + price_service_tax,
                    'price_total': folio.room_price_total + price_service_tax,
                    'price_due': folio.room_price_total + price_service_tax - folio.price_paid,
                })
            service_price_service_tax = sum(folio.line_ids.filtered(lambda l: l.tax_type == 'service' and l.is_service_tax).mapped('amount')) or 0
            if service_price_service_tax:
                folio.update({
                    'service_price_service_tax': service_price_service_tax,
                    'service_price_tax': folio.service_price_tax + service_price_service_tax,
                    'service_price_total': folio.service_price_total + service_price_service_tax,
                    'price_tax': folio.price_tax + service_price_service_tax,
                    'price_total': folio.price_total + service_price_service_tax,
                    'price_due': folio.price_total + service_price_service_tax - folio.price_paid,

                })

        return res

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
                price_untaxed = (price_unit / (100 + municipality.amount)) * 100
                price_municipality = price_unit - price_untaxed

            service_tax = booking_line.tax_id.filtered(lambda t: t.type == 'service')
            if service_tax:
                service_tax = service_tax[0]
                price_before_service_tax = price_untaxed
                price_untaxed = (price_before_service_tax / (100 + service_tax.amount)) * 100
                price_service_tax = price_before_service_tax - price_untaxed
            vat = booking_line.tax_id.filtered(lambda t: t.type == 'vat')
            if vat:
                vat = vat[0]
                price_before_vat = price_untaxed
                price_untaxed = (price_before_vat / (100 + vat.amount)) * 100
                price_vat = price_before_vat - price_untaxed
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
            'price_untaxed': price_untaxed,
            'price_vat': price_vat,
            'price_service_tax': price_service_tax,
            'price_municipality': price_municipality
        }

    def button_update_folio(self):
        timezone = pytz.timezone(self.env.user.tz or 'UTC')
        date_list = self.get_dates_between_exclude_checkout(self.check_in, self.check_out)
        check_in = pytz.utc.localize(self.check_in).astimezone(timezone)
        check_out = pytz.utc.localize(self.check_out).astimezone(timezone)
        rate_plan = self.booking_line_id.rate_plan
        rate_type = rate_plan.rate_type_id
        self.line_ids.filtered(lambda l: not l.payment_id and l.type not in ['food', 'beverage', 'laundry',
                                                                             'rent'] and not l.is_service_tax).unlink()
        if self.room_id:
            self.room_id.write({
                'stay_state': self.env.ref('hotel_booking.hotel_room_stay_status_vacant').id,
            })
        self.room_id = False
        # recompute available rooms
        self.available_room_ids = [(6, 0, self.get_available_rooms())]
        for day in date_list:
            prices = self.get_prices(self.booking_line_id, day.date())
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
                    service_amount = incl.rate * self.booking_line_id.number_of_adults
                    self.env['booking.folio.line'].create({
                        'folio_id': self.id,
                        'day': day,
                        'amount': service_amount,
                        'particulars': incl.service_id.name,
                        'type': incl.service_id.type,
                    })
                    price_untaxed -= incl.rate
                    # create line for service taxes
                    # TODO loop thru all taxes
                    taxes = self.booking_line_id.tax_id.compute_all(service_amount, partner=self.env['res.partner'])
                    price_tax = sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))
                    if price_tax > 0:
                        self.env['booking.folio.line'].create({
                            'folio_id': self.id,
                            'day': day,
                            'amount': price_tax,
                            'particulars': 'VAT',
                            'type': 'tax',
                        })
            # create line for room charge
            self.env['booking.folio.line'].create({
                'folio_id': self.id,
                'day': day,
                'amount': price_untaxed,
                'particulars': 'Room Charge',
                'type': 'room_charge',
            })
            # create line for room charge taxes
            if price_municipality > 0:
                self.env['booking.folio.line'].create({
                    'folio_id': self.id,
                    'day': day,
                    'amount': price_municipality,
                    'particulars': 'Municipality',
                    'type': 'tax',
                    'tax_type': 'municipality'
                })
            if price_service_tax > 0:
                self.env['booking.folio.line'].create({
                    'folio_id': self.id,
                    'day': day,
                    'amount': price_service_tax,
                    'particulars': 'Service Tax',
                    'type': 'tax',
                    'tax_type': 'service'
                })
            if price_municipality > 0:
                self.env['booking.folio.line'].create({
                    'folio_id': self.id,
                    'day': day,
                    'amount': price_vat,
                    'particulars': 'VAT',
                    'type': 'tax',
                    'tax_type': 'vat',
                })
        return self.action_refresh()

    def prepare_invoice_lines(self, lines):
        invoice_line_vals = []
        default_account = self.room_id.product_id.categ_id.property_account_income_categ_id.id
        for line in lines:
            if self.booking_line_id.price_include_tax:
                price_unit = line.amount
                if line.type == 'room_charge':
                    vat_line = self.line_ids.filtered(
                        lambda l: l.day == line.day and l.type == 'tax' and l.tax_type == 'vat' and not l.is_service_tax
                    )
                    service_tax_line = self.line_ids.filtered(
                        lambda l: l.day == line.day and l.type == 'tax' and l.tax_type == 'service' and not l.is_service_tax
                    )
                    municipality_line = self.line_ids.filtered(
                        lambda
                            l: l.day == line.day and l.type == 'tax' and l.tax_type == 'municipality' and not l.is_service_tax
                    )
                else:
                    vat_line = self.line_ids.filtered(
                        lambda l: l.tax_type == 'vat' and l.is_service_tax and l.related_line_id.id == line.id
                    )
                    service_tax_line = self.line_ids.filtered(
                        lambda l: l.tax_type == 'service' and l.is_service_tax and l.related_line_id.id == line.id
                    )
                    municipality_line = self.line_ids.filtered(
                        lambda
                            l: l.tax_type == 'municipality' and l.is_service_tax and l.related_line_id.id == line.id
                    )
                if vat_line:
                    price_unit += vat_line[0].amount
                if service_tax_line:
                    price_unit += service_tax_line[0].amount
                if municipality_line:
                    price_unit += municipality_line[0].amount
            else:
                price_unit = line.amount
            invoice_line_vals.append((0, 0, {
                'product_id': self.room_id.product_id.id,
                'name': line.particulars,
                'quantity': 1,
                'price_unit': price_unit,
                'source_booking_id': self.booking_line_id.id,
                'tax_ids': [(6, 0, self.booking_line_id.tax_id.ids or [])],
                'account_id': line.get_account(line.type) or default_account,
                'folio_line_id': line.id
            }))
        return invoice_line_vals


class FolioLine(models.Model):
    _inherit = 'booking.folio.line'

    tax_type = fields.Selection(selection=[
        ('vat', 'VAT'), ('service', 'Service'), ('municipality', 'Municipality'),
    ])

