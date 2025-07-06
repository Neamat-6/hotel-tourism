from odoo import api, fields, models
from odoo.exceptions import UserError


class VisaBooking(models.Model):
    _name = 'visa.booking'

    visa_name = fields.Char("Visa")
    visa_id = fields.Many2one('product.product', string='Visa')
    visa_type = fields.Selection(selection=[('virtual', 'Virtual'), ('non_virtual', 'Non Virtual')],
                                 string='Type Of Visa')
    no_of_visa = fields.Integer("No Of Visa")
    visa_price = fields.Float("Price Per Visa")
    total_price = fields.Float("Total Price", compute='calc_total_price')
    refund_price = fields.Float("Refund Price")
    net_amount_price = fields.Float("Net Amount", compute='calc_net_amount')
    gross_amount = fields.Float("Gross Amount")
    refund_amount = fields.Float("Refund Amount")
    booking_id = fields.Many2one('tourism.hotel.booking')
    booking_type = fields.Selection(related='booking_id.booking_type')
    account_move_id = fields.Many2one('account.move', 'Invoice')
    account_account_id = fields.Many2one('account.account')
    is_invoiced = fields.Boolean(compute='compute_invoice')

    @api.onchange('no_of_visa', 'visa_price')
    def calc_total_price(self):
        for rec in self:
            rec.total_price = rec.visa_price * rec.no_of_visa

    @api.onchange('total_price', 'refund_price')
    def calc_net_amount(self):
        for rec in self:
            rec.net_amount_price = rec.total_price - rec.refund_price

    def create_visa_invoice(self):
        account_move_obj = self.env['account.move']
        for line in self:
            if line.account_account_id:
                invoice_create_obj = account_move_obj.create({
                    'move_type': 'out_invoice',
                    'partner_id': line.booking_id.travel_agent_name.id,
                    'tourism_booking_id': line.booking_id.id,
                    'visa_booking_id': line.id,
                    'date': line.create_date,
                    'invoice_date': line.create_date,
                    'invoice_line_ids': [(0, 0, {
                        'name': line.visa_id.name,
                        'product_id': line.visa_id.id,
                        'price_unit': line.visa_price,
                        'quantity': line.no_of_visa,
                    }), (0, 0, {
                        'name': 'discount',
                        'account_id': line.account_account_id.id,
                        'price_unit': - line.refund_price,
                        'quantity': 1,
                    })]
                })
                self.account_move_id = invoice_create_obj.id
            else:
                invoice_create_obj = account_move_obj.create({
                    'move_type': 'out_invoice',
                    'partner_id': line.booking_id.travel_agent_name.id,
                    'tourism_booking_id': line.booking_id.id,
                    'visa_booking_id': line.id,
                    'date': line.create_date,
                    'invoice_date': line.create_date,
                    'invoice_line_ids': [(0, 0, {
                        'name': line.visa_id.name,
                        'product_id': line.visa_id.id,
                        'price_unit': line.visa_price,
                        # 'discount': line.refund_price,
                        'quantity': line.no_of_visa,
                    })]
                })
                self.account_move_id = invoice_create_obj.id

    @api.constrains('no_of_visa', 'visa_price', 'total_price', 'refund_price')
    def update_visa_invoice(self):
        account_move_obj = self.account_move_id
        for line in self:
            if line.account_move_id and line.booking_id.state == 'draft':
                account_move_obj.invoice_line_ids = [(5, 0, 0)]
                if line.account_account_id:
                    invoice_update_obj = account_move_obj.update({
                        'move_type': 'out_invoice',
                        'partner_id': line.booking_id.travel_agent_name.id,
                        'tourism_booking_id': line.booking_id.id,
                        'visa_booking_id': line.id,
                        'date': line.create_date,
                        'invoice_date': line.create_date,
                        'invoice_line_ids': [(0, 0, {
                            'name': line.visa_id.name,
                            'product_id': line.visa_id.id,
                            'price_unit': line.visa_price,
                            'quantity': line.no_of_visa,
                        }), (0, 0, {
                            'name': 'discount',
                            'account_id': line.account_account_id.id,
                            'price_unit': - line.refund_price,
                            'quantity': 1,
                        })]
                    })
                    self.update({'account_move_id': account_move_obj.id})
                else:
                    account_move_obj.invoice_line_ids = [(5, 0, 0)]
                    invoice_update_obj = account_move_obj.update({
                        'move_type': 'out_invoice',
                        'partner_id': line.booking_id.travel_agent_name.id,
                        'tourism_booking_id': line.booking_id.id,
                        'visa_booking_id': line.id,
                        'date': line.create_date,
                        'invoice_date': line.create_date,
                        'invoice_line_ids': [(0, 0, {
                            'name': line.visa_id.name,
                            'product_id': line.visa_id.id,
                            'price_unit': line.visa_price,
                            # 'discount': line.refund_price,
                            'quantity': line.no_of_visa,
                        })]
                    })
                    self.update({'account_move_id': account_move_obj.id})
