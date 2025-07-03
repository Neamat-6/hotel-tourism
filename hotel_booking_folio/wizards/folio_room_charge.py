from odoo import fields, models, api
from odoo.exceptions import ValidationError


class FolioRoomCharge(models.TransientModel):
    _name = 'folio.room.charge'
    _description = 'Folio Room Charge'

    folio_id = fields.Many2one('booking.folio')
    amount = fields.Float(string='New Room Charge', required=True)
    all_folio_line_ids = fields.Many2many('booking.folio.line', 'booking_room_charge_folio_rel',
                                          'wizard_id', 'folio_line_id')
    folio_line_ids = fields.Many2many('booking.folio.line', domain="[('id', 'in', all_folio_line_ids)]")
    price_include_tax = fields.Boolean(default=True)
    tax_ids = fields.Many2many('account.tax')

    @api.onchange('price_include_tax')
    def onchange_price_include_tax(self):
        taxes = self.env['account.tax'].search([])
        if self.price_include_tax:
            self.tax_ids = taxes.filtered(lambda t: t.price_include).ids
        else:
            self.tax_ids = taxes.filtered(lambda t: not t.price_include).ids

    def button_update_charge(self):
        if self.amount <= 0:
            if not self.env.user.has_group('hotel_booking_folio.group_update_charge_with_zero'):
                raise ValidationError("you cant set charge less than zero !")
        if self.amount < 0:
            raise ValidationError("New Room Charge must be more than 0!")
        price_unit = self.amount
        price_municipality = 0
        price_vat = 0
        price_untaxed = 0
        if self.price_include_tax:
            vat = self.tax_ids.filtered(lambda t: t.type == 'vat')
            if vat:
                vat = vat[0]
                price_untaxed = (price_unit / (100 + vat.amount)) * 100
                price_vat = price_unit - price_untaxed

            municipality = self.tax_ids.filtered(lambda t: t.type == 'municipality')
            if municipality:
                price_before_municipality = price_untaxed
                municipality = municipality[0]
                price_untaxed = (price_before_municipality / (100 + municipality.amount)) * 100
                price_municipality = price_before_municipality - price_untaxed
        else:
            price_untaxed = price_unit
            price_total = price_unit
            municipality = self.tax_ids.filtered(lambda t: t.type == 'municipality')
            if municipality:
                municipality = municipality[0]
                price_total = price_unit * (municipality.amount / 100 + 1)
                price_municipality = price_total - price_unit

            vat = self.tax_ids.filtered(lambda t: t.type == 'vat')
            if vat:
                price_before_vat = price_total
                vat = vat[0]
                price_total = price_before_vat * (vat.amount / 100 + 1)
                price_vat = price_total - price_before_vat

        for line in self.folio_line_ids:
            line.write({'amount': price_untaxed})
            #  create price history
            self.env['booking.folio.line.price'].create({
                'folio_id': self.folio_id.id,
                'day': line.day,
                'amount': price_untaxed,
                'vat': price_vat,
                'municipality': price_municipality,
            })
            vat_line = self.folio_id.line_ids.filtered(
                lambda l: l.day == line.day and l.type == 'tax' and l.tax_type == 'vat' and not l.is_service_tax
            )
            if vat_line:
                vat_line.write({'amount': price_vat})
            elif not vat_line and price_vat:
                self.env['booking.folio.line'].create({
                    'folio_id': self.folio_id.id,
                    'day': line.day,
                    'amount': price_vat,
                    'particulars': 'VAT',
                    'type': 'tax',
                    'tax_type': 'vat',
                })

            municipality_line = self.folio_id.line_ids.filtered(
                lambda l: l.day == line.day and l.type == 'tax' and l.tax_type == 'municipality' and not l.is_service_tax
            )
            if municipality_line:
                municipality_line.write({'amount': price_municipality})
            elif not municipality_line and price_municipality:
                self.env['booking.folio.line'].create({
                    'folio_id': self.folio_id.id,
                    'day': line.day,
                    'amount': price_municipality,
                    'particulars': 'Municipality',
                    'type': 'tax',
                    'tax_type': 'municipality'
                })
        # audit
        if self.folio_line_ids:
            old_price = round(self.folio_line_ids[0].amount, 2)
            folio = self.folio_id
            self.env['audit.trails'].create({
                'booking_id': folio.booking_id.id,
                'folio_id': folio.id,
                'user_id': self.env.user.id,
                'operation': 'change_price',
                'datetime': fields.Datetime.now(),
                'notes': f'Old Price: {old_price}, New Price: {self.amount}'
            })

        return {
            'type': 'ir.actions.act_window',
            'name': "Folio",
            'res_model': 'booking.folio',
            'view_mode': 'form',
            'target': 'new',
            'res_id': self.folio_id.id
        }
