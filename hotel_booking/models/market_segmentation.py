from odoo import api, fields, models


class MarketSegmentation(models.Model):
    _name = 'market.segmentation'

    name = fields.Char("Name")
