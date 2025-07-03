from odoo import api, fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    user_template_id = fields.Many2one(comodel_name="user.template", string="User Template")
    hide_menu_access_ids = fields.Many2many('ir.ui.menu', string='Hide Access Menu',
                                            related='user_template_id.hide_menu_access_ids')

    @api.model
    def create(self, vals):
        vals['groups_id'] = [(5, 0, 0)]
        user = super(ResUsers, self).create(vals)
        if 'user_template_id' in vals:
            template_id = self.env['user.template'].browse(vals['user_template_id'])
            user.write({'sel_groups_1_9_10': 1})
            user.write({'groups_id': [(4, group.id) for group in template_id.groups_ids]})
        return user

    @api.model
    def write(self, vals):
        user = super(ResUsers, self).write(vals)
        if 'user_template_id' in vals:
            template_id = self.env['user.template'].browse(vals['user_template_id'])
            self.groups_id = [(5, 0, 0)]
            internal_user_group = self.env.ref('base.group_user')
            self.write({'groups_id': [(4, internal_user_group.id)]})
            self.write({'groups_id': [(4, group.id) for group in template_id.groups_ids]})
        return user
