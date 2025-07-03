# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import date, datetime
import json
import pytz


class HotelRoom(models.Model):
    _name = 'hotel.room'
    _description = 'Hotel Room'

    product_id = fields.Many2one('product.product', 'Product_id',
                                 required=True, delegate=True,
                                 ondelete="cascade")
    room_type = fields.Many2one('room.type', string='Type Room')
    floor_id = fields.Many2one('hotel.floor')
    room_c = fields.Float('Room Count')
    hotel_id = fields.Many2one('hotel.hotel')
    sequence = fields.Integer('Sequence', default=10)
    booking_ok = fields.Boolean('Can be booked', default=True)
    room_type_id = fields.Many2one('hotel.room.type', string='Room Type')
    facility_line_ids = fields.Many2many('hotel.room.facility', 'room_id')
    telephone_extension = fields.Char(string='Telephone Ext.')
    image_ids = fields.One2many('hotel.room.image', 'room_id')
    booking_line_id = fields.Many2one('hotel.booking.line')
    room_size = fields.Char(string="Room Size")
    note = fields.Text()

    room_vvv = fields.Float('Room avalible after booking')
    price = fields.Float('price', default=1.0)
    state = fields.Many2one('hotel.room.status', string='Housekeeping Status', required=True)
    state_selection = fields.Selection(related='state.state', store=True, help='used in booking lines colors')
    stay_state = fields.Many2one('hotel.room.stay.status', string='Stayover Status', required=True, store=True)
    housekeeping_stay_state = fields.Many2one('hotel.room.stay.status', string='Housekeeping Stayover Status')
    stay_state_diff = fields.Boolean(compute='compute_stay_state_diff', store=True)
    housekeeper = fields.Many2one('hr.employee', domain=[('is_housekeeper', '=', True)])
    image_128 = fields.Image("Image 128", related='housekeeper.image_128', compute_sudo=True)
    avatar_128 = fields.Image("Avatar 128", related='housekeeper.avatar_128', compute_sudo=True)
    out_of_order_from = fields.Date()
    out_of_order_to = fields.Date()
    room_stay_status_id = fields.Many2one("hotel.room.stay.status", string='Room Stayover Status')
    out_of_order_reason = fields.Many2one('out.of.order.reason')
    bed_type = fields.Many2one('hotel.room.type')
    company_id = fields.Many2one('res.company', related='hotel_id.company_id', store=True)
    # kanban fields
    booking_id = fields.Many2one('hotel.booking', compute='compute_booking_id', store=True)
    booking_date = fields.Datetime(compute='compute_booking_id')
    hotel_booking_date = fields.Date(related='booking_id.new_check_in', store=True)
    hotel_booking_date_out = fields.Date(related='booking_id.new_check_out', store=True)
    booking_guest_name = fields.Char(compute='compute_booking_id')
    booking_checkin = fields.Datetime(compute='compute_booking_id')
    booking_checkout = fields.Datetime(compute='compute_booking_id')
    booking_total_nights = fields.Integer(compute='compute_booking_id')
    booking_paid_amount = fields.Float(compute='compute_booking_id')
    booking_total_amount = fields.Float(compute='compute_booking_id')
    booking_due_amount = fields.Float(compute='compute_booking_id')
    booking_partner_id = fields.Many2one("res.partner", related='booking_id.partner_id', store=True)
    business_source_id = fields.Many2one('business.source', related='booking_id.business_source_id', store=True)
    number_of_guests = fields.Integer()
    housekeeping_number_of_guests = fields.Integer()

    def toggle_active(self):
        if not self.env.user.has_group('hotel_booking.group_archive_room'):
            raise UserError("You do not have permission to archive/unarchive Rooms.")
        return super().toggle_active()

    @api.depends('stay_state', 'housekeeping_stay_state', 'number_of_guests', 'housekeeping_number_of_guests')
    def compute_stay_state_diff(self):
        for rec in self:
            rec.stay_state_diff = False
            if rec.stay_state and rec.housekeeping_stay_state:
                if rec.stay_state.id != rec.housekeeping_stay_state.id:
                    rec.stay_state_diff = True
            elif rec.number_of_guests and rec.housekeeping_number_of_guests:
                if rec.number_of_guests != rec.housekeeping_number_of_guests:
                    rec.stay_state_diff = True

    def button_create_work_orders(self):
        return {
            'type': 'ir.actions.act_window',
            'name': "Work Orders",
            'res_model': 'hotel.work.order',
            'view_mode': 'form',
            'target': 'current',
        }

    def button_out_of_order(self):
        out_of_order = self.env.ref('hotel_booking.out_of_order_action').read()[0]
        return out_of_order

    def action_open_pending_orders(self):
        pending_work_order = self.env.ref('hotel_booking.pending_hotel_work_order_action').read()[0]
        return pending_work_order

    def action_open_complete_orders(self):
        complete_work_order = self.env.ref('hotel_booking.complete_hotel_work_order_action').read()[0]
        return complete_work_order

    def action_view_reservations(self):
        if self.booking_id:
            return {
                'name': _('Reservations'),
                'type': 'ir.actions.act_window',
                'view_mode': 'tree,form',
                'view_type': 'form',
                'res_model': 'hotel.booking',
                'domain': [('id', '=', self.booking_id.id)],
                'target': 'current',
            }
        else:
            return {
                'name': _('Reservations'),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'view_type': 'form',
                'res_model': 'hotel.booking',
                'target': 'current',
            }

    def compute_booking_id(self):
        for rec in self:
            rec.booking_id = False
            rec.booking_date = False
            rec.booking_guest_name = False
            rec.booking_checkin = False
            rec.booking_checkout = False
            rec.booking_total_nights = False
            rec.booking_total_amount = False
            rec.booking_paid_amount = False
            rec.booking_due_amount = False

            if rec.hotel_id:
                timezone = pytz.timezone(self.env.user.tz or 'UTC')
                audit_date = self.env.company.audit_date
                booked_line = self.env['hotel.booking.line'].search([
                    '|', ('room_id', '=', rec.id), ('room_ids', 'in', rec.ids)
                ]).filtered(
                    lambda l: pytz.utc.localize(l.check_in).astimezone(
                        timezone).date() <= audit_date <= pytz.utc.localize(l.check_out).astimezone(
                        timezone).date() and l.booking_state in ['checked_in', 'paid', 'confirmed']
                )
                if booked_line:
                    booked_line = booked_line[0]
                    rec.booking_id = booked_line.booking_id.id
                    rec.booking_date = rec.booking_id.create_date
                    rec.booking_guest_name = rec.booking_id.guest_name
                    rec.booking_checkin = rec.booking_id.check_in
                    rec.booking_checkout = rec.booking_id.check_out
                    rec.booking_total_nights = rec.booking_id.total_nights
                    rec.booking_total_amount = rec.booking_id.move_id.amount_total
                    rec.booking_paid_amount = rec.booking_id.amount_paid
                    rec.booking_due_amount = rec.booking_total_amount - rec.booking_paid_amount

    @api.constrains('out_of_order_from', 'out_of_order_to')
    def check_out_of_order_dates(self):
        for rec in self:
            if rec.out_of_order_from and rec.out_of_order_to:
                if rec.out_of_order_from > rec.out_of_order_to:
                    raise ValidationError('Date from must be before Date to!')

    @api.model
    def get_room_data(self, hotel):
        datas = []
        hotel_id = self.env['hotel.hotel'].browse(hotel)
        company_id = self.env['res.company'].search([('related_hotel_id', '=', hotel)])
        room_types = self.env['room.type'].search([('company_id', '=', company_id.id)])
        for room_type in room_types:
            vals = {
                'id': room_type.id,
                'name': room_type.name,
                'hotel_id': [hotel_id.id, hotel_id.name],
                'plan_ids': [[plan.id, plan.name, plan.rock_rate] for plan in room_type.rate_plan_ids]
            }
            datas.append(vals)
        return datas

    @api.model
    def cron_out_of_order(self):
        rooms = self.env['hotel.room'].sudo().search([
            ('out_of_order_from', '!=', False), ('out_of_order_to', '!=', False)
        ])
        ooo = self.env.ref('hotel_booking.data_hotel_room_stay_status_ooo')
        if rooms:
            out_of_order_rooms = rooms.filtered(lambda r: r.out_of_order_from == r.company_id.audit_date)
            for room in out_of_order_rooms:
                room.write({
                    'stay_state': ooo.id,
                })
            vacant_rooms = rooms.filtered(lambda r: r.out_of_order_to < r.company_id.audit_date and r.stay_state.id == ooo.id)
            for room in vacant_rooms:
                room.write({
                    'out_of_order_from': False,
                    'out_of_order_to': False,
                    'out_of_order_reason': False,
                    'stay_state': self.env.ref('hotel_booking.hotel_room_stay_status_vacant').id,
                    'state': self.env.ref('hotel_booking.hotel_room_status_dirty').id,
                })

    def update_housekeeping_status(self):
        rooms = self.env['hotel.room'].browse(self.env.context.get('active_ids', []))
        return {
            'type': 'ir.actions.act_window',
            'name': _("Update Room Status"),
            'res_model': 'update.room.status',
            'view_mode': 'form',
            'context': {
                'default_update_type': 'housekeeping',
                'default_room_ids': rooms.ids
            },
            'target': 'new',
        }

    def update_housekeeper(self):
        rooms = self.env['hotel.room'].browse(self.env.context.get('active_ids', []))
        return {
            'type': 'ir.actions.act_window',
            'name': _("Update Housekeeper"),
            'res_model': 'update.room.status',
            'view_mode': 'form',
            'context': {
                'default_update_type': 'housekeeper',
                'default_room_ids': rooms.ids
            },
            'target': 'new',
        }

    def update_out_of_order(self):
        rooms = self.env['hotel.room'].browse(self.env.context.get('active_ids', []))
        return {
            'type': 'ir.actions.act_window',
            'name': _("Update Out of Order"),
            'res_model': 'update.room.status',
            'view_mode': 'form',
            'context': {
                'default_update_type': 'ooo',
                'default_room_ids': rooms.ids
            },
            'target': 'new',
        }

    @api.model
    def default_get(self, fields):
        res = super(HotelRoom, self).default_get(fields)
        default_state = self.env['hotel.room.status'].search([('is_default', '=', True)], limit=1)
        if default_state:
            res['state'] = default_state.id
        default_stay_state = self.env['hotel.room.stay.status'].search([('is_default', '=', True)], limit=1)
        if default_stay_state:
            res['stay_state'] = default_stay_state.id
        return res

    @api.model
    def create(self, vals):
        if vals.get('name', False) and vals.get('hotel_id', False):
            rooms = self.env['hotel.room'].search([('name', '=', vals['name']), ('hotel_id', '=', vals['hotel_id'])])
            if rooms:
                raise ValidationError("There is already room with the same name!")
        res = super(HotelRoom, self).create(vals)
        return res



class HotelRoomFacility(models.Model):
    _name = 'hotel.room.facility'
    _description = 'Hotel Room Facility'

    facility_id = fields.Char(string="Facility", required=True)
    description = fields.Text(string="Description")
    qty = fields.Integer(default=1)
    image = fields.Binary(string="Image")


class HotelRoomImage(models.Model):
    _name = 'hotel.room.image'
    _description = 'Hotel Room Image'

    room_id = fields.Many2one('hotel.room')
    image = fields.Binary(string='Image', required=True)
    name = fields.Char(string="Description")
