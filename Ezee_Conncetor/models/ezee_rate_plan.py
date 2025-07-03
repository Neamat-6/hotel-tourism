from odoo import api, fields, models


class EzeeRatePlan(models.Model):
    _name = 'ezee.rate.plan'
    _description = 'Ezee Rate Plan'

    name = fields.Char("Name", required=True)
    code = fields.Char(string='Rate Plan Code')
    room_type_id = fields.Many2one('ezee.room.type')
    room_type_code = fields.Char(related='room_type_id.code', string='Room Type Code')
    rate_type_id = fields.Many2one('ezee.rate.type')
    rate_type_code = fields.Char(related='rate_type_id.code', string='Rate Type Code')
    hotel_id = fields.Many2one('hotel.hotel')
    company_id = fields.Many2one('res.company')
