from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class BookingFolio(models.Model):
    _name = 'booking.folio'
    _description = 'Booking Folio'

    name = fields.Char(required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'),
                       string='Ref No.')
    line_ids = fields.One2many('booking.folio.line', 'folio_id')
    booking_id = fields.Many2one('hotel.booking', ondelete="cascade")
    booking_line_id = fields.Many2one('hotel.booking.line')
    company_id = fields.Many2one('res.company', related='booking_id.company_id', store=True)
    is_print_inv = fields.Boolean('Print')
    number_in_words = fields.Char(string='Number in Words', compute='_compute_check_amount_in_words')
    select_folio = fields.Boolean("Is Selected")


    def _compute_check_amount_in_words(self):
        for rec in self:
            if rec.currency_id:
                rec.number_in_words = rec.currency_id.amount_to_text(rec.price_total)
            else:
                rec.number_in_words = False

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            name = self.env['ir.sequence'].next_by_code('booking.folio.sequence') or _('New')
            if vals.get('room_type_id', False):
                room_type = self.env['room.type'].browse(vals['room_type_id'])
                if room_type.is_virtual:
                    name = f'VM{name}'
            vals['name'] = name
        result = super(BookingFolio, self).create(vals)
        return result

    def print_report(self):
        return self.env.ref('hotel_booking.folio_report_action').report_action(self)

    def button_add_payment(self):
        pass

    def button_open_lines(self):
        return {
            'type': 'ir.actions.act_window',
            'name': "Folio",
            'res_model': 'booking.folio',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }


class BookingFolioLine(models.Model):
    _name = 'booking.folio.line'
    _description = 'Booking Folio Line'
    _order = 'day'

    folio_id = fields.Many2one('booking.folio')
    booking_line_id = fields.Many2one(related='folio_id.booking_line_id', readonly=True)
    payment_id = fields.Many2one('account.payment', readonly=True)
    day = fields.Date()
    particulars = fields.Char(readonly=True)
    description = fields.Char(readonly=True)
    amount = fields.Float()
    type = fields.Selection(selection=[
        ('room_charge', 'Room Charge'),
        ('food', 'Food'),
        ('beverage', 'Beverage'),
        ('laundry', 'Laundry'),
        ('rent', 'Rent'),
        ('tax', 'Tax'),
    ], readonly=True)
    company_id = fields.Many2one('res.company', related='folio_id.company_id', store=True, readonly=True)
    name = fields.Char(related='folio_id.name', store=True, readonly=True)
    booking_id = fields.Many2one(related='folio_id.booking_id', store=True, readonly=True)
    # room_type_id = fields.Many2one('room.type', related='folio_id.room_type_id', store=True)
    room_id = fields.Many2one('hotel.room', related='booking_line_id.room_id', store=True, readonly=True)
    state = fields.Selection(related='booking_id.state', store=True, readonly=True)
    booking_number = fields.Char(related='booking_id.booking_number', store=True, readonly=True)
    partner_id = fields.Many2one(related='booking_id.partner_id', store=True, readonly=True)
    hotel_id = fields.Many2one(related='booking_id.hotel_id', store=True, readonly=True)
    check_in = fields.Datetime(related='booking_id.check_in', store=True, readonly=True)
    check_out = fields.Datetime(related='booking_id.check_out', store=True, readonly=True)
    booking_source_id = fields.Many2one(related='booking_id.booking_source_id', store=True, readonly=True)
    rate_plan = fields.Many2one('hotel.rate.plan', related='booking_line_id.rate_plan', store=True, readonly=True)
    rate_type = fields.Many2one('hotel.rate.type', related='rate_plan.rate_type_id', store=True, readonly=True)
    currency_id = fields.Many2one('res.currency', readonly=True, default=lambda self: self.env.company.currency_id)
    can_print_report = fields.Boolean(compute='check_company_paid')
    is_city_ledger = fields.Boolean()

    def get_account(self, type):
        hotel = self.folio_id.booking_id.hotel_id
        booking_source = self.env['booking.source'].search(
            [('source', '=', self.folio_id.booking_id.booking_source)], limit=1)
        if type == 'room_charge':
            if booking_source and booking_source.account_account_id:
                return booking_source.account_account_id.id
            else:
                return hotel.room_charge_account_id.id
        elif type == 'food':
            return hotel.food_revenue_account_id.id
        elif type == 'beverage':
            return hotel.beverage_revenue_account_id.id
        elif type == 'laundry':
            return hotel.laundry_revenue_account_id.id
        elif type == 'rent':
            return hotel.rent_account_id.id
        elif type == 'tax':
            return hotel.municipality_account_id.id
        else:
            return False

    def action_payment_folio(self):
        return self.env.ref('hotel_booking.payment_folio_report_action').report_action(self)

    def check_company_paid(self):
        if self.booking_id.company_paid == 0.0 and self.booking_id.payment_type_id == 'city_ledger':
            self.can_print_report = True
        else:
            self.can_print_report = False
