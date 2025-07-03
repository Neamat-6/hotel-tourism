from odoo import fields, models, api


class AuditTrails(models.Model):
    _inherit = 'audit.trails'

    operation = fields.Selection(selection_add=[
        ('ezee', 'Ezee Log'), ('ezee_error', 'Ezee Log Error'),
    ], ondelete={'ezee': 'cascade', 'ezee_error': 'cascade'})
    ezee_reference = fields.Char()