from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta
from dateutil.relativedelta import relativedelta


class BookingLineReport(models.TransientModel):
    _name = 'booking.line.report'
    _description = 'Booking Line Report'

    date = fields.Date("Date", required=True)
    states = fields.Selection(
        selection=[('stay_over', 'Stay Over'), ('customer_checkout', 'Checkout'), ('customer_checkin', 'Checkin')])
    hotel_id = fields.Many2one('tourism.hotel.hotel')
    partner_id = fields.Many2one('res.partner')
    total_count = fields.Float(compute='compute_total_count', string='Total Rooms')
    line_ids = fields.One2many('booking.line.report.line', 'wizard_id')

    @api.depends('line_ids.count')
    def compute_total_count(self):
        for rec in self:
            total = 0.0
            for line in rec.line_ids:
                total += line.count
            rec.update({
                'total_count': total
            })

    @api.constrains('start_date', 'end_date')
    def validate_dates(self):
        for rec in self:
            if rec.start_date > rec.end_date:
                raise ValidationError("Start date must be before end date!")

    def button_search(self):
        self.line_ids = [(5, 0, 0)]
        reservation_date = self.date
        domain = [('booking_id.booking_type', '=', 'full_package')]
        if self.hotel_id:
            domain.append(('hotel_id', '=', self.hotel_id.id))
        if self.partner_id:
            domain.append(('booking_id.partner_id', '=', self.partner_id.id))

        if self.states == 'stay_over':
            domain += [('check_in', '<=', reservation_date), ('check_out', '>', reservation_date)]

        elif self.states == 'customer_checkin':
            domain += [('check_in', '=', reservation_date)]

        elif self.states == 'customer_checkout':
            domain += [('check_out', '=', reservation_date)]

        booking_lines = self.env['tourism.hotel.booking.line'].sudo().search(domain)

        for booking_line in booking_lines:
            self.line_ids = [(0, 0, {
                'booking_line_id': booking_line.id
            })]

        return {
            'type': 'ir.actions.act_window',
            'name': _('Booking Report'),
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'booking.line.report',
            'res_id': self.id,
            'target': 'new'
        }

    def get_dates_between_exclude(self, date1, date2):
        if isinstance(date1, str):
            date1 = fields.Datetime.from_string(date1)
        if isinstance(date2, str):
            date2 = fields.Datetime.from_string(date2)
        my_list = []
        for n in range(1, int((date2 - date1).days)):
            my_list.append(date1 + timedelta(n))
        return my_list

    def print_pdf(self):
        return self.env.ref('tourism_hotel_booking.action_booking_line_report').report_action(self)

    def print_xlsx(self):
        return self.env.ref('tourism_hotel_booking.action_booking_line_xlsx_report').report_action(self)


class BookingLineReportLine(models.TransientModel):
    _name = 'booking.line.report.line'
    _description = 'Booking Line Report Line'

    wizard_id = fields.Many2one('booking.line.report')
    booking_line_id = fields.Many2one('tourism.hotel.booking.line')
    booking_id = fields.Many2one('tourism.hotel.booking', related='booking_line_id.booking_id', store=True)
    hotel_id = fields.Many2one('tourism.hotel.hotel', related='booking_line_id.hotel_id')
    room_id = fields.Many2one('tourism.hotel.room', related='booking_line_id.room_id')
    check_in = fields.Datetime(related='booking_line_id.check_in')
    check_out = fields.Datetime(related='booking_line_id.check_out')
    count = fields.Float(related='booking_line_id.count')
    contract_id = fields.Many2one('tourism.hotel.contract', related='booking_line_id.contract_id')
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


class BookingLineReportState(models.Model):
    _name = 'booking.line.report.state'
    _description = 'Booking Report State'

    name = fields.Char()
    type = fields.Selection([
        ('draft', 'Tentative Confirmation'),
        ('waiting_hotel', 'Waiting the Hotel'),
        ('hotel_confirm', 'Confirmed from Hotel'),
        ('waiting_customer', 'Waiting the Customer'),
        ('customer_confirm', 'Confirmed from Customer'),
        ('confirmed', 'Confirmed'),
    ])
