from collections import defaultdict

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta


class RevenueSummary(models.TransientModel):
    _name = 'revenue.summary'
    _description = 'Revenue Summary'

    line_ids = fields.One2many('revenue.summary.line', 'wizard_id')
    date_from = fields.Date(string='From', required=True)
    date_to = fields.Date(string='To', required=True)
    company_ids = fields.Many2many('res.company', string='Companies')
    total_room_charge = fields.Float(compute='compute_totals', store=True)
    total_vat = fields.Float(compute='compute_totals', store=True)
    total_municipality = fields.Float(compute='compute_totals', store=True)
    total_service = fields.Float(compute='compute_totals', store=True)
    total_payment = fields.Float(compute='compute_totals', store=True)
    total = fields.Float(compute='compute_totals', store=True)

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

    def button_search(self):
        # Reset line_ids
        self.line_ids = [(5, 0, 0)]

        current_day = self.date_from
        while current_day <= self.date_to:
            folio_lines = self.env['booking.folio.line'].search([
                ('day', '=', current_day),
                ('state', '!=', 'cancelled'),
                ('booking_id.state', '!=', 'cancelled'),
                ('folio_id.state', '!=', 'cancelled')
            ])
            folio_ids = folio_lines.mapped('folio_id')
            booking_ids = folio_lines.mapped('booking_id')
            total_room_charge = sum(folio_lines.filtered(lambda l: l.type == 'room_charge').mapped('amount'))
            total_vat = sum(folio_lines.filtered(lambda l: l.tax_type == 'vat').mapped('amount'))
            total_municipality = sum(folio_lines.filtered(lambda l: l.tax_type == 'municipality').mapped('amount'))
            total_payment = sum(folio_lines.filtered(lambda l: l.payment_id).mapped('amount'))
            total_service = abs(sum(folio_lines.filtered(
                lambda l: l.type not in ['room_charge', 'tax', 'discount',False] and not l.payment_id and not l.is_city_ledger).mapped('amount')))
            total = total_room_charge + total_vat + total_municipality
            if total or total_payment or total_service:
                self.env['revenue.summary.line'].create({
                    'wizard_id': self.id,
                    'day': current_day,
                    'total_room_charge': round(total_room_charge, 2),
                    'total_service': round(total_service, 2),
                    'total_payment': round(total_payment, 2),
                    'total_vat': round(total_vat, 2),
                    'total_municipality': round(total_municipality, 2),
                    'total': round(total, 2),
                })

            current_day += relativedelta(days=1)

        return {
            'type': 'ir.actions.act_window',
            'name': _('Revenue Summary'),
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'revenue.summary',
            'res_id': self.id,
            'target': 'new'
        }

    def print_pdf(self):
        return self.env.ref('hotel_booking_folio.action_revenue_summary_report').with_context(
            landscape=True).report_action(self)


class RevenueSummaryLine(models.TransientModel):
    _name = 'revenue.summary.line'
    _description = 'Revenue Summary Line'

    wizard_id = fields.Many2one('revenue.summary')
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
