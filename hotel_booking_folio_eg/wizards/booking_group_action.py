from odoo import fields, models, api
from odoo.exceptions import ValidationError


class BookingGroupAction(models.TransientModel):
    _inherit = 'booking.group.action'

    def button_update_room_charge(self):
        if not self.new_room_charge:
            raise ValidationError("Add new room charge!")

        price_unit = self.new_room_charge
        price_municipality = 0
        price_vat = 0
        price_service_tax = 0
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
        for line in self.folio_line_ids:
            line.write({'amount': price_untaxed})
            vat_line = line.folio_id.line_ids.filtered(
                lambda l: l.day == line.day and l.type == 'tax' and l.tax_type == 'vat' and not l.is_service_tax
            )
            if vat_line:
                vat_line.write({'amount': price_vat})
            elif not vat_line and price_vat:
                self.env['booking.folio.line'].create({
                    'folio_id': line.folio_id.id,
                    'day': line.day,
                    'amount': price_vat,
                    'particulars': 'VAT',
                    'type': 'tax',
                    'tax_type': 'vat',
                })

            service_tax_line = line.folio_id.line_ids.filtered(
                lambda l: l.day == line.day and l.type == 'tax' and l.tax_type == 'service' and not l.is_service_tax
            )

            if service_tax_line:
                service_tax_line.write({'amount': price_service_tax})
            elif not service_tax_line and price_service_tax:
                self.env['booking.folio.line'].create({
                    'folio_id': line.folio_id.id,
                    'day': line.day,
                    'amount': price_service_tax,
                    'particulars': 'Service Tax',
                    'type': 'tax',
                    'tax_type': 'service',
                })

            municipality_line = line.folio_id.line_ids.filtered(
                lambda l: l.day == line.day and l.type == 'tax' and l.tax_type == 'municipality' and not l.is_service_tax
            )
            if municipality_line:
                municipality_line.write({'amount': price_municipality})
            elif not municipality_line and price_municipality:
                self.env['booking.folio.line'].create({
                    'folio_id': line.folio_id.id,
                    'day': line.day,
                    'amount': price_municipality,
                    'particulars': 'Municipality',
                    'type': 'tax',
                    'tax_type': 'municipality'
                })
        self.button_refresh()
