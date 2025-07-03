from odoo import api, fields, models


class Conditions(models.Model):
    _name = 'conditions.terms'
    _description = "Terms & Conditions"
    _rec_name = 'name'

    name = fields.Char('Name', required=True)
    terms = fields.Html('Conditions And Terms', required=True)
    type = fields.Selection(selection=[
        ('registration_form', 'Registration Form'),
        ('confirm', 'Booking Confirm'),
    ])

