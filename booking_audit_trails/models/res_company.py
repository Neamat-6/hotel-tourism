from odoo import fields, models, api


class Company(models.Model):
    _inherit = 'res.company'

    def write(self, vals):
        if vals.get('audit_date', False):
            self.env['audit.trails'].create({
                'user_id': self.env.user.id,
                'operation': 'update_audit_date',
                'datetime': fields.Datetime.now(),
                'notes': f"Audit date has been updated from {self.audit_date} to {vals['audit_date']}"
            })
        res = super(Company, self).write(vals)
        return res
