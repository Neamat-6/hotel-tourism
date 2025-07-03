from odoo import models, fields, api
from collections import namedtuple

report_line = namedtuple('report_line', [
    'date',
    'description',
    'journal_id',
    'folio_id',
    'booking_id',
    'check_in',
    'check_out',
    'debit',
    'credit',
    'balance',
])


class CityLedgerReport(models.Model):
    _name = 'city.ledger.report'
    _description = 'City Ledger Report'

    partner_id = fields.Many2one('res.partner', string='Customer')
    company_id = fields.Many2one('res.company', string='Company')
    date_from = fields.Date(string='Start Date')
    date_to = fields.Date(string='End Date')
    transaction_lines = fields.One2many(
        'city.ledger.report.line',
        'report_id',
        string='Transaction Lines',
    )

    @api.model
    def create_report(self, start_date, end_date, customer_id,company_id):
        report_lines = []

        # Fetch opening balance for the customer prior to the start_date
        # opening_balance = sum(self.env['account.move.line'].search([
        #     ('partner_id', '=', customer_id.id), ('date', '<', start_date),
        #     ('move_id.state', '=', 'posted')
        # ]).filtered(lambda l: l.journal_id.is_city_ledger == True).mapped(
        #     lambda l: l.debit - l.credit))

        # report_lines.append((0, 0, {
        #     'date': False,
        #     'journal_id': '',
        #     'description': 'Opening Balance',
        #     'folio_id': '',
        #     'booking_id': '',
        #     'check_in': '',
        #     'check_out': '',
        #     'debit': opening_balance if opening_balance > 0 else 0,
        #     'credit': -opening_balance if opening_balance < 0 else 0,
        #     'balance': opening_balance,
        # }))


        # Fetch transactions from booking folio lines
        city_ledger_booking_foliol_lines = self.env['booking.folio.line'].sudo().search([
            ('day', '>=', start_date),
            ('day', '<=', end_date),
            ('is_city_ledger', '=', True),
        ]).filtered(lambda l: (customer_id in [l.booking_id.online_travel_agent_source,l.booking_id.company_booking_source] and l.booking_id.company_id == company_id))
        debit_lines = [
            report_line(
                line.day,
                line.description,
                False,
                line.folio_id.name,
                line.booking_id.name,
                line.check_in.date(),
                line.check_out.date(),
                abs(line.amount),
                0,
                0,
            ) for line in city_ledger_booking_foliol_lines
        ]

        payment_booking_ids = self.env['account.payment'].search([
            ('journal_dis_partner_id', '=', customer_id.id),
            ('date', '>=', start_date),
            ('date', '<=', end_date),
            ('state', '=', 'posted'),
            ('company_id', '=', company_id.id),
        ])
        h_booking_ids = payment_booking_ids.h_booking_ids.filtered(lambda b: b.company_paid > 0)

        payment_ids = self.env['account.payment'].search([
            ('partner_id', '=', customer_id.id),
            ('date', '>=', start_date),
            ('date', '<=', end_date),
            ('h_booking_ids', '=',False ),
            ('state', '=', 'posted'),
            ('is_advance_payment', '=', True),
             ('company_id', '=', company_id.id),
        ])

        credit_lines = [
            report_line(
                booking.create_date.date(),
                "##",
                ",".join(payment_booking_ids.filtered(lambda p: booking in p.h_booking_ids).journal_id.mapped('name')),
                '##',
                booking.name,
                booking.check_in.date(),
                booking.check_out.date(),
                0,
                booking.company_paid,
                0,
            ) for booking in h_booking_ids
        ]
        credit_lines += [
            report_line(
                payment.create_date.date(),
                "Advance Payment",
                payment.journal_id.name,
                '##',
                "##",
                "##",
                "##",
                0,
                payment.amount,
                0,
            ) for payment in payment_ids
        ]

        # All lines are sorted by date
        transactions = sorted(debit_lines+credit_lines, key=lambda l: l.date)

        total_debit = sum([line.debit for line in transactions])
        total_credit = sum([line.credit for line in transactions])
        total_balance = total_debit - total_credit
        balance = 0
        for line in transactions:
            line_balance = balance +  line.debit - line.credit
            report_lines.append((
                0,
                0,
                {
                    'date': line.date,
                    'journal_id': line.journal_id if line.journal_id else '',
                    'description': line.description,
                    'folio_id': line.folio_id,
                    'booking_id': line.booking_id,
                    'check_in': line.check_in,
                    'check_out': line.check_out,
                    'debit': line.debit,
                    'credit': line.credit,
                    'balance': line_balance,
                }))
            balance = line_balance
            # opening_balance = balance

        report_lines.append((0, 0, {
            'date': False,
            'journal_id': '',
            'description': 'Closing Balance',
            'folio_id': '',
            'booking_id': '',
            'check_in': '',
            'check_out': '',
            'debit': total_debit ,
            'credit': total_credit ,
            'balance': total_balance,
        }))
        report = self.create({
            'partner_id': customer_id.id,
            'date_from': start_date,
            'date_to': end_date,
            'company_id': company_id.id,
            'transaction_lines': report_lines,
        })

        return self.env.ref('hotel_booking.action_city_ledger_report').report_action(report)


class CityLedgerReportLine(models.Model):
    _name = 'city.ledger.report.line'
    _description = 'City Ledger Report Line'

    report_id = fields.Many2one('city.ledger.report', string='City Ledger Report')
    date = fields.Date(string='Date')
    journal_id = fields.Char("Journal")
    description = fields.Char(string='Description')
    debit = fields.Float(string='Debit', digits=(16, 2))
    credit = fields.Float(string='Credit', digits=(16, 2))
    balance = fields.Float(string='Balance', digits=(16, 2))
    folio_id = fields.Char()
    booking_id = fields.Char()
    check_in = fields.Char()
    check_out = fields.Char()
