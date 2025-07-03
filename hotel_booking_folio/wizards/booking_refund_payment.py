from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import logging
logger = logging.getLogger(__name__)


class BookingRefundPayment(models.Model):
    _name = 'booking.refund.payment'

    folio_id = fields.Many2one('booking.folio')
    booking_ids = fields.Many2many('hotel.booking', compute='compute_booking_ids', store=True)
    booking_id = fields.Many2one('hotel.booking', domain="[('id', 'in', booking_ids)]")
    is_group_refunded = fields.Boolean()
    folio_ids = fields.Many2many("booking.folio", compute='get_folio_transfer')
    booking_folio_ids = fields.Many2many('booking.folio',
                                         compute='compute_booking_folio_ids', store=True, string='Folios')

    transfer_folio_id = fields.Many2one('booking.folio',
                                        domain="[('id', 'in', booking_folio_ids), ('id', '!=', folio_id)]")
    state = fields.Selection([
        ('refund', 'Refund'),
        ('transfer', 'Transfer')
    ], string="Type", help="Refund Status of Payment")
    refund_status = fields.Selection([
        ('partially_return', 'Partially Refund'),
        ('fully_return', 'Fully Refund')
    ], string="Refund Status", help="Refund Payment")
    transfer_status = fields.Selection([
        ('partially_transfer', 'Partially Transfer'),
        ('fully_transfer', 'Fully Transfer')
    ], string="Transfer Status", help="Transfer Payment")
    total_amount = fields.Float("Total Payment Amount", readonly=True)
    refund_amount = fields.Float("Refunded Amount")
    transfer_amount = fields.Float("Transfer Amount")
    payment_date = fields.Date("Payment Date", default=fields.Date.today())
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, required=True)
    journal_id = fields.Many2one('account.journal', string='Payment Method',
                                 domain="[('type', 'in', ('bank', 'cash'))]")
    is_city_ledger = fields.Boolean(related='journal_id.is_city_ledger')
    journal_partner_id = fields.Many2one(comodel_name="res.partner", string="City Ledger",
                                         domain=[('is_city_ledger', '=', True)])
    payment_method_line_id = fields.Many2one('account.payment.method.line', string='Payment Method',
                                             readonly=False, store=True,
                                             compute='_compute_payment_method_line_id',
                                             domain="[('id', 'in', available_payment_method_line_ids)]")
    available_payment_method_line_ids = fields.Many2many('account.payment.method.line',
                                                         compute='_compute_payment_method_line_fields')
    booking_refund_payment_line_ids = fields.One2many('booking.refund.payment.line', 'booking_refund_id')
    hide_payment_method_line = fields.Boolean(
        compute='_compute_payment_method_line_fields',
        help="Technical field used to hide the payment method if the selected journal has only one available which is 'manual'")
    partner_id = fields.Many2one('res.partner', string="Customer")
    payment_id = fields.Many2one('account.payment')
    payment_type = fields.Selection([
        ('outbound', 'Send Money'),
        ('inbound', 'Receive Money'),
    ], string='Payment Type')

    @api.depends('folio_id')
    def compute_booking_ids(self):
        for rec in self:
            rec.booking_ids = False
            folio = rec.folio_id
            booking = folio.booking_id
            if booking.company_booking_source or booking.partner_id or folio.partner_id:
                domain = [('state', 'not in', ['cancelled', 'checked_out']), ('company_id', '=', folio.company_id.id)]
                if booking.company_booking_source:
                    domain.append(('company_booking_source', '=', booking.company_booking_source.id))
                elif booking.partner_id or folio.partner_id:
                    domain.append(('partner_id', 'in', [booking.partner_id.id, folio.partner_id.id]))
                bookings = rec.env['hotel.booking'].search(domain)
                rec.booking_ids = [(6, 0, bookings.ids)]

    @api.onchange('state')
    def get_folio_transfer(self):
        for rec in self:
            if rec.folio_id:
                rec.folio_ids = rec.folio_id.booking_id.folio_ids
            else:
                rec.folio_ids = False

    def distribute_total_amount(self):
        total_lines = len(self.booking_folio_ids)
        if total_lines == 0:
            raise ValidationError("there is no lines")
        else:
            if self.refund_status == 'partially_return':
                distribution_ratio = self.refund_amount / total_lines
                for line in self.booking_refund_payment_line_ids:
                    line.amount = distribution_ratio
            else:
                distribution_ratio = self.total_amount / total_lines
                for line in self.booking_refund_payment_line_ids:
                    line.amount = distribution_ratio
        return {
            'name': _('Refunded / Transfer Payment'),
            'res_model': 'booking.refund.payment',
            'view_mode': 'form',
            'target': 'new',
            'type': 'ir.actions.act_window',
            'res_id': self.id
        }

    def get_due_amount(self):
        for rec in self:
            if rec.booking_refund_payment_line_ids:
                for line in rec.booking_refund_payment_line_ids:
                    line.amount = line.due_amount
            rec.update({'total_amount': sum(rec.booking_refund_payment_line_ids.mapped('due_amount'))})
        return {
            'name': _('Refunded / Transfer Payment'),
            'res_model': 'booking.refund.payment',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'type': 'ir.actions.act_window',
            'res_id': self.id
        }

    def button_update_split(self):
        if not len(self.booking_folio_ids) > 1:
            raise ValidationError("you must add more than one folio to split")
        self.booking_refund_payment_line_ids = [(5, 0, 0)]
        for folio in self.booking_folio_ids:
            self.env['booking.refund.payment.line'].create({
                'booking_refund_id': self.id,
                'folio_id': folio.id,
                'amount': 0
            })
        return {
            'name': _('Refunded / Transfer Payment'),
            'res_model': 'booking.refund.payment',
            'view_mode': 'form',
            'target': 'new',
            'type': 'ir.actions.act_window',
            'res_id': self.id
        }

    @api.depends('payment_type', 'journal_id','booking_id')
    def _compute_payment_method_line_id(self):
        for wizard in self:
            available_payment_method_lines = wizard.journal_id._get_available_payment_method_lines(wizard.payment_type)
            if available_payment_method_lines:
                wizard.payment_method_line_id = available_payment_method_lines[0]._origin
            else:
                wizard.payment_method_line_id = False

    @api.depends('booking_id')
    def compute_booking_folio_ids(self):
        for rec in self:
            rec.booking_folio_ids = rec.booking_id.folio_ids.filtered(
                lambda f: f.state != 'cancelled').ids if rec.booking_id else False

    @api.depends('payment_type', 'journal_id')
    def _compute_payment_method_line_fields(self):
        for wizard in self:
            wizard.available_payment_method_line_ids = wizard.journal_id._get_available_payment_method_lines(
                wizard.payment_type)
            if wizard.payment_method_line_id.id not in wizard.available_payment_method_line_ids.ids:
                # In some cases, we could be linked to a payment method line that has been unlinked from the journal.
                # In such cases, we want to show it on the payment.
                wizard.hide_payment_method_line = False
            else:
                wizard.hide_payment_method_line = len(wizard.available_payment_method_line_ids) == 1 \
                                                  and wizard.available_payment_method_line_ids.code == 'manual'

    def action_refund_payments(self):
        logger.info(f'caleeddddddddddddddaction_refund_payments')
        rec = self
        if not rec.is_group_refunded:
            logger.info(f'caleeddddddddddddddaction_refund_payments first stage')
            if rec.state == 'refund':
                if rec.refund_amount and rec.total_amount < rec.refund_amount:
                    raise ValidationError("Please Check Refund Amount")
                amount_to_refund = rec.refund_amount if rec.refund_status == 'partially_return' else rec.total_amount
                if amount_to_refund == 0.0:
                    raise ValidationError("please add refund amount not zero")
                description = "Partially Refund Payment" if rec.refund_status == 'partially_return' else "Fully Refund Payment"
                self.create_payment()
                self.create_folio_line(rec.folio_id.id, amount_to_refund, description, "Refund")
                if self.booking_id.company_paid:
                    if self.booking_id.amount_paid != self.booking_id.company_paid:
                        self.booking_id.update({'company_paid': self.booking_id.amount_paid})
                message = f'{amount_to_refund} Refunded Successfully'
                return {
                    'name': 'Message',
                    'type': 'ir.actions.act_window',
                    'res_model': 'warn.wizard',
                    'view_mode': 'form',
                    'view_type': 'form',
                    'target': 'new',
                    'context': {'default_message': message, 'default_booking_id': self.booking_id.id}
                }
            else:
                logger.info(f'caleeddddddddddddddaction_refund_payments transfer first stage')
                if rec.transfer_amount and rec.total_amount < rec.transfer_amount:
                    raise ValidationError("Please Check Transfer Amount")
                if rec.transfer_amount == 0.0 and rec.transfer_status == 'partially_transfer':
                    raise ValidationError("please add transfer amount not zero")
                amount = rec.transfer_amount if rec.transfer_status == 'partially_transfer' else rec.total_amount
                payment_ids = self.env['account.payment'].sudo().search(
                    [('folio_id', '=', rec.folio_id.id)])
                print('payment_id', payment_ids)
                logger.info(f'caleeddddddddddddddaction_refund_payments transfer payment{payment_ids}')
                if rec.transfer_status == 'fully_transfer':
                    for payment in payment_ids:
                        logger.info(f'caleeddddddddddddddaction_refund_payments fully transfer')
                        self.create_folio_line(rec.folio_id.id, amount,
                                               f"Transfer Payment to {rec.transfer_folio_id.name}",
                                               "Transfer")
                        self.create_folio_line(rec.transfer_folio_id.id, -amount,
                                               f"Transfer Payment From {rec.folio_id.name}",
                                               "Transfer", payment.id)
                        old_payment_line = rec.folio_id.line_ids.filtered(
                            lambda l: l.payment_id.id == payment.id)
                        old_payment_line.write({'payment_id': None})
                        payment.write(
                            {'folio_id': rec.transfer_folio_id.id, 'booking_id': rec.booking_id.id, 'ref': rec.transfer_folio_id.id})
                else:
                    remaining_amount = amount

                    for payment in payment_ids:
                        if remaining_amount <= 0:
                            break

                        # Calculate how much to deduct from this payment
                        deduction = min(payment.amount, remaining_amount)

                        # Create the payment
                        self.create_payment(payment, deduction)
                        logger.info(
                            f'called action_refund_payments transfer partialy new payment {self.payment_id}')
                        # Create folio lines
                        self.create_folio_line(rec.folio_id.id, deduction,
                                               f"Transfer Payment to {rec.transfer_folio_id.name}",
                                               "Transfer", payment.id)
                        self.create_folio_line(rec.transfer_folio_id.id, -deduction,
                                               f"Transfer Payment From {rec.folio_id.name}",
                                               "Transfer", self.payment_id.id)

                        # Update payment amount
                        payment.write({"amount": payment.amount - deduction})

                        # Reduce the remaining amount
                        remaining_amount -= deduction

                rec.folio_id.compute_amount_total()
                rec.transfer_folio_id.compute_amount_total()
                # _compute_amount_paid
                message = f'{amount} Transferred Successfully'
                return {
                    'name': 'Message',
                    'type': 'ir.actions.act_window',
                    'res_model': 'warn.wizard',
                    'view_mode': 'form',
                    'view_type': 'form',
                    'target': 'new',
                    'context': {'default_message': message, 'default_booking_id': self.booking_id.id}
                }
        else:
            logger.info(f'caleeddddddddddddddaction_refund_payments second stage')
            if rec.refund_status == 'partially_return':
                if rec.refund_amount and rec.total_amount < rec.refund_amount:
                    raise ValidationError("Please Check Refund Amount")
                if rec.refund_amount == 0.0:
                    raise ValidationError("please add refund amount not zero")
                self.create_payment()
            else:
                self.create_payment()

    def create_folio_line(self, folio_id, amount, description, particulars, payment_id=None):
        self.env['booking.folio.line'].sudo().create({
            'folio_id': folio_id,
            'day': fields.Date.today(),
            'amount': amount,
            'description': description,
            'particulars': particulars,
            'payment_id': self.payment_id.id if self.payment_id else payment_id
        })

    def create_payment(self, payment_id=None, amount=0):
        to_process = []
        for rec in self:
            if not rec.is_group_refunded:
                if rec.state == 'refund':
                    amount_to_refund = rec.refund_amount if rec.refund_status == 'partially_return' else rec.total_amount
                    payment_vals = {
                        'date': self.payment_date,
                        'amount': amount_to_refund,
                        'payment_type': 'outbound',
                        'partner_type': 'customer',
                        'ref': self.folio_id.name,
                        'journal_id': self.journal_id.id,
                        'partner_id': self.partner_id.id,
                        'booking_id': self.folio_id.booking_id.id,
                        'folio_id': self.folio_id.id,
                        'payment_method_line_id': self.payment_method_line_id.id,
                        'journal_partner_id': self.journal_partner_id.id,
                        'is_payment': True
                    }
                else:
                    payment_vals = {
                        'date': self.payment_date,
                        'amount': amount,
                        'payment_type': 'inbound',
                        'partner_type': 'customer',
                        'ref': self.transfer_folio_id.name,
                        'journal_id': payment_id.journal_id.id,
                        'partner_id': payment_id.partner_id.id,
                        'booking_id': self.transfer_folio_id.booking_id.id,
                        'folio_id': self.transfer_folio_id.id,
                        'payment_method_line_id': payment_id.payment_method_line_id.id,
                        'journal_partner_id': payment_id.journal_partner_id.id,
                        'is_payment': True
                    }
            else:
                # todo handle create payment for group payment
                for line in self.booking_refund_payment_line_ids:
                    to_process = []
                    payment_vals = {
                        'date': self.payment_date,
                        'amount': line.amount,
                        'payment_type': 'outbound',
                        'partner_type': 'customer',
                        'ref': line.folio_id.name,
                        'journal_id': self.journal_id.id,
                        'partner_id': self.partner_id.id,
                        'booking_id': self.booking_id.id,
                        'folio_id': line.folio_id.id,
                        'payment_method_line_id': self.payment_method_line_id.id,
                        'journal_partner_id': self.journal_partner_id.id,
                        'is_payment': True
                    }
                    to_process.append({
                        'create_vals': payment_vals,
                    })
                    group_payments = self.env['account.payment'].create([x['create_vals'] for x in to_process])
                    group_payments.action_post()
                    payment_id = group_payments.id
                    booking_folio_line_obj = self.env['booking.folio.line'].sudo().create({
                        'folio_id': line.folio_id.id,
                        'day': fields.Date.today(),
                        'amount': line.amount,
                        'description': "Group Refunded",
                        'particulars': "Refunded",
                        'payment_id': payment_id
                    })

                break

            to_process.append({
                'create_vals': payment_vals,
            })
            payments = self.env['account.payment'].create([x['create_vals'] for x in to_process])
            payments.action_post()
            self.payment_id = payments.id


class BookingRefundPaymentLine(models.TransientModel):
    _name = 'booking.refund.payment.line'
    _description = 'Booking Payment Register Split'

    booking_refund_id = fields.Many2one('booking.refund.payment')
    currency_id = fields.Many2one('res.currency')
    folio_id = fields.Many2one('booking.folio', required=True)
    due_amount = fields.Monetary(related='folio_id.price_paid', string="Paid Amount")
    amount = fields.Float(required=True)
