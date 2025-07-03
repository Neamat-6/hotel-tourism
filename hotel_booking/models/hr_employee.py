from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    is_housekeeper = fields.Boolean("Is Housekeeper")


class HrEmployeePublic(models.Model):
    _inherit = 'hr.employee.public'

    is_housekeeper = fields.Boolean("Is Housekeeper")
