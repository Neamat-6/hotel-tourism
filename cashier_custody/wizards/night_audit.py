from odoo import fields, models, api
from odoo.exceptions import UserError


class NightAudit(models.TransientModel):
    _inherit = 'night.audit'

    @api.onchange('date')
    def _onchange_date(self):
        payments = self.env['account.payment'].sudo().search([
            ('company_id', '=', self.env.company.id),
            ('closed_cashier', '=', False),
            ('state', '!=', 'cancel'),
            ('booking_id', '!=', False),
        ])
        if payments:
            raise UserError(f"there are operations need to cashier close {payments.mapped('name')}")
        res = super(NightAudit, self)._onchange_date()
        return res
