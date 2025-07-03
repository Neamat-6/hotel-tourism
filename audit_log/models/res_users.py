from odoo import models, api, fields


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model
    def create(self, vals):
        user = super(ResUsers, self).create(vals)
        self.env['user.audit.log'].create({
            'user_id': user.id,
            'model': 'res.users',
            'record_id': user.id,
            'field_name': 'N/A',
            'old_value': 'N/A',
            'new_value': str(vals),
            'action': 'create',
            'changed_by': self.env.user.id,
        })
        return user

    @api.model
    def write(self, values):
        for user in self:
            for field in values.keys():
                if field.startswith('sel_groups_'):
                    self._log_group_selection_changes(user, field, values[field])
                elif field.startswith('in_group_'):
                    self._log_group_checkbox_changes(user, field, values[field])
                elif field in user._fields:
                    old_value = user[field]
                    new_value = values[field]
                    self._log_field_changes(user, field, old_value, new_value)

        return super(ResUsers, self).write(values)

    def _log_group_selection_changes(self, user, field, new_value):
        group_id = int(field.split('_')[-1])
        group = self.env['res.groups'].browse(group_id)

        self.create_audit_log(user, group.display_name, None, group.name)

    def _log_group_checkbox_changes(self, user, field, new_value):
        group_id = int(field.split('_')[-1])
        group = self.env['res.groups'].browse(group_id)

        if new_value:
            old_value = 'False'
            new_value = True
        else:
            old_value = True
            new_value = False

        self.create_audit_log(user, group.full_name, old_value, new_value)

    def _log_field_changes(self, user, field_name, old_value, new_value):
        field_type = user._fields[field_name].type
        if field_type == 'many2one':
            old_value_display = old_value.name if old_value else None
            new_value_display = self.env[user._fields[field_name].comodel_name].browse(new_value).name if new_value else None
        elif field_type == 'many2many':
            if isinstance(new_value, list):
                if new_value:
                    if new_value[0][0] == 6:
                        new_value_ids = new_value[0][2]
                    else:
                        new_value_ids = [item[1] for item in new_value if item[0] in [4, 3]]
                else:
                    new_value_ids = new_value[2]
            else:
                new_value_ids = []

            old_value_display = ', '.join(old_value.mapped('name')) if old_value else None
            new_value_display = ', '.join(self.env['res.company'].browse(new_value_ids).mapped('name')) if new_value_ids else None
        elif field_type == 'one2many':
            old_value_display = ', '.join(old_value.mapped('name')) if old_value else None
            new_value_display = ', '.join(
                self.env[user._fields[field_name].comodel_name].browse(new_value).mapped('name')) if new_value else None
        else:
            old_value_display = old_value
            new_value_display = new_value

        self.create_audit_log(user, field_name, old_value_display, new_value_display)

    def create_audit_log(self, user, field_name, old_value, new_value):
        self.env['user.audit.log'].create({
            'user_id': user.id,
            'field_name': field_name,
            'model': 'res.users',
            'old_value': old_value,
            'new_value': new_value,
            'changed_by': self.env.user.id,
            'action': 'write',
            'date_changed': fields.Datetime.now(),
        })

    def unlink(self):
        for user in self:
            self.env['user.audit.log'].create({
                'user_id': user.id,
                'model': 'res.users',
                'record_id': user.id,
                'field_name': 'N/A',
                'old_value': 'N/A',
                'new_value': 'N/A',
                'action': 'unlink',
                'changed_by': self.env.user.id,
            })
        return super(ResUsers, self).unlink()
