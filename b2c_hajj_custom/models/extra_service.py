from odoo import fields, models, api


class ExtraService(models.Model):
    _name = 'extra.service'
    _description = 'Extra Service'

    name = fields.Char()


class ExtraServiceLine(models.Model):
    _name = 'extra.service.line'
    _description = 'Extra Service Line'

    name = fields.Many2one('extra.service', string='Name')
    sale_price = fields.Float(string='Sale Price')
    cost_price = fields.Float(string='Cost Price')
    package_id = fields.Many2one('booking.package', string='Package ID', required=True, ondelete='cascade')
