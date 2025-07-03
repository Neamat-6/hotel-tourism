from odoo import fields, models, api


class RoomType(models.Model):
    _inherit = 'room.type'

    ntmp_room_type_id = fields.Many2one('ntmp.room.type', string='NTMP Type')
