from odoo import fields, models, api


class RoomType(models.Model):
    _inherit = 'room.type'

    aiosell_code = fields.Char()
