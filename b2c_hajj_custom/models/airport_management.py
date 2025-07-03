from odoo import fields, models


class AirportManagement(models.Model):
    _name = 'airport.management'

    name = fields.Char("Airport Name")
