from odoo import fields, models, api


class AccountPaymentMethod(models.Model):
    _inherit = 'account.payment.method'

    @api.model
    def _get_payment_method_information(self):
        res = super()._get_payment_method_information()
        res['mada'] = {'mode': 'multi', 'domain': [('type', '=', 'bank')]}
        res['visa'] = {'mode': 'multi', 'domain': [('type', '=', 'bank')]}
        res['master_card'] = {'mode': 'multi', 'domain': [('type', '=', 'bank')]}
        return res
