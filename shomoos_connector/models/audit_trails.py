from odoo import fields, models, api


class ShomoosAuditTrails(models.Model):
    _inherit = 'audit.trails'

    operation = fields.Selection(selection_add=[
        ('shomoos', 'Shomoos Log'),
    ], ondelete={'shomoos': 'cascade'})
