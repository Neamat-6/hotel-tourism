from odoo import fields, models, api


class RatePlan(models.Model):
    _inherit = 'hotel.rate.plan'

    aiosell_code = fields.Char()


class RatePlanDayPrice(models.Model):
    _inherit = 'rate.plan.day.price'

    # @api.model
    # def create(self, vals):
    #     res = super(RatePlanDayPrice, self).create(vals)
    #     if res.company_id.enable_aiosell:
    #         wizard = self.env['aiosell.connector'].create({
    #             'date_from': res.date,
    #             'date_to': res.date,
    #             'action_type': 'update_rate',
    #             'company_id': res.company_id.id,
    #             'rate_plan_ids': [(6, 0, res.plan_id.ids)],
    #         })
    #         wizard.button_search()
    #         wizard.button_update_rate()
    #     return res
    #
    # def write(self, vals):
    #     res = super(RatePlanDayPrice, self).write(vals)
    #     if self.company_id.enable_aiosell:
    #         if vals.get('price', False):
    #             wizard = self.env['aiosell.connector'].create({
    #                 'date_from': self.date,
    #                 'date_to': self.date,
    #                 'action_type': 'update_rate',
    #                 'company_id': self.company_id.id,
    #                 'rate_plan_ids': [(6, 0, self.plan_id.ids)],
    #             })
    #             wizard.button_search()
    #             wizard.button_update_rate()
    #     return res
