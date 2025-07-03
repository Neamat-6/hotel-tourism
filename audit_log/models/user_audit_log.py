from odoo import models, fields


class UserAuditLog(models.Model):
    _name = 'user.audit.log'
    _description = 'Detailed User Audit Log'

    user_id = fields.Many2one('res.users', string='User', required=True)
    model = fields.Char(string='Model', required=True)
    record_id = fields.Integer(string='Record ID')
    field_name = fields.Char(string='Field Name')
    old_value = fields.Text(string='Old Value')
    new_value = fields.Text(string='New Value')
    action = fields.Selection([
        ('create', 'Create'),
        ('write', 'Write'),
        ('unlink', 'Delete')
    ], string='Action', required=True)
    changed_by = fields.Many2one('res.users', string='Changed by', required=True)
    date_changed = fields.Datetime(string='Date Changed', default=fields.Datetime.now, required=True)
