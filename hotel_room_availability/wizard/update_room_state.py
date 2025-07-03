from odoo import fields, models, api, _
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError, RedirectWarning, UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class UpdateRoomState(models.TransientModel):
    _name = 'hotel.room.status.update'
    _description = 'Update Room State'

    def _default_date_to(self):
        return str(datetime.today() + relativedelta(days=1))

    room_availability_id = fields.Many2one('room.availability', required=True)
    line_ids = fields.One2many('hotel.room.status.update.line', 'wizard_id')
    hotel_id = fields.Many2one('hotel.hotel')
    date_from = fields.Date(default=str(datetime.today()), required=True)
    date_to = fields.Date(default=_default_date_to, required=True)

    @api.constrains('date_from', 'date_to')
    def check_start_end_date(self):
        if self.date_to and self.date_from:
            if self.date_to < self.date_from:
                raise ValidationError(_('End Date should be greater than Start Date.'))

    @api.model
    def default_get(self, fields):
        res = super(UpdateRoomState, self).default_get(fields)
        if self.env.context.get('active_id') and \
                self.env.context.get('active_model') == 'room.availability' and \
                self.env.context.get('active_id'):
            res['room_availability_id'] = self.env[
                'room.availability'].browse(self.env.context['active_id']).id
        return res

    def update_room_state(self):
        availability_line_obj = self.env['room.type.availability.line']
        for rec in self:
            period_list = []
            date_to = datetime.strptime(
                str(rec.date_to), DEFAULT_SERVER_DATE_FORMAT)
            date_from = datetime.strptime(
                str(rec.date_from), DEFAULT_SERVER_DATE_FORMAT)
            days_between = (date_to - date_from).days
            date_list = [(date_from + timedelta(days=i))
                         for i in range(0, days_between + 1)]
            for line in rec.line_ids:
                for i in date_list:
                    line_rec = availability_line_obj.search([
                        ('date', '=', i.date()),
                        ('room_id', '=', line.hotel_room_id.id),
                        ('room_availability_id', '=',rec.room_availability_id.id)
                    ])
                    if line_rec:
                        line_rec.write({'state': line.state.id})
        return {'type': 'ir.actions.act_window_close'}


class UpdateRoomPricelistLine(models.TransientModel):
    _name = "hotel.room.status.update.line"
    _description = 'Update Room State Line'

    wizard_id = fields.Many2one('hotel.room.status.update')
    hotel_id = fields.Many2one('hotel.hotel', related='wizard_id.hotel_id', store=True)
    hotel_room_id = fields.Many2one('hotel.room', 'Room')
    state = fields.Many2one('hotel.room.status')