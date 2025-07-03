from odoo import api, fields, models


class AdvancePayment(models.TransientModel):
    _name = 'advance.payment'

    currency_id = fields.Many2one('res.currency', string='Currency', store=True, readonly=False,
                                  compute='_compute_currency_id',
                                  help="The payment's currency.")

    amount = fields.Monetary(currency_field='currency_id')
    journal_id = fields.Many2one('account.journal', string='Journal', required=True,
                                 domain="[('type', 'in', ('bank', 'cash'))]")
    advance_payment_account_id = fields.Many2one('account.account', string='Advance Payment Account', required=True,
                                                 domain="[('reconcile', '=', True)]")
    partner_id = fields.Many2one('res.partner', string="Customer")
    booking_id = fields.Many2one('hotel.booking')

    @api.depends('journal_id')
    def _compute_currency_id(self):
        for wizard in self:
            wizard.currency_id = wizard.journal_id.currency_id or wizard.company_id.currency_id

    def create_payment(self):
        self.ensure_one()
        to_process = []
        advance_payment_vals = {
            'date': fields.Date.today(),
            'amount': self.amount,
            'payment_type': 'inbound',
            'partner_type': 'customer',
            'is_advance_payment': True,
            'ref': "Advance Payment",
            'journal_id': self.journal_id.id,
            'currency_id': self.currency_id.id,
            'partner_id': self.partner_id.id,
            'audit_date': self.env.company.audit_date,
            'advance_payment_account_id': self.advance_payment_account_id.id
        }
        to_process.append({
            'create_vals': advance_payment_vals,
        })
        payments = self.env['account.payment'].create([x['create_vals'] for x in to_process])
        payments.action_post()

        vals = {
            'folio_id': self.booking_id.folio_ids[0].id,
            'day': fields.Date.today(),
            'amount': self.amount,
            'description': f"Advance Payment {self.amount} for {self.partner_id.name}",
            'payment_id': payments[0].id if payments else False,
            'particulars': "Advance Payment",
        }
        self.env['booking.folio.line'].sudo().create(vals)

        message = f"Advance Payment {self.amount} Created Successfully"
        return {
            'name': 'Warning',
            'type': 'ir.actions.act_window',
            'res_model': 'warn.wizard',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': {'default_message': message, 'default_booking_id': self.booking_id.id}
        }
