from odoo import fields, models, api
from odoo.exceptions import ValidationError


class FolioService(models.TransientModel):
    _inherit = 'folio.service'

    amount_service_tax = fields.Float(compute='compute_amount', store=True, string='Total Service Tax')

    @api.depends('price', 'tax_ids', 'price_include_tax')
    def compute_amount(self):
        for service in self:
            price_unit = service.price
            price_vat = 0
            price_service_tax = 0
            price_municipality = 0
            price_untaxed = 0
            if service.price_include_tax:
                municipality = service.tax_ids.filtered(lambda t: t.type == 'municipality')
                if municipality:
                    municipality = municipality[0]
                    price_untaxed = (price_unit / (100 + municipality.amount)) * 100
                    price_municipality = price_unit - price_untaxed

                service_tax = service.tax_ids.filtered(lambda t: t.type == 'service')
                if service_tax:
                    service_tax = service_tax[0]
                    price_before_service_tax = price_untaxed
                    price_untaxed = (price_before_service_tax / (100 + service_tax.amount)) * 100
                    price_service_tax = price_before_service_tax - price_untaxed

                vat = service.tax_ids.filtered(lambda t: t.type == 'vat')
                if vat:
                    vat = vat[0]
                    price_before_vat = price_untaxed
                    price_untaxed = (price_before_vat / (100 + vat.amount)) * 100
                    price_vat = price_before_vat - price_untaxed
            else:
                price_untaxed = price_unit

                vat = service.tax_ids.filtered(lambda t: t.type == 'vat')
                if vat:
                    vat = vat[0]
                    price_vat = price_untaxed * (vat.amount / 100)

                service_tax = service.tax_ids.filtered(lambda t: t.type == 'service')
                if service_tax:
                    service_tax = service_tax[0]
                    price_service_tax = (price_untaxed + price_vat) * (service_tax.amount / 100)

                municipality = service.tax_ids.filtered(lambda t: t.type == 'municipality')
                if municipality:
                    municipality = municipality[0]
                    price_municipality = (price_untaxed + price_vat + price_service_tax) * (municipality.amount / 100)

            service.update({
                'amount_vat': price_vat,
                'amount_service_tax': price_service_tax,
                'amount_municipality': price_municipality,
                'amount_tax': price_vat + price_municipality + price_service_tax,
                'amount_total': price_vat + price_municipality + price_service_tax + price_untaxed,
                'amount_untaxed': price_untaxed,
            })

    def create_folio_lines(self):
        vals = []
        folio = self.folio_id
        if self.price <= 0:
            raise ValidationError("price must be more than 0!")
        if self.price_type == 'fixed':
            amount = self.amount_untaxed
            amount_vat = self.amount_vat
            amount_service_tax = self.amount_service_tax
            amount_municipality = self.amount_municipality
        else:
            if self.folio_id.number_of_guests:
                amount = self.amount_untaxed * self.folio_id.number_of_guests
                amount_vat = self.amount_vat * self.folio_id.number_of_guests
                amount_service_tax = self.amount_service_tax * self.folio_id.number_of_guests
                amount_municipality = self.amount_municipality * self.folio_id.number_of_guests
            else:
                plan = self.folio_id.booking_line_id.rate_plan
                quantity = (plan.base_adult + plan.base_child)
                amount = self.amount_untaxed * quantity
                amount_vat = self.amount_vat * quantity
                amount_service_tax = self.amount_service_tax * quantity
                amount_municipality = self.amount_municipality * quantity

        if self.type == 'every_day':
            dates = folio.get_dates_between(folio.check_in, folio.check_out)
        elif self.type == 'every_day_checkin':
            dates = folio.get_dates_between_exclude_checkin(folio.check_in, folio.check_out)
        elif self.type == 'every_day_checkout':
            dates = folio.get_dates_between_exclude_checkout(folio.check_in, folio.check_out)
        else:
            dates = [self.env.company.audit_date]

        for date in dates:
            # service and its tax are related to each other
            service_line = self.env['booking.folio.line'].create({
                'folio_id': folio.id,
                'day': date,
                'amount': amount,
                'particulars': self.service_id.name,
                'type': self.service_id.type,
            })
            vals.append(service_line)
            if amount_vat:
                self.env['booking.folio.line'].create({
                    'folio_id': folio.id,
                    'day': date,
                    'amount': amount_vat,
                    'particulars': self.service_id.name + ' VAT',
                    'type': 'tax',
                    'is_service_tax': True,
                    'related_line_id': service_line.id,
                    'tax_type': 'vat',
                })
            if amount_service_tax:
                self.env['booking.folio.line'].create({
                    'folio_id': folio.id,
                    'day': date,
                    'amount': amount_service_tax,
                    'particulars': self.service_id.name + ' Service Tax',
                    'type': 'tax',
                    'is_service_tax': True,
                    'related_line_id': service_line.id,
                    'tax_type': 'service',
                })
            if amount_municipality:
                self.env['booking.folio.line'].create({
                    'folio_id': folio.id,
                    'day': date,
                    'amount': amount_municipality,
                    'particulars': self.service_id.name + ' Municipality',
                    'type': 'tax',
                    'is_service_tax': True,
                    'related_line_id': service_line.id,
                    'tax_type': 'municipality',
                })
        return vals
