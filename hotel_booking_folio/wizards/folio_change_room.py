from datetime import datetime

from odoo import fields, models, api
from odoo.exceptions import ValidationError, _logger


class FolioChangeRoom(models.TransientModel):
    _name = 'folio.change.room'
    _description = 'Folio Change Room'

    new_room_type_ids = fields.Many2many('room.type', compute='_compute_new_room_type_ids')

    @api.depends('room_type_id', 'company_id')
    def _compute_new_room_type_ids(self):
        for record in self:
            if record.company_id and record.room_type_id:
                record.new_room_type_ids = self.env['room.type'].search([
                    ('id', '!=', record.room_type_id.id),
                    ('company_id', '=', record.company_id.id)
                ])
            else:
                record.new_room_type_ids = self.env['room.type'].search([])

    folio_id = fields.Many2one('booking.folio')
    folio_state = fields.Selection(related='folio_id.state', store=True)
    company_id = fields.Many2one('res.company', related='folio_id.company_id')
    room_type_id = fields.Many2one('room.type')
    check_in = fields.Datetime()
    check_out = fields.Datetime()
    available_room_ids = fields.Many2many('hotel.room')
    available_room2_ids = fields.Many2many('hotel.room', 'folio_change_room_room_rel', 'wizard_id', 'room_id')
    old_room_id = fields.Many2one('hotel.room')
    new_room_id = fields.Many2one('hotel.room',
                                  domain="[('room_type', '=', room_type_id), ('id', 'in', available_room_ids)]")
    unassign = fields.Boolean()
    enable_change_room_type = fields.Boolean()
    new_room_type_id = fields.Many2one('room.type', domain="[('id', 'in', new_room_type_ids)]")
    new_room2_id = fields.Many2one('hotel.room',
                                   domain="[('room_type', '=', new_room_type_id), ('id', 'in', available_room2_ids)]",
                                   string='New Room')
    rate_plan_id = fields.Many2one('hotel.rate.plan', domain="[('room_type_id', '=', new_room_type_id)]")
    price_unit = fields.Float()
    price_include_tax = fields.Boolean(default=True)
    tax_ids = fields.Many2many('account.tax')
    charged_line_ids = fields.Many2many('booking.folio.line',
                                        domain="[('type', '=', 'room_charge'), ('folio_id', '=', folio_id)]")
    has_charge_access = fields.Boolean()
    no_charge = fields.Boolean()

    def button_change_room(self):
        if self.unassign and self.old_room_id:
            self.old_room_id.write({
                'stay_state': self.env.ref('hotel_booking.hotel_room_stay_status_vacant').id,
            })
            self.folio_id.with_context(ignore_updates=True).write({
                'room_id': False
            })
            return {
                'type': 'ir.actions.act_window',
                'name': "Folio",
                'res_model': 'booking.folio',
                'view_mode': 'form',
                'target': 'new',
                'res_id': self.folio_id.id
            }

        # set new room to old room state
        dirty = self.env.ref('hotel_booking.hotel_room_status_dirty').id
        if self.new_room_id:
            if self.new_room_id.state.id == dirty:
                raise ValidationError(f"{self.new_room_id.name} is dirty!")
        if self.old_room_id:
            self.new_room_id.stay_state = self.old_room_id.stay_state.id
        else:
            if self.folio_id.check_in_date == self.folio_id.company_id.audit_date:
                self.new_room_id.stay_state = self.env.ref('hotel_booking.data_hotel_room_stay_status_arrival').id
            else:
                self.new_room_id.stay_state = self.env.ref('hotel_booking.hotel_room_stay_status_vacant').id
        # set old room to vacant
        if self.old_room_id:
            self.old_room_id.stay_state = self.env.ref('hotel_booking.hotel_room_stay_status_vacant').id

        self.folio_id.room_id = self.new_room_id.id
        if self.folio_id.room_id:
            message = f'You Assigned Room {self.folio_id.room_id.name} Successfully'
            return {
                'name': 'Warning',
                'type': 'ir.actions.act_window',
                'res_model': 'warn.wizard',
                'view_mode': 'form',
                'view_type': 'form',
                'target': 'new',
                'context': {'default_message': message, 'default_folio_id': self.folio_id.id}
            }
        # return {
        #     'type': 'ir.actions.act_window',
        #     'name': "Folio",
        #     'res_model': 'booking.folio',
        #     'view_mode': 'form',
        #     'target': 'new',
        #     'res_id': self.folio_id.id
        # }

    @api.onchange('rate_plan_id')
    def onchange_rate_plan(self):
        if self.rate_plan_id:
            folio = self.folio_id
            price_unit = self.rate_plan_id.rock_rate
            price_line = self.rate_plan_id.day_price_ids.filtered(lambda d: d.date == folio.check_in_date)
            if price_line:
                price_line = price_line[0]
                price_unit = price_line.price
            self.price_unit = price_unit
            self.tax_ids = self.rate_plan_id.tax_ids.filtered(lambda t: t.price_include).ids
            if self.new_room_type_id:
                if self.enable_change_room_type and not self.no_charge:
                    day = folio.company_id.audit_date
                    self.available_room2_ids = self.get_available_rooms(day, folio.check_out_date)
                elif self.has_charge_access and not self.no_charge:
                    uncharged_lines = self.folio_id.line_ids.filtered(lambda l: l.type == 'room_charge')
                    if self.charged_line_ids:
                        uncharged_lines = uncharged_lines.filtered(lambda l: l.id not in self.charged_line_ids.ids)
                    first_uncharged_day = uncharged_lines.sorted(lambda line: line.day)
                    if first_uncharged_day:
                        first_uncharged_day = first_uncharged_day[0].day
                        self.available_room2_ids = self.get_available_rooms(first_uncharged_day,
                                                                            self.folio_id.check_out_date)
                else:
                    day = folio.company_id.audit_date
                    self.available_room2_ids = self.get_available_rooms(day, folio.check_out_date)

    @api.onchange('price_include_tax')
    def onchange_price_include_tax(self):
        if self.rate_plan_id and self.enable_change_room_type:
            if self.price_include_tax:
                self.tax_ids = self.rate_plan_id.tax_ids.filtered(lambda t: t.price_include).ids
            else:
                self.tax_ids = self.rate_plan_id.tax_ids.filtered(lambda t: not t.price_include).ids

    def button_change_room_type(self):
        """
                --------update booking line--------
                # if bl has more than one folio then create new bl and update no. of rooms
                # if bl has one folio then just update bl
                # --------update folio lines--------
                # if change with charge then unlink uncharged folio lines and create new folio lines with new prices
        """
        folio = self.folio_id
        booking_line = folio.booking_line_id
        booking_id = folio.booking_id
        partner_id = folio.partner_id
        room_id = folio.room_id
        new_folio = False

        dirty = self.env.ref('hotel_booking.hotel_room_status_dirty').id
        if self.new_room2_id:
            if self.new_room2_id.state.id == dirty:
                raise ValidationError(f"{self.new_room2_id.name} is dirty!")

        if self.new_room_type_id:
            get_available_rooms = self.get_available_rooms(folio.new_check_in, folio.new_check_out)
            _logger.info("------- get_available_rooms %s -------" % get_available_rooms)
            if not get_available_rooms:
                raise ValidationError(f"Please Check Room Type Again {self.new_room_type_id.name} For Availability")

        if booking_line.number_of_rooms == 1:
            vals = {
                'room_type': self.new_room_type_id.id,
                'rate_plan': self.rate_plan_id.id,
                'room_type_id': False,
            }
            if self.has_charge_access and not self.no_charge:
                vals.update({
                    'price_unit': self.price_unit,
                    'price_include_tax': self.price_include_tax,
                    'tax_id': [(6, 0, self.tax_ids.ids)],
                })
            booking_line.with_context(ignore_all_update=True).write(vals)
        else:
            booking_line.with_context(ignore_all_update=True).number_of_rooms -= 1
            vals = {
                'booking_id': booking_id.id,
                'hotel_id': booking_id.hotel_id.id,
                'room_type': self.new_room_type_id.id,
                'rate_plan': self.rate_plan_id.id,
                'number_of_rooms': 1,
                'room_type_id': False,
            }
            if self.has_charge_access and not self.no_charge:
                vals.update({
                    'price_unit': self.price_unit,
                    'price_include_tax': self.price_include_tax,
                    'tax_id': [(6, 0, self.tax_ids.ids)],
                })
            else:
                vals.update({
                    'price_unit': booking_line.price_unit,
                    'price_include_tax': booking_line.price_include_tax,
                    'tax_id': [(6, 0, booking_line.tax_id.ids)],
                })

            new_booking_line = self.env['hotel.booking.line'].with_context(ignore_all_update=True).create(vals)
            folio.write({
                'booking_line_id': new_booking_line.id
            })

        if self.has_charge_access and not self.no_charge:
            uncharged_lines = folio.line_ids.filtered(lambda l: l.type == 'room_charge')
            if self.charged_line_ids:
                uncharged_lines = uncharged_lines.filtered(lambda l: l.id in self.charged_line_ids.ids)
            first_uncharged_day = uncharged_lines.sorted(lambda line: line.day)
            if not first_uncharged_day:
                raise ValidationError("there is no folio lines to update!")
            first_uncharged_day = first_uncharged_day[0].day
            tax_lines = self.get_tax_lines(folio, uncharged_lines)
            tax_lines.unlink()
            uncharged_lines.unlink()
            self.create_new_folios(folio, first_uncharged_day)
        else:
            self.update_room_state(folio)
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def get_tax_lines(self, folio, uncharged_lines):
        return folio.line_ids.filtered(
            lambda l: l.day in uncharged_lines.mapped('day') and l.type == 'tax' and l.tax_type in ['vat',
                                                                                                    'municipality'] and not l.is_service_tax
        )

    def create_new_folios(self, folio, start_date):
        start_date = datetime.combine(start_date, datetime.min.time())
        date_list = folio.get_dates_between_exclude_checkout(start_date, folio.check_out)
        self.update_room_state(folio)
        for day in date_list:
            prices = self.get_prices(day.date())
            price_untaxed = prices['price_untaxed']
            price_vat = prices['price_vat']
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
            #  create price history
            self.env['booking.folio.line.price'].create({
                'folio_id': folio.id,
                'day': day,
                'amount': price_untaxed,
                'vat': price_vat,
                'municipality': price_municipality,
            })

    def update_room_state(self, folio):
        new_room = self.new_room2_id
        if folio.state not in ['draft', 'confirmed']:
            new_room.state = self.env.ref('hotel_booking.hotel_room_status_dirty').id
        if folio.room_id:
            old_room = folio.room_id
            new_room.stay_state = old_room.stay_state.id
            old_room.stay_state = self.env.ref('hotel_booking.hotel_room_stay_status_vacant').id
            folio.with_context(ignore_updates=True).write({
                "room_type_id": self.new_room_type_id.id,
                "room_id": new_room.id,
            })
        else:
            folio.with_context(ignore_updates=True).write({
                "room_type_id": self.new_room_type_id.id,
                "room_id": new_room.id
            })
            if folio.state == 'checked_in':
                if folio.check_in_date == folio.company_id.audit_date:
                    new_room.stay_state = self.env.ref('hotel_booking.data_hotel_room_stay_status_arrived').id
                elif folio.check_out_date == folio.company_id.audit_date:
                    new_room.stay_state = self.env.ref('hotel_booking.data_hotel_room_stay_status_duo_out').id
                else:
                    new_room.stay_state = self.env.ref('hotel_booking.data_hotel_room_stay_status').id
            else:
                if folio.check_in_date == folio.company_id.audit_date:
                    new_room.stay_state = self.env.ref('hotel_booking.data_hotel_room_stay_status_arrival').id
                else:
                    new_room.stay_state = self.env.ref('hotel_booking.hotel_room_stay_status_vacant').id

    def get_available_rooms(self, check_in_date, check_out_date):
        available_rooms = []
        vacant = self.env.ref('hotel_booking.hotel_room_stay_status_vacant').id
        rooms = self.env["hotel.room"].search([
            ('room_type', '=', self.new_room_type_id.id), ('stay_state', '=', vacant)
        ])
        folio = self.folio_id
        for room in rooms:
            domain = [
                ('id', '!=', folio.id),
                ('company_id', '=', folio.company_id.id),
                ('room_id', '=', room.id),
                ('state', 'in', ['part_checked_in', 'checked_in', 'confirmed', 'draft']),
                '|', '|',
                '&', ('check_in_date', '<=', check_in_date), ('check_out_date', '>', check_in_date),
                '&', ('check_in_date', '<=', check_out_date), ('check_out_date', '>', check_out_date),
                '&', ('check_in_date', '<=', check_in_date), ('check_out_date', '>', check_out_date),
            ]
            folio = self.env['booking.folio'].search(domain)
            if not folio:
                available_rooms.append(room.id)
        return available_rooms

    def get_daily_price(self, plan, day):
        return self.env['rate.plan.day.price'].search([('plan_id', '=', plan.id), ('date', '=', day)], limit=1)

    def get_price_unit(self, day):
        if self.folio_id.booking_id.apply_daily_price:
            price_id = self.get_daily_price(self.rate_plan_id, day)
            price_unit = price_id.price
        else:
            price_unit = self.folio_id.booking_line_id.price_unit
        return price_unit

    def get_prices(self, day):
        price_unit = self.get_price_unit(day)
        price_vat = 0
        price_municipality = 0
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

        return {
            'price_untaxed': price_untaxed,
            'price_vat': price_vat,
            'price_municipality': price_municipality
        }
