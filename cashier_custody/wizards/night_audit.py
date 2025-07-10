from odoo import fields, models, api, _
from odoo.exceptions import UserError
import logging
logger = logging.getLogger(__name__)



class NightAuditHelper(models.TransientModel):
    _name = 'night.audit.helper'
    _description = 'Night Audit Wizard Launcher'

    def action_open_night_audit(self):
        self.ensure_one()
        payments = self.env['account.payment'].sudo().search([
            ('company_id', '=', self.env.company.id),
            ('closed_cashier', '=', False),
            ('state', '!=', 'cancel'),
            ('booking_id', '!=', False),
        ])
        if payments:
            payment_info = [
                f"{p.name} (User: {p.user_id.name or 'N/A'})" for p in payments
            ]
            raise UserError(_("There are operations that need cashier close:\n") + "\n".join(payment_info))

        return {
            'type': 'ir.actions.act_window',
            'name': 'Night Audit',
            'res_model': 'night.audit',
            'view_mode': 'form',
            'target': 'new',
        }




class NightAudit(models.TransientModel):
    _inherit = 'night.audit'


    # @api.onchange('date')
    # def _onchange_date(self):
    #     payments = self.env['account.payment'].sudo().search([
    #         ('company_id', '=', self.env.company.id),
    #         ('closed_cashier', '=', False),
    #         ('state', '!=', 'cancel'),
    #         ('booking_id', '!=', False),
    #     ])
    #     if payments:
    #         payment_info = [
    #             f"{payment.name} (User: {payment.user_id.name or 'N/A'})"
    #             for payment in payments
    #         ]
    #         raise UserError(
    #             f"There are operations that need cashier close:\n" +
    #             "\n".join(payment_info)
    #         )
    #     res = super(NightAudit, self)._onchange_date()
    #     return res

    # @api.model
    # def action_open_night_audit(self):
    #     logger.info("Opening Night Audit Wizard")
    #     payments = self.env['account.payment'].sudo().search([
    #         ('company_id', '=', self.env.company.id),
    #         ('closed_cashier', '=', False),
    #         ('state', '!=', 'cancel'),
    #         ('booking_id', '!=', False),
    #     ])
    #     if payments:
    #         payment_info = [
    #             f"{payment.name} (User: {payment.user_id.name or 'N/A'})"
    #             for payment in payments
    #         ]
    #         raise UserError(
    #             f"There are operations that need cashier close:\n" +
    #             "\n".join(payment_info)
    #         )
    #
    #     return {
    #         'name': "Night Audit",
    #         'type': 'ir.actions.act_window',
    #         'res_model': 'night.audit',
    #         'view_mode': 'form',
    #         'target': 'new',
    #     }
