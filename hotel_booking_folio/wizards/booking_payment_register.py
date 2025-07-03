from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError


class BookingPaymentRegister(models.TransientModel):
    _inherit = 'booking.payment.register'

    folio_id = fields.Many2one('booking.folio')
    # split folios
    booking_folio_ids = fields.Many2many('booking.folio', 'booking_payment_register_folio1_rel', 'wizard_id',
                                         'folio_id',
                                         compute='compute_booking_folio_ids', store=True, string='Folios')
    folio_ids = fields.Many2many('booking.folio', string='Folios',
                                 domain="[('id', 'in', booking_folio_ids)]")
    split = fields.Boolean()
    line_ids = fields.One2many('booking.payment.register.line', 'register_id')
    select_all = fields.Boolean(string='Select All Folios')
    is_master_folio = fields.Boolean()
    is_advance_payment = fields.Boolean("Advance Payment ?")
    advance_payment_account_id = fields.Many2one('account.account')
    pay_more = fields.Boolean("Pay More Than Booking")
    pay_amount = fields.Monetary("Amount")
    remaining_amount = fields.Monetary(compute='get_remaining_amount')

    @api.onchange('pay_amount', 'amount')
    def get_remaining_amount(self):
        for rec in self:
            if rec.pay_amount and rec.amount:
                rec.remaining_amount = rec.pay_amount - rec.amount
            else:
                rec.remaining_amount = 0.0

    def check_folios(self):
        for rec in self:
            if len(rec.folio_id.booking_id.folio_ids) < 1 and not self.folio_ids:
                raise ValidationError("please select and update folios")

    def select_update_folios(self):
        self.split = True
        self.select_all = True
        self.select_all_folios()
        self.button_update_split()
        self.get_due_amount()
        return {
            'name': _('Register Payment'),
            'res_model': 'booking.payment.register',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'type': 'ir.actions.act_window',
            'res_id': self.id
        }

    @api.onchange('select_all')
    def select_all_folios(self):
        if self.select_all:
            self.folio_ids = self.env['booking.folio'].search([('id', 'in', self.booking_folio_ids.ids)])
        else:
            self.folio_ids = False

    def get_due_amount(self):
        for rec in self:
            if rec.line_ids:
                for line in rec.line_ids:
                    line.amount = line.due_amount
            rec.amount = sum(rec.line_ids.mapped('due_amount'))
        return {
            'name': _('Register Payment'),
            'res_model': 'booking.payment.register',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'type': 'ir.actions.act_window',
            'res_id': self.id
        }

    def distribute_amount(self):
        total_lines = len(self.line_ids)
        if total_lines == 0:
            raise ValidationError("There Is No Lines")
        else:
            distribution_ratio = self.amount / total_lines
            for line in self.line_ids:
                line.amount = distribution_ratio
        return {
            'name': _('Register Payment'),
            'res_model': 'booking.payment.register',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'type': 'ir.actions.act_window',
            'res_id': self.id
        }

    @api.depends('booking')
    def compute_booking_folio_ids(self):
        for rec in self:
            rec.booking_folio_ids = rec.booking.folio_ids.filtered(
                lambda f: f.state != 'cancelled').ids if rec.booking else False

    def button_update_split(self):
        if not len(self.folio_ids) > 1:
            raise ValidationError("you must add more than one folio to split")
        self.line_ids = [(5, 0, 0)]
        for folio in self.folio_ids:
            self.env['booking.payment.register.line'].create({
                'register_id': self.id,
                'folio_id': folio.id,
                'amount': 0
            })
        return {
            'name': _('Register Payment'),
            'res_model': 'booking.payment.register',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'type': 'ir.actions.act_window',
            'res_id': self.id
        }

    def action_create_payments(self):
        self.ensure_one()
        self.check_folios()
        payments = []
        if self.is_master_folio and not self.line_ids:
            raise ValidationError("Please click on select and update!")
        to_process = []
        advance_process = []
        # in case of split
        if self.split and self.folio_ids:
            # self.get_due_amount()    #todo in group payment amount not distributed so we hash this line
            lst1 = self.folio_ids.ids
            lst2 = self.line_ids.mapped('folio_id').mapped('id')
            lst1.sort()
            lst2.sort()
            if lst1 != lst2:
                raise ValidationError("click on renew lines!")
            if self.amount != sum(self.line_ids.mapped('amount')):
                pass
                # raise ValidationError("split amounts not equal total amount!")
            for line in self.line_ids:
                to_process = []
                payment_vals, advance_payment_vals = self._create_payment_vals_from_wizard()
                if payment_vals:
                    payment_vals['amount'] = line.amount
                    payment_vals['folio_id'] = line.folio_id.id
                    to_process.append({
                        'create_vals': payment_vals,
                    })
                    payments = self.env['account.payment'].create([x['create_vals'] for x in to_process])
                    payments.action_post()
                particulars = self.prepare_particulars()
                # todo check amount and due in split folios
                if line.amount > line.due_amount > 0:
                    total = -line.due_amount
                elif line.amount > line.due_amount and line.due_amount <= 0:
                    total = 0
                else:
                    total = line.amount

                self.env['booking.folio.line'].sudo().create({
                    'folio_id': line.folio_id.id,
                    'day': self.payment_date,
                    'amount': -total,
                    'description': self.communication,
                    'payment_id': payments[0].id if payments else False,
                    'particulars': particulars,
                    'is_city_ledger': self.booking.payment_type_id == 'city_ledger',
                    'show_delete': self.booking.payment_type_id == 'city_ledger',
                })

            self.folio_id.update({'note': self.notes})
            message = f'You Paid {self.amount} Successfully'
            return {
                'name': 'Warning',
                'type': 'ir.actions.act_window',
                'res_model': 'warn.wizard',
                'view_mode': 'form',
                'view_type': 'form',
                'target': 'new',
                'context': {'default_message': message, 'default_booking_id': self.booking.id}
            }
            # todo added advanced payment after loop to not duplicate advanced
            # advance_payment_amount = self.amount - self.booking.amount_due
            # self.journal_partner_id.total_advanced_payment += advance_payment_amount

        else:
            # payment_vals = self._create_payment_vals_from_wizard()
            payment_vals, advance_payment_vals = self._create_payment_vals_from_wizard()
            if payment_vals:
                if self.folio_id:
                    payment_vals['folio_id'] = self.folio_id.id
                to_process.append({
                    'create_vals': payment_vals,
                })
                payments = self.env['account.payment'].create([x['create_vals'] for x in to_process])
                payments.action_post()

            # todo create advance payment but now we want get ref for partner
            if self.pay_type == 'yes':
                if advance_payment_vals:
                    advance_process.append({
                        'create_vals': advance_payment_vals,
                    })
                    advance_payment = self.env['account.payment'].create([x['create_vals'] for x in advance_process])
                    advance_payment.action_post()

            # to_process.append({
            #     'create_vals': payment_vals,
            # })

            particulars = self.prepare_particulars()
            vals = self.prepare_folio_line(payments, particulars)
            if self.folio_id:
                vals['folio_id'] = self.folio_id.id
            self.env['booking.folio.line'].sudo().create(vals)
        if self.folio_id:
            message = f'You Paid {self.amount} Successfully'
            self.folio_id.update({'note': self.notes})
            return {
                'name': 'Warning',
                'type': 'ir.actions.act_window',
                'res_model': 'warn.wizard',
                'view_mode': 'form',
                'view_type': 'form',
                'target': 'new',
                'context': {'default_message': message, 'default_folio_id': self.folio_id.id}
            }

    def prepare_folio_line(self, payments, particulars):
        vals = super().prepare_folio_line(payments, particulars)
        vals.update({'show_delete': self.booking.payment_type_id == 'city_ledger'})
        return vals

    def prepare_particulars(self):
        particulars = ''
        if self.journal_id.type == 'cash':
            particulars = 'Cash'
        elif self.journal_id.type == 'bank':
            if self.journal_id.is_city_ledger:
                particulars = 'City Ledger'
            elif self.payment_method_line_id.name == 'Manual':
                particulars = 'Bank'
            else:
                particulars = self.payment_method_line_id.name
        return particulars


class BookingPaymentRegisterLine(models.TransientModel):
    _name = 'booking.payment.register.line'
    _description = 'Booking Payment Register Split'

    register_id = fields.Many2one('booking.payment.register')
    currency_id = fields.Many2one('res.currency')
    folio_id = fields.Many2one('booking.folio', required=True)
    due_amount = fields.Monetary(related='folio_id.price_due', string="Due Amount")
    amount = fields.Float(required=True)
