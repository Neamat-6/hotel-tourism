import json

from odoo import fields, models, api, _


class HotelServices(models.TransientModel):
    _name = 'hotel.service'
    _description = 'Hotel Service'

    line_ids = fields.One2many('hotel.service.line', 'wizard_id')
    date_from = fields.Date("Date From", required=True)
    date_to = fields.Date("Date To", required=True)
    hotel_services_id = fields.Many2one('hotel.services')
    no_lines = fields.Integer("No. Lines", compute='calc_no_lines')
    print_amount = fields.Boolean("Print Amount")
    total = fields.Float(compute='calc_total', digits=(16, 2))
    company_ids = fields.Many2many('res.company', string='Companies')
    hotel_ids = fields.Many2many('hotel.hotel', string='Hotels')
    room_id = fields.Many2one('hotel.room', "Room No")
    summary_data = fields.Text('Summary Data', readonly=True)

    def calc_no_lines(self):
        if self.line_ids:
            self.no_lines = len(self.line_ids)
        else:
            self.no_lines = 0.0

    @api.onchange('line_ids')
    def calc_total(self):
        if self.line_ids:
            self.total = sum(self.line_ids.mapped('amount'))
        else:
            self.total = 0.0

    def get_booking_folios(self):
        self.line_ids = [(5, 0, 0)]
        domain = []
        date_from = self.date_from
        hotel_services_id = self.hotel_services_id
        domain.append(('state', 'not in', ['cancelled']))
        if self.hotel_ids:
            domain.append(('hotel_id', 'in', self.hotel_ids.ids))
        if self.company_ids:
            domain.append(('company_id', 'in', self.company_ids.ids))
        if date_from:
            domain.append(('day', '>=', date_from))
        if self.date_to:
            domain.append(('day', '<=', self.date_to))
        if hotel_services_id:
            domain.append(('particulars', '=', hotel_services_id.name))
        if self.room_id:
            domain.append(('room_id', '=', self.room_id.id))
        folio_lines = self.env['booking.folio.line'].search(domain)

        summary_data = {}
        for folio in folio_lines:
            particular = folio.particulars
            if particular not in summary_data:
                summary_data[particular] = folio.amount
            else:
                summary_data[particular] += folio.amount

        summary_list = [(particular, total_amount) for particular, total_amount in summary_data.items()]
        self.summary_data = json.dumps(summary_list)

        for folio in folio_lines:
            day = folio.mapped('day')[0]
            particular = folio.mapped('particulars')[0]
            description = folio.mapped('description')[0]
            room = (folio.mapped('room_id')).id
            created_by = (folio.mapped('create_uid')).id
            booking_id = (folio.mapped('booking_id')).id
            amount = sum(folio.mapped('amount'))
            if folio:
                self.env['hotel.service.line'].create({
                    'wizard_id': self.id,
                    'day': day,
                    'particular': particular,
                    'description': description,
                    'created_by': created_by,
                    'booking_id': booking_id,
                    'room_id': room,
                    'amount': amount,
                })
        return {
            'type': 'ir.actions.act_window',
            'name': _('Hotel Services'),
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'hotel.service',
            'res_id': self.id,
            'target': 'new'
        }

    def print_pdf(self):
        return self.env.ref('hotel_booking.action_hotel_service_report').with_context(
            landscape=True).report_action(self)

    def print_xlsx(self):
        return self.env.ref('hotel_booking.action_service_xlsx_report').report_action(self)


class ActualCheckinLine(models.TransientModel):
    _name = 'hotel.service.line'

    wizard_id = fields.Many2one('hotel.service')
    particular = fields.Char("Particular")
    description = fields.Char("Description")
    created_by = fields.Many2one('res.partner', string='Created By')
    room_id = fields.Many2one('hotel.room', "Room No")
    day = fields.Date("Day")
    amount = fields.Float("Amount")
    booking_id = fields.Many2one('hotel.booking')
