from datetime import datetime

import pytz
from dateutil.relativedelta import relativedelta

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class FolioAmendStay(models.Model):
    _name = 'folio.amend.stay'
    _description = 'Folio Amend Stay'

    folio_id = fields.Many2one('booking.folio')
    check_in = fields.Datetime()
    old_check_out = fields.Datetime()
    check_out = fields.Datetime(compute='compute_check_out', store=True)
    new_check_out = fields.Date()
    new_check_in = fields.Date()

    folio_ids = fields.Many2many('booking.folio')
    amend_option = fields.Selection(selection=[('date', 'By Date'), ('number', 'By Number of Days')])
    amend_type = fields.Selection(selection=[('increase', 'Increase'), ('decrease', 'Decrease')])
    amend_number_of_days = fields.Integer()
    day_use = fields.Boolean()
    show_day_use = fields.Boolean(compute='compute_show_day_use', store=True)
    show_new_price = fields.Boolean(compute='compute_show_new_price', store=True)
    new_price = fields.Float("New Charge Price")
    price_include_tax = fields.Boolean(default=True)
    tax_ids = fields.Many2many('account.tax')

    amend_by = fields.Selection(selection=[('check_in', 'Check In'), ('check_out', 'Check Out')], default='check_out')

    @api.constrains('new_check_out', 'check_in')
    def check_new_check_out(self):
        if self.new_check_out and self.check_in:
            if self.new_check_out < self.check_in.date():
                raise ValidationError(_("New Check-Out date cannot be earlier than check in date"))

    @api.constrains('old_check_out', 'new_check_in')
    def check_new_check_in(self):
        if self.new_check_in and self.old_check_out:
            if self.new_check_in > self.old_check_out.date():
                raise ValidationError(_("New Check-In date cannot be after the old Check-Out date."))

    @api.constrains('new_check_out', 'folio_ids')
    def check_new_check_out_folios(self):
        if self.new_check_out:
            for folio in self.folio_ids:
                if folio.check_in:
                    if self.new_check_out < folio.check_in.date():
                        raise ValidationError(_(f"New Check-Out date cannot be earlier than check in date folio {folio.name}"))

    @api.constrains('new_check_in', 'folio_ids')
    def check_new_check_in_folios(self):
        if self.new_check_in:
            for folio in self.folio_ids:
                if folio.check_out:
                    if self.new_check_in > folio.check_out.date():
                        raise ValidationError(_(f"New Check-In date cannot be after the old Check-Out date folio {folio.name}"))

    @api.depends('old_check_out', 'new_check_out')
    def compute_show_new_price(self):
        for rec in self:
            rec.show_new_price = False
            if rec.old_check_out and rec.new_check_out:
                if rec.new_check_out > rec.old_check_out.date():
                    rec.show_new_price = True

    @api.onchange('price_include_tax')
    def onchange_price_include_tax(self):
        taxes = self.env['account.tax'].search([])
        if self.price_include_tax:
            self.tax_ids = taxes.filtered(lambda t: t.price_include).ids
        else:
            self.tax_ids = taxes.filtered(lambda t: not t.price_include).ids

    @api.depends('check_in', 'new_check_out')
    def compute_show_day_use(self):
        for rec in self:
            rec.show_day_use = False
            if rec.check_in and rec.new_check_out:
                if rec.check_in.date() == rec.new_check_out:
                    rec.show_day_use = True

    def button_amend_stay(self):
        duo_out = self.env.ref('hotel_booking.data_hotel_room_stay_status_duo_out')
        stay_over = self.env.ref('hotel_booking.data_hotel_room_stay_status')
        vacant = self.env.ref('hotel_booking.hotel_room_stay_status_vacant')
        arrival = self.env.ref('hotel_booking.data_hotel_room_stay_status_arrival')
        folios = self.env['booking.folio'].browse(self.folio_id.ids) if self.folio_id else self.folio_ids
        particulars = self.env['ir.config_parameter'].sudo().get_param('hotel_booking.particulars')
        for folio in folios:
            price_unit = self.new_price or folio.booking_line_id.price_unit
            rate_type_line_ids = folio.booking_line_id.rate_plan.rate_type_id.inclusion_ids
            if self.amend_by == 'check_out':
                old_check_out = folio.new_check_out
                new_check_out  = self.new_check_out
                if new_check_out < folio.booking_id.audit_date:
                    raise ValidationError(_("New Check out date cannot be less than Audit date"))
                date_list = folio.get_dates_between_exclude_checkout(old_check_out, new_check_out+relativedelta(days=1))
                # case 1: increase nights by check out date
                if self.new_check_out > folio.new_check_out:
                    for date in date_list:
                        room_charge_deduction = 0
                        for line in rate_type_line_ids:
                            if date == folio.new_check_in and line.posting_rule in ['everyday_no_check_in',
                                                                                        'everyday_no_check_in_out']:
                                room_charge_deduction += line.rate * folio.booking_line_id.number_of_adults
                                continue
                            if date == new_check_out and line.posting_rule in ['everyday_no_check_out',
                                                                                        'everyday_no_check_in_out']:
                                room_charge_deduction += line.rate * folio.booking_line_id.number_of_adults
                                continue
                            if date != folio.new_check_in and line.posting_rule in ['check_in', 'check_in_out']:
                                continue
                            if date != new_check_out and line.posting_rule in ['check_out', 'check_in_out']:
                                continue
                            room_charge_deduction += line.rate * folio.booking_line_id.number_of_adults
                            # =====================================================================
                            vat_taxes = line.service_id.tax_ids.filtered(lambda t: t.type == 'vat')
                            municipality_taxes = line.service_id.tax_ids.filtered(lambda t: t.type == 'municipality')
                            total_rate = line.rate * folio.booking_line_id.number_of_adults
                            service_net_amount = 0
                            vat_tax_amount = 0
                            municipality_tax_amount = 0
                            if line.service_id.include_taxes:
                                if vat_taxes and municipality_taxes:
                                    service_net_amount = total_rate / 1.17875
                                    municipality_tax_amount = service_net_amount * 0.025
                                    vat_tax_amount = total_rate - service_net_amount - municipality_tax_amount
                                if vat_taxes and not municipality_taxes:
                                    service_net_amount = total_rate / 1.15
                                    vat_tax_amount = total_rate - service_net_amount
                                    municipality_tax_amount = 0
                            else:
                                service_net_amount = total_rate
                                vat_tax_amount = service_net_amount * 0.15
                                municipality_tax_amount = service_net_amount * 0.025
                            # create line for service
                            # the follwing condition to handle the last old folio line just add not exist service
                            if not any(folio.line_ids.filtered(lambda l: l.day == date and l.particulars == line.service_id.name)):
                                self.env['booking.folio.line'].create({
                                    'folio_id': folio.id,
                                    'number_of_adults': folio.booking_line_id.number_of_adults,
                                    'day': date,
                                    'amount': service_net_amount ,
                                    'particulars': line.service_id.name,
                                    'type': line.service_id.type,
                                })
                                # create line for service taxes
                                if vat_tax_amount > 0:
                                    self.env['booking.folio.line'].create({
                                        'folio_id': folio.id,
                                        'number_of_adults': folio.booking_line_id.number_of_adults,
                                        'day': date,
                                        'amount': vat_tax_amount ,
                                        'particulars': 'VAT',
                                        'is_service_tax': True,
                                        'tax_type': 'vat',
                                        'type': 'tax',
                                    })
                                # create line for service municipality
                                if municipality_tax_amount > 0:
                                    self.env['booking.folio.line'].create({
                                        'folio_id': folio.id,
                                        'number_of_adults': folio.booking_line_id.number_of_adults,
                                        'day': date,
                                        'amount': municipality_tax_amount ,
                                        'particulars': particulars,
                                        'is_service_tax': True,
                                        'tax_type': 'municipality',
                                        'type': 'tax',
                                    })
                        if date != new_check_out or folio.booking_id.day_use :
                            final_room_charge = price_unit - room_charge_deduction
                            final_municipality = 0
                            final_vat = price_unit - room_charge_deduction

                            if self.price_include_tax:
                                for tax in self.tax_ids:
                                    final_room_charge = final_room_charge / (1 + tax.amount / 100)

                                for tax in self.tax_ids.filtered(lambda t: t.type == 'municipality'):
                                    final_municipality = final_room_charge * (tax.amount / 100)

                                for tax in self.tax_ids.filtered(lambda t: t.type == 'vat'):
                                    final_vat = (final_room_charge + final_municipality) * (tax.amount / 100)
                            else:
                                for tax in self.tax_ids.filtered(lambda t: t.type == 'municipality'):
                                    final_municipality = final_room_charge * (tax.amount / 100)

                                for tax in self.tax_ids.filtered(lambda t: t.type == 'vat'):
                                    final_vat = (final_room_charge + final_municipality) * (tax.amount / 100)

                            self.env['booking.folio.line'].create({
                                'folio_id': folio.id,
                                'day': date,
                                'amount': final_room_charge,
                                'particulars': 'Room Charge',
                                'type': 'room_charge',
                            })
                            # create line for room charge taxes
                            if final_vat > 0:
                                self.env['booking.folio.line'].create({
                                    'folio_id': folio.id,
                                    'day': date,
                                    'amount': final_vat,
                                    'particulars': 'VAT',
                                    'type': 'tax',
                                    'tax_type': 'vat',
                                })
                            if final_municipality > 0:
                                self.env['booking.folio.line'].create({
                                    'folio_id': folio.id,
                                    'day': date,
                                    'amount': final_municipality,
                                    'particulars': particulars,
                                    'type': 'tax',
                                    'tax_type': 'municipality',
                                })
                    # create audit trail
                    self.env['audit.trails'].create({
                        'booking_id': folio.booking_id.id,
                        'folio_id': folio.id,
                        'user_id': self.env.user.id,
                        'operation': 'amend_stay',
                        'datetime': fields.Datetime.now(),
                        'notes': f'Increase nights by check out date from {old_check_out} to {new_check_out} for folio {folio.name}'
                    })
                else:
                    old_check_out_lines = folio.line_ids.filtered(lambda l: l.day in folio.get_dates_between_exclude_checkout(new_check_out, old_check_out))
                    # filter keeped line
                    keeped_lines = folio.line_ids.filtered(lambda line: line.payment_id or  line.is_city_ledger or  line.room_charge_type or line.pos_order_ref)
                    # update keeped line with new date
                    # keeped_lines.day = new_check_out
                    # delete other lines
                    old_check_out_lines -= keeped_lines
                    if not self.day_use:
                        old_check_out_lines.unlink()
                    # get last night lines
                    last_night_lines = folio.line_ids.filtered(lambda l: l.day == old_check_out)
                    # update last night lines with new date
                    last_night_lines.day = new_check_out
                    # create audit trail
                    self.env['audit.trails'].create({
                        'booking_id': folio.booking_id.id,
                        'folio_id': folio.id,
                        'user_id': self.env.user.id,
                        'operation': 'amend_stay',
                        'datetime': fields.Datetime.now(),
                        'notes': f'Decrease nights by check out date from {old_check_out} to {new_check_out} for folio {folio.name}'
                    })


                self.env.cr.execute(
                    "UPDATE booking_folio SET new_check_out = %(new_check_out)s , check_out_date =  %(new_check_out)s  , total_nights = %(total_nights)s, check_out = %(check_out)s WHERE id = %(folio_id)s",
                    {
                    'new_check_out': self.new_check_out,
                    'check_out_date': self.new_check_out,
                    'total_nights':( self.new_check_out  - folio.check_in_date).days,
                    'folio_id': folio.id,
                    'check_out' : datetime.combine(self.new_check_out, datetime.min.time())
                    }
                )
                self.env.cr.commit()
                if folio.new_check_out == folio.company_id.audit_date:
                    folio.room_id.stay_state = duo_out.id
                else:
                    folio.room_id.stay_state = stay_over.id
            # ========================================================================================================
            if self.amend_by == 'check_in':
                old_check_in = folio.new_check_in
                new_check_in = self.new_check_in
                self.new_check_out = folio.new_check_out # to avoid error for ezee connector in null date_to
                date_list = folio.get_dates_between_exclude_checkin(new_check_in-relativedelta(days=1), old_check_in)
                # case 2: increase nights by check in date
                if self.new_check_in < folio.new_check_in:
                    for date in date_list:
                        room_charge_deduction = 0
                        for line in rate_type_line_ids:
                            if date == new_check_in and line.posting_rule in ['everyday_no_check_in',
                                                                                        'everyday_no_check_in_out']:
                                room_charge_deduction += line.rate * folio.booking_line_id.number_of_adults
                                continue
                            if date != new_check_in and line.posting_rule in ['check_in', 'check_in_out']:
                                continue
                            room_charge_deduction += line.rate * folio.booking_line_id.number_of_adults
                            # =====================================================================
                            vat_taxes = line.service_id.tax_ids.filtered(lambda t: t.type == 'vat')
                            municipality_taxes = line.service_id.tax_ids.filtered(lambda t: t.type == 'municipality')
                            total_rate = line.rate * folio.booking_line_id.number_of_adults
                            service_net_amount = 0
                            vat_tax_amount = 0
                            municipality_tax_amount = 0
                            if line.service_id.include_taxes:
                                if vat_taxes and municipality_taxes:
                                    service_net_amount = total_rate / 1.17875
                                    municipality_tax_amount = service_net_amount * 0.025
                                    vat_tax_amount = total_rate - service_net_amount - municipality_tax_amount
                                if vat_taxes and not municipality_taxes:
                                    service_net_amount = total_rate / 1.15
                                    vat_tax_amount = total_rate - service_net_amount
                                    municipality_tax_amount = 0
                            else:
                                service_net_amount = total_rate
                                vat_tax_amount = service_net_amount * 0.15
                                municipality_tax_amount = service_net_amount * 0.025
                            # create line for service
                            # the follwing condition to handle the last old folio line just add not exist service
                            if not any(folio.line_ids.filtered(lambda l: l.day == date and l.particulars == line.service_id.name)):
                                self.env['booking.folio.line'].create({
                                    'folio_id': folio.id,
                                    'number_of_adults': folio.booking_line_id.number_of_adults,
                                    'day': date,
                                    'amount': service_net_amount ,
                                    'particulars': line.service_id.name,
                                    'type': line.service_id.type,
                                })
                                # create line for service taxes
                                if vat_tax_amount > 0:
                                    self.env['booking.folio.line'].create({
                                        'folio_id': folio.id,
                                        'number_of_adults': folio.booking_line_id.number_of_adults,
                                        'day': date,
                                        'amount': vat_tax_amount ,
                                        'particulars': 'VAT',
                                        'is_service_tax': True,
                                        'tax_type': 'vat',
                                        'type': 'tax',
                                    })
                                # create line for service municipality
                                if municipality_tax_amount > 0:
                                    self.env['booking.folio.line'].create({
                                        'folio_id': folio.id,
                                        'number_of_adults': folio.booking_line_id.number_of_adults,
                                        'day': date,
                                        'amount': municipality_tax_amount ,
                                        'particulars': particulars,
                                        'is_service_tax': True,
                                        'tax_type': 'municipality',
                                        'type': 'tax',
                                    })
                        if date != old_check_in:
                            final_room_charge = price_unit - room_charge_deduction
                            for tax in folio.booking_line_id.tax_id:
                                final_room_charge = final_room_charge / (1 + tax.amount / 100)

                            final_municipality = 0
                            for tax in folio.booking_line_id.tax_id.filtered(lambda t: t.type == 'municipality'):
                                final_municipality = final_room_charge * (tax.amount / 100)

                            final_vat = price_unit - room_charge_deduction
                            for tax in folio.booking_line_id.tax_id.filtered(lambda t: t.type == 'vat'):
                                final_vat = (final_room_charge + final_municipality) * (tax.amount / 100)

                            self.env['booking.folio.line'].create({
                                'folio_id': folio.id,
                                'day': date,
                                'amount': final_room_charge,
                                'particulars': 'Room Charge',
                                'type': 'room_charge',
                            })
                            # create line for room charge taxes
                            if final_vat > 0:
                                self.env['booking.folio.line'].create({
                                    'folio_id': folio.id,
                                    'day': date,
                                    'amount': final_vat,
                                    'particulars': 'VAT',
                                    'type': 'tax',
                                    'tax_type': 'vat',
                                })
                            if final_municipality > 0:
                                self.env['booking.folio.line'].create({
                                    'folio_id': folio.id,
                                    'day': date,
                                    'amount': final_municipality,
                                    'particulars': particulars,
                                    'type': 'tax',
                                    'tax_type': 'municipality',
                                })
                    # create audit trail
                    self.env['audit.trails'].create({
                        'booking_id': folio.booking_id.id,
                        'folio_id': folio.id,
                        'user_id': self.env.user.id,
                        'operation': 'amend_stay',
                        'datetime': fields.Datetime.now(),
                        'notes': f'Increase nights by check in date from {old_check_in} to {new_check_in} for folio {folio.name}'
                    })
                else:
                    old_check_in_lines = folio.line_ids.filtered(lambda l: l.day in folio.get_dates_between_exclude_checkin(old_check_in, new_check_in))
                    # filter keeped line
                    keeped_lines = folio.line_ids.filtered(lambda line: line.payment_id or  line.is_city_ledger or  line.room_charge_type)
                    # update keeped line with new date
                    # keeped_lines.day = new_check_in
                    # delete other lines
                    old_check_in_lines -= keeped_lines
                    if not self.day_use:
                        old_check_in_lines.unlink()
                    # get first night lines
                    first_night_lines = folio.line_ids.filtered(lambda l: l.day == old_check_in)
                    # update first night lines with new date
                    first_night_lines.day = new_check_in
                    # create audit trail
                    self.env['audit.trails'].create({
                        'booking_id': folio.booking_id.id,
                        'folio_id': folio.id,
                        'user_id': self.env.user.id,
                        'operation': 'amend_stay',
                        'datetime': fields.Datetime.now(),
                        'notes': f'Decrease nights by check in date from {old_check_in} to {new_check_in} for folio {folio.name}'
                    })
                self.env.cr.execute(
                    "UPDATE booking_folio SET new_check_in = %(new_check_in)s , check_in_date =  %(new_check_in)s  , total_nights = %(total_nights)s, check_in = %(check_in)s WHERE id = %(folio_id)s",
                    {
                    'new_check_in': self.new_check_in,
                    'check_in_date': self.new_check_in,
                    'total_nights':( folio.check_out_date - self.new_check_in).days,
                    'folio_id': folio.id,
                    'check_in' : datetime.combine(self.new_check_in, datetime.min.time())
                    }
                )
                self.env.cr.commit()
                if new_check_in == folio.company_id.audit_date:
                    folio.room_id.stay_state = arrival.id
                else:
                    folio.room_id.stay_state = vacant.id
        message = f'{self.folio_id.booking_id.name} is Updated Successfully'
        return {
            'name': 'Message',
            'type': 'ir.actions.act_window',
            'res_model': 'warn.wizard',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': {'default_message': message, 'default_booking_id': self.folio_id.booking_id.id}
        }


    def create_service_folio_line(self, folio, service, date, folio_line, old_line):
        vat_line = folio.line_ids.filtered(lambda l: l.related_line_id.id == old_line.id and l.tax_type == 'vat')
        if vat_line:
            self.env['booking.folio.line'].create({
                'folio_id': folio.id,
                'day': date,
                'amount': vat_line.amount,
                'particulars': service.service_id.name + ' VAT',
                'type': service.service_id.type,
                'is_service_tax': True,
                'related_line_id': folio_line.id,
                'tax_type': 'vat',
            })
        municipality_line = folio.line_ids.filtered(
            lambda l: l.related_line_id.id == old_line.id and l.tax_type == 'municipality')
        if municipality_line:
            self.env['booking.folio.line'].create({
                'folio_id': folio.id,
                'day': date,
                'amount': municipality_line.amount,
                'particulars': service.service_id.name + ' Municipality',
                'type': service.service_id.type,
                'is_service_tax': True,
                'related_line_id': folio_line.id,
                'tax_type': 'municipality',
            })

    @api.depends('new_check_out')
    def compute_check_out(self):
        for rec in self:
            rec.check_out = False
            if rec.new_check_out:
                rec.check_out = datetime.combine(rec.new_check_out, datetime.min.time())

    def prepare_folio_line(self, folio, day, amount, line_type):
        particulars = self.env['ir.config_parameter'].sudo().get_param('hotel_booking.particulars')
        if line_type == 'municipality':
            particulars = particulars
            type = 'tax'
            tax_type = 'municipality'
        elif line_type == 'vat':
            particulars = 'VAT'
            type = 'tax'
            tax_type = 'vat'
        else:
            particulars = 'Room Charge'
            type = line_type
            tax_type = False

        return {
            'folio_id': folio.id,
            'day': day,
            'amount': amount,
            'particulars': particulars,
            'type': type,
            'tax_type': tax_type,
        }

    def create_folio_lines(self, folio, day, prices):
        price_untaxed = prices['price_untaxed']
        price_vat = prices['price_vat']
        price_municipality = prices['price_municipality']

        self.env['booking.folio.line'].create(self.prepare_folio_line(folio, day, price_untaxed, 'room_charge'))
        if price_municipality > 0:
            self.env['booking.folio.line'].create(
                self.prepare_folio_line(folio, day, price_municipality, 'municipality'))
        if price_vat > 0:
            self.env['booking.folio.line'].create(self.prepare_folio_line(folio, day, price_vat, 'vat'))

