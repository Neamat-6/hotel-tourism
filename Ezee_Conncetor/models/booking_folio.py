from odoo import fields, models, api


class Folio(models.Model):
    _inherit = 'booking.folio'

    def get_price_unit(self, booking_line, day):
        if booking_line.booking_id.ezee_apply_daily_price:
            price_unit = booking_line.rate_plan.sudo().rock_rate
            price_id = booking_line.booking_id.daily_price_ids.filtered(
                lambda
                    p: p.date == day and p.room_type_id.id == booking_line.room_type.id and p.rate_plan_id.id == booking_line.rate_plan.id
            )
            if price_id:
                price_id = price_id[0]
                price_id.booking_line_id = booking_line.id
                price_unit = price_id.price
            return price_unit
        else:
            return super(Folio, self).get_price_unit(booking_line, day)

    def write(self, vals):
        res = super(Folio, self).write(vals)
        if self.hotel_id.enable_ezee and self.booking_id.ezee_apply_daily_price:
            update_inventory = False
            if vals.get('state', False):
                if vals['state'] == 'cancelled':
                    update_inventory = True
            elif vals.get('new_check_in', False) or vals.get('new_check_out', False):
                update_inventory = True
            if update_inventory:
                wizard = self.env['ezee.connector'].create({
                    'date_from': self.check_in_date,
                    'date_to': self.check_out_date,
                    'action_type': 'update_inventory',
                    'company_id': self.company_id.id,
                    'room_type_ids': [(6, 0, self.room_type_id.ids)],
                })
                wizard.button_search()
                wizard.button_update_inventory()
                self.env['audit.trails'].create({
                    'booking_id': self.booking_id.id,
                    'folio_id': self.id,
                    'user_id': self.env.user.id,
                    'operation': 'ezee',
                    'datetime': fields.Datetime.now(),
                    'notes': wizard.note
                })
        return res
