from odoo import fields, models, api


class RoomType(models.Model):
    _name = 'ntmp.room.type'
    _description = 'NTMP Room Type'

    code = fields.Char(required=True, string='Type ID')
    name = fields.Char(required=True, string='Type AR')
    name_en = fields.Char(required=True, string='Type EN')
