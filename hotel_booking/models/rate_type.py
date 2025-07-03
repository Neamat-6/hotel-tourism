from odoo import fields, models, api


class RateType(models.Model):
    _name = 'hotel.rate.type'
    _description = 'Rate Type'

    code = fields.Char(string='Short Code', required=True)
    name = fields.Char(required=True)
    is_package = fields.Boolean()
    valid_from = fields.Date()
    valid_to = fields.Date()
    inclusion_ids = fields.One2many('hotel.rate.type.inclusion', 'rate_type_id')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, required=True)
    market_segmentation_id = fields.Many2one('market.segmentation', string='Market Segmentation')


class RateTypeInclusion(models.Model):
    _name = 'hotel.rate.type.inclusion'
    _description = 'Rate Type Inclusion'

    rate_type_id = fields.Many2one('hotel.rate.type')
    service_id = fields.Many2one('hotel.services', required=True)
    posting_rule = fields.Selection(selection=[
        ('check_in_out', 'Check in and check out'),
        ('everyday', 'Everyday'),
        ('everyday_no_check_in', 'Everyday except check in'),
        ('everyday_no_check_in_out', 'Everyday except check in and check out'),
        ('everyday_no_check_out', 'Everyday except check out'),
        ('custom', 'On custom date'),
        ('check_in', 'Only on check in'),
        ('check_out', 'Only on check out'),
    ], required=True)
    charge_rule = fields.Char()
    rate = fields.Float()
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, required=True)
