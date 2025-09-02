from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.http import request


class AccountMove(models.Model):
    _inherit = 'account.move'

    contract_booking_id = fields.Many2one('contract.booking')

class ContractBooking(models.Model):
    _name = 'contract.booking'
    _description = 'Contract Booking'
    _rec_name = 'partner_id'
    _inherit = ["mail.thread", 'portal.mixin']

    source = fields.Selection([('person', 'Direct'), ('company', 'Company')], required=True)
    partner_id = fields.Many2one('res.partner', required=True)
    state= fields.Selection([('draft', 'Tentative Confirmation'),('hotel_confirm', 'Confirmed Waiting Payment'),('confirmed', 'Confirmed'),('cancelled', 'Cancelled')], default='draft')
    move_id = fields.Many2one('account.move', copy=False)
    extra_lines = fields.One2many('extra.booking.line', 'contract_book_id')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id, string='Company')
    total_cost = fields.Float(compute='compute_total_cost', store=True)
    flight_contract = fields.Many2one('flight.schedule', string="Flight Contract", domain="[('is_expired', '=', False)]")
    visa_contract = fields.Many2one('visa.contract', string="Visa Contract", domain="[('is_expired', '=', False)]")
    transport_contract = fields.Many2one('transportation.contract', string="Transportation Contract", domain="[('is_expired', '=', False)]")
    flight_count = fields.Integer(string="Flight Count")
    visa_count = fields.Integer(string="Visa Count")
    transport_count = fields.Integer(string="Transport Count")
    flight_price = fields.Float(string="Flight Price")
    visa_price = fields.Float(string="Visa Price")
    transport_price = fields.Float(string="Transport Price")
    notes = fields.Text()



    @api.onchange('source')
    def _onchange_source(self):
        domain = []
        if self.source == 'person':
            domain = [('is_company', '=', False)]
            # Do NOT clear partner_id here
        elif self.source == 'company':
            domain = [('is_company', '=', True)]
            # Do NOT clear partner_id here

        return {
            'domain': {
                'partner_id': domain
            }
        }

    @api.depends('flight_count', 'visa_count', 'transport_count', 'flight_price', 'visa_price', 'transport_price', 'extra_lines.quantity', 'extra_lines.price_unit')
    def compute_total_cost(self):
        for rec in self:
            total_cost = 0.0
            for line in rec.extra_lines:
                total_cost += line.quantity * line.price_unit
            cost = (rec.flight_count * rec.flight_price) + (rec.visa_count * rec.visa_price) + (rec.transport_count * rec.transport_price)
            total_cost += cost
            rec.total_cost = total_cost

    def _prepare_invoice_lines(self):
        invoice_line_vals = []
        if self.flight_contract and self.flight_count and self.flight_price:
            invoice_line_vals = [(0, 0, {
                    # 'product_id': line.room_id.product_id.id,
                    'name': f"{self.flight_contract.name}",
                    'quantity': self.flight_count,
                    'price_unit': self.flight_price,
                    # 'tax_ids': line.tax_id,
                    # 'account_id': hotel_hotel_obj.account_journal_id.default_account_id.id
                })]
        if self.visa_contract and self.visa_count and self.visa_price:
            invoice_line_vals.append((0, 0, {
                'name': f"{self.visa_contract.name}",
                'quantity': self.visa_count,
                'price_unit': self.visa_price,
            }))
        if self.transport_contract and self.transport_count and self.transport_price:
            invoice_line_vals.append((0, 0, {
                'name': f"{self.transport_contract.transportation_contract_no}",
                'quantity': self.transport_count,
                'price_unit': self.transport_price,
            }))
        for line in self.extra_lines:
            invoice_line_vals.append((0, 0, {
                'name': line.extra_id.name,
                'quantity': line.quantity,
                'price_unit': line.price_unit,
            }))
        return invoice_line_vals

    def update_invoice(self):
        print('callllllllllllllllllled')
        self.move_id.line_ids.unlink()
        self.move_id.invoice_line_ids.unlink()
        print('after delete', self.move_id)
        income_account = self.env['account.account'].search([
            ('user_type_id.type', '=', 'income'),
            ('deprecated', '=', False),
            ('company_id', '=', self.company_id.id)
        ], limit=1)
        print('income_account', income_account)
        invoice_line_vals = self._prepare_invoice_lines()
        self.move_id.write({
            'partner_id': self.partner_id.id,
            'invoice_line_ids': invoice_line_vals
        })
        self.move_id._recompute_dynamic_lines(recompute_all_taxes=True)
        self.move_id.action_post()

    def create_invoice(self):
        self.ensure_one()
        print(f'create_invoice called {self.company_id.name}')
        company = self.company_id or self.env.company
        tax_ids = self.company_id.hotel_default_tax_ids.ids
        invoice_line_vals = self._prepare_invoice_lines()
        move_vals = {
            'move_type': 'out_invoice',
            'partner_id': self.partner_id.id,
            'contract_booking_id': self.id,
            # 'journal_id': journal_id,
            'invoice_user_id': self._uid,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': invoice_line_vals,
            'company_id': self.company_id.id,
        }
        move = self.env['account.move'].with_context({'line_ids': False,}).with_company(company).create(move_vals)
        move.action_post()
        print('mmmmmmmmmove', move)
        self.move_id = move.id

    def create_booking(self):
        for rec in self:
            if not rec.total_cost:
                raise UserError(_("can not create invoice with zero amount"))
            if not rec.move_id:
                rec.create_invoice()
            else:
                print('hhhhhhhhhhhhhhhhhhhhhhhh')
                rec.update_invoice()
            rec.state = 'hotel_confirm'

    def action_confirm(self):
        for rec in self:
            if rec.move_id:
                # if rec.move_id.payment_state != 'paid':
                if rec.move_id.amount_residual != 0:
                    raise UserError("The linked invoice must be fully paid before confirming.")
                rec.state = 'confirmed'
            else:
                raise UserError("Must create invoice first")

    def action_reset_to_draft(self):
        for rec in self:
            rec.move_id.button_draft()
            rec.state = 'draft'


    def action_cancel(self):
        for rec in self:
            rec.move_id.button_cancel()
            rec.state = 'cancelled'

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('Cannot delete a record which is in state \'%s\'.') % (rec.state,))
            if rec.move_id:
                rec.move_id.button_cancel()
                rec.move_id.unlink()
                rec.move_id = False
        return super(ContractBooking, self).unlink()

    def action_open_invoice(self):
        self.ensure_one()
        if self.move_id:
            return {
                'type': 'ir.actions.act_window',
                'name': _('Invoice'),
                'view_mode': 'form',
                'res_model': 'account.move',
                'res_id': self.move_id.id,
                'target': 'current',
            }
        else:
            return {
                'type': 'ir.actions.act_window_close',
            }