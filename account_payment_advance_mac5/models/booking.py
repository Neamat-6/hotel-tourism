from odoo import fields, models, api


class HotelBooking(models.Model):
    _inherit = 'hotel.booking'

    has_advance_payment = fields.Boolean(compute='_has_advance_payment', string='Has advance payment?')

    def _has_advance_payment(self):
        for invoice in self:
            advance_payment_args = [
                ('company_id', '=', invoice.company_id.id),
                ('is_advance_payment', '=', True),
                ('partner_id', '=', invoice.partner_id.id),
                ('partner_type', '=', 'customer'),
                ('residual', '>', 0.0),
                ('state', '=', 'posted'),
            ]
            if self.env['account.payment'].search(advance_payment_args):
                invoice.has_advance_payment = True
            else:
                invoice.has_advance_payment = False

    def action_account_advance_payment(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Apply Advance Payments',
            'view_mode': 'form',
            'view_type': 'form',
            'view_id': self.env.ref('account_payment_advance_mac5.view_account_advance_payment_invoice_form').id,
            'res_model': "account.advance.payment.invoice",
            'target': 'new',
            'binding_model_id': self.id,
            'context': {
                'default_company_id': self.company_id.id,
                'default_currency_id': self.currency_id.id,
                'default_partner_id': self.partner_id.id,
                'default_partner_type': 'customer',
                'default_booking': self.id,
                'default_amount_total': self.amount_total
            }
        }