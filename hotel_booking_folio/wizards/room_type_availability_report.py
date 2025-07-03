from odoo import fields, models, api, _
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError


class RoomTypeAvailabilityReport(models.TransientModel):
    _name = 'room.type.availability.report'
    _description = 'Room Type Availability Report'

    date_from = fields.Date(required=True, string='From')
    date_to = fields.Date(required=True, string='To')
    line_ids = fields.One2many('room.type.availability.report.line', 'wizard_id')

    @api.constrains('date_from', 'date_to')
    def check_dates(self):
        for rec in self:
            if rec.date_to < rec.date_from:
                raise ValidationError(_('To date cannot be earlier than from date!'))

    def button_search(self):
        self.line_ids = [(5, 0, 0)]
        vals = self.prepare_room_type_availability_lines(self.date_from, self.date_to)
        for val in vals:
            new_line = self.line_ids.new(val)
            self.line_ids += new_line
        return {
            'type': 'ir.actions.act_window',
            'name': _('Availability By Room Type'),
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'room.type.availability.report',
            'res_id': self.id,
            'target': 'new'
        }

    def prepare_room_type_availability_lines(self, start, end):
        vals = []
        room_types = self.env['room.type'].search([('company_id', '=', self.env.company.id)])
        while start <= end:
            for room_type in room_types:
                hotel_id = self.env.company.related_hotel_id
                rooms = self.env['hotel.room'].search([('hotel_id', '=', hotel_id.id), ('room_type', '=', room_type.id)])
                total_rooms = len(rooms)
                # Filter out "out of order" rooms during the period
                out_of_order_rooms = self.env['hotel.room'].search([
                    ('id', 'in', rooms.ids),
                    '|',
                    '&', ('out_of_order_from', '<=', end),
                    ('out_of_order_to', '>=', start),
                    '&', ('out_of_order_from', '<=', start),
                    ('out_of_order_to', '>=', end)
                ])

                out_of_order_room_ids = out_of_order_rooms.ids

                booked_rooms = self.get_booked_inventory(room_type, rooms.ids, start)
                available_rooms = int(total_rooms - booked_rooms - len(out_of_order_room_ids))
                # if available_rooms > 1:
                vals.append({
                    'date': start,
                    'room_type_id': room_type.id,
                    'qty_available': available_rooms
                })
            start += relativedelta(days=1)
        return vals

    def get_booked_inventory(self, room_type, rooms, day):
        """
            get booked qty for a specific day
        """
        booked_folios = 0
        if day:
            company = self.env.company
            # arrival
            check_in_folios = self.env['booking.folio'].sudo().search([
                ('state', 'in', ['confirmed', 'draft']), ('company_id', '=', company.id),
                ('check_in', '!=', False), ('check_in_date', '=', day), ('room_type_id', '=', room_type.id)
            ])
            # departure
            check_out_folios = self.env['booking.folio'].sudo().search([
                ('room_id', '!=', False), ('company_id', '=', company.id),
                ('state', '=', 'checked_in'), ('check_in', '!=', False),
                ('check_out_date', '=', day), ('room_id', 'in', rooms), ('room_type_id', '=', room_type.id)
            ])
            exp_check_out_folios = self.env['booking.folio'].sudo().search([
                ('company_id', '=', company.id), ('state', '!=', 'cancelled'),
                ('check_in', '!=', False), ('check_out_date', '=', day), ('room_type_id', '=', room_type.id)
            ])
            exp_inhouse_folios = self.env['booking.folio'].sudo().search([
                ('check_in', '!=', False), ('company_id', '=', company.id), ('state', '!=', 'cancelled'),
                ('room_type_id', '=', room_type.id),
                ('id', 'not in', check_out_folios.ids), ('id', 'not in', exp_check_out_folios.ids),
                ('id', 'not in', check_in_folios.ids)
            ]).filtered(lambda f: f.check_in_date <= day <= f.check_out_date)

            booked_folios = len(check_in_folios) + len(exp_inhouse_folios)
        return booked_folios

    def print_pdf(self):
        return self.env.ref('hotel_booking_folio.action_tb_availability_report').report_action(self)

    def print_xlsx(self):
        return self.env.ref('hotel_booking_folio.action_rt_availability_xlsx_report').report_action(self)


class RoomTypeAvailabilityReportLine(models.TransientModel):
    _name = 'room.type.availability.report.line'
    _description = 'Room Type Availability Report Line'

    wizard_id = fields.Many2one('room.type.availability.report')
    room_type_id = fields.Many2one('room.type')
    qty_available = fields.Integer()
    date = fields.Date()
