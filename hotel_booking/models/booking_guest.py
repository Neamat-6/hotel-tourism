from odoo import fields, models, api


class BookingGuest(models.Model):
    _name = 'booking.guest'
    _description = 'Booking Guest'

    booking_id = fields.Many2one('hotel.booking', ondelete='cascade')
    partner_id = fields.Many2one('res.partner')
    guest_title = fields.Selection(selection=[
        ('dr', 'Dr.'), ('jn', 'Jn.'), ('mam', 'Mam.'), ('mr', 'Mr.'),
        ('mrs', 'Mrs.'), ('ms', 'Ms.'), ('sir', 'Sir'), ('sr', 'Sr.'),
    ], default='mr', required=True)
    guest_name = fields.Char(required=True)
    guest_mobile = fields.Char(string='Mobile')
    guest_email = fields.Char(string='Email')
    guest_address = fields.Char(string='Address')
    guest_country_id = fields.Many2one('res.country', string='Country')
    guest_state_id = fields.Many2one('res.country.state', string='State')
    guest_city = fields.Char(string='City')
    guest_zip_code = fields.Char(string='Zip')
