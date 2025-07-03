# models/activity_activity.py

from odoo import models, fields

class BookingPackageActivityLine(models.Model):
    _name = 'booking.package.activity.line'
    _description = 'Booking Package Activity Line'
    _rec_name = 'date'

    name = fields.Char()
    date = fields.Date(required=True)
    from_time = fields.Float(string="From Time")
    to_time = fields.Float(string="To Time")
    image = fields.Binary(string="Image")
    package_id = fields.Many2one('booking.package', required=True, ondelete='cascade')
    location = fields.Selection([
        ('makkah', 'Makkah'),
        ('madina', 'Madina'),
        ('arfa', 'Arafat'),
        ('minah', 'Minah'),
        ('hotel', 'Hotel')
    ], required=True)
