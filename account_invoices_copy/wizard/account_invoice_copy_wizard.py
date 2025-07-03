from odoo import api, fields, models, _


class AccountInvoiceWizardCopy(models.TransientModel):
    _name = 'account.invoice.wizard.copy'

    new_date_invoice = fields.Date('New invoices date', required=True, default=fields.Date.today())
    new_date_due = fields.Date('New due Date', required=True, default=fields.Date.today())
    target_company = fields.Many2one('res.company', string='Target Company')
    journal_id = fields.Many2one('account.journal', string='Journal Company',
                                 domain="[('company_id','=',target_company)]")

    def copy_invoice(self, records=False):
        if records:
            self._context['active_ids'] = records.ids
            return {
                'name': _('Invoices copy wizard'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'account.invoice.wizard.copy',
                'view_id': self.env.ref('account_invoices_copy.account_invoice_copy_view_copy_form').id,
                'type': 'ir.actions.act_window',
                'target': 'new',
                'context': self._context,
            }

    @api.onchange('new_date_invoice')
    def onchange_new_date_invoice(self):
        self.new_date_due = self.new_date_invoice

    def create_invoices(self):
        for invoice in self.env['account.move'].browse(self._context.get('active_ids')):
            if not invoice.is_copied:
                invoice.copy({
                    'move_type': 'out_invoice',
                    'invoice_date': self.new_date_invoice,
                    'invoice_date_due': self.new_date_due,
                    'user_id': self._context.get('uid'),
                    'state': 'draft',
                    'partner_id': invoice.partner_id.id,
                    'journal_id': self.journal_id.id,
                    'payment_reference': invoice.payment_reference,
                    'folio_id': invoice.folio_id.id,
                    'folio_room_id': invoice.folio_room_id.id,
                    'company_id': self.target_company.id
                })
                invoice.update({'is_copied': True})
