from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class HotelRoomWizard(models.Model):
    _name = 'hotel.room.wizard'

    date_from = fields.Datetime('Date From')
    date_to = fields.Datetime('Date To')
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user)

    def print_report(self):
        data = {
            'model': 'hotel.room.wizard',
            'form': self.read()[0]
        }
        return self.env.ref('hotel_booking.account_payment_report').report_action(self, data=data)


class StudentsReportData(models.AbstractModel):
    _name = "report.hotel_booking.account_payment_report_template"

    @api.model
    def _get_report_values(self, docids, data=None):
        date = data['form']['date']
        user_id = data['form']['user_id']

        domain = []

        if date:
            domain.append(('audit_date', '=', date))
            audit_date_in_report = date
        else:
            audit_date_in_report = ""

        if user_id:
            domain.append(('user_id', '=', user_id[0]))
            user_in_report = user_id[1]
        else:
            user_in_report = ""

        hotel_room_obj = self.env['hotel.room'].search(domain)
        # payment_methods_list = []
        # payment_methods = hotel_room_obj.mapped('journal_id')
        # for method in payment_methods:
        #     payments_to_method = account_payment_obj.filtered(lambda journal: journal.journal_id.id == method.id)
        #     method_total_amount = sum(payments_to_method.mapped('amount_signed'))
        #     payment_methods_list.append([method.name, method_total_amount])
        # print(payment_methods_list)

        return {
            'doc_model': 'account.payment.wizard',
            'docs': hotel_room_obj,
            'audit_date': date,
            'user_id': user_in_report,
        }
