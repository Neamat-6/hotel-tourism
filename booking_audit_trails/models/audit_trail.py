from odoo import fields, models, api


class AuditTrails(models.Model):
    _name = 'audit.trails'
    _description = 'Audit Trails'

    booking_id = fields.Many2one('hotel.booking')
    booking_line_id = fields.Many2one('hotel.booking.line')
    folio_id = fields.Many2one('booking.folio')
    room_id = fields.Many2one('hotel.room')
    user_id = fields.Many2one('res.users')
    operation = fields.Selection(selection=[
        ('add_booking', 'Add Booking'),
        ('change_room', 'Change Room'),
        ('amend_stay', 'Amend Stay'),
        ('change_price', 'Change Price'),
        ('assign_room', 'Assign Room'),
        ('add_payment', 'Add Payment'),
        ('update_payment', 'Update Payment'),
        ('update_source', 'Update Source'),
        ('update_room_state', 'Update Room Status'),
        ('update_room_stay_state', 'Update Room Stay Status'),
        ('update_room_type', 'Update Room Type'),
        ('update_room_floor', 'Update Room Floor'),
        ('checked_in', 'Checked In'),
        ('checked_out', 'Checked Out'),
        ('cancel_folio', "Cancelled Folio"),
        ('update_audit_date', 'Update Audit Date'),
        ('delete_folio_line', 'Delete Folio Line'),
        ('add_service', 'Add Service'),
        ('manual_charge', 'Add Manual Charge'),
    ])
    datetime = fields.Datetime()
    notes = fields.Text(string='Particulars')
