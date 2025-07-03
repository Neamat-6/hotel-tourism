from odoo import models, fields

class HotelDestination(models.Model):
    _name = "hotel.destination"
    _description = "Hotel Destination"
    
    
    name = fields.Char(string="Destination Name", required=True)