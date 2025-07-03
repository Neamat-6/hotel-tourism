from odoo import fields, models, api


class OutOfOrderReason(models.Model):
    _name = 'out.of.order.reason'
    _description = 'Out of Order Reason'

    name = fields.Char()
