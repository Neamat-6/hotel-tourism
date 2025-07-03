from dateutil.relativedelta import relativedelta

from odoo import fields, models


class ApplyDiscount(models.TransientModel):
    _inherit = 'booking.apply.discount'

    folio_id = fields.Many2one('booking.folio')
    note = fields.Char("Char")
    discount = fields.Float(string="Discount %")
    open_discount = fields.Boolean(related='type.open_discount')

    def get_discount_amount(self,discount,amount):
        if not discount.open_discount:
            if discount.type == 'percentage':
                discount_amount = (amount * discount.value) / 100
            else:
                discount_amount = discount.value
        else:
            discount_amount = (amount * self.discount) / 100
        return discount_amount

    def apply_discount(self):
        folio = self.folio_id
        discount = self.type
        note = self.note
        taxes = self.env['account.tax'].search([])
        total_amount = 0.0
        if self.discount_rule == 'all_nights':
            dates = folio.get_dates_between_exclude_checkout(folio.check_in, folio.check_out)
            for date in dates:
                total_amount = 0.0
                if discount.apply_on_room_rate:
                    lines = folio.line_ids.filtered(lambda l: l.day == date.date() and not l.is_service_tax and (l.type == 'room_charge' or l.type == 'tax'))
                    total_amount = sum(lines.mapped('amount'))
                    if total_amount:
                        self.create_folio_line(total_amount, note, discount, date)
                        discount_amount = self.get_discount_amount(discount,total_amount)
                        wizard = self.env['folio.room.charge'].sudo().create({
                            'folio_id': self.folio_id.id,
                            'amount': total_amount - discount_amount,
                            'folio_line_ids': self.folio_id.line_ids.filtered(lambda l: l.type == 'room_charge' and l.day >= self.folio_id.audit_date).ids,
                            'all_folio_line_ids': self.folio_id.line_ids.filtered(lambda l: l.type == 'room_charge').ids,
                            'tax_ids': taxes.filtered(lambda t: t.price_include).ids
                        })
                        wizard.button_update_charge()
                if discount.apply_on_extra_charge:
                    expense_lines = folio.line_ids.filtered(
                        lambda l: l.day == date.date() and (l.type in ['food', 'beverage', 'laundry', 'rent'] or l.is_service_tax)
                    )
                    total_amount = sum(expense_lines.mapped('amount'))
                    if total_amount:
                        self.create_folio_line(total_amount, note, discount, date)
                        for line in expense_lines:
                            discount_amount = self.get_discount_amount(discount,line.amount)
                            line.amount = line.amount - discount_amount

            self.env['audit.trails'].create({
                'booking_id': folio.booking_id.id,
                'user_id': self.env.user.id,
                'operation': 'change_price',
                'datetime': fields.Datetime.now(),
                'notes': f"Update Discount {self.discount} On All Nights , Folio {folio.name}"
            })
        elif self.discount_rule == 'first_night':
            if discount.apply_on_room_rate:
                lines = folio.line_ids.filtered(
                    lambda l: l.day == folio.check_in_date and not l.is_service_tax and (l.type == 'room_charge' or l.type == 'tax'))
                total_amount = sum(lines.mapped('amount'))

                if total_amount:
                    self.create_folio_line(total_amount, note, discount, folio.check_in_date)
                    # ============================== update room charge ==============================
                    discount_amount = self.get_discount_amount(discount,total_amount)
                    wizard = self.env['folio.room.charge'].sudo().create({
                        'folio_id': self.folio_id.id,
                        'amount': total_amount - discount_amount,
                        'folio_line_ids': self.folio_id.line_ids.filtered(lambda l: l.type == 'room_charge' and l.day == folio.check_in_date).ids,
                        'all_folio_line_ids': self.folio_id.line_ids.filtered(lambda l: l.type == 'room_charge').ids,
                        'tax_ids': taxes.filtered(lambda t: t.price_include).ids
                    })
                    wizard.button_update_charge()
            if discount.apply_on_extra_charge:
                expense_lines = folio.line_ids.filtered(
                    lambda l: l.day == folio.check_in_date and (l.type in ['food', 'beverage', 'laundry', 'rent'] or l.is_service_tax)
                )
                if total_amount:
                    self.create_folio_line(total_amount, note, discount, folio.check_in_date)
                    for line in expense_lines:
                        discount_amount = self.get_discount_amount(discount,line.amount)
                        line.amount = line.amount - discount_amount
            # ================================================================================
            self.env['audit.trails'].create({
                'booking_id': folio.booking_id.id,
                'user_id': self.env.user.id,
                'operation': 'change_price',
                'datetime': fields.Datetime.now(),
                'notes': f"Update Discount {self.discount} On First Night, Folio {folio.name}"
            })
        elif self.discount_rule == 'last_night':
            last_night = folio.check_out_date - relativedelta(days=1)
            if discount.apply_on_room_rate:
                lines = folio.line_ids.filtered(lambda l: l.day == last_night and not l.is_service_tax and (l.type == 'room_charge' or l.type == 'tax'))
                total_amount = sum(lines.mapped('amount'))
                if total_amount:
                    self.create_folio_line(total_amount, note, discount, last_night)
                    # ============================== update room charge ==============================
                    discount_amount = self.get_discount_amount(discount,total_amount)
                    wizard = self.env['folio.room.charge'].sudo().create({
                        'folio_id': self.folio_id.id,
                        'amount': total_amount - discount_amount,
                        'folio_line_ids': self.folio_id.line_ids.filtered(lambda l: l.type == 'room_charge' and l.day == last_night).ids,
                        'all_folio_line_ids': self.folio_id.line_ids.filtered(lambda l: l.type == 'room_charge').ids,
                        'tax_ids': taxes.filtered(lambda t: t.price_include).ids
                    })
                    wizard.button_update_charge()
            if discount.apply_on_extra_charge:
                expense_lines = folio.line_ids.filtered(lambda l: l.day == last_night and (l.type in ['food', 'beverage', 'laundry', 'rent'] or l.is_service_tax))
                total_amount = sum(expense_lines.mapped('amount'))
                if total_amount:
                    self.create_folio_line(total_amount, note, discount, last_night)
                    for line in expense_lines:
                        discount_amount = self.get_discount_amount(discount,line.amount)
                        line.amount = line.amount - discount_amount
            # ================================================================================
            self.env['audit.trails'].create({
                'booking_id': folio.booking_id.id,
                'user_id': self.env.user.id,
                'operation': 'change_price',
                'datetime': fields.Datetime.now(),
                'notes': f"Update Discount {self.discount} On Last Night, Folio {folio.name}"
            })
        return {
            'type': 'ir.actions.act_window',
            'name': "Folio",
            'res_model': 'booking.folio',
            'view_mode': 'form',
            'target': 'new',
            'res_id': self.folio_id.id
        }

    def create_folio_line(self, amount, note, discount, date):
        # return # stop create more line for discount to avoid multi discount issues
        folio = self.folio_id
        if not discount.open_discount:
            if discount.type == 'percentage':
                discount_amount = (amount * discount.value) / 100
            else:
                discount_amount = discount.value
        else:
            discount_amount = (amount * self.discount) / 100

        self.env['booking.folio.line'].create({
            'folio_id': folio.id,
            'day': date,
            'amount': 0,
            'discount_amount': discount_amount,
            'particulars': 'Discount',
            'type': 'discount',
            'description': note
        })
