from odoo import fields, models, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    period = fields.Integer(string='Period Per Minutes', default=0.0)
    from_hour = fields.Float(string='From Hour', default=0.0)
    to_hour = fields.Float(string='To Hour', default=0.0)
    is_orderable = fields.Boolean(string='Is orderable', default=False)
