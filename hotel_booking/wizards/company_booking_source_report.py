from collections import defaultdict

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from odoo.tools import float_round

from dateutil.relativedelta import relativedelta


class RevenueSummary(models.TransientModel):
    _name = 'company.booking.source'
    _description = 'Company Booking Source'

    line_ids = fields.One2many('company.booking.source.line', 'wizard_id')
    company_booking_source = fields.Many2one('res.partner', domain="[('travel_type','=','company')]")
    date_from = fields.Date("Date From", required=True)
    date_to = fields.Date("Date to", required=True)
    total = fields.Float()
    total_amount = fields.Float(compute="calc_total_amount", digits=(16, 2))
    total_paid = fields.Float(compute="calc_total_amount", digits=(16, 2))
    balance = fields.Float(compute="calc_total_amount", digits=(16, 2))
    related_hotel = fields.Many2many('hotel.hotel', string='Related Hotel')

    def calc_total_amount(self):
        for rec in self:
            if rec.line_ids:
                total_amount = sum(rec.line_ids.mapped('subtotal'))
                total_paid = sum(rec.line_ids.mapped('total_paid'))
                rec.total_amount = float_round(total_amount, precision_digits=2)
                rec.total_paid = float_round(total_paid, precision_digits=2)
                rec.balance = float_round(total_amount - total_paid, precision_digits=2)
            else:
                rec.total_amount = 0.0
                rec.total_paid = 0.0
                rec.balance = 0.0

    @api.constrains('date_from', 'date_to')
    def check_dates(self):
        for rec in self:
            if rec.date_to < rec.date_from:
                raise ValidationError(_('To date cannot be earlier than from date!'))

    def get_booking_source_folios(self):
        self.line_ids = [(5, 0, 0)]
        domain = []
        if self.date_from:
            domain.append(('check_in', '>=', self.date_from))
        if self.date_to:
            domain.append(('check_out', '<=', self.date_to))
        if self.company_booking_source:
            domain.append(('company_booking_source', '=', self.company_booking_source.id))
        if self.related_hotel:
            domain.append(('hotel_id', 'in', self.related_hotel.ids))

        domain.append(('booking_source', '=', 'company'))

        booking_folio = self.env['booking.folio'].search(domain)

        booking_folio_dict = {}
        for line in booking_folio:
            company_booking_source = line.company_booking_source.id
            related_hotel = (line.mapped('hotel_id')).id
            subtotal = sum(line.mapped('price_total'))
            account_payment_obj = self.env['account.payment'].search(
                [('is_internal_transfer', '=', True), ('destination_journal_id.is_city_ledger', '=', True),
                 ('payment_type', '=', 'inbound'), ('journal_dis_partner_id', '=', company_booking_source)])
            if account_payment_obj:
                total_paid = sum(account_payment_obj.mapped('amount'))
            else:
                total_paid = 0.0
            balance = subtotal - total_paid
            if company_booking_source in booking_folio_dict:
                booking_folio_dict[company_booking_source]['subtotal'] += subtotal
                booking_folio_dict[company_booking_source]['total_paid'] += total_paid
                booking_folio_dict[company_booking_source]['balance'] += balance
            else:
                booking_folio_dict[company_booking_source] = {
                    'subtotal': subtotal,
                    'total_paid': total_paid,
                    'balance': balance,
                    'related_hotel': related_hotel
                }

        # After iterating through all lines, create records in company.booking.source.line
        for company_booking_source, values in booking_folio_dict.items():
            self.env['company.booking.source.line'].create({
                'wizard_id': self.id,
                'company_booking_source': company_booking_source,
                'subtotal': values['subtotal'],
                'total_paid': values['total_paid'],
                'balance': values['balance'],
                'related_hotel': values['related_hotel']
            })
        return {
            'type': 'ir.actions.act_window',
            'name': _('Company Booking Source'),
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'company.booking.source',
            'res_id': self.id,
            'target': 'new'
        }

    def print_pdf(self):
        return self.env.ref('hotel_booking.action_company_booking_source_report').with_context(
            landscape=True).report_action(self)


class RevenueSummaryLine(models.TransientModel):
    _name = 'company.booking.source.line'
    _description = 'Company Booking Source Line'

    wizard_id = fields.Many2one('company.booking.source')
    company_booking_source = fields.Many2one('res.partner', domain="[('is_company','=',True)]")
    total_paid = fields.Float()
    subtotal = fields.Float()
    balance = fields.Float()
    related_hotel = fields.Many2one('hotel.hotel', string="Hotel")
