from odoo import api, fields, models
from odoo.exceptions import ValidationError


class SettledBooking(models.Model):
    _name = 'settled.booking'
    _rec_name = 'partner_id'

    partner_id = fields.Many2one(comodel_name="res.partner", string="City Ledger Company", required=True,
                                 domain=[('is_city_ledger', '=', True)])
    amount = fields.Monetary("Amount")
    currency_id = fields.Many2one('res.currency', readonly=True, tracking=True, string='Currency',
                                  default=lambda self: self.env.user.company_id.currency_id)
    hotel_booking_ids = fields.Many2many('hotel.booking', context={'ignore_record_rule': True}, store=True)
    booking_amount = fields.Monetary("Bookings Amount", compute='onchange_booking_id')
    state = fields.Selection(selection=[('draft', 'Draft'), ('confirm', 'Confirm')], required=False,
                             default='draft')
    partner_advance_payment = fields.Monetary("Advance Payment", related='partner_id.total_advanced_payment',
                                              store=True)
    settled_advance_payment = fields.Boolean("Settled From Advance Payment", default=True, readonly=True)
    hotel_ids = fields.Many2many('hotel.hotel', string='Hotels')
    date_from = fields.Datetime("From Date")
    date_to = fields.Datetime("To Date")
    note = fields.Text("Note")

    @api.onchange('booking_amount')
    def onchange_partner_amount(self):
        if self.settled_advance_payment:
            self.amount = self.booking_amount

    @api.onchange('hotel_booking_ids')
    def onchange_booking_id(self):
        for rec in self:
            if rec.hotel_booking_ids:
                rec.booking_amount = sum(
                    rec.hotel_booking_ids.filtered(lambda l: l.is_selected).mapped('amount_total')) - sum(
                    rec.hotel_booking_ids.filtered(lambda l: l.is_selected).mapped('company_paid'))
            else:
                rec.booking_amount = 0.0

    @api.onchange('partner_id', 'hotel_ids')
    def onchange_partner_id(self):
        self.hotel_booking_ids = [(5, 0, 0)]
        if self.partner_id:
            # rule = self.env.ref('hotel_booking.booking_comp_rule')
            #
            # rule.active = False

            hotel_booking_objs = self.env['hotel.booking'].sudo().with_context(
                ignore_record_rule=True,
                allowed_company_ids=self.env.user.company_ids.ids
            ).search(['|', ('company_booking_source', '=', self.partner_id.id),
                      ('online_travel_agent_source', '=', self.partner_id.id)])

            filtered_hotel_booking_objs = hotel_booking_objs.filtered(lambda l: l.payment_type_id == 'city_ledger' and (l.company_paid < l.amount_total or l.company_paid == 0.0))
            hotel_booking_objs = filtered_hotel_booking_objs.filtered(lambda l: l.amount_total != 0.0)

            if self.hotel_ids:
                hotel_booking_objs = hotel_booking_objs.filtered(lambda l: l.hotel_id.id in self.hotel_ids.ids)
            if self.date_from and self.date_to:
                hotel_booking_objs = hotel_booking_objs.filtered(
                    lambda l: l.check_in <= self.date_to and l.check_out >= self.date_from)
            self.hotel_booking_ids = [(6, 0, hotel_booking_objs.ids)]
            self.unselect_all_booking()
            # rule.active = True

    def action_confirm(self):
        if self.settled_advance_payment:
            if self.amount > self.partner_advance_payment:
                raise ValidationError(f"you should max pay with {self.partner_advance_payment}")
            else:
                self.distribute_advanced_amount()
        else:
            self.distribute_amount()
        self.state = 'confirm'
        # rule = self.env.ref('hotel_booking.booking_comp_rule')
        # if not rule.active:
        #     rule.active = True

    def action_draft(self):
        if self.hotel_booking_ids:
            for rec in self.hotel_booking_ids:
                if rec.is_selected:
                    self.partner_id.total_advanced_payment += rec.company_paid
                    rec.update({'company_paid': 0.0})
        self.state = 'draft'

    def select_all_booking(self):
        if self.hotel_booking_ids:
            for rec in self.hotel_booking_ids:
                rec.is_selected = True

    def unselect_all_booking(self):
        if self.hotel_booking_ids:
            for rec in self.hotel_booking_ids:
                rec.is_selected = False

    def distribute_amount(self):
        if not self.hotel_booking_ids:
            raise ValidationError("No bookings available to distribute the amount.")

        total_lines = len(self.hotel_booking_ids.filtered(lambda l: l.is_selected))
        if total_lines == 0:
            raise ValidationError("No selected bookings to distribute the amount.")

        remaining_amount = self.amount
        selected_lines = self.hotel_booking_ids.filtered(lambda l: l.is_selected)

        sorted_lines = selected_lines.sorted(key=lambda l: l.amount_total)

        for line in sorted_lines:
            if remaining_amount <= 0:
                break

            outstanding_amount = line.amount_total - line.company_paid

            if remaining_amount >= outstanding_amount:
                line.company_paid += outstanding_amount
                remaining_amount -= outstanding_amount
            else:
                line.update({'company_paid': line.company_paid + remaining_amount})
                remaining_amount = 0

        if remaining_amount > 0:
            raise ValidationError(f"Amount remaining after distribution: {remaining_amount}")

        # total_paid = sum(line.company_paid for line in selected_lines)
        # if total_paid < self.booking_amount:
        #     raise ValidationError(f"Please set the amount total greater than or equal to {self.booking_amount}")

    def distribute_advanced_amount(self):
        if not self.hotel_booking_ids:
            raise ValidationError("No bookings available to distribute the amount.")

        total_lines = len(self.hotel_booking_ids.filtered(lambda l: l.is_selected))
        if total_lines == 0:
            raise ValidationError("No selected bookings to distribute the amount.")

        remaining_amount = self.amount
        selected_lines = self.hotel_booking_ids.filtered(lambda l: l.is_selected)

        sorted_lines = selected_lines.sorted(key=lambda l: l.amount_total)

        for line in sorted_lines:
            if remaining_amount <= 0:
                break

            outstanding_amount = line.amount_total - line.company_paid

            if remaining_amount >= outstanding_amount:
                line.company_paid += outstanding_amount
                remaining_amount -= outstanding_amount
            else:
                line.update({'company_paid': line.company_paid + remaining_amount})
                remaining_amount = 0

        if remaining_amount > 0:
            raise ValidationError(f"Amount remaining after distribution: {remaining_amount}")

        # total_paid = sum(line.company_paid for line in selected_lines)
        # if total_paid < self.booking_amount:
        #     raise ValidationError(f"Please set the amount total greater than or equal to {self.booking_amount}")

        advanced = self.amount - self.booking_amount
        self.partner_advance_payment = advanced
        self.partner_id.total_advanced_payment -= self.amount
