from odoo import fields, models, api
import pytz
from datetime import datetime


class Folio(models.Model):
    _inherit = 'booking.folio'

    def write(self, vals):
        self = self.with_context(ignore_updates=True)
        if vals.get('room_id', False) and not self.room_id:
            new_room = self.env['hotel.room'].browse(vals['room_id'])
            self.env['audit.trails'].create({
                'booking_id': self.booking_id.id,
                'folio_id': self.id,
                'user_id': self.env.user.id,
                'operation': 'assign_room',
                'datetime': fields.Datetime.now(),
                'notes': f'Room Type: {new_room.room_type.name} Room: {new_room.name}'
            })
        if vals.get('room_id', False) and self.room_id:
            new_room = self.env['hotel.room'].browse(vals['room_id'])
            self.env['audit.trails'].create({
                'booking_id': self.booking_id.id,
                'folio_id': self.id,
                'user_id': self.env.user.id,
                'operation': 'change_room',
                'datetime': fields.Datetime.now(),
                'notes': f'Old Room Type: {self.room_id.room_type.name} Room: {self.room_id.name}, New Room Type: {new_room.room_type.name} Room: {new_room.name}'
            })
        res = super(Folio, self).write(vals)
        return res

    def button_cancel(self):
        res = super(Folio, self).button_cancel()
        self.env['audit.trails'].create({
            'booking_id': self.booking_id.id,
            'folio_id': self.id,
            'user_id': self.env.user.id,
            'operation': 'cancel_folio',
            'datetime': fields.Datetime.now(),
            'notes': f'Folio {self.name} is Cancelled'
        })
        return res

    def button_check_in(self, book_by_bed=None, bed_partner=None):
        res = super(Folio, self).button_check_in(book_by_bed=book_by_bed, bed_partner=bed_partner)
        self.env['audit.trails'].create({
            'booking_id': self.booking_id.id,
            'folio_id': self.id,
            'user_id': self.env.user.id,
            'operation': 'checked_in',
            'datetime': fields.Datetime.now(),
            'notes': f'{self.name} Checked In Successfully'
        })
        return res

    def button_check_out(self):
        res = super(Folio, self).button_check_out()
        self.env['audit.trails'].create({
            'booking_id': self.booking_id.id,
            'folio_id': self.id,
            'user_id': self.env.user.id,
            'operation': 'checked_out',
            'datetime': fields.Datetime.now(),
            'notes': f'{self.name} Checked Out Successfully'
        })
        return res


class FolioLine(models.Model):
    _inherit = 'booking.folio.line'

    @api.model
    def create(self, vals):
        res = super(FolioLine, self).create(vals)
        if vals.get('payment_id', False):
            self.env['audit.trails'].create({
                'booking_id': res.folio_id.booking_id.id,
                'folio_id': res.folio_id.id,
                'user_id': self.env.user.id,
                'operation': 'add_payment',
                'datetime': fields.Datetime.now(),
            })
        return res

    def action_button_delete(self):
        self.env['audit.trails'].create({
            'booking_id': self.folio_id.booking_id.id,
            'folio_id': self.folio_id.id,
            'user_id': self.env.user.id,
            'operation': 'delete_folio_line',
            'datetime': fields.Datetime.now(),
            'notes': f'Folio Line {self.particulars} is Deleted'
        })
        return super().action_button_delete()
