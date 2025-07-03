from odoo import fields, models


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    cashier_custody_id = fields.Many2one('cashier.custody')
    closed_cashier = fields.Boolean(string="Closed")
    is_selected_payment = fields.Boolean("Is Selected")

    def action_close_cashier(self):
        payments = self.env['account.payment'].browse(self.env.context.get('active_ids', []))
        for payment in payments:
            payment.closed_cashier = True
