from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta


class BookingCancellation(models.TransientModel):
    _name = 'booking.cancellation'
    _description = 'Departure Report'

    line_ids = fields.One2many('booking.cancellation.line', 'wizard_id')
    date_from = fields.Date(string='Date From', required=True)
    date_to = fields.Date(string='Date To', required=True)
    room_type_id = fields.Many2one('room.type', string='Room Type')
    booking_source = fields.Selection(selection=[
        ('online_agent', 'Online Travel Agent'),
        ('company', 'Company'),
        ('direct', 'Direct'),
        ('government_booking', 'Government Booking'),
        ('contract_booking', 'Contract Booking'),
        ('allotment_booking', 'Allotment Booking'),
        ])
    online_travel_agent_source = fields.Many2one('res.partner', domain="[('online_travel_agent', '=', True)]")
    company_booking_source = fields.Many2one('res.partner', domain="[('travel_type', '=', 'company')]")
    rate_type = fields.Many2one('hotel.rate.type', "Rate Type")
    print_subtotal = fields.Boolean("Print Subtotal")
    include_notes = fields.Boolean()

    @api.constrains('date_from', 'date_to')
    def check_dates(self):
        for rec in self:
            if rec.date_to < rec.date_from:
                raise ValidationError(_('Check in Date cannot be earlier than Check out Date !'))

    def get_booking_folios(self):
        self.line_ids = [(5, 0, 0)]
        domain = []
        company_id = self.env.company.id
        date_from = self.date_from
        date_to = self.date_to
        domain.append(('state', '=', 'cancelled'))
        domain.append(('company_id', '=', company_id))
        if date_from:
            domain.append(('check_in', '>=', date_from))
        if date_to:
            domain.append(('check_out', '<=', date_to))
        if self.booking_source:
            domain.append(('booking_source', '=', self.booking_source))
        if self.room_type_id:
            domain.append(('room_type_id', '=', self.room_type_id.id))
        if self.online_travel_agent_source:
            domain.append(('online_travel_agent_source', '=', self.online_travel_agent_source.id))
        if self.company_booking_source:
            domain.append(('company_booking_source', '=', self.company_booking_source.id))
        folio_lines = self.env['booking.folio'].search(domain)
        for folio in folio_lines:
            cancel_audit_trails_line = folio.booking_id.audit_trails.filtered(lambda line:line.folio_id == folio and line.operation== "cancel_folio")
            ref = folio['booking_name']
            partner_id = folio.booking_id.mapped('partner_id').id
            check_in = folio.mapped('check_in')[0]
            check_out = folio.mapped('check_out')[0]
            room_no = sum(folio.mapped('price_total'))
            total_nights = sum(folio.mapped('total_nights'))
            no_guests = sum(folio.mapped('number_of_guests'))
            room_type_id = (folio.mapped('room_type_id')).id
            booking_source = folio['booking_source']
            online_travel_agent_source = (folio.mapped('online_travel_agent_source')).id
            company_booking_source = (folio.mapped('company_booking_source')).id
            subtotal = sum(folio.mapped('price_total'))
            total_paid = sum(folio.mapped('price_paid'))
            note = folio.mapped('booking_note')[0]
            if folio:
                self.env['booking.cancellation.line'].create({
                    'wizard_id': self.id,
                    'ref': ref,
                    'partner_id': partner_id,
                    'check_in': check_in,
                    'check_out': check_out,
                    'room_no': room_no,
                    'no_guests': no_guests,
                    'room_type_id': room_type_id,
                    'booking_source': booking_source,
                    'online_travel_agent_source': online_travel_agent_source,
                    'company_booking_source': company_booking_source,
                    'total_nights': total_nights,
                    'subtotal': subtotal,
                    'total_paid': total_paid,
                    'note': note,
                    'cancelled_at': cancel_audit_trails_line.datetime,
                    'cancelled_by': cancel_audit_trails_line.user_id.id
                })
        return {
            'type': 'ir.actions.act_window',
            'name': _('Booking Cancellation Report'),
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'booking.cancellation',
            'res_id': self.id,
            'target': 'new'
        }

    def print_pdf(self):
        return self.env.ref('hotel_booking.action_booking_cancellation_report').with_context(
            landscape=True).report_action(self)


class BookingCancellationLine(models.TransientModel):
    _name = 'booking.cancellation.line'

    wizard_id = fields.Many2one('booking.cancellation')
    ref = fields.Char("Booking Name")
    partner_id = fields.Many2one('res.partner', string='Guest')
    check_in = fields.Date("Check In")
    check_out = fields.Date("Check Out")
    room_no = fields.Char(string='Room No')
    no_guests = fields.Integer("No Of Guests")
    room_type_id = fields.Many2one('room.type', string='Room Type')
    booking_source = fields.Selection(
        selection=[('online_agent', 'Online Travel Agent'), ('company', 'Company'), ('direct', 'Direct'), ])
    online_travel_agent_source = fields.Many2one('res.partner', domain="[('online_travel_agent', '=', True)]")
    company_booking_source = fields.Many2one('res.partner', domain="[('travel_type', '=', 'company')]")
    total_nights = fields.Integer("Total Nights")
    rate_type = fields.Many2one('hotel.rate.type', "Rate Type")
    subtotal = fields.Float("Subtotal")
    total_paid = fields.Float("Total Paid")
    note = fields.Char("Note")
    cancelled_by = fields.Many2one('res.users', string='Cancelled By')
    cancelled_at = fields.Datetime()
