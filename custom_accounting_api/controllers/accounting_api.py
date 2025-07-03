from odoo import http
from odoo.http import request

class AccountingAPI(http.Controller):

    # Invoices
    @http.route('/api/accounting/invoices', type='json', auth='user', methods=['GET'], csrf=False)
    def get_invoices(self):
        invoices = request.env['account.move'].search([('move_type', 'in', ['out_invoice', 'in_invoice'])])
        data = invoices.read(['name', 'partner_id', 'amount_total', 'state', 'move_type'])
        return {'status': 'success', 'data': data}

    @http.route('/api/accounting/invoices', type='json', auth='user', methods=['POST'], csrf=False)
    def create_invoice(self, **kwargs):
        try:
            invoice = request.env['account.move'].create({
                'partner_id': kwargs.get('partner_id'),
                'move_type': kwargs.get('move_type'),
                'invoice_date': kwargs.get('invoice_date'),
                'invoice_line_ids': [(0, 0, line) for line in kwargs.get('invoice_line_ids')],
            })
            return {'status': 'success', 'invoice_id': invoice.id}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    # Payments
    @http.route('/api/accounting/payments', type='json', auth='user', methods=['GET'], csrf=False)
    def get_payments(self):
        payments = request.env['account.payment'].search([])
        data = payments.read(['name', 'partner_id', 'amount', 'state', 'payment_date'])
        return {'status': 'success', 'data': data}

    @http.route('/api/accounting/payments', type='json', auth='user', methods=['POST'], csrf=False)
    def create_payment(self, **kwargs):
        try:
            payment = request.env['account.payment'].create({
                'payment_type': kwargs.get('payment_type'),
                'partner_id': kwargs.get('partner_id'),
                'amount': kwargs.get('amount'),
                'payment_date': kwargs.get('payment_date'),
                'journal_id': kwargs.get('journal_id'),
            })
            payment.post()
            return {'status': 'success', 'payment_id': payment.id}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    # Chart of Accounts
    @http.route('/api/accounting/accounts', type='json', auth='user', methods=['GET'], csrf=False)
    def get_accounts(self):
        accounts = request.env['account.account'].search([])
        data = accounts.read(['name', 'code', 'user_type_id', 'reconcile'])
        return {'status': 'success', 'data': data}

    # Journal Entries
    @http.route('/api/accounting/journals', type='json', auth='user', methods=['GET'], csrf=False)
    def get_journal_entries(self):
        journals = request.env['account.move'].search([('move_type', '=', 'entry')])
        data = journals.read(['name', 'line_ids', 'state', 'date'])
        return {'status': 'success', 'data': data}

    @http.route('/api/accounting/journals', type='json', auth='user', methods=['POST'], csrf=False)
    def create_journal_entry(self, **kwargs):
        try:
            journal_entry = request.env['account.move'].create({
                'move_type': 'entry',
                'line_ids': [(0, 0, line) for line in kwargs.get('line_ids')],
            })
            return {'status': 'success', 'journal_entry_id': journal_entry.id}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    # Taxes
    @http.route('/api/accounting/taxes', type='json', auth='user', methods=['GET'], csrf=False)
    def get_taxes(self):
        taxes = request.env['account.tax'].search([])
        data = taxes.read(['name', 'amount', 'type_tax_use'])
        return {'status': 'success', 'data': data}

    # Reports
    @http.route('/api/accounting/reports/profit_and_loss', type='json', auth='user', methods=['GET'], csrf=False)
    def get_profit_and_loss(self):
        report = request.env['account.financial.html.report'].search([('name', '=', 'Profit and Loss')], limit=1)
        if not report:
            return {'status': 'error', 'message': 'Report not found'}
        return {'status': 'success', 'data': report.get_html()}

    @http.route('/api/accounting/reports/balance_sheet', type='json', auth='user', methods=['GET'], csrf=False)
    def get_balance_sheet(self):
        report = request.env['account.financial.html.report'].search([('name', '=', 'Balance Sheet')], limit=1)
        if not report:
            return {'status': 'error', 'message': 'Report not found'}
        return {'status': 'success', 'data': report.get_html()}
