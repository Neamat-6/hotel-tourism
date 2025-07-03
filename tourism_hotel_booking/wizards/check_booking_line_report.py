from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta
from dateutil.relativedelta import relativedelta


class BookingLineReport(models.TransientModel):
    _name = 'check.booking.line.report'
    _description = 'Check Booking Line Report'

    check_in_from = fields.Date()
    check_in_to = fields.Date()
    check_out_from = fields.Date()
    check_out_to = fields.Date()
    hotel_id = fields.Many2one('hotel.hotel')
    state_ids = fields.Many2many('booking.line.report.state', string='States')
    partner_id = fields.Many2one('res.partner')
    total_count = fields.Float(compute='compute_total_count', string='Total Rooms')
    line_ids = fields.One2many('check.booking.line.report.line', 'wizard_id')

    @api.depends('line_ids.count')
    def compute_total_count(self):
        for rec in self:
            total = 0.0
            for line in rec.line_ids:
                total += line.count
            rec.update({
                'total_count': total
            })

    def button_search(self):
        self.line_ids = [(5, 0, 0)]
        domain = []
        if self.check_in_from:
            domain.append(('check_in', '>=', self.check_in_from))
        if self.check_in_to:
            domain.append(('check_in', '<=', self.check_in_to))
        if self.check_out_from:
            domain.append(('check_out', '>=', self.check_out_from))
        if self.check_out_to:
            domain.append(('check_out', '<=', self.check_out_to))

        if self.state_ids:
            domain.append(('booking_id.state', 'in', self.state_ids.mapped('type')))
        else:
            domain.append(('booking_id.state', 'not in', ['cancelled', 'draft']))
        if self.hotel_id:
            domain.append(('hotel_id', '=', self.hotel_id.id))
        if self.partner_id:
            domain.append(('booking_id.partner_id', '=', self.partner_id.id))
        booking_lines = self.env['tourism.hotel.booking.line'].sudo().search(domain)
        for booking_line in booking_lines:
            self.line_ids = [(0, 0, {
                'booking_line_id': booking_line.id
            })]

        return {
            'type': 'ir.actions.act_window',
            'name': _('Check Booking Report'),
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'check.booking.line.report',
            'res_id': self.id,
            'target': 'new'
        }

    def print_pdf(self):
        return self.env.ref('tourism_hotel_booking.action_check_booking_line_report').report_action(self)

    def print_xlsx(self):
        return self.env.ref('tourism_hotel_booking.action_check_booking_line_xlsx_report').report_action(self)


class BookingLineReportLine(models.TransientModel):
    _name = 'check.booking.line.report.line'
    _description = 'Check Booking Line Report Line'

    wizard_id = fields.Many2one('check.booking.line.report')
    booking_line_id = fields.Many2one('tourism.hotel.booking.line')
    booking_id = fields.Many2one('tourism.hotel.booking', related='booking_line_id.booking_id', store=True)
    room_id = fields.Many2one('hotel.room', related='booking_line_id.room_id')
    check_in = fields.Datetime(related='booking_line_id.check_in')
    check_out = fields.Datetime(related='booking_line_id.check_out')
    count = fields.Float(related='booking_line_id.count')
    contract_id = fields.Many2one('hotel.contract', related='booking_line_id.contract_id')
    partner_id = fields.Many2one('res.partner', related='booking_id.partner_id')
    # amount fields
    price = fields.Float(string='Line Price', related='booking_line_id.price')
    cost = fields.Float(string='Line Cost', related='booking_line_id.cost')
    tax_amount = fields.Float(string='Line Tax', related='booking_line_id.tax_amount')
    total_amount = fields.Float(string='Line Total', related='booking_line_id.total_amount')
    # booking fields
    booking_amount_total = fields.Monetary(string="Booking Total", related='booking_id.amount_total')
    booking_amount_paid = fields.Monetary(string="Booking Paid", related='booking_id.amount_paid')
    booking_amount_due = fields.Monetary(string="Booking Due", related='booking_id.amount_due')
    currency_id = fields.Many2one('res.currency', related='booking_id.currency_id')
    state = fields.Selection(related='booking_id.state')
