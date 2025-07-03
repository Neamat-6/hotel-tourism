from odoo import fields, models, api


class AuditTrails(models.Model):
    _inherit = 'audit.trails'

    operation = fields.Selection(selection_add=[
        ('ntmp', 'NTMP Log'),
    ], ondelete={'ntmp': 'cascade'})
