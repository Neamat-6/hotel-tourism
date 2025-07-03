from odoo import api, fields, models
from odoo.exceptions import ValidationError


class CityLedgerPayment(models.Model):
    _inherit = 'account.payment'

    city_ledger_payment = fields.Boolean()
    destination_journal_id = fields.Many2one(
        comodel_name='account.journal',
        string='Destination Journal',
        domain="[('type', 'in', ('bank','cash')),('id', '!=', journal_id)]",
        check_company=True,
    )
    h_booking_ids = fields.Many2many('hotel.booking', relation='h_booking_rel', string="Bookings",
                                     context={'ignore_record_rule': True})
    hotel_booking_id = fields.Many2one('hotel.booking', domain=[('id', 'in', 'booking_ids')])
    advance_payment = fields.Float("Advance Payment")
    payment_note = fields.Char("Payment Note")
    system_note = fields.Char("Note")
    hotel_ids = fields.Many2many('hotel.hotel', string='Hotels')
    partner_advance_payment = fields.Monetary("Advance Payment",
                                              related='journal_dis_partner_id.total_advanced_payment', store=True)
    settled_advance_payment = fields.Boolean("Settled From Advance Payment")
    new_check_in = fields.Date("Check In")
    new_check_out = fields.Date("Check Out")

    def unselect_all_booking(self):
        if self.h_booking_ids:
            for rec in self.h_booking_ids:
                rec.is_selected = False

    @api.onchange('select_all')
    def select_all_bookings(self):
        if self.h_booking_ids and self.city_ledger_payment:
            for rec in self.h_booking_ids:
                rec.is_selected = True
            self.partner_amount = sum(self.h_booking_ids.filtered(lambda l: l.is_selected).mapped('paid_amount_city_ledger'))
        else:
            self.partner_amount = 0.0

    @api.onchange('h_booking_ids')
    def onchange_booking_id(self):
        for rec in self:
            if not rec.journal_dis_partner_id:
                rec.h_booking_ids = False
            if rec.city_ledger_payment and rec.h_booking_ids:
                rec.partner_amount = sum(
                    rec.h_booking_ids.filtered(lambda l: l.is_selected).mapped('paid_amount_city_ledger')) - sum(
                    rec.h_booking_ids.filtered(lambda l: l.is_selected).mapped('company_paid'))
            else:
                rec.partner_amount = 0.0

    @api.onchange('journal_dis_partner_id', 'folio_ids', 'booking_ids', 'hotel_ids', 'new_check_in', 'new_check_out')
    def onchange_dis_partner(self):
        print('caleeeddddddddd from city')
        for rec in self:
            print('journal_dis_partner_id', self.journal_dis_partner_id)
            if self.journal_dis_partner_id:
                self.partner_id = self.journal_dis_partner_id.id
                self.h_booking_ids = [(5, 0, 0)]
                company_booking_source = self.env['hotel.booking'].search(
                    ['|', ('company_booking_source', '=', self.journal_dis_partner_id.id),
                     ('online_travel_agent_source', '=', self.journal_dis_partner_id.id), ('state', '!=', 'cancelled'),
                     ('amount_paid', '!=', 0.0),
                     ('paid_amount_city_ledger', '!=', 0.0)]).filtered(lambda l: l.payment_type_id == 'city_ledger' and (
                        l.company_paid < l.paid_amount_city_ledger or l.company_paid == 0.0))
                if self.hotel_ids:
                    company_booking_source = company_booking_source.filtered(
                        lambda l: l.hotel_id.id in self.hotel_ids.ids)
                if rec.city_ledger_payment:
                    if self.new_check_in and self.new_check_out:
                        company_booking_source = company_booking_source.filtered(
                            lambda l: l.new_check_in >= self.new_check_in and l.new_check_out <= self.new_check_out)
                        print('company_booking_source filtered', company_booking_source)
                    rec.h_booking_ids = company_booking_source.ids
                    for line in rec.h_booking_ids:
                        if line.is_selected:
                            line.is_selected = False
                    booking_ids = company_booking_source.ids
                    folio_ids = company_booking_source.mapped('folio_ids')
                    rec.hotel_booking_ids = booking_ids
                    rec.booking_ids = booking_ids
                    rec.hotel_folios_ids = folio_ids
                    rec.folios_ids = folio_ids

    @api.onchange('destination_journal_id', 'journal_id')
    def _onchange_booking_payment_type(self):
        if self.city_ledger_payment:
            account_journal_obj = self.env['account.journal'].search(
                [('is_city_ledger', '=', True), ('company_id', '=', self.journal_id.company_id.id)], limit=1)
            journal_obj = self.env['account.journal'].search(
                [('is_city_ledger', '!=', True), ('type', 'in', ['bank', 'cash'])])
            if account_journal_obj:
                self.destination_journal_id = account_journal_obj.id
            else:
                self.destination_journal_id = False
            # self.journal_id = False
            # self.destination_journal_id = False
            return {
                'domain': {
                    'destination_journal_id': [('type', 'in', ('bank', 'cash')),
                                               ('company_id', '=', self.journal_id.company_id.id),
                                               ('id', '!=', self.journal_id.id), ('id', 'in', account_journal_obj.ids)],
                    'journal_id': [('type', 'in', ('bank', 'cash')),
                                   ('id', 'in', journal_obj.ids)],

                }
            }

    # @api.onchange('journal_id')
    # def onchange_journal(self):
    #     for rec in self:
    #         if rec.journal_id:
    # journal_obj = self.env['account.journal'].search([('type', '=', 'cash')], limit=1)
    # rec.journal_id = journal_obj
    # rec.destination_journal_id = False

    # @api.depends('partner_id', 'journal_id', 'destination_journal_id')
    # def _compute_is_internal_transfer(self):
    #     super(CityLedgerPayment, self)._compute_is_internal_transfer()
    #     for payment in self:
    #         if payment.city_ledger_payment:
    #             payment.is_internal_transfer = True

    @api.onchange('partner_amount')
    def onchange_partner_amount(self):
        if self.settled_advance_payment and not self.move_line_ids:
            self.amount = self.partner_amount

    def action_post(self):
        res = super(CityLedgerPayment, self).action_post()
        if self.city_ledger_payment:
            if self.settled_advance_payment:
                if self.partner_amount > self.partner_advance_payment:
                    raise ValidationError(f"you should max pay with {self.partner_advance_payment}")
                else:
                    self.distribute_advanced_amount()
                    # self.journal_dis_partner_id.total_advanced_payment -= self.partner_amount
            else:
                self.hotel_booking_id.update({'settled_by_city_ledger': True})
                self.distribute_amount()
        if self.is_advance_payment:
            self.partner_id.total_advanced_payment += self.amount
            self.extra_amount = self.amount
        return res

    def action_draft(self):
        res = super(CityLedgerPayment, self).action_draft()
        for rec in self:
            if rec.city_ledger_payment:
                rec.hotel_booking_id.update({'settled_by_city_ledger': False})
            if rec.city_ledger_payment and rec.h_booking_ids:
                if self.amount > self.partner_amount:
                    advanced = self.amount - self.partner_amount
                    self.journal_dis_partner_id.total_advanced_payment -= advanced
                for line in rec.h_booking_ids.filtered(lambda l: l.is_selected):
                    line.update({'company_paid': 0.0})
                # self.journal_dis_partner_id.total_advanced_payment += self.amount
            if rec.is_advance_payment:
                rec.partner_id.total_advanced_payment -= self.amount
                self.extra_amount = 0.0
        return res

    def distribute_amount(self):
        if self.h_booking_ids:
            total_lines = len(self.h_booking_ids)
            amount_per_line = self.amount / total_lines
            for line in self.h_booking_ids.filtered(lambda l: l.is_selected):
                if self.amount > self.partner_amount:
                    line.update({'company_paid': line.paid_amount_city_ledger})
                elif self.amount < self.partner_amount:
                    raise ValidationError(f"please set amount greater than or equal {self.partner_amount}")
                    # line.update({'company_paid': amount_per_line})
                else:
                    line.update({'company_paid': line.paid_amount_city_ledger})
            advanced = self.amount - self.partner_amount
            self.advance_payment = advanced
            self.journal_dis_partner_id.total_advanced_payment += advanced

    def distribute_advanced_amount(self):
        if self.h_booking_ids:
            total_lines = len(self.h_booking_ids)
            amount_per_line = self.amount / total_lines
            for line in self.h_booking_ids.filtered(lambda l: l.is_selected):
                if self.amount > self.partner_amount:
                    line.update({'company_paid': line.paid_amount_city_ledger})
                elif self.amount < self.partner_amount:
                    raise ValidationError(f"please set amount greater than or equal {self.partner_amount}")
                    # line.update({'company_paid': amount_per_line})
                else:
                    line.update({'company_paid': line.paid_amount_city_ledger})
            advanced = self.amount - self.partner_amount
            self.advance_payment = advanced
            self.journal_dis_partner_id.total_advanced_payment -= self.amount

    def action_advance_payment(self):
        return {
            'name': 'Advanced Payment',
            'res_model': 'account.payment',
            'view_mode': 'form',
            # 'res_id': ,
            'target': 'current',
            'type': 'ir.actions.act_window',
            'context': {'default_payment_type': 'inbound', 'default_partner_type': 'customer',
                        'default_is_advance_payment': True},
        }

    def action_settled_payment(self):
        return {
            'name': 'Settled Booking',
            'res_model': 'settled.booking',
            'view_mode': 'form',
            'target': 'current',
            'type': 'ir.actions.act_window',
        }
