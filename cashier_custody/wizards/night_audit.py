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
            payment_info = [
                f"{payment.name} (User: {payment.user_id.name or 'N/A'})"
                for payment in payments
            ]
            raise UserError(
                f"There are operations that need cashier close:\n" +
                "\n".join(payment_info)
            )
        res = super(NightAudit, self)._onchange_date()
        return res
