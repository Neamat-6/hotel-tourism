from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta


class RoomStatus(models.TransientModel):
    _name = 'room.status'
    _description = 'Room Status'

    line_ids = fields.One2many('room.status.line', 'wizard_id')
    stay_state = fields.Many2many('hotel.room.stay.status', string='Stayover Status')
    state = fields.Many2many('hotel.room.status', string='HouseKeeping Status')

    def get_room_status(self):
        self.line_ids = [(5, 0, 0)]
        domain = []
        stay_state = self.stay_state
        state = self.state
        if stay_state:
            domain.append(('stay_state', 'in', stay_state.ids))
        if state:
            domain.append(('state', 'in', state.ids))
        room_lines = self.env['hotel.room'].search(domain)
        for line in room_lines:
            name = line.mapped('name')[0]
            housekeeper = (line.mapped('housekeeper')).id
            out_of_order_from = line.mapped('out_of_order_from')[0]
            out_of_order_to = line.mapped('out_of_order_to')[0]
            out_of_order_reason = (line.mapped('out_of_order_reason')).id
            room_type = (line.mapped('room_type')).id
            booking_id = (line.mapped('booking_id')).id
            stay_state = (line.mapped('stay_state')).id
            state = (line.mapped('state')).id
            if line:
                self.env['room.status.line'].create({
                    'wizard_id': self.id,
                    'name': name,
                    'housekeeper': housekeeper,
                    'out_of_order_from': out_of_order_from,
                    'out_of_order_to': out_of_order_to,
                    'out_of_order_reason': out_of_order_reason,
                    'room_type': room_type,
                    'booking_id': booking_id,
                    'stay_state': stay_state,
                    'state': state,
                })
        return {
            'type': 'ir.actions.act_window',
            'name': _('Room Status'),
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'room.status',
            'res_id': self.id,
            'target': 'new'
        }

    def print_pdf(self):
        return self.env.ref('hotel_booking.action_room_status_report').with_context(
            landscape=True).report_action(self)


class RoomStatusLine(models.TransientModel):
    _name = 'room.status.line'

    wizard_id = fields.Many2one('room.status')
    name = fields.Char(string="Name", required=False)
    room_type = fields.Many2one('room.type', string='Type')
    state = fields.Many2one('hotel.room.status', string='Housekeeping Status')
    stay_state = fields.Many2one('hotel.room.stay.status', string='Stayover Status')
    housekeeper = fields.Many2one('hr.employee')
    out_of_order_from = fields.Date()
    out_of_order_to = fields.Date()
    out_of_order_reason = fields.Many2one('out.of.order.reason')
    business_source_id = fields.Many2one('business.source', related='booking_id.business_source_id', store=True)
    booking_partner_id = fields.Many2one("res.partner", related='booking_id.partner_id', store=True)
    booking_id = fields.Many2one('hotel.booking')
