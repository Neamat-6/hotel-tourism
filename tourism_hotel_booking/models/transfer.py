# -*- coding: utf-8 -*-
from odoo import api, fields, models


class HotelTransfer(models.Model):
    _name = 'tourism.hotel.transfer'
    _description = 'Tourism Hotel Transfer'

    name = fields.Char(compute="_compute_name")
    state = fields.Selection([('draft', 'Draft'), ('done', 'Done')], default="draft", string="Status")
    room_id = fields.Many2one('tourism.hotel.room', required=True)
    type = fields.Selection([('in', 'Check In'), ('out', 'Check Out')], string='Type', required=True)
    transfer_time = fields.Datetime(default=fields.Datetime.now, string="Time")
    booking_line_id = fields.Many2one('tourism.hotel.booking.line', string="Booking #", required=True)
    booking_id = fields.Many2one('tourism.hotel.booking', string="Booking #", readonly=True, related="booking_line_id.booking_id")

    @api.onchange('booking_line_id', 'type')
    def onchange_type_and_booking(self):
        available_rooms = []

        if self.type == "in" and self.booking_line_id:
            room_ids = self.env['tourism.hotel.room'].search([('room_type_id', '=', self.booking_line_id.room_type_id.id), ('booking_line_id', '=', False)])
            available_rooms += room_ids.ids

        if self.type == "out" and self.booking_line_id:
            room_ids = self.env['tourism.hotel.room'].search([('room_type_id', '=', self.booking_line_id.room_type_id.id), ('booking_line_id', '!=', False)])
            available_rooms += room_ids.ids

        return {
            'domain': {
                'room_id': [('id', 'in', available_rooms)]
            }
        }


    def _compute_name(self):
        for transfer in self:
            transfer.name = "%s/%s" % (transfer.room_id.name, transfer.type.upper())

    def action_validate(self):
        self.ensure_one()

        if self.type == "in":
            if self.booking_id.state == "draft":
                self.booking_line_id.write({'room_id': self.room_id.id})
                self.booking_id.button_confirm()

            self.room_id.write({'booking_line_id': self.booking_line_id.id})
            self.booking_line_id.write({'check_in_out_state': 'checked_in'})

        elif self.type == "out":
            self.room_id.write({'booking_line_id': False})
            self.booking_line_id.write({'check_in_out_state': 'checked_out'})

        else:
            raise NotImplementedError

        self.state = "done"


