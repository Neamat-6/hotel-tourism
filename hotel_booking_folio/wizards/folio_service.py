from odoo import fields, models, api
from odoo.exceptions import ValidationError


class FolioService(models.TransientModel):
    _name = 'folio.service'
    _description = 'Add Folio Service'

    service_id = fields.Many2one('hotel.services', required=True)
    price_type = fields.Selection(selection=[
        ('fixed', 'Fixed'), ('multiply_with_guest', 'Multiply With No.of.Guests')
    ], default="fixed", required=True)
    type = fields.Selection(selection=[
        ('every_day', 'Every Day'), ('every_day_checkin', 'Every Day Except Checkin'),
        ('every_day_checkout', 'Every Day Except Checkout'), ('one_time', 'One Time'),
    ], required=True)
    price = fields.Float(required=True)
    folio_id = fields.Many2one('booking.folio')
    price_include_tax = fields.Boolean(default=True)
    plan_tax_ids = fields.Many2many('account.tax', relation='folio_line_plan_tax_rel',
                                    column1='folio_line_id', column2='folio_tax_id')
    tax_ids = fields.Many2many('account.tax', string='Taxes', domain="[('id', 'in', plan_tax_ids)]")
    amount_tax = fields.Float(compute='compute_amount', store=True, string='Total Tax')
    amount_municipality = fields.Float(compute='compute_amount', store=True, string='Total Municipality')
    amount_vat = fields.Float(compute='compute_amount', store=True, string='Total VAT')
    amount_total = fields.Float(compute='compute_amount', store=True, string='Total')
    amount_untaxed = fields.Float(compute='compute_amount', store=True, string='Total Untaxed')
    notes = fields.Char("Notes")
    update_existing_service = fields.Boolean()

    @api.depends('price', 'price_include_tax')
    def compute_amount(self):
        for service in self:
            price_unit = service.price
            price_vat = 0
            price_municipality = 0
            price_untaxed = 0
            if service.service_id.include_taxes:
                vat = service.service_id.tax_ids.filtered(lambda t: t.type == 'vat')
                if vat:
                    price_untaxed = (price_unit / (100 + vat.amount)) * 100
                    price_vat = price_unit - price_untaxed

                municipality = service.service_id.tax_ids.filtered(lambda t: t.type == 'municipality')
                if municipality:
                    price_before_municipality = price_untaxed
                    price_untaxed = (price_before_municipality / (100 + municipality.amount)) * 100
                    price_municipality = price_before_municipality - price_untaxed
            else:
                price_untaxed = price_unit
                price_total = price_unit
                municipality = service.service_id.tax_ids.filtered(lambda t: t.type == 'municipality')
                if municipality:
                    price_total = price_unit * (municipality.amount / 100 + 1)
                    price_municipality = price_total - price_unit

                vat = service.service_id.tax_ids.filtered(lambda t: t.type == 'vat')
                if vat:
                    price_before_vat = price_total
                    price_total = price_before_vat * (vat.amount / 100 + 1)
                    price_vat = price_total - price_before_vat

            service.update({
                'amount_vat': price_vat,
                'amount_municipality': price_municipality,
                'amount_tax': price_vat + price_municipality,
                'amount_total': price_vat + price_municipality + price_untaxed,
                'amount_untaxed': price_untaxed,
            })

    @api.onchange('service_id')
    def onchange_service_id(self):
        if self.service_id:
            self.price = self.service_id.price

    def create_folio_lines(self):
        particulars = self.env['ir.config_parameter'].sudo().get_param('hotel_booking.particulars')
        vals = []
        folio = self.folio_id
        if self.price <= 0:
            raise ValidationError("price must be more than 0!")
        if self.price_type == 'fixed':
            amount = self.amount_untaxed
            amount_vat = self.amount_vat
            amount_municipality = self.amount_municipality
        else:
            if self.folio_id.number_of_guests:
                amount = self.amount_untaxed * self.folio_id.number_of_guests
                amount_vat = self.amount_vat * self.folio_id.number_of_guests
                amount_municipality = self.amount_municipality * self.folio_id.number_of_guests
            else:
                plan = self.folio_id.booking_line_id.rate_plan
                amount = self.amount_untaxed * (plan.base_adult + plan.base_child)
                amount_vat = self.amount_vat * (plan.base_adult + plan.base_child)
                amount_municipality = self.amount_municipality * (plan.base_adult + plan.base_child)

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
                'show_delete': True
            })
            vals.append(service_line)
            if not self.update_existing_service:
                booking_service_id = self.create_service_line(booking_folio_line_id=service_line.id)
                service_line.booking_service_id = booking_service_id
            if amount_vat:
                vat_line = self.env['booking.folio.line'].create({
                    'folio_id': folio.id,
                    'day': date,
                    'amount': amount_vat,
                    'particulars': self.service_id.name + ' VAT',
                    'type': 'tax',
                    'is_service_tax': True,
                    'related_line_id': service_line.id,
                    'tax_type': 'vat',
                })
                vals.append(vat_line)
            if amount_municipality:
                municipality_line = self.env['booking.folio.line'].create({
                    'folio_id': folio.id,
                    'day': date,
                    'amount': amount_municipality,
                    'particulars': self.service_id.name + ' ' + particulars,
                    'type': 'tax',
                    'is_service_tax': True,
                    'related_line_id': service_line.id,
                    'tax_type': 'municipality',
                })
                vals.append(municipality_line)
        return vals

    def create_service_line(self,booking_folio_line_id=None):
        folio = self.folio_id
        booking_service_id = self.env['booking.services'].create({
            'booking_id': folio.booking_id.id,
            'line_id': folio.booking_line_id.id,
            'company_id': folio.company_id.id,
            'service_id': self.service_id.id,
            'price_type': self.price_type,
            'type': self.type,
            'price': self.price,
            'price_include_tax': self.price_include_tax,
            'tax_ids': [(6, 0, self.tax_ids.ids)],
            'booking_folio_line_id': booking_folio_line_id,
        })
        return booking_service_id

    def update_folio_lines(self,booking_service):
        service_line = booking_service.booking_folio_line_id
        service_vat_line = self.folio_id.line_ids.filtered(
            lambda l: l.related_line_id == service_line and l.tax_type == 'vat'
        )
        service_municipality_line = self.folio_id.line_ids.filtered(
            lambda l: l.related_line_id == service_line and l.tax_type == 'municipality'
        )
        service_line.update({
            'amount': self.amount_untaxed,
            'particulars': self.service_id.name,
        })
        service_vat_line.update({
            'amount': self.amount_vat,
            'particulars': self.service_id.name + ' VAT',
        })
        service_municipality_line.update({
            'amount': self.amount_municipality,
            'particulars': self.service_id.name + ' Municipality',
        })


    def button_add_service(self):
        if self.update_existing_service:
            active_ids = self._context.get('active_ids', [])
            booking_service = self.env['booking.services'].browse(active_ids)
            self.update_folio_lines(booking_service)
        else:
            self.create_folio_lines()
        return {
            'type': 'ir.actions.act_window',
            'name': "Folio",
            'res_model': 'booking.folio',
            'view_mode': 'form',
            'target': 'new',
            'res_id': self.folio_id.id
        }
