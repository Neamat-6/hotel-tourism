from odoo import fields, models, api, _
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError, RedirectWarning, UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class UpdateRatePlan(models.TransientModel):
    _name = 'hotel.rate.plan.update'
    _description = 'Update Rate Plan'

    def _default_date_to(self):
        return str(datetime.today() + relativedelta(days=1))

    room_availability_id = fields.Many2one('room.availability', required=True)
    hotel_id = fields.Many2one('hotel.hotel')
    date_from = fields.Date(default=str(datetime.today()), required=True)
    date_to = fields.Date(default=_default_date_to, required=True)
    room_type_id = fields.Many2one('room.type')
    rate_plan_id = fields.Many2one('hotel.rate.plan')
    base_rate = fields.Float()
    extra_adult = fields.Integer()
    extra_child = fields.Integer()

    @api.constrains('date_from', 'date_to')
    def check_start_end_date(self):
        if self.date_to and self.date_from:
            if self.date_to < self.date_from:
                raise ValidationError(_('End Date should be greater than Start Date.'))

    @api.model
    def default_get(self, fields):
        """To get the default prices in the pricelist."""
        res = super(UpdateRatePlan, self).default_get(fields)
        if self.env.context.get('active_id') and \
                self.env.context.get('active_model') == 'room.availability' and \
                self.env.context.get('active_id'):
            res['room_availability_id'] = self.env[
                'room.availability'].browse(self.env.context['active_id']).id
        return res
    
    def update_rate_plan(self):
        """To update the price prices."""
        for rec in self:
            if rec.rate_plan_id:
                start = rec.date_from
                end = rec.date_to
                while start <= end:
                    daily_price = rec.rate_plan_id.day_price_ids.filtered(lambda d: d.date == start)
                    if daily_price:
                        daily_price.write({
                            'price': rec.base_rate
                        })
                    else:
                        self.env['rate.plan.day.price'].create({
                            'plan_id': rec.rate_plan_id.id,
                            'date': start,
                            'price': rec.base_rate,
                        })
                    start += relativedelta(days=1)
        return {'type': 'ir.actions.act_window_close'}

