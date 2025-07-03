from odoo import fields, models, api
from odoo.exceptions import ValidationError


class BookingDiscount(models.Model):
    _name = 'booking.discount'
    _description = 'Booking Discount'

    name = fields.Char(required=True)
    short_code = fields.Char(string='Short Code', required=True)
    type = fields.Selection(selection=[
        ('percentage', 'Percentage'),
        ('flat', 'Flat')
    ], required=True, default='percentage')
    open_discount = fields.Boolean()
    value = fields.Float(requierd=True)
    apply_on_room_rate = fields.Boolean()
    apply_on_extra_charge = fields.Boolean()
    active = fields.Boolean(default=True)
    discount_allowed_users = fields.Many2many('res.users', string='Allowed Access Users')

    @api.model
    def create(self, vals):
        if not vals.get('apply_on_room_rate') and not vals.get('apply_on_extra_charge'):
            raise ValidationError("Please select apply on!")
        res = super(BookingDiscount, self).create(vals)
        return res

    @api.constrains('value')
    def check_value(self):
        for rec in self:
            if not 0 < rec.value < 100 and rec.type == 'percentage':
                raise ValidationError("%value must be between 1 and 100!")
