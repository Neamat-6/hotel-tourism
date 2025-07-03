from odoo import fields, models, api


class HousekeepingDiff(models.TransientModel):
    _name = 'housekeeping.diff'
    _description = 'Housekeeping Diff'

    room_ids = fields.Many2many('hotel.room')

    @api.model
    def default_get(self, fields):
        res = super(HousekeepingDiff, self).default_get(fields)
        rooms = self.env['hotel.room'].search([('stay_state_diff', '=', True)]).ids
        if rooms:
            res['room_ids'] = rooms
        return res

    def print_report(self):
        return self.env.ref('hotel_booking.housekeeping_diff_report_action').report_action(self)
