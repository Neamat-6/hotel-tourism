from odoo import fields, models, api
from odoo.exceptions import UserError
from datetime import datetime, date


class ServiceVoucherScan(models.Model):
    _name = 'service.voucher.scan'
    _inherit = 'barcodes.barcode_events_mixin'
    _description = 'service voucher scan'

    lines = fields.One2many('service.voucher.scan.line', 'scan_id')
    meal_number = fields.Selection(selection=[
        ('1', 'Breakfast'), ('2', 'Lunch'), ('3', 'Dinner'),
    ], default='1', required=True)

    def on_barcode_scanned(self, barcode):
        line_values = {
            'barcode': barcode,
        }
        new_voucher_line = self.lines.new(line_values)
        self.lines += new_voucher_line
        new_voucher_line.check_barcode()

    def redeem_voucher(self):
        for line in self.lines:
            vouchers = self.env['service.voucher'].sudo().search([
                ('name', '=', line.barcode), ('state', '=', 'available'),
                ('meal_number', '=', line.meal_number), ('date_to', '=', date.today())
            ])
            if not vouchers:
                raise UserError('Invalid/expired Voucher!')
            for voucher in vouchers:
                voucher.state = 'redeemed'


class ServiceVoucherScanLine(models.Model):
    _name = 'service.voucher.scan.line'
    _description = 'service voucher scan'

    scan_id = fields.Many2one('service.voucher.scan')
    barcode = fields.Char(required=True)
    meal_number = fields.Selection(selection=[
        ('1', 'Breakfast'), ('2', 'Lunch'), ('3', 'Dinner'),
    ], related='scan_id.meal_number', store=True)

    @api.onchange('barcode', 'meal_number')
    def check_barcode(self):
        if self.barcode:
            voucher = self.env['service.voucher'].sudo().search([
                ('name', '=', self.barcode), ('meal_number', '=', self.scan_id.meal_number),
                ('date_to', '=', date.today()), ('state', '=', 'available')
            ])
            if not voucher:
                raise UserError('Invalid/expired Voucher!')