from odoo import fields, models, api


class PartnerLedgerWizard(models.TransientModel):
    _name = 'partner.ledger.wizard'
    _description = 'Partner Ledger'

    line_ids = fields.One2many('city.ledger.line', 'wizard_id')
    date_from = fields.Date(string='Date From', required=True)
    date_to = fields.Date(string='Date To', required=True)
    partner_id = fields.Many2one('res.partner', "Partner", domain=[('is_city_ledger', '=', False)])

    def generate_report(self):
        self.ensure_one()
        return self.env['partner.ledger.report'].create_report(self.date_from, self.date_to, self.partner_id)


class PartnerLedgerReport(models.Model):
    _name = 'partner.ledger.report'
    _description = 'Partner Ledger Report'

    partner_id = fields.Many2one('res.partner', string='Customer')
    date_from = fields.Date(string='Start Date')
    date_to = fields.Date(string='End Date')
    transaction_lines = fields.One2many('partner.ledger.report.line', 'report_id', string='Transaction Lines')

    @api.model
    def create_report(self, start_date, end_date, customer_id):
        report_lines = []

        transactions_before_start_date = self.env['account.move.line'].search([
            ('partner_id', '=', customer_id.id),
            ('date', '<', start_date),
            ('move_id.state', '=', 'posted')
        ]).filtered(lambda l: l.journal_id.type in ['cash', 'bank'])

        opening_balance = sum(line.debit - line.credit for line in transactions_before_start_date)

        report_lines.append((0, 0, {
            'date': False,
            'journal_id': '',
            'description': 'Opening Balance',
            'folio_id': '',
            'booking_id': '',
            'debit': opening_balance if opening_balance > 0 else 0,
            'credit': -opening_balance if opening_balance < 0 else 0,
            'balance': opening_balance,
        }))

        transactions = self.env['account.move.line'].search([
            ('partner_id', '=', customer_id.id),
            ('date', '>=', start_date),
            ('date', '<=', end_date),
            ('move_id.state', '=', 'posted')
        ], order='date').filtered(lambda l: l.journal_id.type in ['cash', 'bank'])

        # Create report lines
        for line in transactions:
            balance = opening_balance + line.debit - line.credit
            report_lines.append((0, 0, {
                'date': line.date,
                'journal_id': line.journal_id.name,
                'description': line.name or line.move_id.name,
                'folio_id': line.move_id.folio_id.name if line.move_id.folio_id else '',
                'booking_id': line.move_id.booking_id.name if line.move_id.booking_id else '',
                'debit': line.debit,
                'credit': line.credit,
                'balance': balance,
            }))
            opening_balance = balance

        report = self.create({
            'partner_id': customer_id.id,
            'date_from': start_date,
            'date_to': end_date,
            'transaction_lines': report_lines,
        })

        return self.env.ref('hotel_booking.action_partner_ledger_report').report_action(report)


class PartnerLedgerReportLine(models.Model):
    _name = 'partner.ledger.report.line'
    _description = 'Partner Ledger Report Line'

    report_id = fields.Many2one('partner.ledger.report', string='Partner Ledger Report')
    date = fields.Date(string='Date')
    journal_id = fields.Char("Journal")
    description = fields.Char(string='Description')
    debit = fields.Float(string='Debit')
    credit = fields.Float(string='Credit')
    balance = fields.Float(string='Balance')
    folio_id = fields.Char()
    booking_id = fields.Char()
