from odoo import fields, models, api
from dateutil.relativedelta import relativedelta


class RatePlan(models.Model):
    _name = 'hotel.rate.plan'
    _description = 'Rate Plan'

    name = fields.Char(string='Rate Plan', compute='compute_name', store=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, required=True)
    room_type_id = fields.Many2one('room.type', required=True, domain="[('company_id', '=', company_id)]")
    rate_type_id = fields.Many2one('hotel.rate.type', required=True, domain="[('company_id', '=', company_id)]")
    web_description = fields.Text()
    base_adult = fields.Integer()
    max_adult = fields.Integer()
    base_child = fields.Integer()
    max_child = fields.Integer()
    rock_rate = fields.Float()
    extra_adult = fields.Float()
    extra_child = fields.Float()
    price_ids = fields.One2many('hotel.rate.plan.price', 'plan_id')
    day_price_ids = fields.One2many('rate.plan.day.price', 'plan_id')
    tax_ids = fields.Many2many('account.tax', domain="[('type_tax_use', '=', 'sale'), ('company_id', '=', company_id)]")
    include_breakfast = fields.Boolean()
    include_lunch = fields.Boolean()
    include_dinner = fields.Boolean()
    @api.depends('rate_type_id', 'room_type_id')
    def compute_name(self):
        for rec in self:
            rec.name = False
            if rec.rate_type_id and rec.room_type_id:
                rec.name = rec.room_type_id.name + ' ' + rec.rate_type_id.name

    def convert_to_daily_prices(self):
        for price_line in self.price_ids.sorted(key='id', reverse=True):
            start = price_line.date_from
            end = price_line.date_to

            while start <= end:
                daily_price = self.day_price_ids.filtered(lambda d: d.date == start)
                if daily_price:
                    daily_price.write({
                        'price': price_line.price
                    })
                else:
                    self.env['rate.plan.day.price'].create({
                        'plan_id': self.id,
                        'date': start,
                        'price': price_line.price,
                    })
                start += relativedelta(days=1)


class RatePlanPrice(models.Model):
    _name = 'hotel.rate.plan.price'
    _description = 'Rate Plan pricing'

    plan_id = fields.Many2one('hotel.rate.plan')
    date_from = fields.Date(required=True)
    date_to = fields.Date(required=True)
    price = fields.Float()
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, required=True)


class RatePlanDayPrice(models.Model):
    _name = 'rate.plan.day.price'
    _description = 'Rate Plan Daily pricing'
    _order = 'date'

    plan_id = fields.Many2one('hotel.rate.plan')
    date = fields.Date(required=True)
    price = fields.Float(required=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, required=True)

