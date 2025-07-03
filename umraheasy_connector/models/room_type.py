from odoo import fields, models, api


class RoomType(models.Model):
    _inherit = 'room.type'

    umraheasy_code = fields.Char()
