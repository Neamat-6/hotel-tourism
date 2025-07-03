from odoo import fields, models, api, _
from datetime import datetime


class AuditTrails(models.TransientModel):
    _name = 'audit.trails.report'
    _description = 'Audit Trails Report'

    line_ids = fields.One2many('audit.trails.report.line', 'wizard_id')
    start_date = fields.Date(string='From', required=True)
    end_date = fields.Date(string='To', required=True)
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
        ('checked_in', 'Checked In'),
        ('checked_out', 'Checked Out'),
        ('cancel_folio', "Cancelled Folio")
    ])
    room_id = fields.Many2one('hotel.room', string='Room No')

    def button_search(self):
        self.line_ids = [(5, 0, 0)]
        domain = []
        if self.start_date:
            start_date = datetime.combine(self.start_date, datetime.strptime('000000', '%H%M%S').time())
            domain.append(('datetime', '>=', start_date))
        if self.end_date:
            end_date = datetime.combine(self.end_date, datetime.strptime('235959', '%H%M%S').time())
            domain.append(('datetime', '<=', end_date))
        if self.user_id:
            domain.append(('user_id', '=', self.user_id.id))
        if self.room_id:
            domain.append(('room_id', '=', self.room_id.id))
        if self.operation:
            domain.append(('operation', '=', self.operation))
        audit_trails = self.env['audit.trails'].sudo().search(domain)
        for audit in audit_trails:
            self.line_ids = [(0, 0, {
                'audit_id': audit.id
            })]

        return {
            'type': 'ir.actions.act_window',
            'name': _('Audit Trails'),
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'audit.trails.report',
            'res_id': self.id,
            'target': 'new'
        }

    def print_pdf(self):
        return self.env.ref('booking_audit_trails.action_audit_trails_report').report_action(self)

    def print_xlsx(self):
        return self.env.ref('booking_audit_trails.action_audit_trails_xlsx_report').report_action(self)


class AuditTrailsReportLine(models.TransientModel):
    _name = 'audit.trails.report.line'
    _description = 'Audit Trails Report Line'

    wizard_id = fields.Many2one('audit.trails.report')
    audit_id = fields.Many2one('audit.trails')
    booking_id = fields.Many2one('hotel.booking', related='audit_id.booking_id')
    booking_line_id = fields.Many2one('hotel.booking.line', related='audit_id.booking_line_id')
    folio_id = fields.Many2one('booking.folio', related='audit_id.folio_id')
    user_id = fields.Many2one('res.users', related='audit_id.user_id')
    operation = fields.Selection(related='audit_id.operation')
    datetime = fields.Datetime(related='audit_id.datetime')
    notes = fields.Text(related='audit_id.notes')
