from odoo import fields, models, api
from odoo.exceptions import ValidationError
from datetime import date


class RoomChargeWizard(models.TransientModel):
    _name = 'room.charge.wizard'
    _description = 'Room Charge Wizard'

    folio_id = fields.Many2one('booking.folio')
    room_charge_id = fields.Many2one('hotel.room.charge', required=True)

    price = fields.Float(required=True)
    tax_ids = fields.Many2many('account.tax')

    amount_tax = fields.Float(compute='compute_amount', store=True, string='Total Tax')
    amount_municipality = fields.Float(compute='compute_amount', store=True, string='Total Municipality')
    amount_vat = fields.Float(compute='compute_amount', store=True, string='Total VAT')
    amount_total = fields.Float(compute='compute_amount', store=True, string='Total')
    amount_untaxed = fields.Float(compute='compute_amount', store=True, string='Total Untaxed')

    @api.depends('price', 'tax_ids')
    def compute_amount(self):
        for rec in self:
            price_unit = rec.price
            price_vat = 0
            price_municipality = 0
            price_untaxed = 0
            vat = rec.tax_ids.filtered(lambda t: t.type == 'vat')
            if vat:
                vat = vat[0]
                price_untaxed = (price_unit / (100 + vat.amount)) * 100
                price_vat = price_unit - price_untaxed

            municipality = rec.tax_ids.filtered(lambda t: t.type == 'municipality')
            if municipality:
                price_before_municipality = price_untaxed
                municipality = municipality[0]
                price_untaxed = (price_before_municipality / (100 + municipality.amount)) * 100
                price_municipality = price_before_municipality - price_untaxed
            rec.update({
                'amount_vat': price_vat,
                'amount_municipality': price_municipality,
                'amount_tax': price_vat + price_municipality,
                'amount_total': price_vat + price_municipality + price_untaxed,
                'amount_untaxed': price_untaxed,
            })

    def create_folio_lines(self):
        vals = []
        folio = self.folio_id
        if self.price <= 0:
            raise ValidationError("price must be more than 0!")

        amount = self.amount_untaxed
        amount_vat = self.amount_vat
        amount_municipality = self.amount_municipality

        # charge and its tax are related to each other
        charge_line = self.env['booking.folio.line'].create({
            'folio_id': folio.id,
            'day': date.today(),
            'amount': amount,
            'particulars': self.room_charge_id.name,
            'type': 'room_charge',
            'is_cancellation_fee': True if self.room_charge_id.charge_type in ['cancellation', 'no_show'] else False,
            'room_charge_type': self.room_charge_id.charge_type,
            'show_delete': True,
        })
        if amount_vat:
            self.env['booking.folio.line'].create({
                'folio_id': folio.id,
                'day': date.today(),
                'amount': amount_vat,
                'particulars': self.room_charge_id.name + ' VAT',
                'type': 'tax',
                'related_line_id': charge_line.id,
                'tax_type': 'vat',
                'is_cancellation_fee': True if self.room_charge_id.charge_type in ['cancellation', 'no_show'] else False,
                'room_charge_type': self.room_charge_id.charge_type
            })
        if amount_municipality:
            self.env['booking.folio.line'].create({
                'folio_id': folio.id,
                'day': date.today(),
                'amount': amount_municipality,
                'particulars': self.room_charge_id.name + ' Municipality',
                'type': 'tax',
                'related_line_id': charge_line.id,
                'tax_type': 'municipality',
                'is_cancellation_fee': True if self.room_charge_id.charge_type in ['cancellation', 'no_show'] else False,
                'room_charge_type': self.room_charge_id.charge_type
            })
        return vals

    def button_add_room_charge(self):
        self.create_folio_lines()
        return {
            'type': 'ir.actions.act_window',
            'name': "Folio",
            'res_model': 'booking.folio',
            'view_mode': 'form',
            'target': 'new',
            'res_id': self.folio_id.id
        }

