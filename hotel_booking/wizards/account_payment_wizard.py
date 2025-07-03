import math

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AccountPayment(models.Model):
    _name = 'account.payment.wizard'

    date_from = fields.Datetime('Date From')
    date_to = fields.Datetime('Date To')
    audit_date = fields.Date("Audit Date", required=True)
    company_ids = fields.Many2many(comodel_name="res.company", default=lambda self: self.env.user.company_ids.ids)
    # user_id = fields.Many2one('res.users', string='User')
    user_ids = fields.Many2many('res.users', string='Users', required=True)

    def print_report(self):
        data = {
            'model': 'account.payment.wizard',
            'form': self.read()[0]
        }
        print('ddddddddddddddddddd',data)
        return self.env.ref('hotel_booking.account_payment_report').report_action(self, data=data)


class StudentsReportData(models.AbstractModel):
    _name = "report.hotel_booking.account_payment_report_template"

    @api.model
    def _get_report_values(self, docids, data=None):
        audit_date = data['form']['audit_date']
        user_ids = data['form']['user_ids']

        domain = [('booking_id', '!=', False), ('state', '=', 'posted')]
        if audit_date:
            domain.append(('audit_date', '=', audit_date))

        if user_ids:
            domain.append(('user_id', 'in', user_ids))
            users_in_report = self.env['res.users'].sudo().browse(user_ids).mapped('name')
        else:
            users_in_report = ""

        account_payment_obj = self.env['account.payment'].search(domain)
        payment_methods_list = []
        payment_methods = account_payment_obj.mapped('journal_id')
        for method in payment_methods:
            payments_to_method = account_payment_obj.filtered(lambda journal: journal.journal_id.id == method.id)
            method_total_amount = sum(payments_to_method.mapped('amount_signed'))
            truncated_amount = math.floor(method_total_amount * 100) / 100
            currency = payments_to_method[0].currency_id
            currency_code = currency.symbol  # e.g., 'EGP'
            # Append name and formatted amount
            payment_methods_list.append([method.name, f"{truncated_amount} {currency_code}"])

        return {
            'doc_model': 'account.payment.wizard',
            'docs': account_payment_obj,
            'audit_date': audit_date,
            'payment_methods_list': payment_methods_list,
            'user_ids': users_in_report,
        }
