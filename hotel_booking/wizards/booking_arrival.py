from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta


class BookingArrival(models.TransientModel):
    _name = 'booking.arrival'
    _description = 'Arrival Report'

    line_ids = fields.One2many('booking.arrival.line', 'wizard_id')
    check_in_from = fields.Date(string='Check In From', required=True)
    check_in_to = fields.Date(string='Check In To', required=True)
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
    company_booking_source = fields.Many2one('res.partner', domain="[('is_company','=',True)]")
    rate_type = fields.Many2one('hotel.rate.type', "Rate Type")
    print_subtotal = fields.Boolean("Print Subtotal")
    related_hotel = fields.Many2many('hotel.hotel', string='Related Hotel')
    total_amount = fields.Float(compute="calc_total_amount", digits=(16, 2))
    include_notes = fields.Boolean()

    def calc_total_amount(self):
        for rec in self:
            if rec.line_ids:
                rec.total_amount = sum(rec.line_ids.mapped('subtotal'))
            else:
                rec.total_amount = 0.0

    @api.constrains('check_in_to', 'check_in_from')
    def check_dates(self):
        for rec in self:
            if rec.check_in_to < rec.check_in_from:
                raise ValidationError(_('Check in Date From cannot be earlier than Check In Date To !'))

    def get_booking_folios(self):
        self.line_ids = [(5, 0, 0)]
        domain = []
        check_in_from = self.check_in_from
        check_in_to = self.check_in_to
        domain.append(('state', '!=', 'cancelled'))
        if self.related_hotel:
            domain.append(('hotel_id', 'in', self.related_hotel.ids))
        if check_in_from:
            domain.append(('check_in', '>=', check_in_from))
        if check_in_to:
            domain.append(('check_in', '<=', check_in_to))
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
            ref = ''.join(folio.mapped('booking_name'))
            partner_id = folio.booking_id.mapped('partner_id').id
            check_in = folio.mapped('check_in')[0]
            check_out = folio.mapped('check_out')[0]
            room_id = (folio.mapped('room_id')).id
            total_nights = sum(folio.mapped('total_nights'))
            no_guests = sum(folio.mapped('number_of_guests'))
            room_type_id = (folio.mapped('room_type_id')).id
            booking_source = ''.join(folio.mapped('booking_source'))
            online_travel_agent_source = (folio.mapped('online_travel_agent_source')).id
            company_booking_source = (folio.mapped('company_booking_source')).id
            related_hotel = (folio.mapped('hotel_id')).id
            # rate_type = folio.mapped('rate_type_id')
            subtotal = sum(folio.mapped('price_total'))
            note = folio.mapped('booking_note')[0]
            if folio:
                self.env['booking.arrival.line'].create({
                    'wizard_id': self.id,
                    'ref': ref,
                    'partner_id': partner_id,
                    'check_in': check_in,
                    'check_out': check_out,
                    'room_id': room_id,
                    'no_guests': no_guests,
                    'room_type_id': room_type_id,
                    'booking_source': booking_source,
                    'online_travel_agent_source': online_travel_agent_source,
                    'company_booking_source': company_booking_source,
                    'total_nights': total_nights,
                    'subtotal': subtotal,
                    'related_hotel': related_hotel,
                    'note': note,
                })
        return {
            'type': 'ir.actions.act_window',
            'name': _('Arrival Report'),
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'booking.arrival',
            'res_id': self.id,
            'target': 'new'
        }

    def print_pdf(self):
        return self.env.ref('hotel_booking.action_booking_arrival_report').with_context(
            landscape=True).report_action(self)

    def print_xlsx(self):
        return self.env.ref('hotel_booking.action_arrival_xlsx_report').report_action(self)



class BookingArrivalLine(models.TransientModel):
    _name = 'booking.arrival.line'

    wizard_id = fields.Many2one('booking.arrival')
    folio_ids = fields.Many2many('booking.folio')
    booking_ids = fields.Many2many('hotel.booking')
    ref = fields.Char("Booking Name")
    partner_id = fields.Many2one('res.partner', string='Guest')
    check_in = fields.Date("Check In")
    check_out = fields.Date("Check Out")
    room_id = fields.Many2one('hotel.room', string='Room No')
    no_guests = fields.Integer("No Of Guests")
    room_type_id = fields.Many2one('room.type', string='Room Type')
    booking_source = fields.Selection(
        selection=[('online_agent', 'Online Travel Agent'), ('company', 'Company'), ('direct', 'Direct'), ])
    online_travel_agent_source = fields.Many2one('res.partner', domain="[('online_travel_agent', '=', True)]")
    company_booking_source = fields.Many2one('res.partner', domain="[('travel_type', '=', 'company')]")
    total_nights = fields.Integer("Total Nights")
    rate_type = fields.Many2one('hotel.rate.type', "Rate Type")
    subtotal = fields.Float("Subtotal")
    note = fields.Char("Note")
    related_hotel = fields.Many2one('hotel.hotel', string="Hotel")
