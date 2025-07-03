from odoo import api, fields, models


class RoomType(models.Model):
    _inherit = 'room.type'

    image_1920 = fields.Binary('Image')
