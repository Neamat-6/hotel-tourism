from odoo import fields, models, api
from odoo.exceptions import ValidationError


class UpdateRoomStatus(models.TransientModel):
    _name = 'update.room.status'
    _description = 'Update Room Status Wizard'

    update_type = fields.Selection(selection=[
        ('housekeeping', 'housekeeping'),
        ('housekeeper', 'housekeeper'),
        ('stayover', 'stayover'),
        ('ooo', 'Out of Order'),
    ])
    room_ids = fields.Many2many('hotel.room')
    state = fields.Many2one('hotel.room.status', string='Housekeeping Status')
    stay_state = fields.Many2one('hotel.room.stay.status', string='Stayover Status')
    housekeeper = fields.Many2one('hr.employee')
    date_from = fields.Date()
    date_to = fields.Date()
    ooo_reason_id = fields.Many2one('out.of.order.reason', string='Out of Order Reason')
    release_room = fields.Boolean()

    @api.constrains('date_from', 'date_to')
    def check_dates(self):
        for rec in self:
            if rec.date_from and rec.date_to:
                if rec.date_from > rec.date_to:
                    raise ValidationError('Date from must be before Date to!')

    def update_state(self):
        if self.update_type == 'housekeeping':
            for room in self.room_ids:
                room.write({'state': self.state.id})
        elif self.update_type == 'stayover':
            for room in self.room_ids:
                room.write({'state': self.stay_state.id})
        elif self.update_type == 'housekeeper':
            for room in self.room_ids:
                room.write({'housekeeper': self.housekeeper.id})
        elif self.update_type == 'ooo' and not self.release_room:
            for room in self.room_ids:
                if self.date_from < room.company_id.audit_date:
                    raise ValidationError("you can't add date in past!")
                room.write({
                    'out_of_order_from': self.date_from,
                    'out_of_order_to': self.date_to,
                    'out_of_order_reason': self.ooo_reason_id.id,
                })
                if self.date_from == room.company_id.audit_date:
                    room.write({
                        'stay_state': self.env.ref('hotel_booking.data_hotel_room_stay_status_ooo').id,
                    })
        elif self.update_type == 'ooo' and self.release_room:
            for room in self.room_ids:
                if self.date_from < room.company_id.audit_date:
                    raise ValidationError("you can't add date in past!")
                room.write({
                    'out_of_order_from': False,
                    'out_of_order_to': False,
                    'out_of_order_reason': False,
                })
                room.write({
                    'stay_state': self.env.ref('hotel_booking.hotel_room_stay_status_vacant').id,
                    'state': self.env.ref('hotel_booking.hotel_room_status_dirty').id,
                })
