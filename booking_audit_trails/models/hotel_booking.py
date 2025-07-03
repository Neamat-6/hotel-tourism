from odoo import fields, models, api
from hijri_converter import convert
import pytz
from datetime import datetime


class Booking(models.Model):
    _inherit = 'hotel.booking'

    audit_trails = fields.One2many('audit.trails', 'booking_id')

    def get_invoice_issue_date(self):
        trail = self.audit_trails.filtered(lambda t: t.operation == 'checked_out')
        if trail:
            invoice_issue_date = trail.datetime
            timezone = pytz.timezone(self.env.user.tz or 'UTC')
            invoice_issue_date = pytz.utc.localize(invoice_issue_date).astimezone(timezone)
            return invoice_issue_date
        return self.check_out

    def get_invoice_issue_date_formatted(self):
        return self.get_invoice_issue_date().strftime('%Y-%m-%d %H:%M')

    def get_invoice_issue_date_hijri(self):
        invoice_issue_date = self.get_invoice_issue_date()
        hijri_date = convert.Gregorian(invoice_issue_date.year, invoice_issue_date.month, invoice_issue_date.day).to_hijri()
        return str(hijri_date)

    @api.model
    def create(self, vals):
        res = super(Booking, self).create(vals)
        self.env['audit.trails'].create({
            'booking_id': res.id,
            'user_id': self.env.user.id,
            'operation': 'add_booking',
            'datetime': fields.Datetime.now()
        })
        return res

    def write(self, vals):
        if self.booking_source and vals.get('booking_source', False):
            old_booking_source = self.booking_source
            new_booking_source = vals['booking_source']
            self.env['audit.trails'].create({
                'booking_id': self.id,
                'user_id': self.env.user.id,
                'operation': 'update_source',
                'datetime': fields.Datetime.now(),
                'notes': f'Old Source: {old_booking_source}, New Source: {new_booking_source}'
            })
        res = super(Booking, self).write(vals)
        return res
