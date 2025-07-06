
from odoo import api, fields, models


class Conditions(models.Model):
    _name = 'tourism.conditions.terms'
    _description = "Terms & Conditions"
    _rec_name = 'name'

    sequence = fields.Integer(defualt=10)
    name = fields.Char('Name', required=True)
    terms = fields.Html('Conditions And Terms', required=True)


class HotelRoomView(models.Model):
    _name = 'hotel.room.view'
    _description = 'Room View'

    sequence = fields.Integer(defualt=10)
    name = fields.Char(string="Room View", required=True, index=True)


class HotelMeal(models.Model):
    _name = 'hotel.meal'
    _description = 'Meal'

    sequence = fields.Integer(defualt=10)
    name = fields.Char(string="Meal", required=True, index=True)