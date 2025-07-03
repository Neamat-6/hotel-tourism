from odoo import fields, models


class PackageContract(models.Model):
    _name = 'package.contract'

    name = fields.Char("Name")
