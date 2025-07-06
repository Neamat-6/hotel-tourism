from datetime import timedelta

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ContractWizard(models.TransientModel):
    _name = 'contract.wizard'

    contract_line_ids = fields.Many2many('tourism.hotel.contract.line')

    def create_bill(self):
        self.check_dates()
        account_move_obj = self.env['account.move']
        tax_id = self.contract_line_ids.contract_id.mapped('tax_id')
        data = []
        for line in self.contract_line_ids:
            data.append((0, 0, {
                'name': line.room_type.name,
                'price_unit': line.price,
                'quantity': float(line.new_date_difference) * line.count,
                'start_date': line.new_start_date,
                'end_date': line.new_end_date,
                'number_of_days': line.new_date_difference,
                'tax_ids': tax_id
            }))
        bill_create_obj = account_move_obj.create({
            'move_type': 'in_invoice',
            'partner_id': line.contract_id.vendor.id,
            'ref': line.contract_id.vendor.name,
            'date': fields.Date.today(),
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': data,
            'hotel_contract_id': line.contract_id.id
        })
        # bill_create_obj.action_post()

    def check_dates(self):
        for record in self.contract_line_ids:
            if record.contract_id.invoice_ids:
                for line in record.contract_id.invoice_ids:
                    start_date = line.invoice_line_ids.filtered(lambda l: l.name == record.room_type.name).mapped(
                        'start_date')
                    end_date = line.invoice_line_ids.filtered(lambda l: l.name == record.room_type.name).mapped(
                        'end_date')
                    if start_date and end_date:
                        date_string = '-'.join(map(str, start_date))
                        if str(record.new_start_date) <= date_string:
                            raise ValidationError("That Duration Of Date is Already Invoiced")
