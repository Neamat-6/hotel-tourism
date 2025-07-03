from odoo import fields, models, _


class CompanyLedgerReport(models.TransientModel):
    _name = 'company.ledger.report'
    _description = 'Company Ledger Report'

    line_ids = fields.One2many('company.ledger.report.line', 'wizard_id')
    company_booking_source_ids = fields.Many2many('res.partner', domain="[('is_company','=',True)]")
    related_hotel = fields.Many2many('hotel.hotel', string='Related Hotel')

    def get_booking_source_folios(self):
        self.line_ids = [(5, 0, 0)]
        domain = []
        if self.company_booking_source_ids:
            domain.append(('id', 'in', self.company_booking_source_ids.ids))

        domain.append(('is_company', '=', True))

        res_partner_objs = self.env['res.partner'].search(domain)

        for partner in res_partner_objs:
            company = partner['id']
            credit_limit = partner['customer_credit_limit']
            balance = partner['balance']
            due_amount = partner['customer_due_amount']
            advanced_payment = partner['total_advanced_payment']

            if partner:
                self.env['company.ledger.report.line'].create({
                    'wizard_id': self.id,
                    'company_booking_source': company,
                    'credit_limit': credit_limit,
                    'balance': balance,
                    'due_amount': due_amount,
                    'advanced_payment': advanced_payment,
                })
        return {
            'type': 'ir.actions.act_window',
            'name': _('Company Ledger Report'),
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'company.ledger.report',
            'res_id': self.id,
            'target': 'new'
        }

    def print_pdf(self):
        return self.env.ref('hotel_booking.action_company_ledger_report').with_context(
            landscape=True).report_action(self)


class CompanyLEdgerReportLine(models.TransientModel):
    _name = 'company.ledger.report.line'
    _description = 'Company Ledger Report Line'

    wizard_id = fields.Many2one('company.ledger.report')
    company_booking_source = fields.Many2one('res.partner')
    credit_limit = fields.Float(string='Credit Limit')
    balance = fields.Float(string='Balance')
    due_amount = fields.Float(string='Due Amount')
    advanced_payment = fields.Float(string='Advanced Payment')
