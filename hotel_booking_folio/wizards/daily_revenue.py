from dateutil.relativedelta import relativedelta

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class DailyRevenue(models.TransientModel):
    _name = 'daily.revenue'
    _description = 'Daily Revenue'

    line_ids = fields.One2many('daily.revenue.line', 'wizard_id')
    date_from = fields.Date(string='From', required=True)
    date_to = fields.Date(string='To', required=True)
    filter_room_charge = fields.Boolean("Include Room Charge")
    filter_vat = fields.Boolean("Include VAT")
    filter_municipality = fields.Boolean("Include Municipality")
    filter_service = fields.Boolean("Include Service")
    display_folio_numbers = fields.Boolean("Display Folio Numbers")
    company_ids = fields.Many2many('res.company', string='Companies')
    total_room_charge = fields.Float(compute='compute_totals', store=True)
    total_vat = fields.Float(compute='compute_totals', store=True)
    total_municipality = fields.Float(compute='compute_totals', store=True)
    total_service = fields.Float(compute='compute_totals', store=True)
    total_payment = fields.Float(compute='compute_totals', store=True)
    total = fields.Float(compute='compute_totals', store=True)
    filter_folio_state = fields.Selection([
        ('checked_in', 'Checked In'),
        ('checked_out', 'Checked Out'),
        ('confirmed', 'Confirmed'),
    ], string='Folio State')


    @api.depends('line_ids')
    def compute_totals(self):
        for rec in self:
            rec.total_room_charge = 0
            rec.total_vat = 0
            rec.total_municipality = 0
            rec.total_payment = 0
            rec.total_service = 0
            rec.total = 0
            if rec.line_ids:
                rec.total_room_charge = sum(rec.line_ids.mapped('total_room_charge'))
                rec.total_vat = sum(rec.line_ids.mapped('total_vat'))
                rec.total_municipality = sum(rec.line_ids.mapped('total_municipality'))
                rec.total_payment = sum(rec.line_ids.mapped('total_payment'))
                rec.total_service = sum(rec.line_ids.mapped('total_service'))
                rec.total = sum(rec.line_ids.mapped('total'))

    @api.constrains('date_from', 'date_to')
    def check_dates(self):
        for rec in self:
            if rec.date_to < rec.date_from:
                raise ValidationError(_('To date cannot be earlier than from date!'))


    def get_folio_lines(self,start):
        folio_lines = self.env['booking.folio.line'].search(
            [('day', '=', start), ('state', '!=', 'cancelled'), ('booking_id.state', '!=', 'cancelled'),
                ('folio_id.state', '!=', 'cancelled')])
        if self.filter_folio_state:
            folio_lines = folio_lines.filtered(lambda line: line.folio_id.state == self.filter_folio_state)
        return folio_lines

    def get_returned_view(self):
                return {
            'type': 'ir.actions.act_window',
            'name': _('Daily Revenue'),
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'daily.revenue',
            'res_id': self.id,
            'target': 'new'
        }

    def button_search(self):
        self.line_ids = [(5, 0, 0)]
        days = []
        start = self.date_from
        end = self.date_to
        while start <= end:
            days.append(start)
            folio_lines = self.get_folio_lines(start)
            partners = set(folio_lines.mapped('partner_id'))
            for partner in partners:
                lines = folio_lines.filtered(lambda l: l.partner_id == partner)
                folio_ids = lines.mapped('folio_id')
                booking_ids = folio_ids.mapped('booking_id')

                total_room_charge = 0.0
                total_vat = 0.0
                total_municipality = 0.0
                total_service = 0.0

                if self.filter_room_charge:
                    total_room_charge = sum(lines.filtered(lambda l: l.type == 'room_charge').mapped('amount')) or 0.0
                if self.filter_vat:
                    total_vat = sum(lines.filtered(lambda l: l.tax_type == 'vat').mapped('amount')) or 0.0
                if self.filter_municipality:
                    total_municipality = sum(lines.filtered(lambda l: l.tax_type == 'municipality').mapped('amount')) or 0.0
                total_payment = sum(lines.filtered(lambda l: l.payment_id).mapped('amount'))
                if self.filter_service:
                    total_service = abs(sum(lines.filtered(lambda l: l.type not in ['room_charge', 'tax', 'discount',False] and not l.payment_id and not l.is_city_ledger).mapped('amount')))

                total = total_room_charge + total_vat + total_municipality
                # this is cause two partner not created in lines
                if total or total_service or total_payment:
                    self.env['daily.revenue.line'].create({
                        'wizard_id': self.id,
                        'booking_ids': booking_ids.ids,
                        'folio_ids': folio_ids.ids,
                        'day': start,
                        'partner_id': partner.id,
                        'total_room_charge': round(total_room_charge, 2),
                        'total_service': round(total_service, 2),
                        'total_payment': round(total_payment, 2),
                        'total_vat': round(total_vat, 2),
                        'total_municipality': round(total_municipality, 2),
                        'total': round(total, 2),
                        'line_type': lines.mapped('particulars')
                    })
            start += relativedelta(days=1)
        return self.get_returned_view()

    def print_pdf(self):
        return self.env.ref('hotel_booking_folio.action_daily_revenue_report').with_context(
            landscape=True).report_action(self)

    def print_xlsx(self):
        return self.env.ref('hotel_booking_folio.action_daily_revenue_xlsx_report').report_action(self)


class DailyRevenueLine(models.TransientModel):
    _name = 'daily.revenue.line'
    _description = 'Daily Revenue Line'

    wizard_id = fields.Many2one('daily.revenue')
    folio_ids = fields.Many2many('booking.folio')
    booking_ids = fields.Many2many('hotel.booking')
    day = fields.Date()
    partner_id = fields.Many2one('res.partner', string='Guest Name')
    total_room_charge = fields.Float()
    total_vat = fields.Float()
    total_municipality = fields.Float()
    total_service = fields.Float()
    total_payment = fields.Float()
    total = fields.Float()
    line_type = fields.Char()
