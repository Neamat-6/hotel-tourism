from odoo import fields, models, api


class ApplyDiscount(models.TransientModel):
    _name = 'booking.apply.discount'
    _description = 'Apply Discount'

    type = fields.Many2one('booking.discount', required=True)
    discount_rule = fields.Selection(selection=[
        ('all_nights', 'All Nights'),
        ('first_night', 'First Night'),
        ('last_night', 'Last Night'),
    ], required=True)

    def apply_discount(self):
        pass