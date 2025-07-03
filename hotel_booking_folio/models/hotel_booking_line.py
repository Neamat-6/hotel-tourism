import pytz
from odoo import fields, models, api
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
import logging
logger = logging.getLogger(__name__)


class BookingLine(models.Model):
    _inherit = 'hotel.booking.line'

    price_subtotal = fields.Float(compute='compute_amounts', store=True, string='Subtotal')
    price_total = fields.Float(compute='compute_amounts', store=True, string='Total')
    price_tax = fields.Float(compute='compute_amounts', store=True, string='Total Tax')
    folio_ids = fields.One2many('booking.folio', 'booking_line_id')

    @api.model
    def get_dates_between_exclude(self, date1, date2):
        if isinstance(date1, str):
            date1 = fields.Datetime.from_string(date1)
        if isinstance(date2, str):
            date2 = fields.Datetime.from_string(date2)
        my_list = []
        for n in range(0, int((date2 - date1).days)):
            my_list.append(date1 + timedelta(n))
        return my_list

    @api.depends('folio_ids.price_tax', 'folio_ids.price_subtotal', 'folio_ids.price_total', 'folio_ids.state')
    def compute_amounts(self):
        # todo handle rate plan
        for line in self:
            folios = line.folio_ids.filtered(lambda f: f.state != 'cancelled')
            line.update({
                'price_tax': sum(folios.mapped('price_tax')) or 0,
                'price_subtotal': sum(folios.mapped('price_subtotal')) or 0,
                'price_total': sum(folios.mapped('price_total')) or 0,
            })

    @api.model
    def create(self, vals):
        res = super(BookingLine, self).create(vals)
        number_of_rooms = vals['number_of_rooms'] if vals['number_of_rooms'] > 0 else 1
        res.update_folio(number_of_rooms)
        # create daily prices
        if vals.get('rate_plan', False) and res.booking_id.apply_daily_price:
            rate_plan = self.env['hotel.rate.plan'].browse(vals['rate_plan'])
            date_start = res.booking_id.check_in_date
            date_end = res.booking_id.check_out_date
            if res.booking_id.day_use:
                date_end = date_end + relativedelta(days=1)
            while date_start < date_end:
                price_id = self.get_daily_price(rate_plan, date_start)
                self.env['booking.daily.price'].create({
                    'booking_id': res.booking_id.id,
                    'booking_line_id': res.id,
                    'rate_plan_id': rate_plan.id,
                    'price_id': price_id.id if price_id else False,
                    'date': price_id.date if price_id else False,
                    'price': price_id.price if price_id else False,
                })
                date_start += relativedelta(days=1)
        return res

    def write(self, vals):
        # update daily prices
        if vals.get('rate_plan', False) and self.booking_id.apply_daily_price:
            rate_plan = self.env['hotel.rate.plan'].browse(vals['rate_plan'])
            date_start = self.booking_id.check_in_date
            date_end = self.booking_id.check_out_date
            while date_start < date_end:
                self.env['booking.daily.price'].search([('booking_line_id', '=', self.id)]).unlink()
                price_id = self.get_daily_price(rate_plan, date_start)
                self.env['booking.daily.price'].create({
                    'booking_id': self.booking_id.id,
                    'booking_line_id': self.id,
                    'rate_plan_id': rate_plan.id,
                    'price_id': price_id.id if price_id else False,
                    'date': price_id.date if price_id else False,
                    'price': price_id.price if price_id else False,
                })
                date_start += relativedelta(days=1)
        res = super(BookingLine, self).write(vals)
        return res

    def get_daily_price(self, plan, day):
        return self.env['rate.plan.day.price'].search([('plan_id', '=', plan.id), ('date', '=', day)], limit=1)

    def update_folio(self, number_of_rooms, price=False, room_type=False,check_in=False,check_out=False):
        logger.info('update_folioooooooooo')
        if not self.env.context.get('ignore_all_update', False):
            timezone = pytz.timezone(self.env.user.tz or 'UTC')
            if check_in:
                check_in = pytz.utc.localize(check_in).astimezone(timezone)
            else:
                check_in = pytz.utc.localize(self.check_in).astimezone(timezone)
            if check_out:
                check_out = pytz.utc.localize(check_out).astimezone(timezone)
            else:
                check_out = pytz.utc.localize(self.check_out).astimezone(timezone)
            date_list = self.get_dates_between_exclude(check_in, check_out + relativedelta(days=1))
            # check_in = pytz.utc.localize(self.check_in).astimezone(timezone)
            # check_out = pytz.utc.localize(self.check_out).astimezone(timezone)
            if not self.booking_id.quick_group_booking:
                number_of_rooms = 1
            booking_folios = self.folio_ids
            if self.env.context.get('amend_stay', False):
                iterator = self.env.context.get('folio_id')
            else:
                iterator =range(0, number_of_rooms)
            for i in iterator:
                if self.env.context.get('update_existing_folio', False) or self.env.context.get('amend_stay', False):
                    if self.env.context.get('amend_stay', False):
                        folio = i
                    else:
                        folio = booking_folios[i]
                else:
                    logger.info('here before create folio')
                    folio = self.env['booking.folio'].create({
                        'booking_id': self.booking_id.id,
                        'booking_line_id': self.id,
                        'room_type_id': room_type if room_type else self.room_type.id,
                        'check_in': self.check_in,
                        'check_out': self.check_out,
                        'new_check_in': self.booking_id.new_check_in,
                        'new_check_out': self.booking_id.new_check_out,
                        'total_nights': self.booking_id.total_nights,
                        'available_room_ids': [(6, 0, self.available_room_ids.ids)],
                        'number_of_guests': self.number_of_adults,
                    })
                rate_plan = folio.booking_line_id.rate_plan
                rate_type = rate_plan.rate_type_id
                booking_line = folio.booking_line_id

                for day in date_list:
                    prices = self.get_prices(booking_line, day.date())
                    logger.info(f'get_pricesssss {prices}')
                    price_untaxed = prices['price_untaxed']
                    price_vat = prices['price_vat']
                    price_municipality = prices['price_municipality']
                    room_charge_deduction = 0
                    total_price = price_untaxed + price_vat + price_municipality
                    logger.info(f'total_priceeee {total_price}')
                    if rate_type.is_package:
                        for incl in rate_type.inclusion_ids:
                            vat_taxes = incl.service_id.tax_ids.filtered(lambda t: t.type == 'vat')
                            municipality_taxes = incl.service_id.tax_ids.filtered(lambda t: t.type == 'municipality')
                            total_rate = incl.rate * folio.booking_line_id.number_of_adults
                            if incl.service_id.include_taxes:
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

                            # price_untaxed -= room_charge_deduction
                            if day.date() == check_in.date() and incl.posting_rule in ['everyday_no_check_in',
                                                                                       'everyday_no_check_in_out']:
                                room_charge_deduction += incl.rate * folio.booking_line_id.number_of_adults
                                continue
                            if day.date() == check_out.date() and incl.posting_rule in ['everyday_no_check_out',
                                                                                        'everyday_no_check_in_out']:
                                room_charge_deduction += incl.rate * folio.booking_line_id.number_of_adults
                                continue
                            if day.date() != check_in.date() and incl.posting_rule in ['check_in', 'check_in_out']:
                                continue
                            if day.date() != check_out.date() and incl.posting_rule in ['check_out', 'check_in_out']:
                                continue
                            room_charge_deduction += incl.rate * folio.booking_line_id.number_of_adults
                            # if incl.service_id.include_taxes:
                            # create line for service
                            service_line = self.env['booking.folio.line'].create({
                                'folio_id': folio.id,
                                'number_of_adults': folio.booking_line_id.number_of_adults,
                                'day': day,
                                'amount': service_net_amount ,
                                'particulars': incl.service_id.name,
                                'type': incl.service_id.type,
                            })
                            # create line for service taxes
                            if vat_tax_amount > 0:
                              self.env['booking.folio.line'].create({
                                  'folio_id': folio.id,
                                  'number_of_adults': folio.booking_line_id.number_of_adults,
                                  'day': day,
                                  'amount': vat_tax_amount ,
                                  'particulars': 'VAT',
                                  'is_service_tax': True,
                                  'tax_type': 'vat',
                                  'type': 'tax',
                                  'related_line_id': service_line.id
                              })
                            # create line for service municipality
                            if municipality_tax_amount > 0:
                              self.env['booking.folio.line'].create({
                                  'folio_id': folio.id,
                                  'number_of_adults': folio.booking_line_id.number_of_adults,
                                  'day': day,
                                  'amount': municipality_tax_amount ,
                                  'particulars': 'Municipality',
                                  'is_service_tax': True,
                                  'tax_type': 'municipality',
                                  'type': 'tax',
                                  'related_line_id': service_line.id
                              })
                    final_vat = 0
                    final_municipality = 0
                    final_room_charge = 0
                    if self.env.context.get('update_existing_folio', False):
                        logger.info(f'update_existing_folio')
                        room_charge_line = folio.line_ids.filtered(lambda l: l.day == day.date() and l.type == 'room_charge')
                        vat_line = folio.line_ids.filtered(
                            lambda l: l.day == day.date() and l.type == 'tax' and l.tax_type == 'vat' and not l.is_service_tax
                        )
                        municipality_line = folio.line_ids.filtered(
                            lambda l: l.day == day.date() and l.type == 'tax' and l.tax_type == 'municipality' and not l.is_service_tax
                        )
                        if room_charge_line:
                            room_charge_line.write({'amount': price_untaxed})
                            #  create price history
                            self.env['booking.folio.line.price'].create({
                                'folio_id': folio.id,
                                'day': day.date(),
                                'amount': price_untaxed,
                                'vat': price_vat,
                                'municipality': price_municipality,
                            })
                        if vat_line:
                            vat_line.write({'amount': price_vat})
                        if municipality_line:
                            municipality_line.write({'amount': price_municipality})
                    else:
                        logger.info('newwwww')
                        final_room_charge = (self.price_unit or total_price) - room_charge_deduction
                        final_municipality = price_municipality
                        final_vat = price_vat
                        logger.info(f'final_room_charge {final_room_charge}--final_municipality{final_municipality}--final_vat{final_vat}')

                        if self.price_include_tax:
                            logger.info(f'price_include_taxxxxxxxxxxxxxxxx')
                            for tax in self.tax_id:
                                final_room_charge = final_room_charge / (1 + tax.amount / 100)

                            for tax in self.tax_id.filtered(lambda t: t.type == 'municipality'):
                                final_municipality = final_room_charge * (tax.amount / 100)

                            final_vat = (self.price_unit or total_price) - room_charge_deduction
                            for tax in self.tax_id.filtered(lambda t: t.type == 'vat'):
                                final_vat = (final_room_charge + final_municipality) * (tax.amount / 100)

                      # create line for room charge
                    # CHECK IF DAY IS CHECKOUT DAY BUT NOT DAY USE
                    if day.date() != check_out.date() or self.booking_id.day_use:
                        self.env['booking.folio.line'].create({
                            'folio_id': folio.id,
                            'day': day,
                            'amount': final_room_charge,
                            'particulars': 'Room Charge',
                            'type': 'room_charge',
                        })
                        # create line for room charge taxes
                        if final_vat > 0:
                            self.env['booking.folio.line'].create({
                                'folio_id': folio.id,
                                'day': day,
                                'amount': final_vat,
                                'particulars': 'VAT',
                                # 'is_service_tax': True,
                                'type': 'tax',
                                'tax_type': 'vat',
                            })
                        if final_municipality > 0:
                            self.env['booking.folio.line'].create({
                                'folio_id': folio.id,
                                'day': day,
                                'amount': final_municipality,
                                'particulars': 'Municipality',
                                #  'is_service_tax': True,
                                'type': 'tax',
                                'tax_type': 'municipality',
                            })
                        #  create price history
                        self.env['booking.folio.line.price'].create({
                            'folio_id': folio.id,
                            'day': day,
                            'amount': price_untaxed,
                            'vat': price_vat,
                            'municipality': price_municipality,
                        })

    def get_price_unit(self, booking_line, day):
        if booking_line.booking_id.apply_daily_price:
            price_id = self.get_daily_price(booking_line.rate_plan, day)
            price_unit = price_id.price
        else:
            price_unit = booking_line.price_unit
        return price_unit

    def get_prices(self, booking_line, day):
        price_unit = self.get_price_unit(booking_line, day)
        price_vat = 0
        price_municipality = 0
        price_untaxed = 0
        if booking_line.price_include_tax:
            vat = booking_line.tax_id.filtered(lambda t: t.type == 'vat')
            if vat:
                vat = vat[0]
                price_untaxed = (price_unit / (100 + vat.amount)) * 100
                price_vat = price_unit - price_untaxed

            municipality = booking_line.tax_id.filtered(lambda t: t.type == 'municipality')
            if municipality:
                price_before_municipality = price_untaxed
                municipality = municipality[0]
                price_untaxed = (price_before_municipality / (100 + municipality.amount)) * 100
                price_municipality = price_before_municipality - price_untaxed
        else:
            price_untaxed = price_unit
            price_total = price_unit
            municipality = booking_line.tax_id.filtered(lambda t: t.type == 'municipality')
            if municipality:
                municipality = municipality[0]
                price_total = price_unit + (price_unit * municipality.amount / 100)
                price_municipality = price_total - price_unit

            vat = booking_line.tax_id.filtered(lambda t: t.type == 'vat')
            if vat:
                price_before_vat = price_total
                vat = vat[0]
                price_total = price_before_vat + (price_before_vat * vat.amount / 100)
                price_vat = price_total - price_before_vat

        return {
            'price_untaxed': price_untaxed,
            'price_vat': price_vat,
            'price_municipality': price_municipality
        }
