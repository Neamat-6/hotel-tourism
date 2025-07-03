from odoo import fields, models, api


class AuditTrails(models.Model):
    _inherit = 'audit.trails'

    operation = fields.Selection(selection_add=[
        ('aiosell', 'Aiosell Log'),
    ], ondelete={'aiosell': 'cascade'})
