from odoo import fields, models, api
from datetime import datetime


class FolioChangeRoom(models.TransientModel):
    _inherit = 'folio.change.room'

    def get_tax_lines(self, folio, uncharged_lines):
        return folio.line_ids.filtered(
            lambda l: l.day in uncharged_lines.mapped('day') and l.type == 'tax' and l.tax_type in ['vat', 'municipality', 'service'] and not l.is_service_tax
        )

    def get_prices(self, day):
        price_unit = self.get_price_unit(day)
        price_vat = 0
        price_service_tax = 0
        price_municipality = 0
        price_untaxed = 0

        vat = self.tax_ids.filtered(lambda t: t.type == 'vat')
        service_tax = self.tax_ids.filtered(lambda t: t.type == 'service')
        municipality = self.tax_ids.filtered(lambda t: t.type == 'municipality')

        if self.price_include_tax:
            if municipality:
                municipality = municipality[0]
                price_untaxed = (price_unit / (100 + municipality.amount)) * 100
                price_municipality = price_unit - price_untaxed

            if service_tax:
                service_tax = service_tax[0]
                price_before_service_tax = price_untaxed
                price_untaxed = (price_before_service_tax / (100 + service_tax.amount)) * 100
                price_service_tax = price_before_service_tax - price_untaxed

            if vat:
                vat = vat[0]
                price_before_vat = price_untaxed
                price_untaxed = (price_before_vat / (100 + vat.amount)) * 100
                price_vat = price_before_vat - price_untaxed
        else:
            price_untaxed = price_unit

            if vat:
                vat = vat[0]
                price_vat = price_untaxed * (vat.amount / 100)

            if service_tax:
                service_tax = service_tax[0]
                price_service_tax = (price_untaxed + price_vat) * (service_tax.amount / 100)

            if municipality:
                municipality = municipality[0]
                price_municipality = (price_untaxed + price_vat + price_service_tax) * (municipality.amount / 100)

        return {
            'price_untaxed': price_untaxed,
            'price_vat': price_vat,
            'price_service_tax': price_service_tax,
            'price_municipality': price_municipality
        }

    def create_new_folios(self, folio, start_date):
        start_date = datetime.combine(start_date, datetime.min.time())
        date_list = folio.get_dates_between_exclude_checkout(start_date, folio.check_out)
        self.update_room_state(folio)
        for day in date_list:
            prices = self.get_prices(day.date())
            price_untaxed = prices['price_untaxed']
            price_vat = prices['price_vat']
            price_service_tax = prices['price_service_tax']
            price_municipality = prices['price_municipality']
            # create line for room charge
            self.env['booking.folio.line'].create({
                'folio_id': folio.id,
                'day': day,
                'amount': price_untaxed,
                'particulars': 'Room Charge',
                'type': 'room_charge',
            })
            # create line for room charge taxes
            if price_municipality > 0:
                self.env['booking.folio.line'].create({
                    'folio_id': folio.id,
                    'day': day,
                    'amount': price_municipality,
                    'particulars': 'Municipality',
                    'type': 'tax',
                    'tax_type': 'municipality'
                })
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
