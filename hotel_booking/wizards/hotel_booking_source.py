from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta


class HotelBookingSource(models.TransientModel):
    _name = 'hotel.booking.source'
    _description = 'Booking Source'

    line_ids = fields.One2many('hotel.booking.source.line', 'wizard_id')
    booking_source = fields.Selection(selection=[('online_agent', 'Online Travel Agent'),
                                                 ('company', 'Company'), ('direct', 'Direct'), ], required=True)
    online_travel_agent_source = fields.Many2one('res.partner', domain="[('online_travel_agent', '=', True)]")
    company_booking_source = fields.Many2one('res.partner', domain="[('is_company','=',True)]")

    check_in_from = fields.Date(string='Check In From', required=True)
    check_in_to = fields.Date(string='Check In To', required=True)
    check_out_from = fields.Date(string='Check Out From', required=True)
    check_out_to = fields.Date(string='Check Out To', required=True)

    date_from = fields.Date("Date From")
    date_to = fields.Date("Date to")
    room_id = fields.Many2one('hotel.room', "Room No")
    related_hotel = fields.Many2many('hotel.hotel', string='Related Hotel')
    total_amount = fields.Float(compute="calc_total_amount", digits=(16, 2))

    def calc_total_amount(self):
        for rec in self:
            if rec.line_ids:
                rec.total_amount = sum(rec.line_ids.mapped('subtotal'))
            else:
                rec.total_amount = 0.0

    def get_booking_source_folios(self):
        self.line_ids = [(5, 0, 0)]
        domain = []

        check_in_from = self.check_in_from
        check_in_to = self.check_in_to
        check_out_from = self.check_out_from
        check_out_to = self.check_out_to

        booking_source = self.booking_source
        online_travel_agent_source = self.online_travel_agent_source
        company_booking_source = self.company_booking_source

        if check_in_from:
            domain.append(('check_in', '>=', check_in_from))
        if check_in_to:
            domain.append(('check_in', '<=', check_in_to))

        if check_out_from:
            domain.append(('check_out', '>=', check_out_from))
        if check_out_to:
            domain.append(('check_out', '<=', check_out_to))

        # if self.date_from:
        #     domain.append(('check_in', '>=', self.date_from))
        # if self.date_to:
        #     domain.append(('check_out', '<=', self.date_to))

        if booking_source:
            domain.append(('booking_source', '=', self.booking_source))
        if online_travel_agent_source:
            domain.append(('online_travel_agent_source', '=', self.online_travel_agent_source.id))
        if company_booking_source:
            domain.append(('company_booking_source', '=', self.company_booking_source.id))
        if self.related_hotel:
            domain.append(('hotel_id', 'in', self.related_hotel.ids))

        booking_folio = self.env['booking.folio'].search(domain)

        for line in booking_folio:
            ref = line['booking_name']
            partner_id = line.booking_id.mapped('partner_id').id
            check_in = line.mapped('check_in')[0]
            check_out = line.mapped('check_out')[0]
            room_no = sum(line.mapped('price_total'))
            total_nights = sum(line.mapped('total_nights'))
            no_guests = sum(line.mapped('number_of_guests'))
            room_type_id = (line.mapped('room_type_id')).id
            room = (line.mapped('room_id')).id
            booking_source = line['booking_source']
            online_travel_agent_source = (line.mapped('online_travel_agent_source')).id
            company_booking_source = (line.mapped('company_booking_source')).id
            subtotal = sum(line.mapped('price_total'))
            related_hotel = (line.mapped('hotel_id')).id
            total_paid = sum(line.mapped('price_paid'))
            note = line.mapped('booking_note')[0]
            if line:
                self.env['hotel.booking.source.line'].create({
                    'wizard_id': self.id,
                    'ref': ref,
                    'partner_id': partner_id,
                    'check_in': check_in,
                    'check_out': check_out,
                    'room_no': room_no,
                    'no_guests': no_guests,
                    'room_type_id': room_type_id,
                    'room_id': room,
                    'booking_source': booking_source,
                    'online_travel_agent_source': online_travel_agent_source,
                    'company_booking_source': company_booking_source,
                    'total_nights': total_nights,
                    'subtotal': subtotal,
                    'total_paid': total_paid,
                    'related_hotel': related_hotel,
                    'note': note,
                })
        return {
            'type': 'ir.actions.act_window',
            'name': _('Booking Source Report'),
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'hotel.booking.source',
            'res_id': self.id,
            'target': 'new'
        }

    def print_pdf(self):
        return self.env.ref('hotel_booking.action_booking_source_report').with_context(
            landscape=True).report_action(self)


class HotelBookingSourceLine(models.TransientModel):
    _name = 'hotel.booking.source.line'

    wizard_id = fields.Many2one('hotel.booking.source')
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
    company_booking_source = fields.Many2one('res.partner', domain="[('is_company','=',True)]")
    total_nights = fields.Integer("Total Nights")
    rate_type = fields.Many2one('hotel.rate.type', "Rate Type")
    subtotal = fields.Float("Subtotal")
    total_paid = fields.Float("Total Paid")
    note = fields.Char("Note")
    room_id = fields.Many2one('hotel.room', "Room No")
    related_hotel = fields.Many2one('hotel.hotel', string="Hotel")
