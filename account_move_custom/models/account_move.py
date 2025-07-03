from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    def get_account_journal(self):
        journal_entry_values = []
        for rec in self:
            rec.ensure_one()
            if rec.line_ids:
                for line in rec.line_ids:
                    entry_values = {
                        'account_id': line.account_id.new_account_id.id if line.account_id.add_account else line.account_id.id,
                        'name': line.name,
                        'partner_id': rec.partner_id.id,
                        'credit': line.credit,
                        'debit': line.debit,
                    }
                    journal_entry_values.append((0, 0, entry_values))

            if journal_entry_values:
                journal_entry = self.env['account.move'].create({
                    'move_type': 'entry',
                    'journal_id': rec.journal_id.id,
                    'date': rec.invoice_date,
                    'line_ids': journal_entry_values,
                })
                journal_entry.action_post()

            rec.button_draft()
            rec.update({'name': ""})

    def delete_records(self):
        self.unlink()

    def copy_invoices(self):
        invoice_line_list = []
        res_company_objs = self.env['res.company'].search([('target_company', '=', True)], limit=1)
        if res_company_objs:
            for rec in self:
                account_journal_obj = self.env['account.journal'].search(
                    [("name", "=", rec.journal_id.name), ('company_id', '=', res_company_objs.id)])
                move_id = self.env['account.move'].create({
                    'move_type': 'out_invoice',
                    'is_htask_move': True,
                    'partner_id': rec.partner_id.id,
                    'journal_id': account_journal_obj.id,
                    'invoice_date': rec.invoice_date,
                    'payment_reference': rec.payment_reference,
                    'folio_id': rec.folio_id.id,
                    'folio_room_id': rec.folio_room_id.id,
                    'company_id': res_company_objs.id
                })
                for line in rec.line_ids:
                    vals = (0, 0, {
                        'product_id': line.product_id.id,
                        'name': line.product_id.name,
                        'price_unit': line.price_unit,
                        'discount': line.discount,
                        'account_id': line.account_id.id,
                        'quantity': line.quantity,
                        'price_subtotal': line.price_subtotal
                    })
                invoice_line_list.append(vals)
                move_id.invoice_line_ids = invoice_line_list
                # move_id.action_post()
