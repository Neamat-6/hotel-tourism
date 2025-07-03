from odoo import fields, models


class RoomType(models.Model):
    _inherit = 'room.type'

    nationality_ids = fields.Many2many('res.country', string="Nationality")
    region = fields.Selection(string="Region", selection=[('sunni', 'Sunni'), ('shiite', 'Shiite'), ], required=False)
    res_land_ids = fields.Many2many('res.lang', string="Language")
    relationship = fields.Selection([
        ('father', 'Father'),
        ('mother', 'Mother'),
        ('son', 'Son'),
        ('daughter', 'Daughter'),
        ('husband', 'Husband'),
        ('wife', 'Wife'),
    ], string="Relationship")
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
    ], string="Gender")
    is_camp = fields.Boolean("Is Camp")
