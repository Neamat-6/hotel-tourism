from collections import defaultdict
from datetime import datetime, timedelta

from odoo import fields, models, _
from odoo.tools import float_round


class TrialBalanceWizard(models.Model):
    _name = 'trial.balance.wizard'

    date_from = fields.Date("Date From")
    date_to = fields.Date("Date To")
    day = fields.Date("Day")
    company_ids = fields.Many2many('res.company', string='Companies')
    line_ids = fields.One2many(comodel_name="trial.balance.line", inverse_name="wizard_id", required=False, )
    total_amount = fields.Float(compute="calc_total_amount", digits=(16, 2))
    related_hotel = fields.Many2many('hotel.hotel', string='Related Hotel')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    month = fields.Date("Month")
    year = fields.Date("Year")
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user)

    opening_balance_day = fields.Float(string="Opening Balance (Day)")
    payment_received_day = fields.Float(string="Payment Received (Day)")
    changes_raised_day = fields.Float(string="Charges Raised (Day)")
    closing_balance_day = fields.Float(string="Closing Balance (Day)")

    opening_balance_month = fields.Float(string="Opening Balance (Month)")
    payment_received_month = fields.Float(string="Payment Received (Month)")
    changes_raised_month = fields.Float(string="Charges Raised (Month)")
    closing_balance_month = fields.Float(string="Closing Balance (Month)")

    opening_balance_year = fields.Float(string="Opening Balance (Year)")
    payment_received_year = fields.Float(string="Payment Received (Year)")
    changes_raised_year = fields.Float(string="Charges Raised (Year)")
    closing_balance_year = fields.Float(string="Closing Balance (Year)")

    def calc_total_amount(self):
        for rec in self:
            if rec.line_ids:
                total_amount = sum(rec.line_ids.mapped('amount'))
                rec.total_amount = float_round(total_amount, precision_digits=2)
            else:
                rec.total_amount = 0.0

    def print_pdf(self):
        return self.env.ref('hotel_booking_folio.action_trail_balance_report').with_context(
            landscape=True).report_action(self)

    def button_search(self):
        self.line_ids = [(5, 0, 0)]
        domain = [('folio_id.state', '!=', 'cancelled')]
        if self.day:
            day_date = datetime.strptime(str(self.day), '%Y-%m-%d')
            day_start = day_date.strftime('%Y-%m-%d')
            day_end = day_date.strftime('%Y-%m-%d')
            month_start = day_date.replace(day=1).strftime('%Y-%m-%d')
            next_month = (day_date.replace(day=28) + timedelta(days=4)).replace(day=1)
            month_end = (next_month - timedelta(days=1)).strftime('%Y-%m-%d')
            year_start = day_date.replace(month=1, day=1).strftime('%Y-%m-%d')
            year_end = day_date.replace(month=12, day=31).strftime('%Y-%m-%d')

        if self.company_ids:
            domain.append(('company_id', 'in', self.company_ids.ids))

        self.month = month_start
        self.year = year_start

        city_ledger_domain = [('state', '!=', 'cancelled'), ('payment_type_id', '=', 'city_ledger')]

        day_domain = domain + [('day', '=', day_date)]
        day_records = self.env['booking.folio.line'].search(day_domain)

        city_domain_day = city_ledger_domain + [('check_in', '>', self.day)]
        self.opening_balance_day = sum(self.env['hotel.booking'].sudo().search(city_domain_day).mapped('company_paid'))
        self.payment_received_day = sum(self.env['hotel.booking'].sudo().search(city_domain_day).mapped('company_paid'))
        self.changes_raised_day = sum(self.env['hotel.booking'].sudo().search(city_domain_day).mapped('paid_amount_city_ledger'))
        self.closing_balance_day = (self.opening_balance_day + self.changes_raised_day) - self.payment_received_day

        month_domain = domain + [('day', '>=', month_start), ('day', '<=', month_end)]
        month_records = self.env['booking.folio.line'].search(month_domain)

        city_ledger_month = city_ledger_domain + [('check_in', '>=', month_start), ('check_out', '<=', month_end)]
        self.opening_balance_month = sum(self.env['hotel.booking'].sudo().search(city_ledger_month).mapped('company_paid'))
        self.payment_received_month = sum(self.env['hotel.booking'].sudo().search(city_ledger_month).mapped('company_paid'))
        self.changes_raised_month = sum(self.env['hotel.booking'].sudo().search(city_ledger_month).mapped('paid_amount_city_ledger'))
        self.closing_balance_month = (self.opening_balance_month + self.changes_raised_month) - self.payment_received_month

        year_domain = domain + [('day', '>=', year_start), ('day', '<=', year_end)]
        year_records = self.env['booking.folio.line'].search(year_domain)

        city_ledger_year = city_ledger_domain + [('check_in', '>=', year_start), ('check_out', '<=', year_end)]
        self.opening_balance_year = sum(self.env['hotel.booking'].sudo().search(city_ledger_year).mapped('company_paid'))
        self.payment_received_year = sum(self.env['hotel.booking'].sudo().search(city_ledger_year).mapped('company_paid'))
        self.changes_raised_year = sum(self.env['hotel.booking'].sudo().search(city_ledger_year).mapped('paid_amount_city_ledger'))
        self.closing_balance_year = (self.opening_balance_year + self.changes_raised_year) - self.payment_received_year

        grouped_particular = defaultdict(
            lambda: {'type': '', 'description': '', 'day_amount': 0.0, 'month_amount': 0.0, 'year_amount': 0.0})

        for record in day_records:
            grouped_particular[record.particulars]['type'] = record.type
            grouped_particular[record.particulars]['description'] = record.description
            grouped_particular[record.particulars]['day_amount'] += record.amount

        for record in month_records:
            grouped_particular[record.particulars]['type'] = record.type
            grouped_particular[record.particulars]['description'] = record.description
            grouped_particular[record.particulars]['month_amount'] += record.amount

        for record in year_records:
            grouped_particular[record.particulars]['type'] = record.type
            grouped_particular[record.particulars]['description'] = record.description
            grouped_particular[record.particulars]['year_amount'] += record.amount

        trial_balance_line_vals = []
        for particular, values in grouped_particular.items():
            trial_balance_line_vals.append({
                'wizard_id': self.id,
                'day': self.day,
                'type': values['type'],  # Include type here
                'particular': particular,
                'day_amount': values['day_amount'],
                'month_amount': values['month_amount'],
                'year_amount': values['year_amount'],
            })

        self.env['trial.balance.line'].create(trial_balance_line_vals)

        return {
            'type': 'ir.actions.act_window',
            'name': _('Trial Balance Report'),
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'trial.balance.wizard',
            'res_id': self.id,
            'target': 'new'
        }


class TrialBalanceWizardLine(models.Model):
    _name = 'trial.balance.line'

    wizard_id = fields.Many2one('trial.balance.wizard')
    day = fields.Date("Day")
    particular = fields.Char("Particular")
    amount = fields.Float("Amount", digits=(16, 2))
    company_id = fields.Many2one('res.company')
    day_amount = fields.Float("Total Day", digits=(16, 2))
    month_amount = fields.Float("Total Month", digits=(16, 2))
    year_amount = fields.Float("Total Year", digits=(16, 2))
    type = fields.Char()
