from odoo import api, fields, models


class ReservationPackage(models.Model):
    _name = 'reservation.package'
    _description = 'Reservation Package'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def get_default_sequence(self):
        return self.env['ir.sequence'].next_by_code('reservation.package.ref')

    name = fields.Char("Name", required=True)
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirm'), ('cancel', 'Cancelled')], default='draft',
                             string='Status')
    ref = fields.Char("Package #", readonly=True)
    package_start_date = fields.Date("Package Start Date", required=True)
    package_end_date = fields.Date("Package End Date", required=True)
    reservation_date = fields.Date("Reservation Date", required=True)
    package_capacity = fields.Integer("Package capacity", required=True)
    hotel_reservation_package_ids = fields.One2many('hotel.reservation.package', 'reservation_package_id')
    plane_reservation_package_ids = fields.One2many('plane.reservation.package', 'reservation_package_id')
    bus_reservation_package_ids = fields.One2many('bus.reservation.package', 'reservation_package_id')

    @api.model
    def create(self, vals):
        res = super(ReservationPackage, self).create(vals)
        for reservation in res:
            reservation.ref = self.get_default_sequence()
        return res

    def action_confirm(self):
        self.state = 'confirm'

    def action_cancel(self):
        self.state = 'cancel'

    def action_draft(self):
        self.state = 'draft'
